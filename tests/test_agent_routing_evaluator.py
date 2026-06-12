import json

import pytest

from app.agent_models import AgentResult, ToolTrace
from app.agent_routing_evaluator import (
    evaluate_agent_routing,
    evaluate_groundedness,
    evaluate_task_completion,
    evaluate_tool_arguments,
    parse_tool_arguments,
)


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


def test_parse_tool_arguments():
    assert parse_tool_arguments(
        '{"query": "系统架构", "top_k": 3}'
    ) == {
        "query": "系统架构",
        "top_k": 3,
    }
    assert parse_tool_arguments("{invalid json}") == {}
    assert parse_tool_arguments('["not", "an", "object"]') == {}


def test_evaluate_tool_arguments_accepts_valid_tool_chain():
    traces = [
        ToolTrace(
            step=1,
            tool_name="search_thesis",
            arguments='{"query": "系统架构", "top_k": 3}',
            result=(
                '[{"text": "系统架构包括特征处理、模型训练和推理模块。"}]'
            ),
            success=True,
            duration_ms=1.0,
        ),
        ToolTrace(
            step=2,
            tool_name="create_defense_questions",
            arguments=(
                '{"context": '
                '"系统架构包括特征处理、模型训练和推理模块。"}'
            ),
            result='["系统各模块之间如何协作？"]',
            success=True,
            duration_ms=1.0,
        ),
    ]
    rules = [
        {
            "tool_name": "search_thesis",
            "required_fields": ["query"],
            "required_keywords": ["系统架构"],
            "integer_ranges": {
                "top_k": {
                    "minimum": 1,
                    "maximum": 10,
                }
            },
        },
        {
            "tool_name": "create_defense_questions",
            "required_fields": ["context"],
            "context_from_tool": {
                "tool_name": "search_thesis",
                "field": "context",
                "minimum_length": 20,
            },
        },
    ]

    checks = evaluate_tool_arguments(
        tool_traces=traces,
        argument_rules=rules,
    )

    assert len(checks) == 2
    assert all(check["passed"] for check in checks)


def test_evaluate_tool_arguments_accepts_rearranged_context():
    source_text = (
        "系统架构包括特征处理、词表管理、数据集构建、模型定义、"
        "训练控制、推理封装和流程调度。"
    )
    traces = [
        ToolTrace(
            step=1,
            tool_name="search_thesis",
            arguments='{"query": "系统架构"}',
            result=json.dumps(
                [{"text": source_text}],
                ensure_ascii=False,
            ),
            success=True,
            duration_ms=1.0,
        ),
        ToolTrace(
            step=2,
            tool_name="create_defense_questions",
            arguments=json.dumps(
                {
                    "context": (
                        "论文中的系统模块如下：\n"
                        "特征处理、词表管理、数据集构建、模型定义、"
                        "训练控制、推理封装和流程调度。"
                    )
                },
                ensure_ascii=False,
            ),
            result="[]",
            success=True,
            duration_ms=1.0,
        ),
    ]
    rules = [
        {
            "tool_name": "search_thesis",
        },
        {
            "tool_name": "create_defense_questions",
            "context_from_tool": {
                "tool_name": "search_thesis",
                "minimum_length": 20,
            },
        },
    ]

    checks = evaluate_tool_arguments(
        tool_traces=traces,
        argument_rules=rules,
    )

    assert checks[1]["passed"] is True


def test_evaluate_tool_arguments_rejects_invalid_values():
    traces = [
        ToolTrace(
            step=1,
            tool_name="search_thesis",
            arguments='{"query": "人工智能", "top_k": 20}',
            result=(
                '[{"text": "系统架构包括特征处理、模型训练和推理模块。"}]'
            ),
            success=True,
            duration_ms=1.0,
        ),
        ToolTrace(
            step=2,
            tool_name="create_defense_questions",
            arguments='{"context": "模型自行编造的无关内容"}',
            result="[]",
            success=True,
            duration_ms=1.0,
        ),
    ]
    rules = [
        {
            "tool_name": "search_thesis",
            "required_fields": ["query"],
            "required_keywords": ["系统架构"],
            "integer_ranges": {
                "top_k": {
                    "minimum": 1,
                    "maximum": 10,
                }
            },
        },
        {
            "tool_name": "create_defense_questions",
            "required_fields": ["context"],
            "context_from_tool": {
                "tool_name": "search_thesis",
                "field": "context",
                "minimum_length": 20,
            },
        },
    ]

    checks = evaluate_tool_arguments(
        tool_traces=traces,
        argument_rules=rules,
    )

    assert checks[0]["passed"] is False
    assert "参数缺少关键词：系统架构" in checks[0]["errors"]
    assert "top_k 不能大于 10" in checks[0]["errors"]
    assert checks[1]["passed"] is False
    assert (
        "context 未使用 search_thesis 的检索结果"
        in checks[1]["errors"]
    )


