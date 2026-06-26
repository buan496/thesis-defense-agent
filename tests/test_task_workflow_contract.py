import pytest

from app.task_resume import (
    AUTO_EXECUTABLE_STEP_TYPES,
    HUMAN_INPUT_STEP_TYPES,
)
from app.task_runner import DEFENSE_TASK_STEP_ORDER
from app.task_workflow_contract import (
    get_auto_step_types,
    get_human_step_types,
    get_step_contract,
    get_workflow_step_types,
    validate_task_workflow_contract,
)


def test_contract_step_order_matches_task_runner():
    assert get_workflow_step_types() == DEFENSE_TASK_STEP_ORDER


def test_contract_auto_steps_match_resume_policy():
    assert get_auto_step_types() == AUTO_EXECUTABLE_STEP_TYPES


def test_contract_human_steps_match_resume_policy():
    assert get_human_step_types() == HUMAN_INPUT_STEP_TYPES


def test_contract_validation_has_no_issues():
    assert validate_task_workflow_contract() == []


def test_retrieve_context_contract_accepts_query_or_topic():
    contract = get_step_contract("retrieve_context")

    assert contract.execution_mode == "auto"
    assert contract.required_any_input_groups == (("query", "topic"),)
    assert contract.output_fields == ("query", "context", "sources")
    assert contract.resume_action == "execute_current_step"


def test_wait_for_answer_contract_is_human_input_step():
    contract = get_step_contract("wait_for_answer")

    assert contract.execution_mode == "human"
    assert contract.required_input_fields == ("question",)
    assert contract.output_fields == ("question", "answer")
    assert contract.resume_action == "wait_for_human_input"


def test_summarize_training_contract_requires_full_training_round():
    contract = get_step_contract("summarize_training")

    assert contract.required_input_fields == (
        "question",
        "answer",
        "evaluation",
        "rewritten_answer",
        "follow_up_question",
        "follow_up_answer",
        "follow_up_evaluation",
    )
    assert "summary" in contract.output_fields
    assert "weaknesses" in contract.output_fields
    assert "next_suggestions" in contract.output_fields


def test_unknown_step_contract_raises_error():
    with pytest.raises(ValueError):
        get_step_contract("unknown_step")
