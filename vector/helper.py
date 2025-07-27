import json
import requests
from google.auth import default
from google.auth.transport.requests import Request

def upsert_datapoints_to_index(datapointId,featureVector: list):
 
    project_id = "healthy-wares-340911"
    location = "us-central1"
    index_id = "6461418619090763776"
    service_endpoint = f"https://{location}-aiplatform.googleapis.com"
    index_resource = f"projects/{project_id}/locations/{location}/indexes/{index_id}"
    url = f"{service_endpoint}/v1/{index_resource}:upsertDatapoints"

    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    access_token = credentials.token

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {"datapoints":[{"datapointId" :datapointId,
                "featureVector": featureVector}
]}
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        print("✅ Upsert successful.")
        return response.json()
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return {"error": response.text, "status": response.status_code}
