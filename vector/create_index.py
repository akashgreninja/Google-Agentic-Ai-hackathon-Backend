# create_index.py

from google.cloud import aiplatform

# ------------------------------
# ✅ REQUIRED: Set these values
# ------------------------------
PROJECT_ID = "healthy-wares-340911"
LOCATION = "us-central1"  # or your region
INDEX_DISPLAY_NAME = "agentic-map-index"
EMBEDDING_DIMENSIONS = 1408  # for Vertex multimodal embeddings
APPROX_NEIGHBORS = 150  # default value

# ------------------------------
# 🔧 Initialize Vertex AI SDK
# ------------------------------
aiplatform.init(
    project=PROJECT_ID,
    location=LOCATION
)

# ------------------------------
# 🚀 Create Matching Engine Index
# ------------------------------
print(f"Creating Matching Engine Index '{INDEX_DISPLAY_NAME}'...")

index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name=INDEX_DISPLAY_NAME,
    dimensions=EMBEDDING_DIMENSIONS,
    approximate_neighbors_count=APPROX_NEIGHBORS,
    index_update_method="STREAM_UPDATE",  # Enables live vector upserts
    distance_measure_type="DOT_PRODUCT",  # OR use "COSINE_DISTANCE" if needed
)

# ------------------------------
# ✅ Output index resource name
# ------------------------------
print("\n✅ Index creation started. It may take 5–10 minutes.")
print(f"Resource name: {index.resource_name}")
