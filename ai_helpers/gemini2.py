import firebase_admin
from firebase_admin import firestore, credentials
from geopy.distance import geodesic
from typing import List, Dict, Tuple
import os
from google import genai


class GeminiCityDataGetter:
    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate("./firebasekey.json")
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()


    def get_relevant_incidents(
        self,
        user_id: str = None,
        user_location: Tuple[float, float] = None,
        radius_km: float = 10
    ) -> List[Dict]:
        """
        Fetches incidents from Firestore within a radius of the user location.
        - Always includes incidents in PRIORITY_CATEGORIES.
        - Filters other incidents by user's interests (if provided).
        - Sorts all by interest priority (if applicable) and distance.
        """
        PRIORITY_CATEGORIES = [
            "Flood", "Power Cut", "Road Block", "Accident", "Fire", "Flash Mob", "Garbage", "Tree Fall", "Stampede"
        ]

        # Step 1: Get user interests if user_id is provided
        interests = None
        if user_id:
            user_doc = self.db.collection("users").document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                interests = user_data.get("interests")

        def interest_priority(category):
            if not interests:
                return float('inf')  # If no interests, deprioritize
            try:
                return interests.index(category)
            except ValueError:
                return float('inf')

        priority_incidents = []
        other_incidents = []

        events = self.db.collection("bangalore").document("incidents").collection("all").stream()

        for doc in events:
            data = doc.to_dict()
            location = data.get("location")

            if not location:
                continue

            # Handle location types (GeoPoint or dict)
            if isinstance(location, dict):
                inc_lat = location.get("lat")
                inc_lng = location.get("lng")
            else:
                inc_lat = getattr(location, "latitude", None)
                inc_lng = getattr(location, "longitude", None)

            if inc_lat is None or inc_lng is None:
                continue

            # Filter by distance
            if user_location:
                distance_km = geodesic(user_location, (inc_lat, inc_lng)).km
                if distance_km > radius_km:
                    continue
                data["distance"] = distance_km
            else:
                data["distance"] = 0  # fallback

            category = data.get("category")
            incident = {"id": doc.id, **data}

            # Always include priority categories
            if category in PRIORITY_CATEGORIES:
                priority_incidents.append(incident)
            # Include only interested categories for others
            elif not interests or category in interests:
                other_incidents.append(incident)

        # Sort by interest and distance
        def sort_key(x):
            return (interest_priority(x.get("category")), x.get("distance", 0))

        priority_incidents.sort(key=sort_key)
        other_incidents.sort(key=sort_key)

        all_incidents = priority_incidents + other_incidents

        # Add AI-generated titles to each incident
        if all_incidents:
            pre_prompt = (
                "You are a smart civic assistant. For each of the following incident reports, generate a short, informative **title** summarizing the issue. "
                "Base it on severity (like 'Fire' > 'Garbage'), category, area, and count. "
                "Return a JSON list of titles, matching the order of incidents given. DO NOT include anything else.\n\n"
                "Examples:\n"
                "[{'category': 'Flood', 'area': 'Indiranagar', 'count': 3, 'summary': 'Water overflowed onto roads.'}] → ['Flooding in Indiranagar - 3 Reports']\n\n"
                "Input:\n" + str([
                    {
                        "category": inc.get("category"),
                        "area": inc.get("area"),
                        "count": inc.get("count", 1),
                        "summary": inc.get("summary", "")
                    } for inc in all_incidents
                ]) + "\n\nOutput (JSON list of titles):"
            )

            client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[pre_prompt]
                )
                import json
                titles = json.loads(response.text.strip())
                for incident, title in zip(all_incidents, titles):
                    incident["title"] = title
            except Exception as e:
                # Fallback: Add default title if Gemini fails
                for incident in all_incidents:
                    incident["title"] = f"{incident.get('category', 'Incident')} in {incident.get('area', 'Unknown Area')}"

        return all_incidents

    def get_incidents_along_route(
        self,
        src_lat: float,
        src_lng: float,
        dest_lat: float,
        dest_lng: float,
        step_km: float = 2,
        corridor_radius_km: float = 1.5
    ) -> List[Dict]:
        """
        Fetch incidents that occur along the route between source and destination.

        Args:```````````````````````````````````````````````````````````````
            src_lat (float): Source latitude.
            src_lng (float): Source longitude.
            dest_lat (float): Destination latitude.
            dest_lng (float): Destination longitude.
            step_km (float): Distance between interpolation waypoints.
            corridor_radius_km (float): Radius around waypoints to consider.

        Returns:
            List[dict]: Incidents near the defined route corridor.
        """
        # creates straight line from A-B 
        def interpolate_points(
            lat1: float, lng1: float, lat2: float, lng2: float, steps: int
        ) -> List[Tuple[float, float]]:
            return [
                (
                    lat1 + (lat2 - lat1) * i / steps,
                    lng1 + (lng2 - lng1) * i / steps
                )
                for i in range(steps + 1)
            ]

        total_distance = geodesic((src_lat, src_lng), (dest_lat, dest_lng)).km
        steps = max(1, int(total_distance // step_km))
        waypoints = interpolate_points(src_lat, src_lng, dest_lat, dest_lng, steps)

        seen_ids = set()
        matched_incidents = []

        # Search in the correct collection: 'all' instead of 'events'
        all_incidents = self.db.collection("bangalore").document("incidents").collection("all").stream()

        for doc in all_incidents:
            data = doc.to_dict()
            incident_location = data.get("location")
            if not incident_location or doc.id in seen_ids:
                continue

            for lat, lng in waypoints:
                # Support both dict and GeoPoint for location
                if isinstance(incident_location, dict):
                    inc_lat = incident_location.get("lat")
                    inc_lng = incident_location.get("lng")
                else:
                    inc_lat = getattr(incident_location, "latitude", None)
                    inc_lng = getattr(incident_location, "longitude", None)
                if inc_lat is None or inc_lng is None:
                    continue
                dist = geodesic((lat, lng), (inc_lat, inc_lng)).km
                if dist <= corridor_radius_km:
                    matched_incidents.append({**data, "distance_from_route": dist})
                    seen_ids.add(doc.id)
                    break  # No need to check other waypoints for this incident

        return matched_incidents

    def agentic_predictive_analysis(self, incidents: List[Dict]) -> str:
        # Group and summarize issues
        issues = []
        for inc in incidents:
            cat = inc.get("category", "Unknown")
            count = inc.get("count", 1)
            area = inc.get("area", "Unknown Area")
            summary = inc.get("summary", "")
            issues.append(f"Category: {cat}, Area: {area}, Count: {count}, Summary: {summary}")
        issues_str = "\n".join(issues)
        pre_prompt = (
            f"You are an AI city safety assistant. Given the following event reports for the area around latitude {incidents[0].get('location', {}).get('lat', 'N/A')} and longitude {incidents[0].get('location', {}).get('lng', 'N/A')}, respond in a single sentence: 'Avoid <area> <road/region if available> because <reason>'. Use the most urgent and relevant issue for this location. Do not add extra explanation.\n\n"
            "Event Reports:\n" + issues_str + "\n\nOutput:"
        )
        # Call Gemini
        client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[pre_prompt]
            )
            return response.text
        except Exception as e:
            return f"Gemini API error: {str(e)}"
