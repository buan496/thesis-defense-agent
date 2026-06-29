from dataclasses import asdict

import pytest

from app.postgres_session_repository import PostgresSessionRepository
from app.session_models import AgentSession
from app.storage_repositories import SessionRepository


class FakeCursor:
    def __init__(
        self,
        row=None,
        fail_on_execute=False,
    ):
        self.row = row
        self.fail_on_execute = fail_on_execute
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        if self.fail_on_execute:
            raise RuntimeError("database write failed")

        self.executed.append((query, params))

    def fetchone(self):
        return self.row

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def create_session() -> AgentSession:
    session = AgentSession(
        session_id="session-1",
        metadata={
            "thesis_direction": "bilingual speech recognition",
        },
    )
    session.add_message(
        role="user",
        content="remember my thesis direction",
    )

    return session


def test_postgres_session_repository_saves_session_with_upsert():
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    repository: SessionRepository = PostgresSessionRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )
    session = create_session()

    saved_id = repository.save(session)

    assert saved_id == "session-1"
    assert connection.committed is True
    assert connection.rolled_back is False
    assert connection.closed is True
    assert cursor.closed is True

    query, params = cursor.executed[0]
    assert "INSERT INTO agent_sessions" in query
    assert "ON CONFLICT (session_id) DO UPDATE" in query
    assert "updated_at = now()" in query
    assert params[0] == session.session_id
    assert params[2] == session.created_at


def test_postgres_session_repository_loads_session_from_payload_dict():
    session = create_session()
    cursor = FakeCursor(row=(asdict(session),))
    connection = FakeConnection(cursor)
    repository: SessionRepository = PostgresSessionRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )

    loaded_session = repository.load("session-1")

    assert loaded_session == session
    assert loaded_session.messages[0]["content"] == "remember my thesis direction"
    assert loaded_session.metadata["thesis_direction"] == (
        "bilingual speech recognition"
    )
    assert connection.closed is True
    assert cursor.closed is True
    query, params = cursor.executed[0]
    assert query == "SELECT payload FROM agent_sessions WHERE session_id = %s"
    assert params == ("session-1",)


def test_postgres_session_repository_loads_session_from_payload_json_string():
    payload = (
        '{"session_id":"session-1",'
        '"created_at":"2026-01-01T00:00:00+00:00",'
        '"messages":[{"role":"user","content":"hello"}],'
        '"metadata":{"topic":"system architecture"}}'
    )
    cursor = FakeCursor(row=(payload,))
    connection = FakeConnection(cursor)
    repository = PostgresSessionRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )

    loaded_session = repository.load("session-1")

    assert loaded_session.session_id == "session-1"
    assert loaded_session.messages[0]["content"] == "hello"
    assert loaded_session.metadata["topic"] == "system architecture"


def test_postgres_session_repository_raises_for_missing_session():
    cursor = FakeCursor(row=None)
    connection = FakeConnection(cursor)
    repository = PostgresSessionRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )

    with pytest.raises(FileNotFoundError):
        repository.load("missing-session")

    assert connection.closed is True
    assert cursor.closed is True


def test_postgres_session_repository_rolls_back_on_save_failure():
    cursor = FakeCursor(fail_on_execute=True)
    connection = FakeConnection(cursor)
    repository = PostgresSessionRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )

    with pytest.raises(RuntimeError):
        repository.save(create_session())

    assert connection.committed is False
    assert connection.rolled_back is True
    assert connection.closed is True
    assert cursor.closed is True


def test_postgres_session_repository_requires_database_url():
    with pytest.raises(ValueError):
        PostgresSessionRepository("")


def test_postgres_session_repository_rejects_invalid_payload():
    cursor = FakeCursor(row=({"session_id": "session-1"},))
    connection = FakeConnection(cursor)
    repository = PostgresSessionRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )

    with pytest.raises(ValueError, match="missing fields"):
        repository.load("session-1")


def test_postgres_session_repository_rejects_invalid_metadata_type():
    payload = {
        "session_id": "session-1",
        "created_at": "2026-01-01T00:00:00+00:00",
        "messages": [],
        "metadata": [],
    }
    cursor = FakeCursor(row=(payload,))
    connection = FakeConnection(cursor)
    repository = PostgresSessionRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )

    with pytest.raises(ValueError, match="metadata must be a dict"):
        repository.load("session-1")
