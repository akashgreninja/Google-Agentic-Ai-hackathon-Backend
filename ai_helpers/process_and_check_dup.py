import uuid
from typing import Dict
from google.cloud import firestore, aiplatform_v1
from google.cloud.aiplatform_v1 import IndexDatapoint, UpsertDatapointsRequest,Index ,UpsertDatapointsResponse

from vector.vertex_embed import embed_text_gemini
from vector.check_duplicate import check_duplicate_incident
from ai_helpers.helper import upsert_datapoints_to_index

# --------------- CONFIG ---------------
PROJECT_ID = "healthy-wares-340911"

INDEX_RESOURCE_PATH = f"projects/718852823294/locations/us-central1/indexes/6461418619090763776"

# --------------- CLIENTS ---------------
db = firestore.Client(project=PROJECT_ID)
index_client = aiplatform_v1.IndexServiceClient()
print(index_client)

# --------------- MAIN FUNCTION ---------------
def process_incident(incident_json: Dict) -> Dict:
    """
    Processes and checks whether an incident is duplicate.
    Stores in appropriate Firestore collection and indexes if new.
    """
    try:
        # Validate essential fields
        summary = incident_json.get("summary")
        image_url = incident_json.get("image_url")
        lat = incident_json.get("location", {}).get("lat")
        lng = incident_json.get("location", {}).get("lng")
        timestamp = incident_json.get("timestamp")
        print("Validating essential fields...")
        if not all([summary, image_url, lat, lng]):
            raise ValueError("Missing one or more required fields: summary, image_url, location.lat, location.lng")

        # Generate embedding using only essential fields
        vector = embed_text_gemini(summary+str(lat)+str(lng)+str(timestamp))
        # print("Vector generated successfully.")
        with open("vector.txt", "w") as f:
          f.write(",".join(map(str, vector)))
        # Check for duplicates using essential fields
        partial_input = {
            "summary": summary,
            "image_url": image_url,
            "location": {"lat": lat, "lng": lng},
            "timestamp": incident_json.get("timestamp")
        }

        is_duplicate = check_duplicate_incident(partial_input,vector)

        # Generate unique Firestore ID
        incident_id = str(uuid.uuid4())
        # incident_id = "021a1bf8-c735-42ee-a8f9-02b0b8e22f1e"  # For testing purposes
        print(f"Generated unique incident ID: {incident_id}")
        # Store full JSON as-is to Firestore
        # collection_name = "duplicates" if is_duplicate else "all"
        # db.collection("bangalore").document("incidents").collection(collection_name).document(incident_id).set(incident_json)
        # print("i am herer now")

        
        
        # print(datapoints)
        # Index only if not duplicate
        if not is_duplicate:
            # upsert_req = UpsertDatapointsRequest(
            #     index="projects/718852823294/locations/us-central1/indexes/6461418619090763776",
            #     datapoints=[datapoints]
                
            # )
            # print(Index.UpsertDatapoints(upsert_req)) = 1107e584-b0cb-4e17-899b-ad028320cf57

            # incident_id = "1107e584-b0cb-4e17-899b-ad028320cf57"
            upsert_datapoints_to_index(datapointId=incident_id,featureVector=vector)
            # print(upsert_req)
            # response = index_client.upsert_datapoints(request=upsert_req)
            print("done")

        return {
            "status": "duplicate" if is_duplicate else "new",
            "incident_id": incident_id
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
