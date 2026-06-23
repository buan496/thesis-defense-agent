import json

from app.benchmark_draft_exporter import (
    build_benchmark_draft_item,
    export_accepted_candidates_to_benchmark_draft,
    infer_benchmark_type,
)


def test_infer_benchmark_type():
    assert infer_benchmark_type({"tags": ["faithfulness"]}) == "faithfulness"
    assert infer_benchmark_type({"tags": ["rag"]}) == "rag_retrieval"
    assert infer_benchmark_type({"tags": ["routing_error"]}) == "agent_routing"
    assert infer_benchmark_type({"source_type": "agent_trace"}) == "agent_routing"
    assert infer_benchmark_type({"tags": []}) == "manual"


def test_build_benchmark_draft_item_for_agent_routing():
    item = build_benchmark_draft_item(
        {
            "candidate_id": "feedback-1",
            "source_feedback_id": "1",
            "source_type": "agent_trace",
            "source_id": "line:1",
            "comment": "工具选错",
            "tags": ["routing_error"],
            "metadata": {"query": "系统架构"},
            "review": {"reviewer": "buan496"},
        }
    )

    assert item["draft_id"] == "draft-feedback-1"
    assert item["benchmark_type"] == "agent_routing"
    assert item["draft_fields"] == {
        "user_message": "",
        "expected_tools": [],
        "expected_arguments": {},
        "expected_answer_contains": [],
    }
    assert item["metadata"] == {"query": "系统架构"}


def test_export_accepted_candidates_to_benchmark_draft(tmp_path):
    output_path = tmp_path / "draft.json"
    candidate_report = {
        "candidates": [
            {
                "candidate_id": "accepted",
                "status": "accepted",
                "source_feedback_id": "1",
                "source_type": "agent_trace",
                "source_id": "line:1",
                "comment": "接受",
                "tags": ["routing_error"],
                "metadata": {},
                "review": {},
            },
            {
                "candidate_id": "rejected",
                "status": "rejected",
                "source_feedback_id": "2",
                "source_type": "agent_trace",
                "source_id": "line:2",
                "comment": "拒绝",
                "tags": [],
                "metadata": {},
            },
            {
                "candidate_id": "pending",
                "status": "needs_review",
                "source_feedback_id": "3",
                "source_type": "agent_trace",
                "source_id": "line:3",
                "comment": "待复核",
                "tags": [],
                "metadata": {},
            },
        ]
    }

    draft = export_accepted_candidates_to_benchmark_draft(
        candidate_report=candidate_report,
        output_file_path=str(output_path),
    )

    assert draft["count"] == 1
    assert draft["items"][0]["source_candidate_id"] == "accepted"

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["count"] == 1
    assert saved["items"][0]["source_candidate_id"] == "accepted"
