from collections.abc import Callable

from app.config import RAG_TOP_K, RAG_VECTOR_STORE_PATH
from app.embeddings import create_embedding
from app.vector_store import search_vector_store
from app.vector_store_io import load_vector_store


def search_thesis(
    query: str,
    top_k: int = RAG_TOP_K,
    vector_store_path: str = RAG_VECTOR_STORE_PATH,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
) -> list[dict]:
    if not query.strip():
        raise ValueError("query 不能为空")

    if not 1 <= top_k <= 10:
        raise ValueError("top_k 必须在 1 到 10 之间")

    store = load_vector_store(vector_store_path)

    return search_vector_store(
        query=query,
        store=store,
        top_k=top_k,
        embedding_fn=embedding_fn,
    )