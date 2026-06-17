from pathlib import Path
from typing import Any

from app.task_models import DefenseTask, TaskStep
from app.task_runner import (
    complete_current_step,
    create_next_step,
)
from app.task_store import (
    DEFAULT_TASK_DIRECTORY,
    load_defense_task,
    save_defense_task,
)


def create_defense_task(
    topic: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
) -> tuple[DefenseTask, Path]:
    task = DefenseTask(topic=topic)

    task_path = save_defense_task(
        task,
        directory=directory,
    )

    return task, task_path


def start_next_task_step(
    task_id: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
    input: dict[str, Any] | None = None,
) -> tuple[DefenseTask, TaskStep | None, Path]:
    task = load_defense_task(
        task_id=task_id,
        directory=directory,
    )

    step = create_next_step(
        task,
        input=input,
    )

    task_path = save_defense_task(
        task,
        directory=directory,
    )

    return task, step, task_path


def complete_task_step(
    task_id: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
    output: dict[str, Any] | None = None,
) -> tuple[DefenseTask, TaskStep, Path]:
    task = load_defense_task(
        task_id=task_id,
        directory=directory,
    )

    step = complete_current_step(
        task,
        output=output,
    )

    task_path = save_defense_task(
        task,
        directory=directory,
    )

    return task, step, task_path


def get_defense_task(
    task_id: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
) -> DefenseTask:
    return load_defense_task(
        task_id=task_id,
        directory=directory,
    )