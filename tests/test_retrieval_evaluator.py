import json

import pytest

from app.retrieval_evaluator import (
    compare_retrieval_strategies,
    compare_retrievers,
    evaluate_retrieval,
    scan_hybrid_weights,
    search_multi_query_store,
)


def fake_embedding(text: str) -> list[float]:
    if "系统架构" in text:
        return [1.0, 0.0]

    return [0.0, 1.0]


def test_evaluate_retrieval(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    embedding_cache_path = tmp_path / "query_embedding_cache.json"

    benchmark = [
        {
            "query": "系统架构包括什么？",
            "expected_keywords": ["特征处理"],
        }
    ]

    store = [
        {
            "id": 0,
            "text": "系统架构包括特征处理模块。",
            "embedding": [1.0, 0.0],
            "source": "test",
        }
    ]

    benchmark_path.write_text(
        json.dumps(benchmark, ensure_ascii=False),
        encoding="utf-8",
    )
    vector_store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )

    report = evaluate_retrieval(
        benchmark_path=str(benchmark_path),
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        embedding_cache_path=str(embedding_cache_path),
        embedding_model="test-model",
    )

    assert report["average_score"] == 1.0
    assert report["results"][0]["rewritten_query"] == (
        "系统架构包括什么？"
    )
    assert report["results"][0]["search_queries"] == [
        "系统架构包括什么？"
    ]
    assert report["results"][0]["hit_count"] == 1
    assert report["embedding_cache"]["hits"] == 0
    assert report["embedding_cache"]["misses"] == 1
    assert embedding_cache_path.exists()


def test_evaluate_retrieval_reuses_embedding_cache(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"

    benchmark = [
        {
            "query": "系统架构包括什么？",
            "expected_keywords": ["特征处理"],
        }
    ]

    store = [
        {
            "id": 0,
            "text": "系统架构包括特征处理模块。",
            "source": "test",
            "embedding": [1.0, 0.0],
        }
    ]

    benchmark_path.write_text(
        json.dumps(benchmark, ensure_ascii=False),
        encoding="utf-8",
    )
    vector_store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )

    call_count = {"value": 0}

    def counting_embedding(text: str) -> list[float]:
        call_count["value"] += 1
        return [1.0, 0.0]

    first_report = evaluate_retrieval(
        benchmark_path=str(benchmark_path),
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=counting_embedding,
        embedding_cache_path=str(cache_path),
        embedding_model="test-model",
    )
    second_report = evaluate_retrieval(
        benchmark_path=str(benchmark_path),
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=counting_embedding,
        embedding_cache_path=str(cache_path),
        embedding_model="test-model",
    )

    assert first_report["embedding_cache"]["hits"] == 0
    assert first_report["embedding_cache"]["misses"] == 1
    assert second_report["embedding_cache"]["hits"] == 1
    assert second_report["embedding_cache"]["misses"] == 0
    assert call_count["value"] == 1


def test_evaluate_retrieval_supports_bm25(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark = [
        {
            "query": "系统架构",
            "expected_keywords": ["特征处理"],
        }
    ]
    store = [
        {
            "id": 0,
            "text": "系统架构包括特征处理模块",
            "source": "test",
            "embedding": [0.0, 1.0],
        },
        {
            "id": 1,
            "text": "天气很好",
            "source": "test",
            "embedding": [1.0, 0.0],
        },
    ]
    benchmark_path.write_text(
        json.dumps(benchmark, ensure_ascii=False),
        encoding="utf-8",
    )
    vector_store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )

    report = evaluate_retrieval(
        benchmark_path=str(benchmark_path),
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        embedding_cache_path=str(cache_path),
        embedding_model="test-model",
        retriever="bm25",
    )

    assert report["retriever"] == "bm25"
    assert report["average_score"] == 1.0
    assert report["embedding_cache"]["misses"] == 0


