import math
from app.embeddings import create_fake_embedding

def dot_product(a: list[float],b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vectors must have the same length")

    total = 0.0

    for x, y in zip(a, b):
        total += x * y

    return total


def vector_norm(vector: list[float]) -> float:
    total = 0.0

    for value in vector:
        total += value * value

    return math.sqrt(total)


def cosine_similarity(a: list[float],b: list[float]) ->float:
    if len(a) != len(b):
        raise ValueError("Vectors must have the same length")
    
    norm_a = vector_norm(a)
    norm_b = vector_norm(b)
    
    if norm_a == 0.0 or norm_b == 0.0:
        raise ValueError("Zero vector cannot be used for cosine similarity")
    
    return dot_product(a,b) / (norm_a * norm_b)



def build_vector_store(chunks: list[dict], embedding_fn=create_fake_embedding) -> list[dict]:
    store = []

    for chunk in chunks:
        item = {
            "id": chunk["id"],
            "text": chunk["text"],
            "source": chunk["source"],
            "embedding": embedding_fn(chunk["text"]),
        }
        store.append(item)

    return store

def search_vector_store(query: str, store: list[dict], top_k: int = 3, embedding_fn=create_fake_embedding) -> list[dict]:
    query_embedding = embedding_fn(query)

    results = []

    for item in store:
        score = cosine_similarity(query_embedding, item["embedding"])

        results.append({
            "id": item["id"],
            "text": item["text"],
            "source": item["source"],
            "score": score,
        })

    results.sort(key=lambda item: item["score"], reverse=True)

    return results[:top_k]