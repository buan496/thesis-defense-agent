import pytest

from app.hybrid_retriever import normalize_scores, search_hybrid


def simple_embedding(text: str) -> list[float]:
    if "系统" in text or "架构" in text:
        return [1.0, 0.0]

    return [0.0, 1.0]


def test_normalize_scores():
    scores = normalize_scores(
        [
            {"id": 1, "score": 10},
            {"id": 2, "score": 20},
        ]
    )

    assert scores == {
        1: 0.0,
        2: 1.0,
    }


def test_normalize_scores_handles_same_positive_score():
    scores = normalize_scores(
        [
            {"id": 1, "score": 3},
            {"id": 2, "score": 3},
        ]
    )

    assert scores == {
        1: 1.0,
        2: 1.0,
    }


def test_search_hybrid_returns_fused_scores():
    store = [
        {
            "id": 0,
            "text": "系统架构包括特征处理模块",
            "source": "a.txt",
            "embedding": [1.0, 0.0],
        },
        {
            "id": 1,
            "text": "天气很好",
            "source": "a.txt",
            "embedding": [0.0, 1.0],
        },
    ]

    results = search_hybrid(
        query="系统架构",
        store=store,
        top_k=1,
        vector_weight=0.5,
        bm25_weight=0.5,
        embedding_fn=simple_embedding,
    )

    assert len(results) == 1
    assert results[0]["id"] == 0
    assert "hybrid_score" in results[0]
    assert "vector_score" in results[0]
    assert "bm25_score" in results[0]
    assert results[0]["hybrid_score"] > 0


def test_search_hybrid_rejects_negative_weight():
    with pytest.raises(ValueError):
        search_hybrid(
            query="系统",
            store=[],
            vector_weight=-1,
            bm25_weight=1,
        )


def test_search_hybrid_rejects_zero_total_weight():
    with pytest.raises(ValueError):
        search_hybrid(
            query="系统",
            store=[],
            vector_weight=0,
            bm25_weight=0,
        )
