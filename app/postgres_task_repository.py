import json

from dataclasses import asdict
from typing import Any, Callable, Protocol

from app.task_models import DefenseTask, TaskStep
from app.task_store import validate_task_id


class CursorProtocol(Protocol):
    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> Any:
        ...

    def fetchone(self) -> tuple[Any, ...] | None:
        ...

    def close(self) -> Any:
        ...


class ConnectionProtocol(Protocol):
    def cursor(self) -> CursorProtocol:
        ...

    def commit(self) -> Any:
        ...

    def rollback(self) -> Any:
        ...

    def close(self) -> Any:
        ...


ConnectFn = Callable[[str], ConnectionProtocol]


class PostgresTaskRepository:
    def __init__(
        self,
        database_url: str,
        connect_fn: ConnectFn | None = None,
    ):
        if not database_url.strip():
            raise ValueError("database_url is required")

        self.database_url = database_url
        self.connect_fn = connect_fn

    def save(self, task: DefenseTask) -> str:
        validate_task_id(task.task_id)

        payload = asdict(task)
        connection = self._connect()
        cursor = connection.cursor()

        try:
            cursor.execute(
                (
                    "INSERT INTO defense_tasks "
                    "(task_id, topic, status, current_step_id, payload, "
                    "created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s) "
                    "ON CONFLICT (task_id) DO UPDATE SET "
                    "topic = EXCLUDED.topic, "
                    "status = EXCLUDED.status, "
                    "current_step_id = EXCLUDED.current_step_id, "
                    "payload = EXCLUDED.payload, "
                    "updated_at = EXCLUDED.updated_at"
                ),
                (
                    task.task_id,
                    task.topic,
                    task.status,
                    task.current_step_id,
                    _jsonb(payload),
                    task.created_at,
                    task.updated_at,
                ),
            )
            connection.commit()
            return task.task_id
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def load(self, task_id: str) -> DefenseTask:
        validate_task_id(task_id)

        connection = self._connect()
        cursor = connection.cursor()

        try:
            cursor.execute(
                "SELECT payload FROM defense_tasks WHERE task_id = %s",
                (task_id,),
            )
            row = cursor.fetchone()

            if row is None:
                raise FileNotFoundError(f"Defense task not found: {task_id}")

            task = _task_from_payload(row[0])

            if task.task_id != task_id:
                raise ValueError(
                    "Loaded PostgreSQL task payload task_id does not match "
                    f"requested task_id: {task_id}"
                )

            return task
        finally:
            cursor.close()
            connection.close()

    def _connect(self) -> ConnectionProtocol:
        if self.connect_fn is not None:
            return self.connect_fn(self.database_url)

        import psycopg

        return psycopg.connect(self.database_url)


def _jsonb(value: dict) -> Any:
    from psycopg.types.json import Jsonb

    return Jsonb(value)


def _task_from_payload(payload: Any) -> DefenseTask:
    if isinstance(payload, str):
        payload = json.loads(payload)

    if not isinstance(payload, dict):
        raise ValueError("PostgreSQL task payload must be a JSON object")

    required_fields = {
        "task_id",
        "topic",
        "status",
        "current_step_id",
        "steps",
        "metadata",
        "created_at",
        "updated_at",
    }
    missing_fields = required_fields - payload.keys()

    if missing_fields:
        raise ValueError(
            f"PostgreSQL task payload missing fields: {sorted(missing_fields)}"
        )

    if not isinstance(payload["steps"], list):
        raise ValueError("PostgreSQL task payload steps must be a list")

    return DefenseTask(
        task_id=payload["task_id"],
        topic=payload["topic"],
        status=payload["status"],
        current_step_id=payload["current_step_id"],
        steps=[
            TaskStep(**step_data)
            for step_data in payload["steps"]
        ],
        metadata=payload["metadata"],
        created_at=payload["created_at"],
        updated_at=payload["updated_at"],
    )
