import json

import pytest

from app.benchmark_draft_converter import (
    build_agent_argument_rules,
    convert_benchmark_draft_item_to_entry,
    convert_benchmark_draft_to_entries,
    export_validated_benchmark_draft,
)


def test_convert_benchmark_draft_item_to_rag_entry():
    entry = convert_benchmark_draft_item_to_entry(
        {
            "benchmark_type": "rag_retrieval",
            "draft_fields": {
                "query": "系统架构有哪些模块？",
                "expected_keywords": ["特征处理模块"],
            },
        }
    )

    assert entry == {
        "query": "系统架构有哪些模块？",
        "expected_keywords": ["特征处理模块"],
    }


def test_convert_benchmark_draft_item_to_faithfulness_entry():
    entry = convert_benchmark_draft_item_to_entry(
        {
            "draft_id": "draft-1",
            "benchmark_type": "faithfulness",
            "draft_fields": {
                "question": "是否实现流式识别？",
                "evidence": "流式识别属于后续方向。",
                "answer": "当前尚未实现。",
                "expected_passed": True,
            },
        }
    )

    assert entry == {
        "name": "draft-1",
        "question": "是否实现流式识别？",
        "evidence": "流式识别属于后续方向。",
        "answer": "当前尚未实现。",
        "expected_passed": True,
    }


def test_convert_benchmark_draft_item_to_agent_routing_entry():
    entry = convert_benchmark_draft_item_to_entry(
        {
            "benchmark_type": "agent_routing",
            "draft_fields": {
                "user_message": "系统架构有哪些模块？",
                "expected_tools": ["search_thesis"],
                "expected_arguments": {
                    "search_thesis": {
                        "required_fields": ["query"],
                        "required_keywords": ["系统架构"],
                    }
                },
                "expected_answer_contains": ["特征处理模块"],
            },
        }
    )

    assert entry == {
        "user_message": "系统架构有哪些模块？",
        "expected_tools": ["search_thesis"],
        "argument_rules": [
            {
                "tool_name": "search_thesis",
                "required_fields": ["query"],
                "required_keywords": ["系统架构"],
            }
        ],
        "completion_rules": {
            "non_empty": True,
            "required_keywords": ["特征处理模块"],
        },
    }


def test_build_agent_argument_rules():
    assert build_agent_argument_rules(
        {
            "search_thesis": {
                "required_fields": ["query"],
            }
        }
    ) == [
        {
            "tool_name": "search_thesis",
            "required_fields": ["query"],
        }
    ]


def test_convert_benchmark_draft_to_entries_rejects_invalid_draft():
    with pytest.raises(ValueError, match="validation failed"):
        convert_benchmark_draft_to_entries(
            {
                "items": [
                    {
                        "draft_id": "invalid",
                        "benchmark_type": "rag_retrieval",
                        "draft_fields": {
                            "query": "",
                            "expected_keywords": [],
                        },
                    }
                ]
            }
        )


def test_export_validated_benchmark_draft(tmp_path):
    output_directory = tmp_path / "exports"
    draft = {
        "items": [
            {
                "draft_id": "rag-1",
                "benchmark_type": "rag_retrieval",
                "draft_fields": {
                    "query": "系统架构有哪些模块？",
                    "expected_keywords": ["特征处理模块"],
                },
            },
            {
                "draft_id": "faith-1",
                "benchmark_type": "faithfulness",
                "draft_fields": {
                    "question": "是否实现流式识别？",
                    "evidence": "流式识别属于后续方向。",
                    "answer": "当前尚未实现。",
                    "expected_passed": True,
                },
            },
        ]
    }

    report = export_validated_benchmark_draft(
        draft=draft,
        output_directory=str(output_directory),
    )

    assert report["counts"]["rag_retrieval"] == 1
    assert report["counts"]["faithfulness"] == 1
    assert "rag_retrieval" in report["files"]
    assert "faithfulness" in report["files"]

    rag_entries = json.loads(
        (output_directory / "rag_benchmark_draft.json").read_text(
            encoding="utf-8"
        )
    )
    assert rag_entries == [
        {
            "query": "系统架构有哪些模块？",
            "expected_keywords": ["特征处理模块"],
        }
    ]
