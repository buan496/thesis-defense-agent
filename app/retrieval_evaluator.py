import json
from collections.abc import Callable
from pathlib import Path

from app.config import QUERY_EMBEDDING_CACHE_PATH, RAG_VECTOR_STORE_META_PATH,EMBEDDING_MODEL
from app.vector_store_metadata import load_vector_store_metadata
from app.bm25_retriever import search_bm25
from app.embeddings import create_embedding
from app.hybrid_retriever import search_hybrid
from app.query_rewriter import rewrite_query
from app.reranker import rerank_results
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
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    embedding_cache_path: str = QUERY_EMBEDDING_CACHE_PATH,
    embedding_model: str = EMBEDDING_MODEL,
    retriever: str = "vector",
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
    use_reranker: bool = False,
    rerank_candidate_multiplier: int = 3,
    use_query_rewrite: bool = False,
    query_rewriter: Callable[[str], str] = rewrite_query,
) -> dict:
    if retriever not in {"vector", "bm25", "hybrid"}:
        raise ValueError("retriever must be vector, bm25, or hybrid")
    
    if use_reranker and rerank_candidate_multiplier <= 0:
        raise ValueError(
            "rerank_candidate_multiplier must be greater than 0"
        )

    store = load_vector_store(vector_store_path)
    embedding_cache = load_embedding_cache(
        embedding_cache_path,
        embedding_model,
    )
    cache_stats = {
        "hits": 0,
        "misses": 0,
    }
    
    def cached_embedding_fn(text: str) -> list[float]:
        cached_embedding = get_cached_embedding(text, embedding_cache)

        if cached_embedding is not None:
            cache_stats["hits"] += 1
            return cached_embedding

        cache_stats["misses"] += 1
        embedding = embedding_fn(text)
        embedding_cache["items"][text] = embedding
        save_embedding_cache(embedding_cache_path, embedding_cache)

        return embedding

    with open(benchmark_path, encoding="utf-8") as file:
        benchmark = json.loads(file.read())

    results = []
    scores = []

    for item in benchmark:
        query = item["query"]
        search_query = query_rewriter(query) if use_query_rewrite else query
        expected_keywords = item["expected_keywords"]

        candidate_top_k = top_k

        if use_reranker:
            candidate_top_k = top_k * rerank_candidate_multiplier

        search_results = search_retrieval_store(
            query=search_query,
            store=store,
            top_k=candidate_top_k,
            retriever=retriever,
            embedding_fn=cached_embedding_fn,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight,
        )

        if use_reranker:
            search_results = rerank_results(
                query=search_query,
                results=search_results,
                top_k=top_k,
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
                "rewritten_query": search_query,
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
        "embedding_cache": {
            "model": embedding_model,
            "hits": cache_stats["hits"],
            "misses": cache_stats["misses"],
        },
        "top_k": top_k,
        "retriever": retriever,
        "vector_weight": vector_weight,
        "bm25_weight": bm25_weight,
        "use_reranker": use_reranker,
        "rerank_candidate_multiplier": rerank_candidate_multiplier,
        "use_query_rewrite": use_query_rewrite,
        "average_score": average_score,
        "results": results,
    }


