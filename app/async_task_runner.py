import asyncio
import inspect
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable


AsyncCallable = Callable[..., Awaitable[Any]]


@dataclass
class AsyncTaskRecord:
    task_id: str
    name: str
    status: str
    created_at: float
    idempotency_key: str | None = None
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
            "idempotency_key": self.idempotency_key,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "result": self.result,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AsyncTaskRecord":
        return cls(
            task_id=data["task_id"],
            name=data["name"],
            status=data["status"],
            created_at=data["created_at"],
            idempotency_key=data.get("idempotency_key"),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            result=data.get("result"),
            error_type=data.get("error_type"),
            error_message=data.get("error_message"),
        )

    @property
    def is_terminal(self) -> bool:
        return self.status in {"completed", "failed", "cancelled"}


class AsyncTaskRunner:
    def __init__(
        self,
        max_concurrent_tasks: int | None = None,
        storage_path: str | Path | None = None,
    ) -> None:
        if max_concurrent_tasks is not None and max_concurrent_tasks <= 0:
            raise ValueError("max_concurrent_tasks must be greater than 0")

        self._records: dict[str, AsyncTaskRecord] = {}
        self.max_concurrent_tasks = max_concurrent_tasks
        self.storage_path = Path(storage_path) if storage_path is not None else None
        self._semaphore = (
            asyncio.Semaphore(max_concurrent_tasks)
            if max_concurrent_tasks is not None
            else None
        )
        self._load_records()

    def create_task(
        self,
        name: str,
        coroutine_factory: AsyncCallable,
        *args: Any,
        idempotency_key: str | None = None,
        **kwargs: Any,
    ) -> AsyncTaskRecord:
        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError("task name must not be empty")

        if not callable(coroutine_factory):
            raise TypeError("coroutine_factory must be callable")

        normalized_idempotency_key = self._normalize_idempotency_key(
            idempotency_key,
        )

        if normalized_idempotency_key is not None:
            existing_record = self.get_task_by_idempotency_key(
                normalized_idempotency_key,
            )

            if existing_record is not None:
                return existing_record

        task_id = uuid.uuid4().hex
        record = AsyncTaskRecord(
            task_id=task_id,
            name=normalized_name,
            status="pending",
            idempotency_key=normalized_idempotency_key,
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
        self._persist_records()
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
            if record.is_terminal:
                return record.to_dict()

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
            if record.is_terminal:
                return record.to_dict()

            raise RuntimeError("task record has no asyncio task")

        if record.task.done():
            return record.to_dict()

        record.status = "cancelling"
        self._persist_records()
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

    def get_task_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> AsyncTaskRecord | None:
        normalized_key = self._normalize_idempotency_key(idempotency_key)

        if normalized_key is None:
            return None

        for record in self._records.values():
            if record.idempotency_key == normalized_key:
                return record

        return None

    def _normalize_idempotency_key(
        self,
        idempotency_key: str | None,
    ) -> str | None:
        if idempotency_key is None:
            return None

        normalized_key = idempotency_key.strip()

        if not normalized_key:
            raise ValueError("idempotency_key must not be empty")

        return normalized_key

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
        try:
            if self._semaphore is not None:
                async with self._semaphore:
                    await self._execute_record(
                        record,
                        coroutine_factory,
                        *args,
                        **kwargs,
                    )
                return

            await self._execute_record(
                record,
                coroutine_factory,
                *args,
                **kwargs,
            )
        except asyncio.CancelledError:
            if record.status != "cancelled":
                record.status = "cancelled"
                record.error_type = "CancelledError"
                record.error_message = "task was cancelled"
                record.finished_at = time.monotonic()
                self._persist_records()
            raise

    async def _execute_record(
        self,
        record: AsyncTaskRecord,
        coroutine_factory: AsyncCallable,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        record.status = "running"
        record.started_at = time.monotonic()
        self._persist_records()

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
            self._persist_records()

    def _load_records(self) -> None:
        if self.storage_path is None or not self.storage_path.exists():
            return

        with self.storage_path.open(encoding="utf-8") as file:
            data = json.loads(file.read())

        if not isinstance(data, list):
            raise ValueError("async task storage must contain a list")

        for item in data:
            record = AsyncTaskRecord.from_dict(item)
            self._recover_interrupted_record(record)
            self._records[record.task_id] = record

        self._persist_records()

    def _recover_interrupted_record(
        self,
        record: AsyncTaskRecord,
    ) -> None:
        if record.status in {"pending", "running", "cancelling"}:
            record.status = "failed"
            record.error_type = "TaskInterruptedError"
            record.error_message = "task was interrupted before completion"
            record.finished_at = (
                record.finished_at
                or record.started_at
                or record.created_at
            )

    def _persist_records(self) -> None:
        if self.storage_path is None:
            return

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.storage_path.with_suffix(
            f"{self.storage_path.suffix}.tmp",
        )
        data = [
            record.to_dict()
            for record in self._records.values()
        ]

        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        temporary_path.replace(self.storage_path)
