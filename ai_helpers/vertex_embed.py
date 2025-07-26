import os
from google.cloud import aiplatform_v1beta1

# Set Google Application Credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./vertexkey.json"

# Initialize Vertex AI client
client = aiplatform_v1beta1.PredictionServiceClient()

# Model endpoint for public multimodal embedding
VERTEX_MODEL = (
    "projects/cloud-ml-public/locations/us-central1/publishers/google/models/multimodalembedding@001"
)

def embed_text_and_image(text: str, image_url: str):
    """Generate multimodal embedding for a text + image pair using Vertex AI public model."""
    instance = {
        "content": {
            "parts": [
                {"text": text},
                {"file_data": {"mime_type": "image/jpeg", "file_uri": image_url}},
            ]
        }
    }

    response = client.predict(
        endpoint=VERTEX_MODEL,
        instances=[instance]
    )

    return response.predictions[0]["embedding"]
