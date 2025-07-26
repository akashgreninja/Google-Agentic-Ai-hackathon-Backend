from vertexai.language_models import TextEmbeddingModel

# def embed_text_gemini(text: str) -> list:
#     model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
#     embeddings = model.get_embeddings([text])
#     print(len(embeddings[0].values))
#     return embeddings[0].values 
# # === CONFIG ===
# PROJECT_ID = "healthy-wares-340911"  # 🔁 Replace with your actual GCP project ID
# DEPLOYED_INDEX_ID = "hack_endpoint_1753532741674"  # Your deployed index ID
# INDEX_ENDPOINT_NAME = (
#     "projects/718852823294/locations/us-central1/indexEndpoints/5648184634815545344"
# )  # 🔁 Replace this too


from google import genai
from google.genai.types import EmbedContentConfig

client = genai.Client()
def embed_text_gemini(text: str) -> list:
    response = client.models.embed_content(
    model="gemini-embedding-001",
    contents=text,
    config=EmbedContentConfig(
        # task_type="RETRIEVAL_DOCUMENT",  # Optional
        output_dimensionality=1408,  # Optional
        # title="Driver's License",  # Optional
    ),
)
    print(len(response.embeddings[0].values))
    return response.embeddings[0].values  # Assuming the first embedding is what you need
# Example response:
# embeddings=[ContentEmbedding(values=[-0.06302902102470398, 0.00928034819662571, 0.014716853387653828, -0.028747491538524628, ... ],
# statistics=ContentEmbeddingStatistics(truncated=False, token_count=13.0))]
# metadata=EmbedContentMetadata(billable_character_count=112)