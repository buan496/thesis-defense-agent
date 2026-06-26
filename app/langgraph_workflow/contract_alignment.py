from app.task_workflow_contract import (
    get_step_contract,
    get_workflow_step_types,
)


DEMO_TASK_CONTRACT_STEP_TYPES = (
    "retrieve_context",
    "generate_question",
    "wait_for_answer",
)

INTERRUPT_DEMO_NODE_TO_CONTRACT_STEP = {
    "retrieve_context": "retrieve_context",
    "generate_question": "generate_question",
    "answer_interrupt": "wait_for_answer",
}


def get_demo_task_contract_step_types() -> tuple[str, ...]:
    return DEMO_TASK_CONTRACT_STEP_TYPES


def get_interrupt_demo_contract_mapping() -> dict[str, str]:
    return dict(INTERRUPT_DEMO_NODE_TO_CONTRACT_STEP)


def validate_demo_task_contract_alignment() -> list[str]:
    issues = []
    workflow_prefix = tuple(
        get_workflow_step_types()[: len(DEMO_TASK_CONTRACT_STEP_TYPES)]
    )

    if DEMO_TASK_CONTRACT_STEP_TYPES != workflow_prefix:
        issues.append(
            "LangGraph demo task steps do not match task workflow prefix"
        )

    for step_type in DEMO_TASK_CONTRACT_STEP_TYPES:
        get_step_contract(step_type)

    return issues


def validate_interrupt_demo_contract_alignment() -> list[str]:
    issues = []

    for node_name, contract_step_type in (
        INTERRUPT_DEMO_NODE_TO_CONTRACT_STEP.items()
    ):
        contract = get_step_contract(contract_step_type)

        if (
            node_name == "answer_interrupt"
            and contract.execution_mode != "human"
        ):
            issues.append(
                "answer_interrupt must map to a human input contract step"
            )

    return issues
