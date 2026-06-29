from dataclasses import asdict

import pytest

from app.postgres_task_repository import PostgresTaskRepository
from app.storage_repositories import TaskRepository
from app.task_models import DefenseTask, TaskStep


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


def create_task() -> DefenseTask:
    task = DefenseTask(
        task_id="task-1",
        topic="system architecture",
    )
    step = TaskStep(step_type="retrieve_context")
    step.mark_completed(
        output={
            "context": "module design",
        }
    )
    task.add_step(step)

    return task


def test_postgres_task_repository_saves_task_with_upsert():
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    repository: TaskRepository = PostgresTaskRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )
    task = create_task()

    saved_id = repository.save(task)

    assert saved_id == "task-1"
    assert connection.committed is True
    assert connection.rolled_back is False
    assert connection.closed is True
    assert cursor.closed is True

    query, params = cursor.executed[0]
    assert "INSERT INTO defense_tasks" in query
    assert "ON CONFLICT (task_id) DO UPDATE" in query
    assert params[0] == task.task_id
    assert params[1] == task.topic
    assert params[2] == task.status
    assert params[3] == task.current_step_id
    assert params[5] == task.created_at
    assert params[6] == task.updated_at


def test_postgres_task_repository_loads_task_from_payload_dict():
    task = create_task()
    cursor = FakeCursor(row=(asdict(task),))
    connection = FakeConnection(cursor)
    repository: TaskRepository = PostgresTaskRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )

    loaded_task = repository.load("task-1")

    assert loaded_task == task
    assert loaded_task.steps[0].output["context"] == "module design"
    assert connection.closed is True
    assert cursor.closed is True
    query, params = cursor.executed[0]
    assert query == "SELECT payload FROM defense_tasks WHERE task_id = %s"
    assert params == ("task-1",)


def test_postgres_task_repository_loads_task_from_payload_json_string():
    task = create_task()
    payload = (
        '{"task_id":"task-1","topic":"system architecture",'
        '"status":"running","current_step_id":null,"steps":[],'
        '"metadata":{},"created_at":"2026-01-01T00:00:00+00:00",'
        '"updated_at":"2026-01-01T00:00:00+00:00"}'
    )
    cursor = FakeCursor(row=(payload,))
    connection = FakeConnection(cursor)
    repository = PostgresTaskRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )

    loaded_task = repository.load(task.task_id)

    assert loaded_task.task_id == "task-1"
    assert loaded_task.topic == "system architecture"


def test_postgres_task_repository_raises_for_missing_task():
    cursor = FakeCursor(row=None)
    connection = FakeConnection(cursor)
    repository = PostgresTaskRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )

    with pytest.raises(FileNotFoundError):
        repository.load("missing-task")

    assert connection.closed is True
    assert cursor.closed is True


def test_postgres_task_repository_rolls_back_on_save_failure():
    cursor = FakeCursor(fail_on_execute=True)
    connection = FakeConnection(cursor)
    repository = PostgresTaskRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )

    with pytest.raises(RuntimeError):
        repository.save(create_task())

    assert connection.committed is False
    assert connection.rolled_back is True
    assert connection.closed is True
    assert cursor.closed is True


def test_postgres_task_repository_requires_database_url():
    with pytest.raises(ValueError):
        PostgresTaskRepository("")


def test_postgres_task_repository_rejects_invalid_payload():
    cursor = FakeCursor(row=({"task_id": "task-1"},))
    connection = FakeConnection(cursor)
    repository = PostgresTaskRepository(
        "postgresql://example",
        connect_fn=lambda database_url: connection,
    )

    with pytest.raises(ValueError, match="missing fields"):
        repository.load("task-1")
