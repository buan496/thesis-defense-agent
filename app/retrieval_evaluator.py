import json
import time
from collections.abc import Callable
from pathlib import Path

from app.config import (
    EMBEDDING_MODEL,
    MILVUS_COLLECTION,
    MILVUS_METRIC_TYPE,
    MILVUS_TOKEN,
    MILVUS_URI,
    MILVUS_VECTOR_SIZE,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    QDRANT_DISTANCE,
    QDRANT_URL,
    QDRANT_VECTOR_SIZE,
    QUERY_EMBEDDING_CACHE_PATH,
    RAG_VECTOR_STORE_META_PATH,
)
from app.vector_store_metadata import load_vector_store_metadata
from app.bm25_retriever import search_bm25
from app.embeddings import create_embedding
from app.hybrid_retriever import search_hybrid
from app.llm_query_rewriter import rewrite_query_with_llm
from app.multi_query_rewriter import generate_multi_queries
from app.model_reranker import rerank_results_with_model
from app.query_rewriter import rewrite_query
from app.reranker import rerank_results
from app.vector_store import search_vector_store
from app.vector_store_repository import (
    JsonVectorStoreRepository,
    MilvusVectorStoreRepository,
    QdrantVectorStoreRepository,
    VectorStoreRepository,
)
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
    use_model_reranker: bool = False,
    model_rerank_candidate_multiplier: int = 3,
    model_reranker_scorer: Callable[[str, dict], float] | None = None,
    use_query_rewrite: bool = False,
    query_rewriter: Callable[[str], str] = rewrite_query,
    use_llm_query_rewrite: bool = False,
    llm_query_rewriter: Callable[[str], str] = rewrite_query_with_llm,
    use_multi_query: bool = False,
    multi_query_generator: Callable[[str], list[str]] = generate_multi_queries,
    vector_store_repository: VectorStoreRepository | None = None,
) -> dict:
    if retriever not in {"vector", "bm25", "hybrid"}:
        raise ValueError("retriever must be vector, bm25, or hybrid")
    
    if use_reranker and rerank_candidate_multiplier <= 0:
        raise ValueError(
            "rerank_candidate_multiplier must be greater than 0"
        )
    
    if use_model_reranker and model_rerank_candidate_multiplier <= 0:
        raise ValueError(
            "model_rerank_candidate_multiplier must be greater than 0"
        )
    
    if use_reranker and use_model_reranker:
        raise ValueError(
            "use_reranker and use_model_reranker cannot both be true"
        )
    
    if use_query_rewrite and use_llm_query_rewrite:
        raise ValueError(
            "use_query_rewrite and use_llm_query_rewrite cannot both be true"
        )

    repository = vector_store_repository or JsonVectorStoreRepository(
        vector_store_path
    )
    store = repository.load()
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
        if use_query_rewrite:
            search_query = query_rewriter(query)
        elif use_llm_query_rewrite:
            search_query = llm_query_rewriter(query)
        else:
            search_query = query
        search_queries = (
            multi_query_generator(search_query)
            if use_multi_query
            else [search_query]
        )
        expected_keywords = item["expected_keywords"]

        candidate_top_k = top_k

        if use_reranker:
            candidate_top_k = top_k * rerank_candidate_multiplier
        
        if use_model_reranker:
            candidate_top_k = top_k * model_rerank_candidate_multiplier

        search_results = search_multi_query_store(
            queries=search_queries,
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
        
        if use_model_reranker:
            if model_reranker_scorer is None:
                search_results = rerank_results_with_model(
                    query=search_query,
                    results=search_results,
                    top_k=top_k,
                )
            else:
                search_results = rerank_results_with_model(
                    query=search_query,
                    results=search_results,
                    top_k=top_k,
                    scorer=model_reranker_scorer,
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
                "search_queries": search_queries,
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
        "use_model_reranker": use_model_reranker,
        "model_rerank_candidate_multiplier": (
            model_rerank_candidate_multiplier
        ),
        "use_query_rewrite": use_query_rewrite,
        "use_llm_query_rewrite": use_llm_query_rewrite,
        "use_multi_query": use_multi_query,
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
    use_model_reranker: bool = False,
    model_rerank_candidate_multiplier: int = 3,
    model_reranker_scorer: Callable[[str, dict], float] | None = None,
    use_query_rewrite: bool = False,
    query_rewriter: Callable[[str], str] = rewrite_query,
    use_llm_query_rewrite: bool = False,
    llm_query_rewriter: Callable[[str], str] = rewrite_query_with_llm,
    use_multi_query: bool = False,
    multi_query_generator: Callable[[str], list[str]] = generate_multi_queries,
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
                use_model_reranker=use_model_reranker,
                model_rerank_candidate_multiplier=(
                    model_rerank_candidate_multiplier
                ),
                model_reranker_scorer=model_reranker_scorer,
                use_query_rewrite=use_query_rewrite,
                query_rewriter=query_rewriter,
                use_llm_query_rewrite=use_llm_query_rewrite,
                llm_query_rewriter=llm_query_rewriter,
                use_multi_query=use_multi_query,
                multi_query_generator=multi_query_generator,
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
        "use_model_reranker": use_model_reranker,
        "model_rerank_candidate_multiplier": (
            model_rerank_candidate_multiplier
        ),
        "use_query_rewrite": use_query_rewrite,
        "use_llm_query_rewrite": use_llm_query_rewrite,
        "use_multi_query": use_multi_query,
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
    use_model_reranker: bool = False,
    model_rerank_candidate_multiplier: int = 3,
    model_reranker_scorer: Callable[[str, dict], float] | None = None,
    use_query_rewrite: bool = False,
    query_rewriter: Callable[[str], str] = rewrite_query,
    use_llm_query_rewrite: bool = False,
    llm_query_rewriter: Callable[[str], str] = rewrite_query_with_llm,
    use_multi_query: bool = False,
    multi_query_generator: Callable[[str], list[str]] = generate_multi_queries,
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
                use_model_reranker=use_model_reranker,
                model_rerank_candidate_multiplier=(
                    model_rerank_candidate_multiplier
                ),
                model_reranker_scorer=model_reranker_scorer,
                use_query_rewrite=use_query_rewrite,
                query_rewriter=query_rewriter,
                use_llm_query_rewrite=use_llm_query_rewrite,
                llm_query_rewriter=llm_query_rewriter,
                use_multi_query=use_multi_query,
                multi_query_generator=multi_query_generator,
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
        "use_model_reranker": use_model_reranker,
        "model_rerank_candidate_multiplier": (
            model_rerank_candidate_multiplier
        ),
        "use_query_rewrite": use_query_rewrite,
        "use_llm_query_rewrite": use_llm_query_rewrite,
        "use_multi_query": use_multi_query,
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


def compare_retrieval_strategies(
    benchmark_path: str,
    vector_store_path: str,
    top_k: int,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    embedding_cache_path: str = QUERY_EMBEDDING_CACHE_PATH,
    embedding_model: str = EMBEDDING_MODEL,
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
    rerank_candidate_multiplier: int = 3,
    model_rerank_candidate_multiplier: int = 3,
    model_reranker_scorer: Callable[[str, dict], float] | None = None,
    query_rewriter: Callable[[str], str] = rewrite_query,
    llm_query_rewriter: Callable[[str], str] = rewrite_query_with_llm,
    multi_query_generator: Callable[[str], list[str]] = generate_multi_queries,
    include_expensive: bool = False,
) -> dict:
    strategies = [
        {
            "strategy_name": "hybrid",
        },
        {
            "strategy_name": "hybrid+query_rewrite",
            "use_query_rewrite": True,
        },
        {
            "strategy_name": "hybrid+multi_query",
            "use_multi_query": True,
        },
        {
            "strategy_name": "hybrid+query_rewrite+multi_query",
            "use_query_rewrite": True,
            "use_multi_query": True,
        },
        {
            "strategy_name": "hybrid+reranker",
            "use_reranker": True,
        },
    ]

    if include_expensive:
        strategies.extend(
            [
                {
                    "strategy_name": "hybrid+model_reranker",
                    "use_model_reranker": True,
                },
                {
                    "strategy_name": "hybrid+llm_query_rewrite",
                    "use_llm_query_rewrite": True,
                },
                {
                    "strategy_name": "hybrid+llm_query_rewrite+multi_query",
                    "use_llm_query_rewrite": True,
                    "use_multi_query": True,
                },
            ]
        )

    reports = []

    for strategy in strategies:
        report = evaluate_retrieval(
            benchmark_path=benchmark_path,
            vector_store_path=vector_store_path,
            top_k=top_k,
            embedding_fn=embedding_fn,
            embedding_cache_path=embedding_cache_path,
            embedding_model=embedding_model,
            retriever="hybrid",
            vector_weight=vector_weight,
            bm25_weight=bm25_weight,
            use_reranker=strategy.get("use_reranker", False),
            rerank_candidate_multiplier=rerank_candidate_multiplier,
            use_model_reranker=strategy.get("use_model_reranker", False),
            model_rerank_candidate_multiplier=(
                model_rerank_candidate_multiplier
            ),
            model_reranker_scorer=model_reranker_scorer,
            use_query_rewrite=strategy.get("use_query_rewrite", False),
            query_rewriter=query_rewriter,
            use_llm_query_rewrite=strategy.get(
                "use_llm_query_rewrite",
                False,
            ),
            llm_query_rewriter=llm_query_rewriter,
            use_multi_query=strategy.get("use_multi_query", False),
            multi_query_generator=multi_query_generator,
        )
        report["strategy_name"] = strategy["strategy_name"]
        reports.append(report)

    best_report = max(
        reports,
        key=lambda report: report["average_score"],
    ) if reports else None

    return {
        "benchmark_path": benchmark_path,
        "vector_store_path": vector_store_path,
        "top_k": top_k,
        "retriever": "hybrid",
        "vector_weight": vector_weight,
        "bm25_weight": bm25_weight,
        "rerank_candidate_multiplier": rerank_candidate_multiplier,
        "model_rerank_candidate_multiplier": (
            model_rerank_candidate_multiplier
        ),
        "include_expensive": include_expensive,
        "best_strategy": (
            best_report["strategy_name"]
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


def evaluate_vector_store_repository(
    benchmark_path: str,
    repository: VectorStoreRepository,
    repository_name: str,
    top_k: int,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    embedding_cache_path: str = QUERY_EMBEDDING_CACHE_PATH,
    embedding_model: str = EMBEDDING_MODEL,
) -> dict:
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
    durations = []

    for item in benchmark:
        query = item["query"]
        expected_keywords = item["expected_keywords"]
        started_at = time.perf_counter()
        search_results = repository.search(
            query=query,
            top_k=top_k,
            embedding_fn=cached_embedding_fn,
        )
        duration_ms = (time.perf_counter() - started_at) * 1000
        durations.append(duration_ms)
        score_report = score_retrieved_keywords(
            retrieved_text="\n".join(
                result["text"] for result in search_results
            ),
            expected_keywords=expected_keywords,
        )
        scores.append(score_report["score"])

        results.append(
            {
                "query": query,
                "hit_count": score_report["hit_count"],
                "total": score_report["total"],
                "missing": score_report["missing"],
                "score": score_report["score"],
                "duration_ms": duration_ms,
                "result_count": len(search_results),
            }
        )

    total_duration_ms = sum(durations)
    average_duration_ms = (
        total_duration_ms / len(durations)
        if durations
        else 0.0
    )

    return {
        "benchmark_path": benchmark_path,
        "repository": repository_name,
        "top_k": top_k,
        "average_score": sum(scores) / len(scores) if scores else 0.0,
        "average_duration_ms": average_duration_ms,
        "total_duration_ms": total_duration_ms,
        "embedding_cache": {
            "model": embedding_model,
            "hits": cache_stats["hits"],
            "misses": cache_stats["misses"],
        },
        "results": results,
    }


def compare_vector_store_repositories(
    benchmark_path: str,
    vector_store_path: str,
    top_k: int,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    embedding_cache_path: str = QUERY_EMBEDDING_CACHE_PATH,
    embedding_model: str = EMBEDDING_MODEL,
    repositories: dict[str, VectorStoreRepository] | None = None,
    qdrant_url: str = QDRANT_URL,
    qdrant_collection: str = QDRANT_COLLECTION,
    qdrant_vector_size: int = QDRANT_VECTOR_SIZE,
    qdrant_distance: str = QDRANT_DISTANCE,
    qdrant_api_key: str = QDRANT_API_KEY,
    include_milvus: bool = False,
    milvus_uri: str = MILVUS_URI,
    milvus_collection: str = MILVUS_COLLECTION,
    milvus_vector_size: int = MILVUS_VECTOR_SIZE,
    milvus_metric_type: str = MILVUS_METRIC_TYPE,
    milvus_token: str = MILVUS_TOKEN,
) -> dict:
    selected_repositories = repositories or _build_vector_store_repositories(
        vector_store_path=vector_store_path,
        qdrant_url=qdrant_url,
        qdrant_collection=qdrant_collection,
        qdrant_vector_size=qdrant_vector_size,
        qdrant_distance=qdrant_distance,
        qdrant_api_key=qdrant_api_key,
        include_milvus=include_milvus,
        milvus_uri=milvus_uri,
        milvus_collection=milvus_collection,
        milvus_vector_size=milvus_vector_size,
        milvus_metric_type=milvus_metric_type,
        milvus_token=milvus_token,
    )
    reports = []

    for repository_name, repository in selected_repositories.items():
        reports.append(
            evaluate_vector_store_repository(
                benchmark_path=benchmark_path,
                repository=repository,
                repository_name=repository_name,
                top_k=top_k,
                embedding_fn=embedding_fn,
                embedding_cache_path=embedding_cache_path,
                embedding_model=embedding_model,
            )
        )

    best_report = max(
        reports,
        key=lambda report: (
            report["average_score"],
            -report["average_duration_ms"],
        ),
    ) if reports else None
    report_by_name = {
        report["repository"]: report
        for report in reports
    }
    json_report = report_by_name.get("json")
    qdrant_report = report_by_name.get("qdrant")

    score_delta = None
    duration_delta_ms = None

    if json_report is not None and qdrant_report is not None:
        score_delta = (
            qdrant_report["average_score"]
            - json_report["average_score"]
        )
        duration_delta_ms = (
            qdrant_report["average_duration_ms"]
            - json_report["average_duration_ms"]
        )

    return {
        "benchmark_path": benchmark_path,
        "vector_store_path": vector_store_path,
        "top_k": top_k,
        "best_repository": (
            best_report["repository"]
            if best_report is not None
            else None
        ),
        "score_delta_qdrant_minus_json": score_delta,
        "duration_delta_ms_qdrant_minus_json": duration_delta_ms,
        "reports": reports,
    }


def _build_vector_store_repositories(
    vector_store_path: str,
    qdrant_url: str,
    qdrant_collection: str,
    qdrant_vector_size: int,
    qdrant_distance: str,
    qdrant_api_key: str,
    include_milvus: bool,
    milvus_uri: str,
    milvus_collection: str,
    milvus_vector_size: int,
    milvus_metric_type: str,
    milvus_token: str,
) -> dict[str, VectorStoreRepository]:
    selected_repositories: dict[str, VectorStoreRepository] = {
        "json": JsonVectorStoreRepository(vector_store_path),
        "qdrant": QdrantVectorStoreRepository(
            url=qdrant_url,
            collection_name=qdrant_collection,
            vector_size=qdrant_vector_size,
            distance=qdrant_distance,
            api_key=qdrant_api_key,
        ),
    }

    if include_milvus:
        selected_repositories["milvus"] = MilvusVectorStoreRepository(
            uri=milvus_uri,
            collection_name=milvus_collection,
            vector_size=milvus_vector_size,
            metric_type=milvus_metric_type,
            token=milvus_token,
        )

    return selected_repositories


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


def score_retrieved_keywords(
    retrieved_text: str,
    expected_keywords: list,
) -> dict:
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

    total = len(expected_keywords)

    return {
        "hit_count": hit_count,
        "total": total,
        "missing": missing_keywords,
        "score": hit_count / total if total else 0.0,
    }


def search_multi_query_store(
    queries: list[str],
    store: list[dict],
    top_k: int,
    retriever: str,
    embedding_fn: Callable[[str], list[float]],
    vector_weight: float,
    bm25_weight: float,
) -> list[dict]:
    merged_results = {}

    for query in queries:
        results = search_retrieval_store(
            query=query,
            store=store,
            top_k=top_k,
            retriever=retriever,
            embedding_fn=embedding_fn,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight,
        )

        for result in results:
            result_key = _retrieval_result_key(result)
            existing_result = merged_results.get(result_key)

            if existing_result is None:
                merged_result = dict(result)
                merged_result["matched_queries"] = [query]
                merged_results[result_key] = merged_result
                continue

            existing_result["matched_queries"].append(query)

            if result.get("score", 0.0) > existing_result.get("score", 0.0):
                best_result = dict(result)
                best_result["matched_queries"] = existing_result[
                    "matched_queries"
                ]
                merged_results[result_key] = best_result

    sorted_results = sorted(
        merged_results.values(),
        key=lambda item: item.get("score", 0.0),
        reverse=True,
    )

    return sorted_results[:top_k]


def _retrieval_result_key(result: dict) -> str:
    if "id" in result:
        return f"id:{result['id']}"

    return f"{result.get('source', '')}:{result.get('text', '')}"

