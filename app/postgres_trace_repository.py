import json

from typing import Any, Callable, Protocol


class CursorProtocol(Protocol):
    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> Any:
        ...

    def fetchone(self) -> tuple[Any, ...] | None:
        ...

    def fetchall(self) -> list[tuple[Any, ...]]:
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


class PostgresTraceRepository:
    def __init__(
        self,
        database_url: str,
        connect_fn: ConnectFn | None = None,
    ):
        if not database_url.strip():
            raise ValueError("database_url is required")

        self.database_url = database_url
        self.connect_fn = connect_fn

    def append(self, record: dict[str, Any]) -> str:
        if not isinstance(record, dict):
            raise ValueError("trace record must be a dict")

        connection = self._connect()
        cursor = connection.cursor()

        try:
            cursor.execute(
                (
                    "INSERT INTO trace_records "
                    "(source_type, source_id, event_type, success, payload) "
                    "VALUES (%s, %s, %s, %s, %s) "
                    "RETURNING id"
                ),
                (
                    _extract_source_type(record),
                    _extract_source_id(record),
                    _extract_event_type(record),
                    _extract_success(record),
                    _jsonb(record),
                ),
            )
            row = cursor.fetchone()

            if row is None:
                raise RuntimeError("PostgreSQL trace insert did not return id")

            connection.commit()
            return f"postgres:trace_records:{row[0]}"
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def load_all(self) -> list[dict[str, Any]]:
        connection = self._connect()
        cursor = connection.cursor()

        try:
            cursor.execute("SELECT payload FROM trace_records ORDER BY id ASC")
            return [
                _payload_to_record(row[0])
                for row in cursor.fetchall()
            ]
        finally:
            cursor.close()
            connection.close()

    def _connect(self) -> ConnectionProtocol:
        if self.connect_fn is not None:
            return self.connect_fn(self.database_url)

        import psycopg

        return psycopg.connect(self.database_url)


def _extract_source_type(record: dict[str, Any]) -> str:
    source_type = record.get("source_type")

    if isinstance(source_type, str) and source_type.strip():
        return source_type

    if "result" in record and "user_message" in record:
        return "agent"

    if record.get("event_type") == "sub_agent_tool_executed":
        return "sub_agent_execution"

    if record.get("event_type") == "sub_agent_plan_created":
        return "sub_agent_plan"

    return "unknown"


def _extract_source_id(record: dict[str, Any]) -> str | None:
    source_id = record.get("source_id")

    if isinstance(source_id, str) and source_id.strip():
        return source_id

    task_id = record.get("task_id")

    if isinstance(task_id, str) and task_id.strip():
        return task_id

    return None


def _extract_event_type(record: dict[str, Any]) -> str:
    event_type = record.get("event_type")

    if isinstance(event_type, str) and event_type.strip():
        return event_type

    if "result" in record and "user_message" in record:
        return "agent_run"

    return "unknown"


def _extract_success(record: dict[str, Any]) -> bool | None:
    success = record.get("success")

    if isinstance(success, bool):
        return success

    audit = record.get("audit")

    if isinstance(audit, dict) and isinstance(audit.get("success"), bool):
        return audit["success"]

    return None


def _jsonb(value: dict[str, Any]) -> Any:
    from psycopg.types.json import Jsonb

    return Jsonb(value)


def _payload_to_record(payload: Any) -> dict[str, Any]:
    if isinstance(payload, str):
        payload = json.loads(payload)

    if not isinstance(payload, dict):
        raise ValueError("PostgreSQL trace payload must be a JSON object")

    return payload
