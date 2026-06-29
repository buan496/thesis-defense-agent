from pathlib import Path
from collections.abc import Callable
from typing import Any

from app.answer_rewrite import rewrite_answer
from app.config import RAG_TOP_K, RAG_VECTOR_STORE_PATH
from app.long_term_memory import (
    add_training_summary,
    add_weakness,
    load_long_term_memory,
    save_long_term_memory,
)
from app.defense_questions import generate_questions_from_context_with_audit
from app.embeddings import create_embedding
from app.evaluation import evaluate_answer
from app.follow_up import generate_follow_up_question
from app.task_executor import execute_task_step
from app.task_models import DefenseTask, TaskStep
from app.training_summary import summarize_training
from app.task_runner import (
    complete_current_step,
    create_next_step,
    get_next_step_type,
)
from app.task_store import (
    DEFAULT_TASK_DIRECTORY,
    load_defense_task,
    save_defense_task,
)
from app.storage_repositories import TaskRepository


TaskSaveReference = str | Path


def _load_task(
    task_id: str,
    directory: str | Path,
    task_repository: TaskRepository | None,
) -> DefenseTask:
    if task_repository is not None:
        return task_repository.load(task_id)

    return load_defense_task(
        task_id=task_id,
        directory=directory,
    )


def _save_task(
    task: DefenseTask,
    directory: str | Path,
    task_repository: TaskRepository | None,
) -> TaskSaveReference:
    if task_repository is not None:
        return task_repository.save(task)

    return save_defense_task(
        task,
        directory=directory,
    )


def create_defense_task(
    topic: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
    task_repository: TaskRepository | None = None,
) -> tuple[DefenseTask, TaskSaveReference]:
    task = DefenseTask(topic=topic)

    task_path = _save_task(
        task,
        directory=directory,
        task_repository=task_repository,
    )

    return task, task_path


def start_next_task_step(
    task_id: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
    input: dict[str, Any] | None = None,
    task_repository: TaskRepository | None = None,
) -> tuple[DefenseTask, TaskStep | None, TaskSaveReference]:
    return _start_next_task_step_with_repository(
        task_id=task_id,
        directory=directory,
        input=input,
        task_repository=task_repository,
    )


def _start_next_task_step_with_repository(
    task_id: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
    input: dict[str, Any] | None = None,
    task_repository: TaskRepository | None = None,
) -> tuple[DefenseTask, TaskStep | None, TaskSaveReference]:
    task = _load_task(
        task_id=task_id,
        directory=directory,
        task_repository=task_repository,
    )

    step = create_next_step(
        task,
        input=input,
    )

    task_path = _save_task(
        task,
        directory=directory,
        task_repository=task_repository,
    )

    return task, step, task_path


def complete_task_step(
    task_id: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
    output: dict[str, Any] | None = None,
    task_repository: TaskRepository | None = None,
) -> tuple[DefenseTask, TaskStep, TaskSaveReference]:
    task = _load_task(
        task_id=task_id,
        directory=directory,
        task_repository=task_repository,
    )

    step = complete_current_step(
        task,
        output=output,
    )

    task_path = _save_task(
        task,
        directory=directory,
        task_repository=task_repository,
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
    answer_evaluator: Callable[[str, str], str] = evaluate_answer,
    answer_rewriter: Callable[
        [str, str, str | None],
        str,
    ] = rewrite_answer,
    follow_up_generator: Callable[
        [str, str, str | None, str | None],
        str,
    ] = generate_follow_up_question,
    follow_up_evaluator: Callable[[str, str], str] = evaluate_answer,
    training_summarizer: Callable[
        [str, str, str, str, str, str, str],
        str,
    ] = summarize_training,
    long_term_memory_path: str | Path | None = None,
    task_repository: TaskRepository | None = None,
) -> tuple[DefenseTask, TaskStep, TaskSaveReference]:
    task = _load_task(
        task_id=task_id,
        directory=directory,
        task_repository=task_repository,
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
            answer_evaluator=answer_evaluator,
            answer_rewriter=answer_rewriter,
            follow_up_generator=follow_up_generator,
            follow_up_evaluator=follow_up_evaluator,
            training_summarizer=training_summarizer,
        )
    except Exception as error:
        step.mark_failed(f"{type(error).__name__}: {error}")
        task.mark_failed(step.error or str(error))
        _save_task(
            task,
            directory=directory,
            task_repository=task_repository,
        )
        raise

    task_path = _save_task(
        task,
        directory=directory,
        task_repository=task_repository,
    )

    if get_next_step_type(task) is None:
        task.mark_completed()
        task_path = _save_task(
            task,
            directory=directory,
            task_repository=task_repository,
        )
    
    if (
        executed_step.step_type == "summarize_training"
        and executed_step.status == "completed"
        and long_term_memory_path is not None
    ):
        persist_training_summary_to_memory(
            task=task,
            step=executed_step,
            memory_path=long_term_memory_path,
        )

    return task, executed_step, task_path


