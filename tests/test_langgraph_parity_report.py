import pytest

from app.langgraph_workflow.parity_report import (
    build_langgraph_task_parity_report,
    get_langgraph_summary_demo_steps,
    map_langgraph_steps_to_task_steps,
)
from app.task_workflow_contract import get_workflow_step_types


def test_get_langgraph_summary_demo_steps():
    assert get_langgraph_summary_demo_steps() == [
        "retrieve_context",
        "generate_question",
        "answer_interrupt",
        "evaluate_answer",
        "rewrite_answer",
        "generate_follow_up",
        "follow_up_interrupt",
        "evaluate_follow_up_answer",
        "summarize_training",
    ]


def test_map_langgraph_steps_to_task_steps():
    mapped_steps = map_langgraph_steps_to_task_steps(
        [
            "retrieve_context",
            "generate_question",
            "answer_interrupt",
            "follow_up_interrupt",
        ]
    )

    assert mapped_steps == [
        "retrieve_context",
        "generate_question",
        "wait_for_answer",
        "wait_for_follow_up_answer",
    ]


def test_map_langgraph_steps_rejects_unmapped_step():
    with pytest.raises(ValueError):
        map_langgraph_steps_to_task_steps(["unknown_node"])


def test_build_langgraph_task_parity_report_passes_for_summary_demo():
    report = build_langgraph_task_parity_report()

    assert report["task_contract_steps"] == get_workflow_step_types()
    assert report["mapped_langgraph_steps"] == get_workflow_step_types()
    assert report["missing_steps"] == []
    assert report["extra_steps"] == []
    assert report["order_matches"] is True
    assert report["passed"] is True


def test_build_langgraph_task_parity_report_detects_missing_step():
    report = build_langgraph_task_parity_report(
        langgraph_steps=[
            "retrieve_context",
            "generate_question",
            "answer_interrupt",
        ]
    )

    assert "evaluate_answer" in report["missing_steps"]
    assert report["passed"] is False


def test_build_langgraph_task_parity_report_detects_order_mismatch():
    report = build_langgraph_task_parity_report(
        langgraph_steps=[
            "generate_question",
            "retrieve_context",
            "answer_interrupt",
            "evaluate_answer",
            "rewrite_answer",
            "generate_follow_up",
            "follow_up_interrupt",
            "evaluate_follow_up_answer",
            "summarize_training",
        ]
    )

    assert report["missing_steps"] == []
    assert report["extra_steps"] == []
    assert report["order_matches"] is False
    assert report["passed"] is False
