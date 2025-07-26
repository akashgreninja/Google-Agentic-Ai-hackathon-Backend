import firebase_admin
import os 
from firebase_admin import credentials, firestore
from google import genai
from google.genai import types
from datetime import datetime, timedelta
from google.cloud.firestore_v1 import GeoPoint
import json
import requests
import math
from geopy.distance import geodesic

class GeminiCityAnalyzer:
    def __init__(self):
        self.client = genai.Client(api_key="")
        key_path = os.path.join(os.path.dirname(__file__), '..', 'firebasekey.json')
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(os.path.abspath(key_path))
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(d_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c  # Distance in km

    def analyze_incident(self, image_url: str, lat: float, lng: float, area: str) -> dict:
        """
        Analyze an incident from an image or video URL. If the URL is a video (e.g., ends with .mp4), upload and process as video, otherwise as image.
        """
        is_video = image_url.lower().endswith('.mp4')
        is_video = True  # For testing purposes, always treat as video
        try:
            file_response = requests.get(image_url)
            file_response.raise_for_status()
            file_bytes = file_response.content
        except Exception as e:
            return {"error": f"Failed to fetch file: {str(e)}"}

        if is_video:
            # 🔽 Step 2: Upload video to Gemini
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_vid:
                tmp_vid.write(file_bytes)
                tmp_vid.flush()
                video_path = tmp_vid.name
            try:
                myfile = self.client.files.upload(file=video_path)
            except Exception as e:
                return {"error": f"Failed to upload video to Gemini: {str(e)}"}

            # 🔽 Step 3: Gemini video prompt
            prompt = (
                "Summarize this video. Then create a quiz with an answer key based on the information in this video. "
                f"Also, classify the event as per the following categories: ['Flood', 'Pothole', 'Power Cut', 'Road Block', 'Accident', 'Fire', 'Flash Mob', 'Garbage', 'Tree Fall', 'Stampede', 'Other', "
                "'Concert', 'Cricket Match', 'Football Match', 'Marathon', 'Protest', 'Political Rally', 'Food Festival', 'Book Fair', 'Art Exhibition', 'Theatre Play', 'Movie Screening', 'Workshop', 'Seminar', 'Conference', 'Tech Meetup', 'Hackathon', 'Blood Donation Camp', 'Health Camp', 'Free Vaccination Drive', 'Lost & Found', 'Animal Rescue', 'Waterlogging', 'Traffic Jam', 'Metro Disruption', 'Public Transport Strike', 'Street Performance', 'Cultural Festival', 'Religious Procession', 'Ganesh Visarjan', 'Holi Celebration', 'Diwali Fireworks', 'Christmas Parade', 'New Year Event', 'Pottery Fair', 'Craft Fair', 'Farmers Market', 'Car Show', 'Bike Rally', 'Charity Run']\n"
                f"Return ONLY this exact JSON format:\n{{\n  'category': '...',\n  'summary': '...',\n  'severity': '...',\n  'location': {{ 'lat': {lat}, 'lng': {lng} }},\n  'timestamp': '{datetime.utcnow().isoformat()}Z',\n  'image_url': '{image_url}',\n  'area': '{area}',\n  'zipcode': '...',\n  'mood': ...,\n  'quiz': ...\n}}\nOnly return clean JSON. Do not include markdown or extra explanation."
            )
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[myfile, prompt]
                )
                result = json.loads(response.text.replace("'", '"'))
            except Exception as e:
                return {"error": f"Gemini API failed (video): {str(e)}"}
        else:
            # 🔽 Step 2: Prepare image part
            image_part = types.Part.from_bytes(data=file_bytes, mime_type="image/jpeg")
            # 🔽 Step 3: Prompt
            prompt = f"""
You are a city AI safety assistant analyzing civic incidents from citizen-submitted photos in Bengaluru. Your job is to classify events such as floods, accidents, stampedes, power outages, fire incidents, garbage accumulation, potholes, etc., and return a structured report.
Analyze the attached photo. Based on visible context, determine:
- The type of incident (use categories below)
- A short summary of the situation with actionable advice like "Avoid this area" or "Seek shelter" keep it max 15 words.
- Severity (Low, Medium, High)
- The approximate human-readable area name (e.g., "Jayanagar", "HSR Layout")
- The approximate postal code (zipcode)
- Analyze public sentiment for this event and assign a mood score from 0 (very negative) to 10 (very positive) based on likely public reaction to the incident.

Use ONLY one of the following categories:
["Flood", "Pothole", "Power Cut", "Road Block", "Accident", "Fire", "Flash Mob", "Garbage", "Tree Fall", "Stampede", "Other",
"Concert", "Cricket Match", "Football Match", "Marathon", "Protest", "Political Rally", "Food Festival", "Book Fair", "Art Exhibition", "Theatre Play", "Movie Screening", "Workshop", "Seminar", "Conference", "Tech Meetup", "Hackathon", "Blood Donation Camp", "Health Camp", "Free Vaccination Drive", "Lost & Found", "Animal Rescue", "Waterlogging", "Traffic Jam", "Metro Disruption", "Public Transport Strike", "Street Performance", "Cultural Festival", "Religious Procession", "Ganesh Visarjan", "Holi Celebration", "Diwali Fireworks", "Christmas Parade", "New Year Event", "Pottery Fair", "Craft Fair", "Farmers Market", "Car Show", "Bike Rally", "Charity Run"]

Return ONLY this exact JSON format:
{{
  "category": "...",
  "summary": "...",
  "severity": "...",
  "location": {{ "lat": {lat}, "lng": {lng} }},
  "timestamp": "{datetime.utcnow().isoformat()}Z",
  "image_url": "{image_url}",
  "area": "{area}",
  "zipcode": "...",
  "mood": ... // integer from 0 to 10
}}
Only return clean JSON. Do not include markdown or extra explanation.
"""
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[image_part, prompt]
                )
                result = json.loads(response.text)
            except Exception as e:
                return {"error": f"Gemini API failed: {str(e)}"}

        try:
            incident_data = result
            incident_data["geo"] = GeoPoint(lat, lng)

            category = incident_data.get("category")
            timestamp = datetime.utcnow()
            incident_data["timestamp"] = timestamp

            # 🔽 Step 5: Deduplication check
            fifteen_minutes_ago = timestamp - timedelta(minutes=15)
            incidents_ref = self.db.collection("bangalore").document("incidents").collection("all")
            recent_snapshots = incidents_ref.where("category", "==", category).stream()

            for doc in recent_snapshots:
                data = doc.to_dict()
                loc = data.get("location")
                ts = data.get("timestamp")

                if not loc or not ts:
                    continue

                # Convert Firestore timestamp or string to offset-naive UTC datetime
                if hasattr(ts, 'astimezone'):
                    ts = ts.astimezone(tz=None).replace(tzinfo=None)
                elif isinstance(ts, str):
                    try:
                        ts = datetime.fromisoformat(ts.replace("Z", ""))
                    except Exception:
                        continue

                if ts < fifteen_minutes_ago:
                    continue

                distance_km = self.haversine(lat, lng, loc["lat"], loc["lng"])
                if distance_km <= 0.1:  # Within 100 meters
                    # Check for existing duplicate
                    duplicates_ref = self.db.collection("bangalore").document("incidents").collection("duplicates")
                    duplicate_query = duplicates_ref.where("category", "==", category).where("location.lat", "==", loc["lat"]).where("location.lng", "==", loc["lng"]).stream()
                    count = 1
                    duplicate_doc = None
                    for dup_doc in duplicate_query:
                        duplicate_doc = dup_doc
                        dup_data = dup_doc.to_dict()
                        count = dup_data.get("count", 1) + 1
                        break
                    incident_data["count"] = count
                    if duplicate_doc:
                        # Update existing duplicate
                        duplicates_ref.document(duplicate_doc.id).set(incident_data)
                    else:
                        # Save new duplicate
                        duplicates_ref.add(incident_data)
                    print(f"Duplicate incident detected: {category} at {loc['lat']}, {loc['lng']} - Count: {count}")
                    return {"success": "True"}

            # 🔽 Step 6: Save new unique incident
            doc_ref = incidents_ref.document()
            doc_ref.set(incident_data)
            print(f"New incident saved: {category} at {lat}, {lng} with data {incident_data}")
            # Removed direct call to send_location_based_alert; now handled by FastAPI BackgroundTasks
            return {"success": True, "data": incident_data}

        except Exception as e:
            return {"error": f"Failed to upload to Firestore: {str(e)}"}


