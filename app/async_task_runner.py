import asyncio
import inspect
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


AsyncCallable = Callable[..., Awaitable[Any]]


@dataclass
class AsyncTaskRecord:
    task_id: str
    name: str
    status: str
    created_at: float
    started_at: float | None = None
    finished_at: float | None = None
    result: Any = None
    error_type: str | None = None
    error_message: str | None = None
    task: asyncio.Task[Any] | None = field(default=None, repr=False)

    @property
    def duration_ms(self) -> float | None:
        if self.started_at is None:
            return None

        end_time = self.finished_at if self.finished_at is not None else time.monotonic()
        return (end_time - self.started_at) * 1000

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "result": self.result,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }


class AsyncTaskRunner:
    def __init__(self) -> None:
        self._records: dict[str, AsyncTaskRecord] = {}

    def create_task(
        self,
        name: str,
        coroutine_factory: AsyncCallable,
        *args: Any,
        **kwargs: Any,
    ) -> AsyncTaskRecord:
        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError("task name must not be empty")

        if not callable(coroutine_factory):
            raise TypeError("coroutine_factory must be callable")

        task_id = uuid.uuid4().hex
        record = AsyncTaskRecord(
            task_id=task_id,
            name=normalized_name,
            status="pending",
            created_at=time.monotonic(),
        )
        record.task = asyncio.create_task(
            self._run_record(
                record,
                coroutine_factory,
                *args,
                **kwargs,
            )
        )
        self._records[task_id] = record
        return record

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        return self._get_record(task_id).to_dict()

    async def await_task(
        self,
        task_id: str,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        record = self._get_record(task_id)

        if record.task is None:
            raise RuntimeError("task record has no asyncio task")

        try:
            await asyncio.wait_for(
                asyncio.shield(record.task),
                timeout=timeout,
            )
        except asyncio.TimeoutError as error:
            raise TimeoutError(f"task timed out: {task_id}") from error

        return record.to_dict()

    async def cancel_task(self, task_id: str) -> dict[str, Any]:
        record = self._get_record(task_id)

        if record.task is None:
            raise RuntimeError("task record has no asyncio task")

        if record.task.done():
            return record.to_dict()

        record.status = "cancelling"
        record.task.cancel()

        try:
            await record.task
        except asyncio.CancelledError:
            pass

        return record.to_dict()

    def list_task_statuses(self) -> list[dict[str, Any]]:
        return [
            record.to_dict()
            for record in self._records.values()
        ]

    def _get_record(self, task_id: str) -> AsyncTaskRecord:
        try:
            return self._records[task_id]
        except KeyError as error:
            raise KeyError(f"task not found: {task_id}") from error

    async def _run_record(
        self,
        record: AsyncTaskRecord,
        coroutine_factory: AsyncCallable,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        record.status = "running"
        record.started_at = time.monotonic()

        try:
            coroutine = coroutine_factory(*args, **kwargs)

            if not inspect.isawaitable(coroutine):
                raise TypeError("coroutine_factory must return an awaitable")

            record.result = await coroutine
            record.status = "completed"
        except asyncio.CancelledError:
            record.status = "cancelled"
            record.error_type = "CancelledError"
            record.error_message = "task was cancelled"
            raise
        except Exception as error:
            record.status = "failed"
            record.error_type = type(error).__name__
            record.error_message = str(error)
        finally:
            record.finished_at = time.monotonic()
