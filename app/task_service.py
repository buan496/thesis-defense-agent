from pathlib import Path
from collections.abc import Callable
from typing import Any

from app.config import RAG_TOP_K, RAG_VECTOR_STORE_PATH
from app.defense_questions import generate_questions_from_context_with_audit
from app.embeddings import create_embedding
from app.task_executor import execute_task_step
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


def execute_current_task_step(
    task_id: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
    vector_store_path: str = RAG_VECTOR_STORE_PATH,
    top_k: int = RAG_TOP_K,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    question_generator: Callable[
        [str],
        list[str] | dict,
    ] = generate_questions_from_context_with_audit,
) -> tuple[DefenseTask, TaskStep, Path]:
    task = load_defense_task(
        task_id=task_id,
        directory=directory,
    )

    step = task.get_current_step()

    if step is None:
        raise ValueError("当前任务没有可执行步骤")

    if step.status == "completed":
        raise ValueError("当前步骤已经完成，不能重复执行")

    try:
        executed_step = execute_task_step(
            step,
            vector_store_path=vector_store_path,
            top_k=top_k,
            embedding_fn=embedding_fn,
            question_generator=question_generator,
        )
    except Exception as error:
        step.mark_failed(f"{type(error).__name__}: {error}")
        task.mark_failed(step.error or str(error))
        save_defense_task(
            task,
            directory=directory,
        )
        raise

    task_path = save_defense_task(
        task,
        directory=directory,
    )

    return task, executed_step, task_path


def get_defense_task(
    task_id: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
) -> DefenseTask:
    return load_defense_task(
        task_id=task_id,
        directory=directory,
    )
