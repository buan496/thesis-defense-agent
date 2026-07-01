import asyncio
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.async_task_runner import AsyncTaskRunner
from app.config import ASYNC_TASK_MAX_CONCURRENT_TASKS, ASYNC_TASK_STORE_PATH


router = APIRouter(prefix="/async-tasks", tags=["async-tasks"])
_runner = AsyncTaskRunner(
    max_concurrent_tasks=ASYNC_TASK_MAX_CONCURRENT_TASKS,
    storage_path=ASYNC_TASK_STORE_PATH,
)


class CreateAsyncTaskRequest(BaseModel):
    name: str = Field(min_length=1)
    delay_seconds: float = Field(default=0.05, ge=0, le=10)
    result: str = Field(default="ok")


class AsyncTaskResponse(BaseModel):
    task: dict[str, Any]


async def demo_sleep_job(
    delay_seconds: float,
    result: str,
) -> dict[str, Any]:
    await asyncio.sleep(delay_seconds)
    return {
        "result": result,
        "delay_seconds": delay_seconds,
    }


def get_async_task_runner() -> AsyncTaskRunner:
    return _runner


@router.post("")
async def create_async_task(
    request: CreateAsyncTaskRequest,
    runner: AsyncTaskRunner = Depends(get_async_task_runner),
) -> AsyncTaskResponse:
    name = request.name.strip()

    if not name:
        raise HTTPException(
            status_code=422,
            detail="name must not be empty",
        )

    try:
        record = runner.create_task(
            name=name,
            coroutine_factory=demo_sleep_job,
            delay_seconds=request.delay_seconds,
            result=request.result,
        )
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return AsyncTaskResponse(
        task=record.to_dict(),
    )


@router.get("/{task_id}")
async def get_async_task(
    task_id: str,
    runner: AsyncTaskRunner = Depends(get_async_task_runner),
) -> AsyncTaskResponse:
    try:
        status = runner.get_task_status(task_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    return AsyncTaskResponse(task=status)


@router.delete("/{task_id}")
async def cancel_async_task(
    task_id: str,
    runner: AsyncTaskRunner = Depends(get_async_task_runner),
) -> AsyncTaskResponse:
    try:
        status = await runner.cancel_task(task_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    return AsyncTaskResponse(task=status)
