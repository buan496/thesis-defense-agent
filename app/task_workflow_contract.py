from dataclasses import dataclass

from app.task_resume import (
    AUTO_EXECUTABLE_STEP_TYPES,
    HUMAN_INPUT_STEP_TYPES,
)
from app.task_runner import DEFENSE_TASK_STEP_ORDER


@dataclass(frozen=True)
class TaskStepContract:
    step_type: str
    execution_mode: str
    required_input_fields: tuple[str, ...] = ()
    required_any_input_groups: tuple[tuple[str, ...], ...] = ()
    optional_input_fields: tuple[str, ...] = ()
    output_fields: tuple[str, ...] = ()
    resume_action: str = ""


DEFENSE_TASK_WORKFLOW_CONTRACT: tuple[TaskStepContract, ...] = (
    TaskStepContract(
        step_type="retrieve_context",
        execution_mode="auto",
        required_any_input_groups=(("query", "topic"),),
        output_fields=("query", "context", "sources"),
        resume_action="execute_current_step",
    ),
    TaskStepContract(
        step_type="generate_question",
        execution_mode="auto",
        required_input_fields=("context",),
        optional_input_fields=("topic",),
        output_fields=("question", "questions", "topic"),
        resume_action="execute_current_step",
    ),
    TaskStepContract(
        step_type="wait_for_answer",
        execution_mode="human",
        required_input_fields=("question",),
        output_fields=("question", "answer"),
        resume_action="wait_for_human_input",
    ),
    TaskStepContract(
        step_type="evaluate_answer",
        execution_mode="auto",
        required_input_fields=("question", "answer"),
        output_fields=("question", "answer", "evaluation"),
        resume_action="execute_current_step",
    ),
    TaskStepContract(
        step_type="rewrite_answer",
        execution_mode="auto",
        required_input_fields=("question", "answer"),
        optional_input_fields=("evaluation",),
        output_fields=(
            "question",
            "answer",
            "evaluation",
            "rewritten_answer",
        ),
        resume_action="execute_current_step",
    ),
    TaskStepContract(
        step_type="generate_follow_up",
        execution_mode="auto",
        required_input_fields=("question", "answer"),
        optional_input_fields=("evaluation", "rewritten_answer"),
        output_fields=(
            "question",
            "answer",
            "evaluation",
            "rewritten_answer",
            "follow_up_question",
        ),
        resume_action="execute_current_step",
    ),
    TaskStepContract(
        step_type="wait_for_follow_up_answer",
        execution_mode="human",
        required_input_fields=("follow_up_question",),
        optional_input_fields=(
            "question",
            "answer",
            "evaluation",
            "rewritten_answer",
        ),
        output_fields=(
            "question",
            "answer",
            "evaluation",
            "rewritten_answer",
            "follow_up_question",
            "follow_up_answer",
        ),
        resume_action="wait_for_human_input",
    ),
    TaskStepContract(
        step_type="evaluate_follow_up_answer",
        execution_mode="auto",
        required_input_fields=("follow_up_question", "follow_up_answer"),
        optional_input_fields=(
            "question",
            "answer",
            "evaluation",
            "rewritten_answer",
        ),
        output_fields=(
            "question",
            "answer",
            "evaluation",
            "rewritten_answer",
            "follow_up_question",
            "follow_up_answer",
            "follow_up_evaluation",
        ),
        resume_action="execute_current_step",
    ),
    TaskStepContract(
        step_type="summarize_training",
        execution_mode="auto",
        required_input_fields=(
            "question",
            "answer",
            "evaluation",
            "rewritten_answer",
            "follow_up_question",
            "follow_up_answer",
            "follow_up_evaluation",
        ),
        output_fields=(
            "question",
            "answer",
            "evaluation",
            "rewritten_answer",
            "follow_up_question",
            "follow_up_answer",
            "follow_up_evaluation",
            "summary",
            "weaknesses",
            "next_suggestions",
        ),
        resume_action="execute_current_step",
    ),
)


def get_workflow_step_types() -> list[str]:
    return [
        contract.step_type
        for contract in DEFENSE_TASK_WORKFLOW_CONTRACT
    ]


def get_auto_step_types() -> set[str]:
    return {
        contract.step_type
        for contract in DEFENSE_TASK_WORKFLOW_CONTRACT
        if contract.execution_mode == "auto"
    }


def get_human_step_types() -> set[str]:
    return {
        contract.step_type
        for contract in DEFENSE_TASK_WORKFLOW_CONTRACT
        if contract.execution_mode == "human"
    }


def get_step_contract(step_type: str) -> TaskStepContract:
    for contract in DEFENSE_TASK_WORKFLOW_CONTRACT:
        if contract.step_type == step_type:
            return contract

    raise ValueError(f"Unknown task step type: {step_type}")


def validate_task_workflow_contract() -> list[str]:
    issues = []
    contract_step_types = get_workflow_step_types()
    contract_auto_steps = get_auto_step_types()
    contract_human_steps = get_human_step_types()

    if contract_step_types != DEFENSE_TASK_STEP_ORDER:
        issues.append(
            "Workflow contract step order does not match task runner order"
        )

    if contract_auto_steps != AUTO_EXECUTABLE_STEP_TYPES:
        issues.append(
            "Workflow contract auto steps do not match resume policy"
        )

    if contract_human_steps != HUMAN_INPUT_STEP_TYPES:
        issues.append(
            "Workflow contract human steps do not match resume policy"
        )

    for contract in DEFENSE_TASK_WORKFLOW_CONTRACT:
        if contract.execution_mode == "auto":
            expected_action = "execute_current_step"
        elif contract.execution_mode == "human":
            expected_action = "wait_for_human_input"
        else:
            issues.append(
                f"Invalid execution mode for step: {contract.step_type}"
            )
            continue

        if contract.resume_action != expected_action:
            issues.append(
                f"Invalid resume action for step: {contract.step_type}"
            )

    return issues
