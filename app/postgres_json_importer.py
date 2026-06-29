from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.repository_factory import RepositoryBundle
from app.session_store import DEFAULT_SESSION_DIRECTORY, load_agent_session
from app.storage_repositories import JsonlTraceRepository
from app.task_store import DEFAULT_TASK_DIRECTORY, load_defense_task
from app.config import AGENT_TRACE_PATH


@dataclass(frozen=True)
class ImportSectionReport:
    source_count: int
    imported_count: int
    saved_identifiers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_count": self.source_count,
            "imported_count": self.imported_count,
            "saved_identifiers": self.saved_identifiers,
        }


@dataclass(frozen=True)
class ImportJsonStorageReport:
    tasks: ImportSectionReport
    sessions: ImportSectionReport
    traces: ImportSectionReport
    dry_run: bool

    @property
    def total_source_count(self) -> int:
        return (
            self.tasks.source_count
            + self.sessions.source_count
            + self.traces.source_count
        )

    @property
    def total_imported_count(self) -> int:
        return (
            self.tasks.imported_count
            + self.sessions.imported_count
            + self.traces.imported_count
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tasks": self.tasks.to_dict(),
            "sessions": self.sessions.to_dict(),
            "traces": self.traces.to_dict(),
            "dry_run": self.dry_run,
            "total_source_count": self.total_source_count,
            "total_imported_count": self.total_imported_count,
        }


def import_json_storage_to_repositories(
    repositories: RepositoryBundle,
    task_directory: str | Path = DEFAULT_TASK_DIRECTORY,
    session_directory: str | Path = DEFAULT_SESSION_DIRECTORY,
    trace_file_path: str | Path = AGENT_TRACE_PATH,
    include_tasks: bool = True,
    include_sessions: bool = True,
    include_traces: bool = True,
    dry_run: bool = False,
) -> ImportJsonStorageReport:
    return ImportJsonStorageReport(
        tasks=import_tasks_from_json_directory(
            repository=repositories.task_repository,
            directory=task_directory,
            enabled=include_tasks,
            dry_run=dry_run,
        ),
        sessions=import_sessions_from_json_directory(
            repository=repositories.session_repository,
            directory=session_directory,
            enabled=include_sessions,
            dry_run=dry_run,
        ),
        traces=import_traces_from_jsonl_file(
            repository=repositories.trace_repository,
            file_path=trace_file_path,
            enabled=include_traces,
            dry_run=dry_run,
        ),
        dry_run=dry_run,
    )


def import_tasks_from_json_directory(
    repository,
    directory: str | Path,
    enabled: bool = True,
    dry_run: bool = False,
) -> ImportSectionReport:
    if not enabled:
        return ImportSectionReport(source_count=0, imported_count=0)

    directory_path = Path(directory)
    task_paths = sorted(directory_path.glob("*.json")) if directory_path.exists() else []
    saved_identifiers = []

    for task_path in task_paths:
        task = load_defense_task(
            task_path.stem,
            directory=directory_path,
        )

        if not dry_run:
            saved_identifiers.append(repository.save(task))

    return ImportSectionReport(
        source_count=len(task_paths),
        imported_count=0 if dry_run else len(saved_identifiers),
        saved_identifiers=saved_identifiers,
    )


def import_sessions_from_json_directory(
    repository,
    directory: str | Path,
    enabled: bool = True,
    dry_run: bool = False,
) -> ImportSectionReport:
    if not enabled:
        return ImportSectionReport(source_count=0, imported_count=0)

    directory_path = Path(directory)
    session_paths = (
        sorted(directory_path.glob("*.json")) if directory_path.exists() else []
    )
    saved_identifiers = []

    for session_path in session_paths:
        session = load_agent_session(
            session_path.stem,
            directory=directory_path,
        )

        if not dry_run:
            saved_identifiers.append(repository.save(session))

    return ImportSectionReport(
        source_count=len(session_paths),
        imported_count=0 if dry_run else len(saved_identifiers),
        saved_identifiers=saved_identifiers,
    )


def import_traces_from_jsonl_file(
    repository,
    file_path: str | Path,
    enabled: bool = True,
    dry_run: bool = False,
) -> ImportSectionReport:
    if not enabled:
        return ImportSectionReport(source_count=0, imported_count=0)

    records = JsonlTraceRepository(file_path).load_all()
    saved_identifiers = []

    for record in records:
        if not dry_run:
            saved_identifiers.append(repository.append(record))

    return ImportSectionReport(
        source_count=len(records),
        imported_count=0 if dry_run else len(saved_identifiers),
        saved_identifiers=saved_identifiers,
    )
