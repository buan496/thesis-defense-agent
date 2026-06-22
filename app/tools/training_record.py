from pathlib import Path
from typing import Any

from app.task_models import DefenseTask, TaskStep
from app.task_store import DEFAULT_TASK_DIRECTORY, load_defense_task


def get_latest_step_by_type(
    task: DefenseTask,
    step_type: str,
) -> TaskStep | None:
    for step in reversed(task.steps):
        if step.step_type == step_type:
            return step

    return None


def get_step_output_value(
    task: DefenseTask,
    step_type: str,
    key: str,
) -> Any:
    step = get_latest_step_by_type(task, step_type)

    if step is None:
        return None

    return step.output.get(key)


def query_training_record(
    task_id: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
) -> dict[str, Any]:
    if not task_id.strip():
        raise ValueError("task_id 不能为空")

    task = load_defense_task(
        task_id=task_id,
        directory=directory,
    )

    return {
        "task_id": task.task_id,
        "topic": task.topic,
        "status": task.status,
        "step_count": len(task.steps),
        "completed_step_count": len(
            [
                step
                for step in task.steps
                if step.status == "completed"
            ]
        ),
        "question": get_step_output_value(
            task,
            "generate_question",
            "question",
        ),
        "student_answer": get_step_output_value(
            task,
            "wait_for_answer",
            "answer",
        ),
        "evaluation": get_step_output_value(
            task,
            "evaluate_answer",
            "evaluation",
        ),
        "rewritten_answer": get_step_output_value(
            task,
            "rewrite_answer",
            "rewritten_answer",
        ),
        "follow_up_question": get_step_output_value(
            task,
            "generate_follow_up",
            "follow_up_question",
        ),
        "follow_up_answer": get_step_output_value(
            task,
            "wait_for_follow_up_answer",
            "follow_up_answer",
        ),
        "follow_up_evaluation": get_step_output_value(
            task,
            "evaluate_follow_up_answer",
            "follow_up_evaluation",
        ),
        "summary": get_step_output_value(
            task,
            "summarize_training",
            "summary",
        ),
    }
