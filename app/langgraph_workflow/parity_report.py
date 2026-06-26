from typing import Any

from app.task_workflow_contract import get_workflow_step_types


LANGGRAPH_SUMMARY_DEMO_STEPS = (
    "retrieve_context",
    "generate_question",
    "answer_interrupt",
    "evaluate_answer",
    "rewrite_answer",
    "generate_follow_up",
    "follow_up_interrupt",
    "evaluate_follow_up_answer",
    "summarize_training",
)

LANGGRAPH_NODE_TO_TASK_STEP = {
    "retrieve_context": "retrieve_context",
    "generate_question": "generate_question",
    "answer_interrupt": "wait_for_answer",
    "evaluate_answer": "evaluate_answer",
    "rewrite_answer": "rewrite_answer",
    "generate_follow_up": "generate_follow_up",
    "follow_up_interrupt": "wait_for_follow_up_answer",
    "evaluate_follow_up_answer": "evaluate_follow_up_answer",
    "summarize_training": "summarize_training",
}


def get_langgraph_summary_demo_steps() -> list[str]:
    return list(LANGGRAPH_SUMMARY_DEMO_STEPS)


def map_langgraph_steps_to_task_steps(
    langgraph_steps: list[str] | tuple[str, ...],
    node_mapping: dict[str, str] | None = None,
) -> list[str]:
    mapping = node_mapping or LANGGRAPH_NODE_TO_TASK_STEP
    mapped_steps = []

    for step in langgraph_steps:
        if step not in mapping:
            raise ValueError(f"Unmapped LangGraph step: {step}")

        mapped_steps.append(mapping[step])

    return mapped_steps


def build_langgraph_task_parity_report(
    langgraph_steps: list[str] | tuple[str, ...] | None = None,
    task_contract_steps: list[str] | None = None,
    node_mapping: dict[str, str] | None = None,
) -> dict[str, Any]:
    task_steps = task_contract_steps or get_workflow_step_types()
    graph_steps = list(langgraph_steps or LANGGRAPH_SUMMARY_DEMO_STEPS)
    mapped_graph_steps = map_langgraph_steps_to_task_steps(
        graph_steps,
        node_mapping=node_mapping,
    )
    missing_steps = [
        step
        for step in task_steps
        if step not in mapped_graph_steps
    ]
    extra_steps = [
        step
        for step in mapped_graph_steps
        if step not in task_steps
    ]
    order_matches = mapped_graph_steps == task_steps

    return {
        "task_contract_steps": task_steps,
        "langgraph_steps": graph_steps,
        "mapped_langgraph_steps": mapped_graph_steps,
        "node_mapping": dict(node_mapping or LANGGRAPH_NODE_TO_TASK_STEP),
        "missing_steps": missing_steps,
        "extra_steps": extra_steps,
        "order_matches": order_matches,
        "passed": order_matches
        and not missing_steps
        and not extra_steps,
    }
