import logging
import time

from openai import OpenAI
from app.config import EMBEDDING_API_KEY, EMBEDDING_BASE_URL, EMBEDDING_MODEL


logger = logging.getLogger(__name__)

def create_fake_embedding(text: str) -> list[float]:
    return [
        float(len(text)),
        float(text.count("论文")),
        float(text.count("系统")),
    ]
    
    
def create_embedding(text: str) -> list[float]:
    if not EMBEDDING_API_KEY:
        raise ValueError("EMBEDDING_API_KEY is not set")

    text = text.encode("utf-8", errors="ignore").decode("utf-8")
    
    client = OpenAI(
        api_key=EMBEDDING_API_KEY,
        base_url=EMBEDDING_BASE_URL,
    )

    max_retries = 3
    
    for attempt in range(1, max_retries + 1):
        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
            )
            return response.data[0].embedding

        except Exception as error:
            logger.warning("embedding 调用失败，第 %s 次重试: %s", attempt, error)

            if attempt == max_retries:
                raise

            time.sleep(2)