def test_evaluate_retrieval_supports_hybrid(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark = [
        {
            "query": "系统架构",
            "expected_keywords": ["特征处理"],
        }
    ]
    store = [
        {
            "id": 0,
            "text": "系统架构包括特征处理模块",
            "source": "test",
            "embedding": [1.0, 0.0],
        },
        {
            "id": 1,
            "text": "天气很好",
            "source": "test",
            "embedding": [0.0, 1.0],
        },
    ]
    benchmark_path.write_text(
        json.dumps(benchmark, ensure_ascii=False),
        encoding="utf-8",
    )
    vector_store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )

    report = evaluate_retrieval(
        benchmark_path=str(benchmark_path),
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=lambda text: [1.0, 0.0] if "系统" in text else [0.0, 1.0],
        embedding_cache_path=str(cache_path),
        embedding_model="test-model",
        retriever="hybrid",
        vector_weight=0.6,
        bm25_weight=0.4,
    )

    assert report["retriever"] == "hybrid"
    assert report["vector_weight"] == 0.6
    assert report["bm25_weight"] == 0.4
    assert report["average_score"] == 1.0


def test_evaluate_retrieval_rejects_unknown_retriever(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark_path.write_text("[]", encoding="utf-8")
    vector_store_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        evaluate_retrieval(
            benchmark_path=str(benchmark_path),
            vector_store_path=str(vector_store_path),
            top_k=1,
            embedding_fn=fake_embedding,
            embedding_cache_path=str(cache_path),
            embedding_model="test-model",
            retriever="unknown",
        )


def test_evaluate_retrieval_supports_reranker(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark = [
        {
            "query": "系统架构 模块",
            "expected_keywords": ["特征处理"],
        }
    ]
    store = [
        {
            "id": 0,
            "text": "这是普通内容",
            "source": "test",
            "embedding": [1.0, 0.0],
        },
        {
            "id": 1,
            "text": "系统架构包括特征处理模块",
            "source": "test",
            "embedding": [0.6, 0.4],
        },
    ]
    benchmark_path.write_text(
        json.dumps(benchmark, ensure_ascii=False),
        encoding="utf-8",
    )
    vector_store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )

    report = evaluate_retrieval(
        benchmark_path=str(benchmark_path),
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=lambda text: [1.0, 0.0],
        embedding_cache_path=str(cache_path),
        embedding_model="test-model",
        use_reranker=True,
        rerank_candidate_multiplier=2,
    )

    assert report["use_reranker"] is True
    assert report["rerank_candidate_multiplier"] == 2
    assert report["average_score"] == 1.0
    assert report["results"][0]["missing"] == []


def test_evaluate_retrieval_supports_query_rewrite(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark = [
        {
            "query": "系统有哪些模块？",
            "expected_keywords": ["特征处理"],
        }
    ]
    store = [
        {
            "id": 0,
            "text": "普通内容",
            "source": "test",
            "embedding": [0.0, 1.0],
        },
        {
            "id": 1,
            "text": "系统架构包括特征处理模块",
            "source": "test",
            "embedding": [1.0, 0.0],
        },
    ]
    benchmark_path.write_text(
        json.dumps(benchmark, ensure_ascii=False),
        encoding="utf-8",
    )
    vector_store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )

    def rewrite_for_test(query: str) -> str:
        return query + " 特征处理"

    def embedding_for_test(text: str) -> list[float]:
        if "特征处理" in text:
            return [1.0, 0.0]

        return [0.0, 1.0]

    report = evaluate_retrieval(
        benchmark_path=str(benchmark_path),
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=embedding_for_test,
        embedding_cache_path=str(cache_path),
        embedding_model="test-model",
        use_query_rewrite=True,
        query_rewriter=rewrite_for_test,
    )

    assert report["use_query_rewrite"] is True
    assert report["results"][0]["query"] == "系统有哪些模块？"
    assert report["results"][0]["rewritten_query"] == (
        "系统有哪些模块？ 特征处理"
    )
    assert report["average_score"] == 1.0


def test_evaluate_retrieval_supports_llm_query_rewrite(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark = [
        {
            "query": "系统是怎么设计的？",
            "expected_keywords": ["特征处理"],
        }
    ]
    store = [
        {
            "id": 0,
            "text": "普通内容",
            "source": "test",
            "embedding": [0.0, 1.0],
        },
        {
            "id": 1,
            "text": "系统架构包括特征处理模块",
            "source": "test",
            "embedding": [1.0, 0.0],
        },
    ]
    benchmark_path.write_text(
        json.dumps(benchmark, ensure_ascii=False),
        encoding="utf-8",
    )
    vector_store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )

    def llm_rewrite_for_test(query: str) -> str:
        return "系统架构 特征处理"

    def embedding_for_test(text: str) -> list[float]:
        if "特征处理" in text:
            return [1.0, 0.0]

        return [0.0, 1.0]

    report = evaluate_retrieval(
        benchmark_path=str(benchmark_path),
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=embedding_for_test,
        embedding_cache_path=str(cache_path),
        embedding_model="test-model",
        use_llm_query_rewrite=True,
        llm_query_rewriter=llm_rewrite_for_test,
    )

    assert report["use_llm_query_rewrite"] is True
    assert report["results"][0]["query"] == "系统是怎么设计的？"
    assert report["results"][0]["rewritten_query"] == "系统架构 特征处理"
    assert report["average_score"] == 1.0


def test_evaluate_retrieval_supports_multi_query(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark = [
        {
            "query": "系统有哪些模块？",
            "expected_keywords": ["特征处理"],
        }
    ]
    store = [
        {
            "id": 0,
            "text": "普通内容",
            "source": "test",
            "embedding": [0.8, 0.2],
        },
        {
            "id": 1,
            "text": "系统架构包括特征处理模块",
            "source": "test",
            "embedding": [0.0, 1.0],
        },
    ]
    benchmark_path.write_text(
        json.dumps(benchmark, ensure_ascii=False),
        encoding="utf-8",
    )
    vector_store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )

    def multi_query_for_test(query: str) -> list[str]:
        return [query, "特征处理"]

    def embedding_for_test(text: str) -> list[float]:
        if "特征处理" in text:
            return [0.0, 1.0]

        return [1.0, 0.0]

    report = evaluate_retrieval(
        benchmark_path=str(benchmark_path),
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=embedding_for_test,
        embedding_cache_path=str(cache_path),
        embedding_model="test-model",
        use_multi_query=True,
        multi_query_generator=multi_query_for_test,
    )

    assert report["use_multi_query"] is True
    assert report["results"][0]["search_queries"] == [
        "系统有哪些模块？",
        "特征处理",
    ]
    assert report["average_score"] == 1.0


def test_evaluate_retrieval_supports_model_reranker(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark = [
        {
            "query": "系统架构包括哪些模块？",
            "expected_keywords": ["特征处理"],
        }
    ]
    store = [
        {
            "id": 0,
            "text": "普通内容",
            "source": "test",
            "embedding": [1.0, 0.0],
        },
        {
            "id": 1,
            "text": "系统架构包括特征处理模块",
            "source": "test",
            "embedding": [0.6, 0.4],
        },
    ]
    benchmark_path.write_text(
        json.dumps(benchmark, ensure_ascii=False),
        encoding="utf-8",
    )
    vector_store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )

    def fake_model_scorer(query: str, candidate: dict) -> float:
        if "特征处理" in candidate["text"]:
            return 0.95

        return 0.1

    report = evaluate_retrieval(
        benchmark_path=str(benchmark_path),
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=lambda text: [1.0, 0.0],
        embedding_cache_path=str(cache_path),
        embedding_model="test-model",
        use_model_reranker=True,
        model_rerank_candidate_multiplier=2,
        model_reranker_scorer=fake_model_scorer,
    )

    assert report["use_model_reranker"] is True
    assert report["model_rerank_candidate_multiplier"] == 2
    assert report["average_score"] == 1.0


def test_evaluate_retrieval_rejects_invalid_rerank_multiplier(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark_path.write_text("[]", encoding="utf-8")
    vector_store_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        evaluate_retrieval(
            benchmark_path=str(benchmark_path),
            vector_store_path=str(vector_store_path),
            top_k=1,
            embedding_fn=fake_embedding,
            embedding_cache_path=str(cache_path),
            embedding_model="test-model",
            use_reranker=True,
            rerank_candidate_multiplier=0,
        )


def test_evaluate_retrieval_rejects_invalid_model_rerank_multiplier(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark_path.write_text("[]", encoding="utf-8")
    vector_store_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        evaluate_retrieval(
            benchmark_path=str(benchmark_path),
            vector_store_path=str(vector_store_path),
            top_k=1,
            embedding_fn=fake_embedding,
            embedding_cache_path=str(cache_path),
            embedding_model="test-model",
            use_model_reranker=True,
            model_rerank_candidate_multiplier=0,
        )


def test_evaluate_retrieval_rejects_two_rerankers_at_once(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark_path.write_text("[]", encoding="utf-8")
    vector_store_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        evaluate_retrieval(
            benchmark_path=str(benchmark_path),
            vector_store_path=str(vector_store_path),
            top_k=1,
            embedding_fn=fake_embedding,
            embedding_cache_path=str(cache_path),
            embedding_model="test-model",
            use_reranker=True,
            use_model_reranker=True,
        )


def test_evaluate_retrieval_rejects_two_query_rewriters_at_once(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark_path.write_text("[]", encoding="utf-8")
    vector_store_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        evaluate_retrieval(
            benchmark_path=str(benchmark_path),
            vector_store_path=str(vector_store_path),
            top_k=1,
            embedding_fn=fake_embedding,
            embedding_cache_path=str(cache_path),
            embedding_model="test-model",
            use_query_rewrite=True,
            use_llm_query_rewrite=True,
        )


def test_compare_retrievers(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark = [
        {
            "query": "系统架构",
            "expected_keywords": ["特征处理"],
        }
    ]
    store = [
        {
            "id": 0,
            "text": "系统架构包括特征处理模块",
            "source": "test",
            "embedding": [1.0, 0.0],
        }
    ]
    benchmark_path.write_text(
        json.dumps(benchmark, ensure_ascii=False),
        encoding="utf-8",
    )
    vector_store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )

    report = compare_retrievers(
        benchmark_path=str(benchmark_path),
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=lambda text: [1.0, 0.0],
        embedding_cache_path=str(cache_path),
        embedding_model="test-model",
        vector_weight=0.6,
        bm25_weight=0.4,
        use_reranker=True,
        rerank_candidate_multiplier=2,
        use_model_reranker=False,
        model_rerank_candidate_multiplier=3,
        use_query_rewrite=True,
        use_llm_query_rewrite=False,
        use_multi_query=True,
    )

    assert report["top_k"] == 1
    assert report["vector_weight"] == 0.6
    assert report["bm25_weight"] == 0.4
    assert report["use_reranker"] is True
    assert report["rerank_candidate_multiplier"] == 2
    assert report["use_model_reranker"] is False
    assert report["model_rerank_candidate_multiplier"] == 3
    assert report["use_query_rewrite"] is True
    assert report["use_llm_query_rewrite"] is False
    assert report["use_multi_query"] is True
    assert report["best_retriever"] in {"vector", "bm25", "hybrid"}
    assert [
        item["retriever"]
        for item in report["reports"]
    ] == ["vector", "bm25", "hybrid"]


def test_scan_hybrid_weights(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark = [
        {
            "query": "绯荤粺鏋舵瀯",
            "expected_keywords": ["鐗瑰緛澶勭悊"],
        }
    ]
    store = [
        {
            "id": 0,
            "text": "绯荤粺鏋舵瀯鍖呮嫭鐗瑰緛澶勭悊妯″潡",
            "source": "test",
            "embedding": [1.0, 0.0],
        }
    ]
    benchmark_path.write_text(
        json.dumps(benchmark, ensure_ascii=False),
        encoding="utf-8",
    )
    vector_store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )

    report = scan_hybrid_weights(
        benchmark_path=str(benchmark_path),
        vector_store_path=str(vector_store_path),
        top_k=1,
        weight_pairs=[(1.0, 0.0), (0.5, 0.5)],
        embedding_fn=lambda text: [1.0, 0.0],
        embedding_cache_path=str(cache_path),
        embedding_model="test-model",
        use_reranker=True,
        rerank_candidate_multiplier=2,
        use_model_reranker=False,
        model_rerank_candidate_multiplier=3,
        use_query_rewrite=True,
        use_llm_query_rewrite=False,
        use_multi_query=True,
    )

    assert report["top_k"] == 1
    assert report["use_reranker"] is True
    assert report["rerank_candidate_multiplier"] == 2
    assert report["use_model_reranker"] is False
    assert report["model_rerank_candidate_multiplier"] == 3
    assert report["use_query_rewrite"] is True
    assert report["use_llm_query_rewrite"] is False
    assert report["use_multi_query"] is True
    assert report["best_average_score"] == 1.0
    assert len(report["reports"]) == 2
    assert [
        (
            item["vector_weight"],
            item["bm25_weight"],
        )
        for item in report["reports"]
    ] == [(1.0, 0.0), (0.5, 0.5)]


def test_compare_retrieval_strategies_excludes_expensive_by_default(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark = [
        {
            "query": "project",
            "expected_keywords": ["feature"],
        }
    ]
    store = [
        {
            "id": 0,
            "text": "project overview",
            "source": "test",
            "embedding": [1.0, 0.0],
        },
        {
            "id": 1,
            "text": "architecture feature module",
            "source": "test",
            "embedding": [0.0, 1.0],
        },
    ]
    benchmark_path.write_text(
        json.dumps(benchmark, ensure_ascii=False),
        encoding="utf-8",
    )
    vector_store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )

    def embedding_for_test(text: str) -> list[float]:
        if "feature" in text:
            return [0.0, 1.0]

        return [1.0, 0.0]

    report = compare_retrieval_strategies(
        benchmark_path=str(benchmark_path),
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=embedding_for_test,
        embedding_cache_path=str(cache_path),
        embedding_model="test-model",
        query_rewriter=lambda query: "feature",
        multi_query_generator=lambda query: [query, "feature"],
    )

    strategy_names = [
        item["strategy_name"]
        for item in report["reports"]
    ]

    assert report["include_expensive"] is False
    assert strategy_names == [
        "hybrid",
        "hybrid+query_rewrite",
        "hybrid+multi_query",
        "hybrid+query_rewrite+multi_query",
        "hybrid+reranker",
    ]
    assert "hybrid+model_reranker" not in strategy_names
    assert "hybrid+llm_query_rewrite" not in strategy_names
    assert report["best_strategy"] == "hybrid+query_rewrite"
    assert report["best_average_score"] == 1.0


def test_compare_retrieval_strategies_can_include_expensive(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    vector_store_path = tmp_path / "vector_store.json"
    cache_path = tmp_path / "cache.json"
    benchmark = [
        {
            "query": "project",
            "expected_keywords": ["feature"],
        }
    ]
    store = [
        {
            "id": 0,
            "text": "project overview",
            "source": "test",
            "embedding": [1.0, 0.0],
        },
        {
            "id": 1,
            "text": "architecture feature module",
            "source": "test",
            "embedding": [0.0, 1.0],
        },
    ]
    benchmark_path.write_text(
        json.dumps(benchmark, ensure_ascii=False),
        encoding="utf-8",
    )
    vector_store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )

    def embedding_for_test(text: str) -> list[float]:
        if "feature" in text:
            return [0.0, 1.0]

        return [1.0, 0.0]

    def model_scorer(query: str, candidate: dict) -> float:
        if "feature" in candidate["text"]:
            return 1.0

        return 0.0

    report = compare_retrieval_strategies(
        benchmark_path=str(benchmark_path),
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=embedding_for_test,
        embedding_cache_path=str(cache_path),
        embedding_model="test-model",
        query_rewriter=lambda query: "feature",
        llm_query_rewriter=lambda query: "feature",
        multi_query_generator=lambda query: [query, "feature"],
        model_reranker_scorer=model_scorer,
        include_expensive=True,
    )

    strategy_names = [
        item["strategy_name"]
        for item in report["reports"]
    ]

    assert report["include_expensive"] is True
    assert "hybrid+model_reranker" in strategy_names
    assert "hybrid+llm_query_rewrite" in strategy_names
    assert "hybrid+llm_query_rewrite+multi_query" in strategy_names
    assert report["best_average_score"] == 1.0


def test_search_multi_query_store_deduplicates_results():
    store = [
        {
            "id": 0,
            "text": "系统架构包括特征处理模块",
            "source": "test",
            "embedding": [1.0, 0.0],
        },
    ]

    results = search_multi_query_store(
        queries=["系统架构", "特征处理"],
        store=store,
        top_k=2,
        retriever="vector",
        embedding_fn=lambda text: [1.0, 0.0],
        vector_weight=0.7,
        bm25_weight=0.3,
    )

    assert len(results) == 1
    assert results[0]["matched_queries"] == ["系统架构", "特征处理"]
