import pytest

from app.reranker import rerank_results, tokenize_for_rerank


def test_tokenize_for_rerank_splits_english_words_and_chinese_chars():
    tokens = tokenize_for_rerank("LAConformer 系统架构")

    assert "LAConformer" in tokens
    assert "系" in tokens
    assert "统" in tokens


def test_rerank_results_prefers_keyword_match():
    results = [
        {"id": 1, "text": "这是普通内容", "score": 0.9},
        {"id": 2, "text": "系统架构包含特征处理模块和训练模块", "score": 0.7},
    ]

    reranked = rerank_results("系统架构 模块", results, top_k=2)

    assert reranked[0]["id"] == 2
    assert "rerank_score" in reranked[0]
    assert reranked[0]["keyword_hits"] > 0


def test_rerank_results_preserves_original_result_fields():
    results = [
        {
            "id": 1,
            "text": "系统架构包含训练模块",
            "score": 0.8,
            "source": "data/thesis.pdf",
        },
    ]

    reranked = rerank_results("系统架构", results, top_k=1)

    assert reranked[0]["source"] == "data/thesis.pdf"


def test_rerank_results_respects_top_k():
    results = [
        {"id": 1, "text": "系统架构", "score": 0.9},
        {"id": 2, "text": "训练模块", "score": 0.8},
        {"id": 3, "text": "其他内容", "score": 0.7},
    ]

    reranked = rerank_results("系统架构", results, top_k=1)

    assert len(reranked) == 1


def test_rerank_results_empty_results():
    assert rerank_results("系统架构", [], top_k=3) == []


def test_rerank_results_invalid_top_k():
    with pytest.raises(ValueError):
        rerank_results("系统架构", [], top_k=0)
