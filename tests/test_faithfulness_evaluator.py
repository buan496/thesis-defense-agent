import pytest

from app.agent_models import AgentResult,ToolTrace
from app.faithfulness_evaluator import (
    build_faithfulness_prompt,
    evaluate_agent_faithfulness,
    evaluate_faithfulness,
    extract_search_evidence,
)

def test_build_faithfulness_prompt():
    prompt = build_faithfulness_prompt(
        question="论文使用了哪些数据集？",
        answer="论文使用了 AISHELL-1。",
        evidence="数据部分使用 AISHELL-1 和 LibriSpeech。",
    )

    assert "论文使用了哪些数据集" in prompt
    assert "AISHELL-1" in prompt
    assert "LibriSpeech" in prompt
    assert "unsupported_claims" in prompt
    assert "contradictions" in prompt
    assert "遗漏证据中的部分信息属于完整性问题" in prompt
    assert "只陈述了部分受支持事实" in prompt
    
def test_evaluate_faithfulness_parses_result():
    def fake_llm(prompt: str) -> str:
        assert "AISHELL-1" in prompt

        return """
        {
            "score": 1.0,
            "passed": true,
            "reason": "回答受到证据支持",
            "unsupported_claims": [],
            "contradictions": []
        }
        """

    result = evaluate_faithfulness(
        question="论文使用了哪些数据集？",
        answer="论文使用了 AISHELL-1。",
        evidence="论文使用 AISHELL-1 和 LibriSpeech。",
        llm_fn=fake_llm,
    )

    assert result["passed"] is True
    assert result["score"] == 1.0
    
    
    
def test_evaluate_faithfulness_rejects_invalid_json():
    def fake_llm(prompt: str) -> str:
        return "这不是 JSON"

    with pytest.raises(
        ValueError,
        match="Faithfulness Judge 返回的不是合法 JSON",
    ):
        evaluate_faithfulness(
            question="问题",
            answer="回答",
            evidence="证据",
            llm_fn=fake_llm,
        )
        
def test_extract_search_evidence():
    traces = [
        ToolTrace(
            step=1,
            tool_name="search_thesis",
            arguments='{"query": "数据集"}',
            result="论文使用 AISHELL-1。",
            success=True,
            duration_ms=10.0,
        ),
        ToolTrace(
            step=2,
            tool_name="create_defense_questions",
            arguments="{}",
            result="生成的问题",
            success=True,
            duration_ms=10.0,
        ),
        ToolTrace(
            step=3,
            tool_name="search_thesis",
            arguments='{"query": "英文数据"}',
            result="论文使用 LibriSpeech。",
            success=True,
            duration_ms=10.0,
        ),
    ]

    evidence = extract_search_evidence(traces)

    assert "AISHELL-1" in evidence
    assert "LibriSpeech" in evidence
    assert "生成的问题" not in evidence
    
def test_extract_search_evidence_ignores_failed_search():
    traces = [
        ToolTrace(
            step=1,
            tool_name="search_thesis",
            arguments="{}",
            result="这条失败结果不应该成为证据",
            success=False,
            duration_ms=10.0,
        )
    ]

    evidence = extract_search_evidence(traces)

    assert evidence == ""
    
def test_evaluate_agent_faithfulness():
    agent_result = AgentResult(
        final_output="论文使用 AISHELL-1 数据集。",
        steps=2,
        tool_traces=[
            ToolTrace(
                step=1,
                tool_name="search_thesis",
                arguments='{"query": "数据集"}',
                result="论文使用 AISHELL-1 和 LibriSpeech。",
                success=True,
                duration_ms=10.0,
            )
        ],
    )

    def fake_llm(prompt: str) -> str:
        assert "论文使用 AISHELL-1 数据集" in prompt
        assert "AISHELL-1 和 LibriSpeech" in prompt

        return """
        {
            "score": 1.0,
            "passed": true,
            "reason": "回答受到证据支持",
            "unsupported_claims": [],
            "contradictions": []
        }
        """

    result = evaluate_agent_faithfulness(
        question="论文使用了哪些数据集？",
        agent_result=agent_result,
        llm_fn=fake_llm,
    )

    assert result["evaluated"] is True
    assert result["passed"] is True
    assert result["score"] == 1.0
    assert "LibriSpeech" in result["evidence"]
    
def test_evaluate_agent_faithfulness_without_evidence():
    agent_result = AgentResult(
        final_output="这是一个没有检索依据的回答。",
        steps=1,
        tool_traces=[],
    )

    def fake_llm(prompt: str) -> str:
        raise AssertionError("没有证据时不应该调用 LLM")

    result = evaluate_agent_faithfulness(
        question="论文使用了哪些数据集？",
        agent_result=agent_result,
        llm_fn=fake_llm,
    )

    assert result["evaluated"] is False
    assert result["passed"] is False
    assert result["score"] == 0.0
    assert result["evidence"] == ""
