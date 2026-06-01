from openai import OpenAI
from app.config import EMBEDDING_API_KEY, EMBEDDING_BASE_URL, EMBEDDING_MODEL

def create_fake_embedding(text: str) -> list[float]:
    return [
        float(len(text)),
        float(text.count("论文")),
        float(text.count("系统")),
    ]
    
    
def create_embedding(text: str) -> list[float]:
    if not EMBEDDING_API_KEY:
        raise ValueError("EMBEDDING_API_KEY is not set")

    client = OpenAI(
        api_key=EMBEDDING_API_KEY,
        base_url=EMBEDDING_BASE_URL,
    )

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )

    return response.data[0].embedding