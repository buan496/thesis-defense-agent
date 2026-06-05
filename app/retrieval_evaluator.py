import json
from pathlib import Path

from app.config import RAG_VECTOR_STORE_META_PATH,QUERY_EMBEDDING_CACHE_PATH
from app.vector_store_metadata import load_vector_store_metadata
from app.embeddings import create_embedding
from app.vector_store import search_vector_store
from app.vector_store_io import load_vector_store
from app.embedding_cache import (
    get_cached_embedding,
    load_embedding_cache,
    save_embedding_cache,
)


def evaluate_retrieval(
    benchmark_path: str,
    vector_store_path: str,
    top_k: int,
) -> dict:
    store = load_vector_store(vector_store_path)
    embedding_cache = load_embedding_cache(QUERY_EMBEDDING_CACHE_PATH)
    
    def cached_embedding_fn(text: str) -> list[float]:
        cached_embedding = get_cached_embedding(text, embedding_cache)

        if cached_embedding is not None:
            return cached_embedding

        embedding = create_embedding(text)
        embedding_cache[text] = embedding
        save_embedding_cache(QUERY_EMBEDDING_CACHE_PATH, embedding_cache)

        return embedding

    with open(benchmark_path, encoding="utf-8") as file:
        benchmark = json.loads(file.read())

    results = []
    scores = []

    for item in benchmark:
        query = item["query"]
        expected_keywords = item["expected_keywords"]

        search_results = search_vector_store(
            query,
            store,
            top_k=top_k,
            embedding_fn=cached_embedding_fn,
        )

        retrieved_text = "\n".join(
            result["text"] for result in search_results
        )

        hit_count = 0
        missing_keywords = []

        for keyword in expected_keywords:
            if isinstance(keyword, list):
                hit = any(option in retrieved_text for option in keyword)
                label = "/".join(keyword)
            else:
                hit = keyword in retrieved_text
                label = keyword

            if hit:
                hit_count += 1
            else:
                missing_keywords.append(label)

        score = hit_count / len(expected_keywords)
        scores.append(score)

        results.append(
            {
                "query": query,
                "hit_count": hit_count,
                "total": len(expected_keywords),
                "missing": missing_keywords,
                "score": score,
            }
        )

    average_score = sum(scores) / len(scores)

    vector_store_metadata = None

    if Path(RAG_VECTOR_STORE_META_PATH).exists():
        vector_store_metadata = load_vector_store_metadata(RAG_VECTOR_STORE_META_PATH)
    return {
        "benchmark_path": benchmark_path,
        "vector_store_path": vector_store_path,
        "vector_store_metadata": vector_store_metadata,
        "top_k": top_k,
        "average_score": average_score,
        "results": results,
    }