def compare_retrievers(
    benchmark_path: str,
    vector_store_path: str,
    top_k: int,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    embedding_cache_path: str = QUERY_EMBEDDING_CACHE_PATH,
    embedding_model: str = EMBEDDING_MODEL,
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
    use_reranker: bool = False,
    rerank_candidate_multiplier: int = 3,
    use_query_rewrite: bool = False,
    query_rewriter: Callable[[str], str] = rewrite_query,
    retrievers: list[str] | None = None,
) -> dict:
    retriever_names = retrievers or ["vector", "bm25", "hybrid"]
    reports = []

    for retriever in retriever_names:
        reports.append(
            evaluate_retrieval(
                benchmark_path=benchmark_path,
                vector_store_path=vector_store_path,
                top_k=top_k,
                embedding_fn=embedding_fn,
                embedding_cache_path=embedding_cache_path,
                embedding_model=embedding_model,
                retriever=retriever,
                vector_weight=vector_weight,
                bm25_weight=bm25_weight,
                use_reranker=use_reranker,
                rerank_candidate_multiplier=rerank_candidate_multiplier,
                use_query_rewrite=use_query_rewrite,
                query_rewriter=query_rewriter,
            )
        )

    best_report = max(
        reports,
        key=lambda report: report["average_score"],
    ) if reports else None

    return {
        "benchmark_path": benchmark_path,
        "vector_store_path": vector_store_path,
        "top_k": top_k,
        "vector_weight": vector_weight,
        "bm25_weight": bm25_weight,
        "use_reranker": use_reranker,
        "rerank_candidate_multiplier": rerank_candidate_multiplier,
        "use_query_rewrite": use_query_rewrite,
        "best_retriever": (
            best_report["retriever"]
            if best_report is not None
            else None
        ),
        "reports": reports,
    }


def scan_hybrid_weights(
    benchmark_path: str,
    vector_store_path: str,
    top_k: int,
    weight_pairs: list[tuple[float, float]] | None = None,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    embedding_cache_path: str = QUERY_EMBEDDING_CACHE_PATH,
    embedding_model: str = EMBEDDING_MODEL,
    use_reranker: bool = False,
    rerank_candidate_multiplier: int = 3,
    use_query_rewrite: bool = False,
    query_rewriter: Callable[[str], str] = rewrite_query,
) -> dict:
    pairs = weight_pairs or [
        (1.0, 0.0),
        (0.8, 0.2),
        (0.7, 0.3),
        (0.5, 0.5),
        (0.3, 0.7),
        (0.0, 1.0),
    ]
    reports = []

    for vector_weight, bm25_weight in pairs:
        reports.append(
            evaluate_retrieval(
                benchmark_path=benchmark_path,
                vector_store_path=vector_store_path,
                top_k=top_k,
                embedding_fn=embedding_fn,
                embedding_cache_path=embedding_cache_path,
                embedding_model=embedding_model,
                retriever="hybrid",
                vector_weight=vector_weight,
                bm25_weight=bm25_weight,
                use_reranker=use_reranker,
                rerank_candidate_multiplier=rerank_candidate_multiplier,
                use_query_rewrite=use_query_rewrite,
                query_rewriter=query_rewriter,
            )
        )

    best_report = max(
        reports,
        key=lambda report: report["average_score"],
    ) if reports else None

    return {
        "benchmark_path": benchmark_path,
        "vector_store_path": vector_store_path,
        "top_k": top_k,
        "use_reranker": use_reranker,
        "rerank_candidate_multiplier": rerank_candidate_multiplier,
        "use_query_rewrite": use_query_rewrite,
        "best_vector_weight": (
            best_report["vector_weight"]
            if best_report is not None
            else None
        ),
        "best_bm25_weight": (
            best_report["bm25_weight"]
            if best_report is not None
            else None
        ),
        "best_average_score": (
            best_report["average_score"]
            if best_report is not None
            else None
        ),
        "reports": reports,
    }


def search_retrieval_store(
    query: str,
    store: list[dict],
    top_k: int,
    retriever: str,
    embedding_fn: Callable[[str], list[float]],
    vector_weight: float,
    bm25_weight: float,
) -> list[dict]:
    if retriever == "vector":
        return search_vector_store(
            query,
            store,
            top_k=top_k,
            embedding_fn=embedding_fn,
        )

    if retriever == "bm25":
        return search_bm25(
            query,
            store,
            top_k=top_k,
        )

    if retriever == "hybrid":
        return search_hybrid(
            query=query,
            store=store,
            top_k=top_k,
            embedding_fn=embedding_fn,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight,
        )

    raise ValueError("retriever must be vector, bm25, or hybrid")

