import json

from dataclasses import asdict
from typing import Any, Callable, Protocol

from app.session_models import AgentSession
from app.session_store import validate_session_id


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


class PostgresSessionRepository:
    def __init__(
        self,
        database_url: str,
        connect_fn: ConnectFn | None = None,
    ):
        if not database_url.strip():
            raise ValueError("database_url is required")

        self.database_url = database_url
        self.connect_fn = connect_fn

    def save(self, session: AgentSession) -> str:
        validate_session_id(session.session_id)

        payload = asdict(session)
        connection = self._connect()
        cursor = connection.cursor()

        try:
            cursor.execute(
                (
                    "INSERT INTO agent_sessions "
                    "(session_id, payload, created_at) "
                    "VALUES (%s, %s, %s) "
                    "ON CONFLICT (session_id) DO UPDATE SET "
                    "payload = EXCLUDED.payload, "
                    "updated_at = now()"
                ),
                (
                    session.session_id,
                    _jsonb(payload),
                    session.created_at,
                ),
            )
            connection.commit()
            return session.session_id
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def load(self, session_id: str) -> AgentSession:
        validate_session_id(session_id)

        connection = self._connect()
        cursor = connection.cursor()

        try:
            cursor.execute(
                "SELECT payload FROM agent_sessions WHERE session_id = %s",
                (session_id,),
            )
            row = cursor.fetchone()

            if row is None:
                raise FileNotFoundError(f"Agent session not found: {session_id}")

            session = _session_from_payload(row[0])

            if session.session_id != session_id:
                raise ValueError(
                    "Loaded PostgreSQL session payload session_id does not "
                    f"match requested session_id: {session_id}"
                )

            return session
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


def _session_from_payload(payload: Any) -> AgentSession:
    if isinstance(payload, str):
        payload = json.loads(payload)

    if not isinstance(payload, dict):
        raise ValueError("PostgreSQL session payload must be a JSON object")

    required_fields = {
        "session_id",
        "created_at",
        "messages",
        "metadata",
    }
    missing_fields = required_fields - payload.keys()

    if missing_fields:
        raise ValueError(
            "PostgreSQL session payload missing fields: "
            f"{sorted(missing_fields)}"
        )

    if not isinstance(payload["messages"], list):
        raise ValueError("PostgreSQL session payload messages must be a list")

    if not isinstance(payload["metadata"], dict):
        raise ValueError("PostgreSQL session payload metadata must be a dict")

    return AgentSession(
        session_id=payload["session_id"],
        created_at=payload["created_at"],
        messages=payload["messages"],
        metadata=payload["metadata"],
    )
