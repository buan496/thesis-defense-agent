import pytest

from app.postgres_trace_repository import PostgresTraceRepository
from app.storage_repositories import TraceRepository


class FakeCursor:
    def __init__(
        self,
        one_row=(1,),
        all_rows=None,
        fail_on_execute=False,
    ):
        self.one_row = one_row
        self.all_rows = all_rows or []
        self.fail_on_execute = fail_on_execute
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        if self.fail_on_execute:
            raise RuntimeError("database write failed")

        self.executed.append((query, params))

    def fetchone(self):
        return self.one_row

    def fetchall(self):
        return self.all_rows

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


def test_postgres_trace_repository_appends_trace_record():
    cursor = FakeCursor(one_row=(42,))
    connection = FakeConnection(cursor)
    repository: TraceRepository = PostgresTraceRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )
    record = {
        "source_type": "agent",
        "source_id": "session-1",
        "event_type": "agent_run",
        "success": True,
        "message": "ok",
    }

    saved_id = repository.append(record)

    assert saved_id == "postgres:trace_records:42"
    assert connection.committed is True
    assert connection.rolled_back is False
    assert connection.closed is True
    assert cursor.closed is True

    query, params = cursor.executed[0]
    assert "INSERT INTO trace_records" in query
    assert "RETURNING id" in query
    assert params[:4] == (
        "agent",
        "session-1",
        "agent_run",
        True,
    )


def test_postgres_trace_repository_infers_agent_trace_fields():
    cursor = FakeCursor(one_row=(1,))
    connection = FakeConnection(cursor)
    repository = PostgresTraceRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )
    record = {
        "user_message": "系统架构",
        "result": {
            "tool_traces": [],
        },
    }

    repository.append(record)

    _, params = cursor.executed[0]
    assert params[0] == "agent"
    assert params[1] is None
    assert params[2] == "agent_run"
    assert params[3] is None


def test_postgres_trace_repository_infers_sub_agent_execution_fields():
    cursor = FakeCursor(one_row=(1,))
    connection = FakeConnection(cursor)
    repository = PostgresTraceRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )
    record = {
        "event_type": "sub_agent_tool_executed",
        "audit": {
            "success": False,
        },
    }

    repository.append(record)

    _, params = cursor.executed[0]
    assert params[0] == "sub_agent_execution"
    assert params[2] == "sub_agent_tool_executed"
    assert params[3] is False


def test_postgres_trace_repository_loads_all_payloads_in_order():
    records = [
        {"event_type": "agent_run", "success": True},
        '{"event_type":"tool_call","success":false}',
    ]
    cursor = FakeCursor(
        all_rows=[
            (records[0],),
            (records[1],),
        ]
    )
    connection = FakeConnection(cursor)
    repository: TraceRepository = PostgresTraceRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )

    loaded_records = repository.load_all()

    assert loaded_records == [
        {"event_type": "agent_run", "success": True},
        {"event_type": "tool_call", "success": False},
    ]
    assert connection.closed is True
    assert cursor.closed is True
    query, params = cursor.executed[0]
    assert query == "SELECT payload FROM trace_records ORDER BY id ASC"
    assert params is None


def test_postgres_trace_repository_rolls_back_on_append_failure():
    cursor = FakeCursor(fail_on_execute=True)
    connection = FakeConnection(cursor)
    repository = PostgresTraceRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )

    with pytest.raises(RuntimeError):
        repository.append({"event_type": "agent_run"})

    assert connection.committed is False
    assert connection.rolled_back is True
    assert connection.closed is True
    assert cursor.closed is True


def test_postgres_trace_repository_requires_database_url():
    with pytest.raises(ValueError):
        PostgresTraceRepository("")


def test_postgres_trace_repository_rejects_non_dict_append():
    repository = PostgresTraceRepository(
        "postgresql://example",
        connect_fn=lambda database_url: FakeConnection(FakeCursor()),
    )

    with pytest.raises(ValueError, match="trace record must be a dict"):
        repository.append(["not", "a", "dict"])


def test_postgres_trace_repository_rejects_invalid_payload():
    cursor = FakeCursor(all_rows=[(["not", "a", "dict"],)])
    connection = FakeConnection(cursor)
    repository = PostgresTraceRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )

    with pytest.raises(ValueError, match="trace payload must be a JSON object"):
        repository.load_all()