def test_evaluate_agent_routing_separates_route_and_arguments(
    tmp_path,
):
    benchmark_path = tmp_path / "agent_routing_benchmark.json"
    benchmark_path.write_text(
        json.dumps(
            [
                {
                    "user_message": "论文使用了哪些数据集？",
                    "expected_tools": ["search_thesis"],
                    "argument_rules": [
                        {
                            "tool_name": "search_thesis",
                            "required_fields": ["query"],
                            "required_keywords": ["数据集"],
                        }
                    ],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fake_agent(user_message: str) -> AgentResult:
        return AgentResult(
            final_output="测试回答",
            steps=2,
            tool_traces=[
                ToolTrace(
                    step=1,
                    tool_name="search_thesis",
                    arguments='{"query": "系统架构"}',
                    result="[]",
                    success=True,
                    duration_ms=1.0,
                )
            ],
        )

    report = evaluate_agent_routing(
        benchmark_path=str(benchmark_path),
        agent_fn=fake_agent,
    )

    assert report["routing_accuracy"] == 1.0
    assert report["argument_accuracy"] == 0.0
    assert report["accuracy"] == 0.0
    assert report["results"][0]["routing_passed"] is True
    assert report["results"][0]["arguments_passed"] is False


def test_evaluate_task_completion_rejects_empty_output():
    check = evaluate_task_completion(
        final_output="   ",
        rules={
            "non_empty": True,
        },
    )

    assert check["passed"] is False
    assert check["errors"] == ["最终回答不能为空"]
    assert check["question_count"] == 0


def test_evaluate_task_completion_checks_required_keywords():
    passing_check = evaluate_task_completion(
        final_output=(
            "论文使用 AISHELL 中文语音数据，"
            "同时使用 LibriSpeech 英文数据。"
        ),
        rules={
            "required_keywords": [
                ["AISHELL-1", "AISHELL"],
                "LibriSpeech",
            ],
        },
    )
    failing_check = evaluate_task_completion(
        final_output="论文使用了中文和英文语音数据。",
        rules={
            "required_keywords": [
                ["AISHELL-1", "AISHELL"],
                "LibriSpeech",
            ],
        },
    )

    assert passing_check["passed"] is True
    assert failing_check["passed"] is False
    assert failing_check["errors"] == [
        "最终回答缺少关键词：AISHELL-1/AISHELL",
        "最终回答缺少关键词：LibriSpeech",
    ]


def test_evaluate_task_completion_checks_question_count():
    passing_check = evaluate_task_completion(
        final_output=(
            "1. 系统架构如何设计？\n"
            "2. 为什么采用 Conformer？\n"
            "3. 语言感知前端如何工作？\n"
            "4. 实验如何验证效果？\n"
            "5. 系统存在哪些局限？"
        ),
        rules={
            "non_empty": True,
            "minimum_question_count": 5,
        },
    )
    failing_check = evaluate_task_completion(
        final_output=(
            "1. 系统架构如何设计？\n"
            "2. 实验如何验证效果？"
        ),
        rules={
            "non_empty": True,
            "minimum_question_count": 5,
        },
    )

    assert passing_check["passed"] is True
    assert passing_check["question_count"] == 5
    assert failing_check["passed"] is False
    assert failing_check["question_count"] == 2
    assert failing_check["errors"] == [
        "问题数量不足：期望至少 5 个，实际 2 个"
    ]


def test_evaluate_agent_routing_separates_task_completion(
    tmp_path,
):
    benchmark_path = tmp_path / "agent_routing_benchmark.json"
    benchmark_path.write_text(
        json.dumps(
            [
                {
                    "user_message": "根据论文生成5个答辩问题",
                    "expected_tools": [
                        "search_thesis",
                        "create_defense_questions",
                    ],
                    "argument_rules": [],
                    "completion_rules": {
                        "non_empty": True,
                        "minimum_question_count": 5,
                    },
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fake_agent(user_message: str) -> AgentResult:
        return AgentResult(
            final_output=(
                "1. 系统架构如何设计？\n"
                "2. 实验如何验证效果？"
            ),
            steps=3,
            tool_traces=[
                ToolTrace(
                    step=1,
                    tool_name="search_thesis",
                    arguments='{"query": "系统架构"}',
                    result="[]",
                    success=True,
                    duration_ms=1.0,
                ),
                ToolTrace(
                    step=2,
                    tool_name="create_defense_questions",
                    arguments='{"context": "论文内容"}',
                    result="[]",
                    success=True,
                    duration_ms=1.0,
                ),
            ],
        )

    report = evaluate_agent_routing(
        benchmark_path=str(benchmark_path),
        agent_fn=fake_agent,
    )

    assert report["routing_accuracy"] == 1.0
    assert report["argument_accuracy"] == 1.0
    assert report["completion_rate"] == 0.0
    assert report["end_to_end_success_rate"] == 0.0
    assert report["results"][0]["completion_passed"] is False
    assert report["results"][0]["passed"] is False


def test_evaluate_groundedness_accepts_supported_claim():
    check = evaluate_groundedness(
        final_output=(
            "论文使用 AISHELL-1 中文数据集和 "
            "LibriSpeech 英文数据集。"
        ),
        tool_traces=[
            ToolTrace(
                step=1,
                tool_name="search_thesis",
                arguments='{"query": "论文使用的数据集"}',
                result=(
                    "数据部分使用 AISHELL-1 和 "
                    "LibriSpeech 的多个子集。"
                ),
                success=True,
                duration_ms=1.0,
            )
        ],
        rules={
            "required_claims": [
                {
                    "claim": "AISHELL",
                    "answer_keywords": [
                        ["AISHELL-1", "AISHELL"],
                    ],
                    "evidence_keywords": [
                        ["AISHELL-1", "AISHELL"],
                    ],
                },
                {
                    "claim": "LibriSpeech",
                    "evidence_keywords": ["LibriSpeech"],
                },
            ]
        },
    )

    assert check["passed"] is True
    assert check["score"] == 1.0
    assert check["supported_claims"] == 2


def test_evaluate_groundedness_rejects_claim_without_evidence():
    check = evaluate_groundedness(
        final_output="论文使用 AISHELL-1 数据集。",
        tool_traces=[
            ToolTrace(
                step=1,
                tool_name="search_thesis",
                arguments='{"query": "论文使用的数据集"}',
                result="论文片段只提到了 LibriSpeech。",
                success=True,
                duration_ms=1.0,
            )
        ],
        rules={
            "required_claims": [
                {
                    "claim": "AISHELL-1",
                    "evidence_keywords": ["AISHELL-1"],
                }
            ]
        },
    )

    assert check["passed"] is False
    assert check["score"] == 0.0
    assert check["claims"][0]["claim_in_answer"] is True
    assert check["claims"][0]["evidence_found"] is False


def test_evaluate_groundedness_rejects_missing_claim_in_answer():
    check = evaluate_groundedness(
        final_output="论文使用了中英文语音数据集。",
        tool_traces=[
            ToolTrace(
                step=1,
                tool_name="search_thesis",
                arguments='{"query": "论文使用的数据集"}',
                result="论文使用 AISHELL-1 和 LibriSpeech。",
                success=True,
                duration_ms=1.0,
            )
        ],
        rules={
            "required_claims": [
                {
                    "claim": "AISHELL-1",
                    "evidence_keywords": ["AISHELL-1"],
                }
            ]
        },
    )

    assert check["passed"] is False
    assert check["claims"][0]["claim_in_answer"] is False
    assert check["claims"][0]["evidence_found"] is True


def test_evaluate_groundedness_requires_successful_search():
    check = evaluate_groundedness(
        final_output="论文使用 AISHELL-1 数据集。",
        tool_traces=[
            ToolTrace(
                step=1,
                tool_name="search_thesis",
                arguments='{"query": "论文使用的数据集"}',
                result="AISHELL-1",
                success=False,
                duration_ms=1.0,
            )
        ],
        rules={
            "required_claims": [
                {
                    "claim": "AISHELL-1",
                    "evidence_keywords": ["AISHELL-1"],
                }
            ]
        },
    )

    assert check["passed"] is False
    assert check["score"] == 0.0
    assert (
        "没有成功的 search_thesis 结果可作为证据"
        in check["errors"]
    )


def test_evaluate_agent_routing_separates_groundedness(
    tmp_path,
):
    benchmark_path = tmp_path / "agent_routing_benchmark.json"
    benchmark_path.write_text(
        json.dumps(
            [
                {
                    "user_message": "论文使用了哪些数据集？",
                    "expected_tools": ["search_thesis"],
                    "completion_rules": {
                        "non_empty": True,
                        "required_keywords": ["AISHELL-1"],
                    },
                    "grounding_rules": {
                        "required_claims": [
                            {
                                "claim": "AISHELL-1",
                                "evidence_keywords": ["AISHELL-1"],
                            }
                        ]
                    },
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fake_agent(user_message: str) -> AgentResult:
        return AgentResult(
            final_output="论文使用 AISHELL-1 数据集。",
            steps=2,
            tool_traces=[
                ToolTrace(
                    step=1,
                    tool_name="search_thesis",
                    arguments='{"query": "论文使用的数据集"}',
                    result="检索片段只提到了 LibriSpeech。",
                    success=True,
                    duration_ms=1.0,
                )
            ],
        )

    report = evaluate_agent_routing(
        benchmark_path=str(benchmark_path),
        agent_fn=fake_agent,
    )

    assert report["routing_accuracy"] == 1.0
    assert report["completion_rate"] == 1.0
    assert report["end_to_end_success_rate"] == 1.0
    assert report["groundedness_score"] == 0.0
    assert report["grounded_task_rate"] == 0.0
    assert report["end_to_end_grounded_success_rate"] == 0.0
    assert report["results"][0]["task_pipeline_passed"] is True
    assert report["results"][0]["grounding_passed"] is False
    assert report["results"][0]["passed"] is False


def test_evaluate_agent_routing_includes_faithfulness(
    tmp_path,
):
    benchmark_path = tmp_path / "agent_routing_benchmark.json"
    benchmark_path.write_text(
        json.dumps(
            [
                {
                    "user_message": "系统是否已经实现流式识别？",
                    "expected_tools": ["search_thesis"],
                    "completion_rules": {
                        "non_empty": True,
                    },
                    "faithfulness_rules": {
                        "enabled": True,
                        "minimum_score": 0.8,
                    },
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    agent_result = AgentResult(
        final_output="当前系统尚未实现流式识别。",
        steps=2,
        tool_traces=[
            ToolTrace(
                step=1,
                tool_name="search_thesis",
                arguments='{"query": "流式识别"}',
                result="流式识别属于后续改进方向。",
                success=True,
                duration_ms=1.0,
            )
        ],
    )

    def fake_agent(user_message: str) -> AgentResult:
        return agent_result

    def fake_faithfulness(
        question: str,
        result: AgentResult,
    ) -> dict:
        assert question == "系统是否已经实现流式识别？"
        assert result is agent_result

        return {
            "evaluated": True,
            "score": 1.0,
            "passed": True,
            "reason": "回答与证据一致",
            "unsupported_claims": [],
            "contradictions": [],
            "evidence": "流式识别属于后续改进方向。",
        }

    report = evaluate_agent_routing(
        benchmark_path=str(benchmark_path),
        agent_fn=fake_agent,
        faithfulness_fn=fake_faithfulness,
    )

    assert report["faithfulness_cases"] == 1
    assert report["faithfulness_score"] == 1.0
    assert report["faithfulness_pass_rate"] == 1.0
    assert report["end_to_end_faithful_success_rate"] == 1.0
    assert report["results"][0]["faithfulness_passed"] is True
    assert report["results"][0]["passed"] is True


def test_evaluate_agent_routing_separates_faithfulness_failure(
    tmp_path,
):
    benchmark_path = tmp_path / "agent_routing_benchmark.json"
    benchmark_path.write_text(
        json.dumps(
            [
                {
                    "user_message": "系统是否已经实现流式识别？",
                    "expected_tools": ["search_thesis"],
                    "completion_rules": {
                        "non_empty": True,
                    },
                    "faithfulness_rules": {
                        "enabled": True,
                        "minimum_score": 0.8,
                    },
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fake_agent(user_message: str) -> AgentResult:
        return AgentResult(
            final_output="当前系统已经完整实现流式识别。",
            steps=2,
            tool_traces=[
                ToolTrace(
                    step=1,
                    tool_name="search_thesis",
                    arguments='{"query": "流式识别"}',
                    result="流式识别属于后续改进方向。",
                    success=True,
                    duration_ms=1.0,
                )
            ],
        )

    def fake_faithfulness(
        question: str,
        result: AgentResult,
    ) -> dict:
        return {
            "evaluated": True,
            "score": 0.0,
            "passed": False,
            "reason": "回答将未来计划描述为已经完成",
            "unsupported_claims": [
                "系统已经完整实现流式识别",
            ],
            "contradictions": [
                "证据说明流式识别属于后续改进方向",
            ],
            "evidence": "流式识别属于后续改进方向。",
        }

    report = evaluate_agent_routing(
        benchmark_path=str(benchmark_path),
        agent_fn=fake_agent,
        faithfulness_fn=fake_faithfulness,
    )

    assert report["routing_accuracy"] == 1.0
    assert report["completion_rate"] == 1.0
    assert report["end_to_end_success_rate"] == 1.0
    assert report["end_to_end_grounded_success_rate"] == 1.0
    assert report["faithfulness_score"] == 0.0
    assert report["faithfulness_pass_rate"] == 0.0
    assert report["end_to_end_faithful_success_rate"] == 0.0
    assert report["results"][0]["grounded_pipeline_passed"] is True
    assert report["results"][0]["faithfulness_passed"] is False
    assert report["results"][0]["passed"] is False
