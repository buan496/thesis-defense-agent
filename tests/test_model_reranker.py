import json

import pytest

from app.model_reranker import (
    build_rerank_prompt,
    rerank_results_with_model,
    score_candidate_with_llm,
)


def test_build_rerank_prompt_contains_query_and_candidate():
    prompt = build_rerank_prompt(
        query="系统架构包括哪些模块？",
        candidate={
            "source": "data/thesis.pdf",
            "text": "系统架构包括特征处理模块。",
        },
    )

    assert "系统架构包括哪些模块？" in prompt
    assert "系统架构包括特征处理模块。" in prompt
    assert "data/thesis.pdf" in prompt
    assert "JSON" in prompt


def test_score_candidate_with_llm_parses_json_score():
    def fake_llm(prompt: str) -> str:
        return json.dumps(
            {
                "score": 0.8,
                "reason": "候选片段能回答问题",
            },
            ensure_ascii=False,
        )

    score = score_candidate_with_llm(
        query="系统架构包括哪些模块？",
        candidate={"text": "系统架构包括特征处理模块。"},
        llm_fn=fake_llm,
    )

    assert score == 0.8


def test_score_candidate_with_llm_strips_markdown_json_block():
    def fake_llm(prompt: str) -> str:
        return """```json
{"score": 0.6, "reason": "部分相关"}
```"""

    score = score_candidate_with_llm(
        query="系统架构包括哪些模块？",
        candidate={"text": "系统架构包括特征处理模块。"},
        llm_fn=fake_llm,
    )

    assert score == 0.6


def test_score_candidate_with_llm_clamps_score():
    def fake_llm(prompt: str) -> str:
        return '{"score": 2.0, "reason": "超出范围"}'

    score = score_candidate_with_llm(
        query="系统架构包括哪些模块？",
        candidate={"text": "系统架构包括特征处理模块。"},
        llm_fn=fake_llm,
    )

    assert score == 1.0


def test_score_candidate_with_llm_requires_score_field():
    def fake_llm(prompt: str) -> str:
        return '{"reason": "缺少分数"}'

    with pytest.raises(ValueError):
        score_candidate_with_llm(
            query="系统架构包括哪些模块？",
            candidate={"text": "系统架构包括特征处理模块。"},
            llm_fn=fake_llm,
        )


def test_rerank_results_with_model_orders_by_model_score():
    results = [
        {
            "id": 0,
            "text": "普通内容",
            "score": 0.9,
        },
        {
            "id": 1,
            "text": "系统架构包括特征处理模块。",
            "score": 0.4,
        },
    ]

    def fake_scorer(query: str, candidate: dict) -> float:
        if "特征处理" in candidate["text"]:
            return 0.95

        return 0.1

    reranked = rerank_results_with_model(
        query="系统架构包括哪些模块？",
        results=results,
        top_k=1,
        scorer=fake_scorer,
    )

    assert reranked[0]["id"] == 1
    assert reranked[0]["model_rerank_score"] == 0.95


def test_rerank_results_with_model_rejects_invalid_top_k():
    with pytest.raises(ValueError):
        rerank_results_with_model(
            query="系统架构",
            results=[],
            top_k=0,
        )
