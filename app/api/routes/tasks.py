from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.middleware import CORRELATION_ID_HEADER
from app.api.routes.async_tasks import get_async_task_runner
from app.async_boundary import run_sync_in_thread
from app.async_task_runner import AsyncTaskRunner
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


class AsyncTaskStepResponse(BaseModel):
    async_task: dict[str, Any]


class TaskAnalysisResponse(BaseModel):
    analysis: dict[str, Any]


class TaskReportResponse(BaseModel):
    path: str
    markdown: str


class StartTaskStepRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)


class SubmitAnswerRequest(BaseModel):
    answer: str = Field(min_length=1)


def get_task_directory() -> Path:
    return DEFAULT_TASK_DIRECTORY


def get_request_correlation_id(request: Request) -> str | None:
    state_correlation_id = getattr(request.state, "correlation_id", None)

    if state_correlation_id:
        return state_correlation_id

    header_value = request.headers.get(CORRELATION_ID_HEADER)

    if header_value and header_value.strip():
        return header_value.strip()

    return None


def create_task_service(
    topic: str,
    directory: Path,
    correlation_id: str | None = None,
):
    from app.task_service import create_defense_task

    return create_defense_task(
        topic=topic,
        directory=directory,
        correlation_id=correlation_id,
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
    correlation_id: str | None = None,
):
    from app.task_service import start_next_task_step

    return start_next_task_step(
        task_id=task_id,
        directory=directory,
        input=input,
        correlation_id=correlation_id,
    )


def execute_task_step_service(
    task_id: str,
    directory: Path,
    correlation_id: str | None = None,
):
    from app.task_service import execute_current_task_step

    return execute_current_task_step(
        task_id=task_id,
        directory=directory,
        correlation_id=correlation_id,
    )


async def execute_task_step_background_job(
    task_id: str,
    directory: Path,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    task, step, task_path = await run_sync_in_thread(
        execute_task_step_service,
        task_id=task_id,
        directory=directory,
        correlation_id=correlation_id,
    )

    return {
        "task": asdict(task),
        "step": asdict(step),
        "path": str(task_path),
    }


def submit_task_answer_service(
    task_id: str,
    answer: str,
    directory: Path,
    correlation_id: str | None = None,
):
    from app.task_service import submit_task_answer

    return submit_task_answer(
        task_id=task_id,
        answer=answer,
        directory=directory,
        correlation_id=correlation_id,
    )


def submit_follow_up_answer_service(
    task_id: str,
    answer: str,
    directory: Path,
    correlation_id: str | None = None,
):
    from app.task_service import submit_follow_up_answer

    return submit_follow_up_answer(
        task_id=task_id,
        answer=answer,
        directory=directory,
        correlation_id=correlation_id,
    )


def analyze_task_service(
    task_id: str,
    directory: Path,
) -> dict[str, Any]:
    from app.task_service import get_defense_task
    from app.task_trace_analyzer import analyze_task_trace

    task = get_defense_task(
        task_id=task_id,
        directory=directory,
    )

    return analyze_task_trace(task)


def export_task_report_service(
    task_id: str,
    directory: Path,
) -> tuple[Path, str]:
    from app.task_markdown_exporter import export_task_markdown_report
    from app.task_service import get_defense_task

    task = get_defense_task(
        task_id=task_id,
        directory=directory,
    )
    output_path = export_task_markdown_report(task)

    return output_path, output_path.read_text(encoding="utf-8")


@router.post("")
def create_task(
    http_request: Request,
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
        correlation_id=get_request_correlation_id(http_request),
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
    http_request: Request,
    request: StartTaskStepRequest,
    directory: Path = Depends(get_task_directory),
) -> TaskStepResponse:
    try:
        task, step, task_path = start_task_step_service(
            task_id=task_id,
            directory=directory,
            input=request.input,
            correlation_id=get_request_correlation_id(http_request),
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
    http_request: Request,
    directory: Path = Depends(get_task_directory),
) -> TaskStepResponse:
    try:
        task, step, task_path = execute_task_step_service(
            task_id=task_id,
            directory=directory,
            correlation_id=get_request_correlation_id(http_request),
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


@router.post("/{task_id}/steps/execute-async")
async def execute_task_step_async(
    task_id: str,
    http_request: Request,
    directory: Path = Depends(get_task_directory),
    async_runner: AsyncTaskRunner = Depends(get_async_task_runner),
) -> AsyncTaskStepResponse:
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

    current_step = task.get_current_step()

    if current_step is None:
        raise HTTPException(
            status_code=400,
            detail="current task has no executable step",
        )

    idempotency_key = (
        f"execute_task_step:{task.task_id}:{current_step.step_id}"
    )

    try:
        async_task = async_runner.create_task(
            name=f"execute_task_step:{task_id}",
            coroutine_factory=execute_task_step_background_job,
            task_id=task_id,
            directory=directory,
            correlation_id=get_request_correlation_id(http_request),
            idempotency_key=idempotency_key,
        )
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return AsyncTaskStepResponse(
        async_task=async_task.to_dict(),
    )


@router.post("/{task_id}/answer")
def submit_answer(
    task_id: str,
    http_request: Request,
    request: SubmitAnswerRequest,
    directory: Path = Depends(get_task_directory),
) -> TaskStepResponse:
    answer = request.answer.strip()

    if not answer:
        raise HTTPException(
            status_code=422,
            detail="answer must not be empty",
        )

    try:
        task, step, task_path = submit_task_answer_service(
            task_id=task_id,
            answer=answer,
            directory=directory,
            correlation_id=get_request_correlation_id(http_request),
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


@router.get("/{task_id}/analysis")
def analyze_task(
    task_id: str,
    directory: Path = Depends(get_task_directory),
) -> TaskAnalysisResponse:
    try:
        analysis = analyze_task_service(
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

    return TaskAnalysisResponse(analysis=analysis)


@router.post("/{task_id}/report/export")
def export_task_report(
    task_id: str,
    directory: Path = Depends(get_task_directory),
) -> TaskReportResponse:
    try:
        output_path, markdown = export_task_report_service(
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

    return TaskReportResponse(
        path=str(output_path),
        markdown=markdown,
    )


@router.post("/{task_id}/follow-up-answer")
def submit_follow_up_answer(
    task_id: str,
    http_request: Request,
    request: SubmitAnswerRequest,
    directory: Path = Depends(get_task_directory),
) -> TaskStepResponse:
    answer = request.answer.strip()

    if not answer:
        raise HTTPException(
            status_code=422,
            detail="answer must not be empty",
        )

    try:
        task, step, task_path = submit_follow_up_answer_service(
            task_id=task_id,
            answer=answer,
            directory=directory,
            correlation_id=get_request_correlation_id(http_request),
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
