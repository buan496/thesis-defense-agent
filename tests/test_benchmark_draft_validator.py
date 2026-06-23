from app.benchmark_draft_validator import (
    validate_benchmark_draft,
    validate_benchmark_draft_item,
)


def test_validate_benchmark_draft_item_passes_agent_routing():
    result = validate_benchmark_draft_item(
        {
            "draft_id": "draft-1",
            "benchmark_type": "agent_routing",
            "draft_fields": {
                "user_message": "系统架构有哪些模块？",
                "expected_tools": ["search_thesis"],
                "expected_arguments": {"query": "系统架构"},
                "expected_answer_contains": ["特征处理模块"],
            },
        }
    )

    assert result["passed"]
    assert result["errors"] == []


def test_validate_benchmark_draft_item_fails_empty_fields():
    result = validate_benchmark_draft_item(
        {
            "draft_id": "draft-1",
            "benchmark_type": "agent_routing",
            "draft_fields": {
                "user_message": "",
                "expected_tools": [],
                "expected_arguments": {},
                "expected_answer_contains": [],
            },
        }
    )

    assert not result["passed"]
    assert "field user_message must not be empty" in result["errors"]
    assert "field expected_tools must not be empty" in result["errors"]
    assert "field expected_answer_contains must not be empty" in result["errors"]


def test_validate_benchmark_draft_item_fails_wrong_type():
    result = validate_benchmark_draft_item(
        {
            "draft_id": "draft-1",
            "benchmark_type": "rag_retrieval",
            "draft_fields": {
                "query": "系统架构",
                "expected_keywords": "特征处理模块",
            },
        }
    )

    assert not result["passed"]
    assert "field expected_keywords must be list" in result["errors"]


def test_validate_benchmark_draft_item_fails_unknown_type():
    result = validate_benchmark_draft_item(
        {
            "draft_id": "draft-1",
            "benchmark_type": "unknown",
            "draft_fields": {},
        }
    )

    assert not result["passed"]
    assert "unknown benchmark_type: unknown" in result["errors"]


def test_validate_benchmark_draft():
    report = validate_benchmark_draft(
        {
            "items": [
                {
                    "draft_id": "valid",
                    "benchmark_type": "faithfulness",
                    "draft_fields": {
                        "question": "是否实现流式识别？",
                        "evidence": "流式识别属于后续改进方向。",
                        "answer": "当前尚未实现。",
                        "expected_passed": True,
                    },
                },
                {
                    "draft_id": "invalid",
                    "benchmark_type": "manual",
                    "draft_fields": {"notes": ""},
                },
            ]
        }
    )

    assert report["item_count"] == 2
    assert report["valid_count"] == 1
    assert report["invalid_count"] == 1
    assert not report["passed"]
