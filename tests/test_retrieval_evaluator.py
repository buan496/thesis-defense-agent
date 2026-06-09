import json

from app.retrieval_evaluator import evaluate_retrieval


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
