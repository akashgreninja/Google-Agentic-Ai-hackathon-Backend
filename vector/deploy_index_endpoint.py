# deploy_index_endpoint.py

from google.cloud import aiplatform

# ------------------------------
# ✅ REQUIRED: Set these values
# ------------------------------
PROJECT_ID = "your-gcp-project-id"
LOCATION = "us-central1"  # or your region
INDEX_RESOURCE_NAME = "projects/your-gcp-project-id/locations/us-central1/indexes/1234567890123456789"
INDEX_DISPLAY_NAME = "agentic-map-endpoint"
DEPLOYED_INDEX_ID = "agentic-map-deployed"

# ------------------------------
# 🔧 Initialize Vertex AI SDK
# ------------------------------
aiplatform.init(
    project=PROJECT_ID,
    location=LOCATION
)

# ------------------------------
# 🚀 Create the Endpoint
# ------------------------------
print(f"Creating Index Endpoint: {INDEX_DISPLAY_NAME}")

endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
    display_name=INDEX_DISPLAY_NAME,
    public_endpoint_enabled=True,  # Allow external access
)

print(f"\n✅ Endpoint created: {endpoint.resource_name}")

# ------------------------------
# 📦 Deploy Index to the Endpoint
# ------------------------------
print("\nDeploying index to endpoint...")

endpoint.deploy_index(
    index=INDEX_RESOURCE_NAME,
    deployed_index_id=DEPLOYED_INDEX_ID,
    traffic_split={"0": 100}
)

print(f"\n✅ Index deployed to endpoint '{INDEX_DISPLAY_NAME}' with deployed index ID: {DEPLOYED_INDEX_ID}")
print(f"🚀 Endpoint resource name: {endpoint.resource_name}")
