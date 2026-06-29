from app.postgres_session_repository import PostgresSessionRepository
from app.postgres_task_repository import PostgresTaskRepository
from app.postgres_trace_repository import PostgresTraceRepository
from app.repository_factory import (
    create_repositories,
    normalize_storage_backend,
)
from app.storage_repositories import (
    JsonSessionRepository,
    JsonTaskRepository,
    JsonlTraceRepository,
)

import pytest


def test_create_repositories_uses_json_backend_by_default(tmp_path):
    bundle = create_repositories(
        storage_backend="json",
        task_directory=tmp_path / "tasks",
        session_directory=tmp_path / "sessions",
        trace_file_path=tmp_path / "traces" / "agent_trace.jsonl",
    )

    assert bundle.storage_backend == "json"
    assert isinstance(bundle.task_repository, JsonTaskRepository)
    assert isinstance(bundle.session_repository, JsonSessionRepository)
    assert isinstance(bundle.trace_repository, JsonlTraceRepository)
    assert bundle.task_repository.directory == tmp_path / "tasks"
    assert bundle.session_repository.directory == tmp_path / "sessions"
    assert bundle.trace_repository.file_path == (
        tmp_path / "traces" / "agent_trace.jsonl"
    )


def test_create_repositories_uses_postgres_backend():
    def fake_connect(database_url):
        raise AssertionError("factory should not connect immediately")

    bundle = create_repositories(
        storage_backend="postgres",
        database_url="postgresql://example",
        postgres_connect_fn=fake_connect,
    )

    assert bundle.storage_backend == "postgres"
    assert isinstance(bundle.task_repository, PostgresTaskRepository)
    assert isinstance(bundle.session_repository, PostgresSessionRepository)
    assert isinstance(bundle.trace_repository, PostgresTraceRepository)
    assert bundle.task_repository.database_url == "postgresql://example"
    assert bundle.session_repository.database_url == "postgresql://example"
    assert bundle.trace_repository.database_url == "postgresql://example"


def test_create_repositories_normalizes_backend_name():
    bundle = create_repositories(
        storage_backend=" Postgres ",
        database_url="postgresql://example",
    )

    assert bundle.storage_backend == "postgres"


def test_create_repositories_requires_database_url_for_postgres():
    with pytest.raises(ValueError, match="DATABASE_URL is required"):
        create_repositories(
            storage_backend="postgres",
            database_url="",
        )


def test_create_repositories_rejects_unknown_backend():
    with pytest.raises(ValueError, match="Unsupported STORAGE_BACKEND"):
        create_repositories(storage_backend="sqlite")


def test_normalize_storage_backend():
    assert normalize_storage_backend(" JSON ") == "json"
    assert normalize_storage_backend("Postgres") == "postgres"
