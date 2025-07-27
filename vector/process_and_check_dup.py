import uuid
from typing import Dict
from google.cloud import firestore, aiplatform_v1
from google.cloud.aiplatform_v1 import IndexDatapoint, UpsertDatapointsRequest,Index ,UpsertDatapointsResponse

from vector.vertex_embed import embed_text_gemini
from vector.check_duplicate import check_duplicate_incident
from vector.helper import upsert_datapoints_to_index

PROJECT_ID = "healthy-wares-340911"

INDEX_RESOURCE_PATH = f"projects/718852823294/locations/us-central1/indexes/6461418619090763776"

db = firestore.Client(project=PROJECT_ID)
index_client = aiplatform_v1.IndexServiceClient()
print(index_client)

def process_incident(incident_json: Dict) -> Dict:
    """
    Processes and checks whether an incident is duplicate.
    Stores in appropriate Firestore collection and indexes if new.
    """
    try:
        summary = incident_json.get("summary")
        image_url = incident_json.get("image_url")
        lat = incident_json.get("location", {}).get("lat")
        lng = incident_json.get("location", {}).get("lng")
        timestamp = incident_json.get("timestamp")
        print("Validating essential fields...")
        if not all([summary, image_url, lat, lng]):
            raise ValueError("Missing one or more required fields: summary, image_url, location.lat, location.lng")

        vector = embed_text_gemini(summary+str(lat)+str(lng)+str(timestamp))
        with open("vector.txt", "w") as f:
          f.write(",".join(map(str, vector)))
        partial_input = {
            "summary": summary,
            "image_url": image_url,
            "location": {"lat": lat, "lng": lng},
            "timestamp": incident_json.get("timestamp")
        }

        is_duplicate = check_duplicate_incident(partial_input,vector)

        incident_id = str(uuid.uuid4())
        print(f"Generated unique incident ID: {incident_id}")
        
        if not is_duplicate:
       
            upsert_datapoints_to_index(datapointId=incident_id,featureVector=vector)
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
