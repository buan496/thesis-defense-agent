import json

import pytest

from app.llm_query_rewriter import (
    build_llm_query_rewrite_prompt,
    rewrite_query_with_llm,
)


def test_build_llm_query_rewrite_prompt_contains_original_query():
    prompt = build_llm_query_rewrite_prompt("系统架构有哪些模块？")

    assert "系统架构有哪些模块？" in prompt
    assert "RAG 检索 query 改写器" in prompt
    assert '"query"' in prompt
    assert "不要回答问题" in prompt


def test_rewrite_query_with_llm_parses_json():
    def fake_llm(prompt: str) -> str:
        return json.dumps(
            {
                "query": "系统架构 特征处理 数据与词表 模型 训练 推理",
            },
            ensure_ascii=False,
        )

    rewritten_query = rewrite_query_with_llm(
        "系统是怎么设计的？",
        llm_fn=fake_llm,
    )

    assert rewritten_query == "系统架构 特征处理 数据与词表 模型 训练 推理"


def test_rewrite_query_with_llm_strips_markdown_json_block():
    def fake_llm(prompt: str) -> str:
        return """```json
{"query": "AISHELL LibriSpeech 数据集"}
```"""

    rewritten_query = rewrite_query_with_llm(
        "论文用了哪些数据？",
        llm_fn=fake_llm,
    )

    assert rewritten_query == "AISHELL LibriSpeech 数据集"


def test_rewrite_query_with_llm_normalizes_whitespace():
    def fake_llm(prompt: str) -> str:
        return '{"query": "  系统架构   模块   训练  "}'

    rewritten_query = rewrite_query_with_llm(
        "系统有哪些模块？",
        llm_fn=fake_llm,
    )

    assert rewritten_query == "系统架构 模块 训练"


def test_rewrite_query_with_llm_rejects_empty_input():
    with pytest.raises(ValueError):
        rewrite_query_with_llm("   ")


def test_rewrite_query_with_llm_requires_query_field():
    def fake_llm(prompt: str) -> str:
        return '{"text": "系统架构"}'

    with pytest.raises(ValueError):
        rewrite_query_with_llm(
            "系统有哪些模块？",
            llm_fn=fake_llm,
        )


def test_rewrite_query_with_llm_rejects_empty_query_field():
    def fake_llm(prompt: str) -> str:
        return '{"query": "   "}'

    with pytest.raises(ValueError):
        rewrite_query_with_llm(
            "系统有哪些模块？",
            llm_fn=fake_llm,
        )
