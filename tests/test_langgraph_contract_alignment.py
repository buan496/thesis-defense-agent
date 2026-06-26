from app.langgraph_workflow.contract_alignment import (
    get_demo_task_contract_step_types,
    get_interrupt_demo_contract_mapping,
    validate_demo_task_contract_alignment,
    validate_interrupt_demo_contract_alignment,
)
from app.task_workflow_contract import (
    get_step_contract,
    get_workflow_step_types,
)


def test_demo_task_contract_steps_match_workflow_prefix():
    demo_steps = get_demo_task_contract_step_types()

    assert demo_steps == tuple(get_workflow_step_types()[:3])
    assert demo_steps == (
        "retrieve_context",
        "generate_question",
        "wait_for_answer",
    )


def test_demo_task_contract_alignment_has_no_issues():
    assert validate_demo_task_contract_alignment() == []


def test_interrupt_demo_maps_answer_interrupt_to_human_wait_step():
    mapping = get_interrupt_demo_contract_mapping()
    contract = get_step_contract(mapping["answer_interrupt"])

    assert mapping["answer_interrupt"] == "wait_for_answer"
    assert contract.execution_mode == "human"
    assert contract.resume_action == "wait_for_human_input"


def test_interrupt_demo_contract_alignment_has_no_issues():
    assert validate_interrupt_demo_contract_alignment() == []
