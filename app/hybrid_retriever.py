from collections.abc import Callable

from app.bm25_retriever import search_bm25
from app.embeddings import create_fake_embedding
from app.vector_store import search_vector_store


def normalize_scores(
    results: list[dict],
    score_key: str = "score",
) -> dict[int, float]:
    if not results:
        return {}

    scores = [
        item[score_key]
        for item in results
    ]
    min_score = min(scores)
    max_score = max(scores)

    if max_score == min_score:
        return {
            item["id"]: 1.0 if max_score > 0 else 0.0
            for item in results
        }

    return {
        item["id"]: (
            item[score_key] - min_score
        ) / (max_score - min_score)
        for item in results
    }


def search_hybrid(
    query: str,
    store: list[dict],
    top_k: int = 3,
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
    embedding_fn: Callable[[str], list[float]] = create_fake_embedding,
) -> list[dict]:
    if vector_weight < 0 or bm25_weight < 0:
        raise ValueError("weights must be greater than or equal to 0")

    if vector_weight + bm25_weight == 0:
        raise ValueError("at least one weight must be greater than 0")

    candidate_count = max(top_k, len(store))
    vector_results = search_vector_store(
        query=query,
        store=store,
        top_k=candidate_count,
        embedding_fn=embedding_fn,
    )
    bm25_results = search_bm25(
        query=query,
        store=store,
        top_k=candidate_count,
    )
    normalized_vector_scores = normalize_scores(vector_results)
    normalized_bm25_scores = normalize_scores(bm25_results)
    items_by_id = {
        item["id"]: item
        for item in store
    }
    candidate_ids = (
        set(normalized_vector_scores)
        | set(normalized_bm25_scores)
    )
    results = []

    for item_id in candidate_ids:
        item = items_by_id[item_id]
        vector_score = normalized_vector_scores.get(item_id, 0.0)
        bm25_score = normalized_bm25_scores.get(item_id, 0.0)
        hybrid_score = (
            vector_weight * vector_score
            + bm25_weight * bm25_score
        )

        results.append(
            {
                "id": item["id"],
                "text": item["text"],
                "source": item["source"],
                "score": hybrid_score,
                "hybrid_score": hybrid_score,
                "vector_score": vector_score,
                "bm25_score": bm25_score,
            }
        )

    results.sort(key=lambda item: item["hybrid_score"], reverse=True)

    return results[:top_k]