def persist_training_summary_to_memory(
    task: DefenseTask,
    step: TaskStep,
    memory_path: str | Path,
) -> Path:
    summary = step.output.get("summary")

    if not summary:
        raise ValueError("summarize_training output missing summary")

    memory = load_long_term_memory(memory_path)
    memory = add_training_summary(
        memory,
        summary=summary,
        task_id=task.task_id,
        topic=task.topic,
    )

    for weakness in step.output.get("weaknesses", []):
        if isinstance(weakness, str) and weakness.strip():
            memory = add_weakness(
                memory,
                weakness=weakness,
                source_task_id=task.task_id,
            )

    return save_long_term_memory(memory, memory_path)


def submit_task_answer(
    task_id: str,
    answer: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
    task_repository: TaskRepository | None = None,
) -> tuple[DefenseTask, TaskStep, TaskSaveReference]:
    if not answer.strip():
        raise ValueError("学生回答不能为空")

    task = _load_task(
        task_id=task_id,
        directory=directory,
        task_repository=task_repository,
    )

    step = task.get_current_step()

    if step is None:
        raise ValueError("当前任务没有可提交回答的步骤")

    if step.step_type != "wait_for_answer":
        raise ValueError(
            "当前步骤不是 wait_for_answer，不能提交学生回答"
        )

    if step.status == "completed":
        raise ValueError("当前回答步骤已经完成，不能重复提交")

    output: dict[str, Any] = {
        "answer": answer,
    }

    if "question" in step.input:
        output["question"] = step.input["question"]

    step.mark_completed(output=output)

    task_path = _save_task(
        task,
        directory=directory,
        task_repository=task_repository,
    )

    return task, step, task_path


def submit_follow_up_answer(
    task_id: str,
    answer: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
    task_repository: TaskRepository | None = None,
) -> tuple[DefenseTask, TaskStep, TaskSaveReference]:
    if not answer.strip():
        raise ValueError("追问回答不能为空")

    task = _load_task(
        task_id=task_id,
        directory=directory,
        task_repository=task_repository,
    )

    step = task.get_current_step()

    if step is None:
        raise ValueError("当前任务没有可提交追问回答的步骤")

    if step.step_type != "wait_for_follow_up_answer":
        raise ValueError(
            "当前步骤不是 wait_for_follow_up_answer，不能提交追问回答"
        )

    if step.status == "completed":
        raise ValueError("当前追问回答步骤已经完成，不能重复提交")

    output: dict[str, Any] = {
        "follow_up_answer": answer,
    }

    if "follow_up_question" in step.input:
        output["follow_up_question"] = step.input["follow_up_question"]

    for field in [
        "question",
        "answer",
        "evaluation",
        "rewritten_answer",
    ]:
        if field in step.input:
            output[field] = step.input[field]

    step.mark_completed(output=output)

    task_path = _save_task(
        task,
        directory=directory,
        task_repository=task_repository,
    )

    return task, step, task_path


def get_defense_task(
    task_id: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
    task_repository: TaskRepository | None = None,
) -> DefenseTask:
    return _load_task(
        task_id=task_id,
        directory=directory,
        task_repository=task_repository,
    )
