from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.config import (
    AGENT_TRACE_PATH,
    DATABASE_URL,
    STORAGE_BACKEND,
)
from app.postgres_session_repository import PostgresSessionRepository
from app.postgres_task_repository import PostgresTaskRepository
from app.postgres_trace_repository import PostgresTraceRepository
from app.session_store import DEFAULT_SESSION_DIRECTORY
from app.storage_repositories import (
    JsonSessionRepository,
    JsonTaskRepository,
    JsonlTraceRepository,
    SessionRepository,
    TaskRepository,
    TraceRepository,
)
from app.task_store import DEFAULT_TASK_DIRECTORY


ConnectFn = Callable[[str], Any]


@dataclass(frozen=True)
class RepositoryBundle:
    task_repository: TaskRepository
    session_repository: SessionRepository
    trace_repository: TraceRepository
    storage_backend: str


def create_repositories(
    storage_backend: str = STORAGE_BACKEND,
    database_url: str = DATABASE_URL,
    task_directory: str | Path = DEFAULT_TASK_DIRECTORY,
    session_directory: str | Path = DEFAULT_SESSION_DIRECTORY,
    trace_file_path: str | Path = AGENT_TRACE_PATH,
    postgres_connect_fn: ConnectFn | None = None,
) -> RepositoryBundle:
    backend = normalize_storage_backend(storage_backend)

    if backend == "json":
        return RepositoryBundle(
            task_repository=JsonTaskRepository(task_directory),
            session_repository=JsonSessionRepository(session_directory),
            trace_repository=JsonlTraceRepository(trace_file_path),
            storage_backend=backend,
        )

    if backend == "postgres":
        if not database_url.strip():
            raise ValueError(
                "DATABASE_URL is required when STORAGE_BACKEND=postgres"
            )

        return RepositoryBundle(
            task_repository=PostgresTaskRepository(
                database_url,
                connect_fn=postgres_connect_fn,
            ),
            session_repository=PostgresSessionRepository(
                database_url,
                connect_fn=postgres_connect_fn,
            ),
            trace_repository=PostgresTraceRepository(
                database_url,
                connect_fn=postgres_connect_fn,
            ),
            storage_backend=backend,
        )

    raise ValueError(
        "Unsupported STORAGE_BACKEND. Expected 'json' or 'postgres', "
        f"got: {storage_backend}"
    )


def normalize_storage_backend(storage_backend: str) -> str:
    return storage_backend.strip().lower()
