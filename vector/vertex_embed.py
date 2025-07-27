from vertexai.language_models import TextEmbeddingModel


from google import genai
from google.genai.types import EmbedContentConfig

client = genai.Client()
def embed_text_gemini(text: str) -> list:
    response = client.models.embed_content(
    model="gemini-embedding-001",
    contents=text,
    config=EmbedContentConfig(
        output_dimensionality=1408,  
    ),
)
    return response.embeddings[0].values  
