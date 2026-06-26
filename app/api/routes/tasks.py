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


def get_task_directory() -> Path:
    return DEFAULT_TASK_DIRECTORY


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

    from app.task_service import create_defense_task

    task, task_path = create_defense_task(
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
    from app.task_service import get_defense_task

    try:
        task = get_defense_task(
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
