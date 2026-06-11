import json

import pytest

from app.agent_models import AgentResult, ToolTrace
from app.agent_routing_evaluator import evaluate_agent_routing


def create_agent_result(tool_names: list[str]) -> AgentResult:
    return AgentResult(
        final_output="测试回答",
        steps=len(tool_names) + 1,
        tool_traces=[
            ToolTrace(
                step=index,
                tool_name=tool_name,
                arguments="{}",
                result="{}",
                success=True,
                duration_ms=1.0,
            )
            for index, tool_name in enumerate(tool_names, start=1)
        ],
    )


def test_evaluate_agent_routing_checks_tool_order(tmp_path):
    benchmark_path = tmp_path / "agent_routing_benchmark.json"
    benchmark_path.write_text(
        json.dumps(
            [
                {
                    "user_message": "你好",
                    "expected_tools": [],
                },
                {
                    "user_message": "论文使用了哪些数据集？",
                    "expected_tools": ["search_thesis"],
                },
                {
                    "user_message": "根据论文生成答辩问题",
                    "expected_tools": [
                        "search_thesis",
                        "create_defense_questions",
                    ],
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    routes = {
        "你好": [],
        "论文使用了哪些数据集？": ["search_thesis"],
        "根据论文生成答辩问题": [
            "create_defense_questions",
            "search_thesis",
        ],
    }

    def fake_agent(user_message: str) -> AgentResult:
        return create_agent_result(routes[user_message])

    report = evaluate_agent_routing(
        benchmark_path=str(benchmark_path),
        agent_fn=fake_agent,
    )

    assert report["total"] == 3
    assert report["passed"] == 2
    assert report["failed"] == 1
    assert report["accuracy"] == 2 / 3
    assert report["results"][2]["passed"] is False


def test_evaluate_agent_routing_records_agent_errors(tmp_path):
    benchmark_path = tmp_path / "agent_routing_benchmark.json"
    benchmark_path.write_text(
        json.dumps(
            [
                {
                    "user_message": "根据论文生成答辩问题",
                    "expected_tools": [
                        "search_thesis",
                        "create_defense_questions",
                    ],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def failing_agent(user_message: str) -> AgentResult:
        raise RuntimeError("模型服务不可用")

    report = evaluate_agent_routing(
        benchmark_path=str(benchmark_path),
        agent_fn=failing_agent,
    )

    assert report["passed"] == 0
    assert report["failed"] == 1
    assert report["accuracy"] == 0.0
    assert report["results"][0]["actual_tools"] == []
    assert report["results"][0]["error"] == (
        "RuntimeError: 模型服务不可用"
    )


def test_evaluate_agent_routing_rejects_empty_benchmark(tmp_path):
    benchmark_path = tmp_path / "empty_benchmark.json"
    benchmark_path.write_text("[]", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="Agent 路由 benchmark 不能为空",
    ):
        evaluate_agent_routing(
            benchmark_path=str(benchmark_path),
        )
