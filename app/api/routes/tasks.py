from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.task_store import DEFAULT_TASK_DIRECTORY


router = APIRouter(prefix="/tasks", tags=["tasks"])


class CreateTaskRequest(BaseModel):
    topic: str = Field(min_length=1)


class TaskResponse(BaseModel):
    task: dict[str, Any]
    path: str | None = None


class TaskStepResponse(BaseModel):
    task: dict[str, Any]
    step: dict[str, Any] | None
    path: str | None = None


class StartTaskStepRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)


def get_task_directory() -> Path:
    return DEFAULT_TASK_DIRECTORY


def create_task_service(
    topic: str,
    directory: Path,
):
    from app.task_service import create_defense_task

    return create_defense_task(
        topic=topic,
        directory=directory,
    )


def get_task_service(
    task_id: str,
    directory: Path,
):
    from app.task_service import get_defense_task

    return get_defense_task(
        task_id=task_id,
        directory=directory,
    )


def start_task_step_service(
    task_id: str,
    directory: Path,
    input: dict[str, Any],
):
    from app.task_service import start_next_task_step

    return start_next_task_step(
        task_id=task_id,
        directory=directory,
        input=input,
    )


def execute_task_step_service(
    task_id: str,
    directory: Path,
):
    from app.task_service import execute_current_task_step

    return execute_current_task_step(
        task_id=task_id,
        directory=directory,
    )


@router.post("")
def create_task(
    request: CreateTaskRequest,
    directory: Path = Depends(get_task_directory),
) -> TaskResponse:
    topic = request.topic.strip()

    if not topic:
        raise HTTPException(
            status_code=422,
            detail="topic must not be empty",
        )

    task, task_path = create_task_service(
        topic=topic,
        directory=directory,
    )

    return TaskResponse(
        task=asdict(task),
        path=str(task_path),
    )


@router.get("/{task_id}")
def get_task(
    task_id: str,
    directory: Path = Depends(get_task_directory),
) -> TaskResponse:
    try:
        task = get_task_service(
            task_id=task_id,
            directory=directory,
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return TaskResponse(
        task=asdict(task),
        path=str(directory / f"{task.task_id}.json"),
    )


@router.post("/{task_id}/steps/start")
def start_task_step(
    task_id: str,
    request: StartTaskStepRequest,
    directory: Path = Depends(get_task_directory),
) -> TaskStepResponse:
    try:
        task, step, task_path = start_task_step_service(
            task_id=task_id,
            directory=directory,
            input=request.input,
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return TaskStepResponse(
        task=asdict(task),
        step=asdict(step) if step is not None else None,
        path=str(task_path),
    )


@router.post("/{task_id}/steps/execute")
def execute_task_step(
    task_id: str,
    directory: Path = Depends(get_task_directory),
) -> TaskStepResponse:
    try:
        task, step, task_path = execute_task_step_service(
            task_id=task_id,
            directory=directory,
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return TaskStepResponse(
        task=asdict(task),
        step=asdict(step),
        path=str(task_path),
    )
