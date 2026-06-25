from pathlib import Path
from typing import Any

from app.long_term_memory import (
    add_training_summary,
    add_weakness,
    load_long_term_memory,
    save_long_term_memory,
)
from app.task_models import DefenseTask


def export_task_to_long_term_memory(
    task: DefenseTask,
    memory_path: str | Path,
) -> dict[str, Any]:
    if task.status != "completed":
        raise ValueError("only completed tasks can be exported to memory")

    summary_step = find_latest_completed_step(
        task,
        step_type="summarize_training",
    )

    if summary_step is None:
        raise ValueError("task has no completed summarize_training step")

    summary = summary_step.output.get("summary", "")

    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("summarize_training step has no summary")

    memory = load_long_term_memory(memory_path)
    memory = add_training_summary(
        memory,
        summary=summary,
        task_id=task.task_id,
        topic=task.topic,
    )

    exported_weaknesses = []

    for weakness in extract_summary_weaknesses(summary_step.output):
        memory = add_weakness(
            memory,
            weakness=weakness,
            source_task_id=task.task_id,
        )
        exported_weaknesses.append(weakness)

    saved_path = save_long_term_memory(
        memory,
        path=memory_path,
    )

    return {
        "task_id": task.task_id,
        "topic": task.topic,
        "memory_path": str(saved_path),
        "summary_exported": True,
        "weakness_count": len(exported_weaknesses),
        "weaknesses": exported_weaknesses,
    }


def find_latest_completed_step(
    task: DefenseTask,
    step_type: str,
):
    for step in reversed(task.steps):
        if step.step_type == step_type and step.status == "completed":
            return step

    return None


def extract_summary_weaknesses(
    summary_output: dict[str, Any],
) -> list[str]:
    weaknesses = summary_output.get("weaknesses", [])

    if weaknesses is None:
        return []

    if isinstance(weaknesses, str):
        weaknesses = [weaknesses]

    if not isinstance(weaknesses, list):
        raise ValueError("weaknesses must be a list or string")

    return [
        weakness.strip()
        for weakness in weaknesses
        if isinstance(weakness, str) and weakness.strip()
    ]