# to test this we need to add fcm token to user
    def send_location_based_alert(self, area: str, incident_data: dict):
        """
        Query Firestore for users whose saved location is within a 2 km radius of the incident's location.
        Send an FCM push notification to those users using their saved FCM tokens.
        Additionally, aggregate incidents in the last 2 hours and summarize using Gemini.
        """
        from firebase_admin import messaging
        try:
            # Step 1: Query incidents in the last 2 hours for the same area
            now = datetime.utcnow()
            two_hours_ago = now - timedelta(hours=2)
            incidents_ref = self.db.collection("bangalore").document("incidents").collection("all")
            # Get all incidents in the last 2 hours
            recent_incidents = [doc.to_dict() for doc in incidents_ref.stream()]
            filtered_incidents = []
            for inc in recent_incidents:
                ts = inc.get("timestamp")
                inc_area = inc.get("area", "")
                # Convert Firestore timestamp or string to offset-naive UTC datetime
                if hasattr(ts, 'astimezone'):
                    ts = ts.astimezone(tz=None).replace(tzinfo=None)
                elif isinstance(ts, str):
                    try:
                        ts = datetime.fromisoformat(ts.replace("Z", ""))
                    except Exception:
                        continue
                if ts and ts >= two_hours_ago and inc_area.lower() == area.lower():
                    filtered_incidents.append(inc)

            # Step 2: Aggregate by category and count
            category_counts = {}
            for inc in filtered_incidents:
                cat = inc.get("category", "Other")
                count = inc.get("count", 1)
                category_counts[cat] = category_counts.get(cat, 0) + count

            # Step 3: Prepare summary prompt for Gemini
            if category_counts:
                summary_parts = []
                for cat, cnt in category_counts.items():
                    summary_parts.append(f"{cnt} {cat}{'s' if cnt > 1 else ''}")
                summary_str = ", ".join(summary_parts)
                summary_prompt = (
                    f"There were {summary_str} reported in {area} in the last 2 hours. "
                    "Summarize this for a city alert. Mention if roads are expected to be congested or if there are any safety advisories. "
                    "Return a short, clear, human-friendly summary for a push notification."
                )
                try:
                    gemini_response = self.client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[summary_prompt]
                    )
                    summary_text = gemini_response.text.strip()
                except Exception as e:
                    summary_text = summary_prompt  # fallback to prompt if Gemini fails
            else:
                # If no recent incidents, ask Gemini to generate a city alert and actionable suggestion for this incident
                incident_summary = incident_data.get("summary", f"Incident reported in {area}.")
                incident_category = incident_data.get("category", "event")
                suggestion_prompt = (
                    f"A new {incident_category} was reported in {area}. Summary: {incident_summary}\n"
                    "Write a short city alert for this event, and add a clear actionable suggestion for citizens (e.g., avoid the area, seek shelter, expect delays, etc). "
                    "Return a short, clear, human-friendly summary for a push notification."
                )
                try:
                    gemini_response = self.client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[suggestion_prompt]
                    )
                    # Post-process Gemini's response to extract only the main summary text
                    import re
                    text = gemini_response.text.strip()
                    # Remove markdown, headers, and keep only the first non-header, non-empty paragraph
                    # Remove markdown headers and lines with only dashes
                    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("**") and not l.strip().startswith("---") and not l.strip().startswith("#")]
                    # Remove lines that are just 'City Alert:' or 'Push Notification Summary:'
                    lines = [l for l in lines if not re.match(r'^(City Alert:|Push Notification Summary:)', l, re.I)]
                    # Join lines, but only keep the first paragraph (up to a blank line)
                    summary_text = ""
                    for l in lines:
                        if summary_text:
                            summary_text += " "
                        summary_text += l
                    summary_text = summary_text.strip()
                except Exception as e:
                    summary_text = incident_summary

            # Step 4: Existing notification logic (unchanged)
            users_ref = self.db.collection("users")
            matching_users = users_ref.stream()
            print("Fetched users from Firestore")

            for user_doc in matching_users:
                user_data = user_doc.to_dict()
                user_location = user_data.get("location")
                print(f"Processing user: {user_doc.id}, Location: {user_location}")

                if user_location:
                    # Handle nested 'geo' structure
                    if 'geo' in user_location:
                        user_lat = user_location['geo'].get('lat')
                        user_lng = user_location['geo'].get('lng')
                    else:
                        user_lat = user_location.get('lat')
                        user_lng = user_location.get('lng')

                    if user_lat is not None and user_lng is not None:
                        distance_km = geodesic(
                            (incident_data["location"]["lat"], incident_data["location"]["lng"]),
                            (user_lat, user_lng)
                        ).km
                        print(f"Calculated distance: {distance_km} km for user {user_doc.id}")

                        if distance_km <= 2:  # Within 2 km radius
                            fcm_token = user_data.get("fcmToken")
                            print(f"User {user_doc.id} is within radius. FCM Token: {fcm_token}")

                            if fcm_token:
                                # Prepare FCM notification payload
                                # Ensure timestamp is a datetime object before calling isoformat
                                if isinstance(incident_data["timestamp"], str):
                                    incident_data["timestamp"] = datetime.fromisoformat(incident_data["timestamp"].replace("Z", ""))

                                # Prepare FCM notification payload
                                message = messaging.Message(
                                    data={
                                        "title": f"Incidents in {area}",
                                        "body": summary_text,
                                        "category": incident_data.get("category", ""),
                                        "summary": incident_data.get("summary", ""),
                                        "severity": incident_data.get("severity", ""),
                                        "area": area,
                                        "timestamp": incident_data["timestamp"].isoformat(),
                                    },
                                    token=fcm_token,
                                )

                                # Send FCM notification
                                response = messaging.send(message)
                                print(f"Notification sent to {fcm_token}: {response}")
                                print(f"Incident data: {summary_text}")

        except Exception as e:
            print(f"Error sending notifications: {str(e)}")
