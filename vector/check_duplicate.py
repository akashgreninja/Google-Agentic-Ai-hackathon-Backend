import math
from datetime import datetime
from typing import Dict, Tuple

from google.api_core.exceptions import GoogleAPICallError, DeadlineExceeded
from google.cloud import aiplatform_v1
from google.cloud import firestore

from vector.vertex_embed import embed_text_gemini

# === CONFIG ===
PROJECT_ID = "healthy-wares-340911"
DEPLOYED_INDEX_ID = "hack_point_1753552023722"
INDEX_ENDPOINT = (
    "projects/718852823294/locations/us-central1/indexEndpoints/5648184634815545344"
)
SIMILARITY_THRESHOLD = 0.1         # You can tune this
SECONDARY_THRESHOLD = 0.15 
GEO_DISTANCE_THRESHOLD_KM = 0.5
TIME_DIFFERENCE_THRESHOLD_MIN = 30

# === CLIENTS ===
match_client = aiplatform_v1.MatchServiceClient(
    client_options={"api_endpoint": "186185309.us-central1-718852823294.vdb.vertexai.goog"}
)
db = firestore.Client(project=PROJECT_ID)


# === UTILITY FUNCTIONS ===
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def time_difference_minutes(t1: str, t2: str) -> float:
    dt1 = datetime.fromisoformat(t1.replace("Z", "+00:00"))
    dt2 = datetime.fromisoformat(t2.replace("Z", "+00:00"))
    return abs((dt1 - dt2).total_seconds() / 60)


# === MAIN FUNCTION ===
def check_duplicate_incident(incident_json: Dict,vector) -> bool:
    summary = incident_json.get("summary", "")
    lat = incident_json.get("location", {}).get("lat")
    lng = incident_json.get("location", {}).get("lng")
    timestamp = incident_json.get("timestamp")

    if not (summary and lat and lng and timestamp):
        raise ValueError("Missing required fields in incident JSON.")

    try:
        # Step 1: Embed
        # vector = embed_text_gemini(summary + f" lat:{lat} lng:{lng}")
        print("Vector generated successfully.")
        datapoint = aiplatform_v1.IndexDatapoint(
  feature_vector=vector
)       
        query = aiplatform_v1.FindNeighborsRequest.Query(
  datapoint=datapoint,

  # The number of nearest neighbors to be retrieved
  neighbor_count=10
)
        request = aiplatform_v1.FindNeighborsRequest(
    index_endpoint=INDEX_ENDPOINT,
 deployed_index_id=DEPLOYED_INDEX_ID,
  # Request can have multiple queries
  queries=[query],
  return_full_datapoint=False,
)
        print("Query prepared successfully.")

        # Step 3: Execute query
        response = match_client.find_neighbors(request=request)

# Flatten the list of neighbors
        all_neighbors = []
        distances = set()
        close_neighbors = []

        for result in response.nearest_neighbors:
            for neighbor in result.neighbors:
                distance = neighbor.distance
                datapoint_id = neighbor.datapoint.datapoint_id

                print(f"Neighbor found: {datapoint_id} with distance {distance:.4f}")

                # 1. Check similarity threshold
                if distance <= SIMILARITY_THRESHOLD:
                    print(f"✅ Duplicate: within SIMILARITY_THRESHOLD ({distance})")
                    return True, {
                        "reason": "Similarity threshold",
                        "datapoint_id": datapoint_id,
                        "distance": distance
                    }

                # 2. Check for repeated distance
                if distance in distances:
                    print(f"✅ Duplicate: same distance seen before ({distance})")
                    return True, {
                        "reason": "Repeated distance",
                        "datapoint_id": datapoint_id,
                        "distance": distance
                    }

                # 3. Track distances and close neighbors
                distances.add(distance)
                if distance <= SECONDARY_THRESHOLD:
                    close_neighbors.append({
                        "datapoint_id": datapoint_id,
                        "distance": distance
                    })

        # 4. If multiple close neighbors exist
        if len(close_neighbors) >= 2:
            print(f"✅ Duplicate: multiple close neighbors under SECONDARY_THRESHOLD ({len(close_neighbors)})")
            return True, {
                "reason": "Multiple close neighbors",
                "neighbors": close_neighbors
            }

        # No strong match found
        print("❌ No duplicate found.")
        return False, {}


        if all_neighbors:
            print("Neighbors found:", len(all_neighbors))
            return True
        else:
            print("No neighbors found.")
            return False


        
    except (GoogleAPICallError, DeadlineExceeded) as e:
        print(f"Error during query execution: {e}")
        return False