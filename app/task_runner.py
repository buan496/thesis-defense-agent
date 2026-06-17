from typing import Any

from app.task_models import DefenseTask, TaskStep


DEFENSE_TASK_STEP_ORDER = [
    "retrieve_context",
    "generate_question",
    "wait_for_answer",
    "evaluate_answer",
    "rewrite_answer",
    "generate_follow_up",
    "wait_for_follow_up_answer",
    "evaluate_follow_up_answer",
    "summarize_training",
]


def get_next_step_type(task: DefenseTask) -> str | None:
    current_step = task.get_current_step()

    if current_step is None:
        return DEFENSE_TASK_STEP_ORDER[0]

    if current_step.status != "completed":
        return None

    current_index = DEFENSE_TASK_STEP_ORDER.index(
        current_step.step_type
    )

    next_index = current_index + 1

    if next_index >= len(DEFENSE_TASK_STEP_ORDER):
        return None

    return DEFENSE_TASK_STEP_ORDER[next_index]


def build_next_step_input(
    task: DefenseTask,
    input: dict[str, Any] | None = None,
) -> dict[str, Any]:
    next_input = {}
    current_step = task.get_current_step()

    if current_step is not None and current_step.status == "completed":
        next_input.update(current_step.output)

    if input is not None:
        next_input.update(input)

    return next_input


def create_next_step(
    task: DefenseTask,
    input: dict[str, Any] | None = None,
) -> TaskStep | None:
    next_step_type = get_next_step_type(task)

    if next_step_type is None:
        return None

    step = TaskStep(
        step_type=next_step_type,
        input=build_next_step_input(
            task,
            input=input,
        ),
    )

    task.add_step(step)

    return step


def complete_current_step(
    task: DefenseTask,
    output: dict[str, Any] | None = None,
) -> TaskStep:
    current_step = task.get_current_step()

    if current_step is None:
        raise ValueError("当前任务没有可完成的步骤")

    current_step.mark_completed(output=output or {})

    if get_next_step_type(task) is None:
        task.mark_completed()

    return current_step
