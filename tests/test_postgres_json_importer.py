from app.postgres_json_importer import (
    import_json_storage_to_repositories,
    import_sessions_from_json_directory,
    import_tasks_from_json_directory,
    import_traces_from_jsonl_file,
)
from app.repository_factory import RepositoryBundle
from app.session_models import AgentSession
from app.session_store import save_agent_session
from app.storage_repositories import JsonlTraceRepository
from app.task_models import DefenseTask, TaskStep
from app.task_store import save_defense_task


class FakeTaskRepository:
    def __init__(self):
        self.saved = []

    def save(self, task):
        self.saved.append(task)
        return task.task_id

    def load(self, task_id):
        raise NotImplementedError


class FakeSessionRepository:
    def __init__(self):
        self.saved = []

    def save(self, session):
        self.saved.append(session)
        return session.session_id

    def load(self, session_id):
        raise NotImplementedError


class FakeTraceRepository:
    def __init__(self):
        self.records = []

    def append(self, record):
        self.records.append(record)
        return f"trace-{len(self.records)}"

    def load_all(self):
        return self.records


def create_task(task_id="task-1"):
    task = DefenseTask(
        task_id=task_id,
        topic="system architecture",
    )
    step = TaskStep(step_type="retrieve_context")
    step.mark_completed(output={"context": "module design"})
    task.add_step(step)
    return task


def create_session(session_id="session-1"):
    session = AgentSession(
        session_id=session_id,
        metadata={"topic": "system architecture"},
    )
    session.add_message(role="user", content="hello")
    return session


def test_import_tasks_from_json_directory(tmp_path):
    task_directory = tmp_path / "tasks"
    save_defense_task(create_task(), task_directory)
    repository = FakeTaskRepository()

    report = import_tasks_from_json_directory(
        repository=repository,
        directory=task_directory,
    )

    assert report.source_count == 1
    assert report.imported_count == 1
    assert report.saved_identifiers == ["task-1"]
    assert repository.saved[0].task_id == "task-1"


def test_import_tasks_from_missing_directory_returns_zero(tmp_path):
    report = import_tasks_from_json_directory(
        repository=FakeTaskRepository(),
        directory=tmp_path / "missing",
    )

    assert report.source_count == 0
    assert report.imported_count == 0


def test_import_sessions_from_json_directory(tmp_path):
    session_directory = tmp_path / "sessions"
    save_agent_session(create_session(), session_directory)
    repository = FakeSessionRepository()

    report = import_sessions_from_json_directory(
        repository=repository,
        directory=session_directory,
    )

    assert report.source_count == 1
    assert report.imported_count == 1
    assert report.saved_identifiers == ["session-1"]
    assert repository.saved[0].session_id == "session-1"


def test_import_traces_from_jsonl_file(tmp_path):
    trace_path = tmp_path / "traces" / "agent_trace.jsonl"
    source_repository = JsonlTraceRepository(trace_path)
    source_repository.append({"event_type": "agent_run", "success": True})
    source_repository.append({"event_type": "tool_call", "success": False})
    target_repository = FakeTraceRepository()

    report = import_traces_from_jsonl_file(
        repository=target_repository,
        file_path=trace_path,
    )

    assert report.source_count == 2
    assert report.imported_count == 2
    assert report.saved_identifiers == ["trace-1", "trace-2"]
    assert target_repository.records == [
        {"event_type": "agent_run", "success": True},
        {"event_type": "tool_call", "success": False},
    ]


def test_import_traces_from_missing_file_returns_zero(tmp_path):
    report = import_traces_from_jsonl_file(
        repository=FakeTraceRepository(),
        file_path=tmp_path / "missing.jsonl",
    )

    assert report.source_count == 0
    assert report.imported_count == 0


def test_import_json_storage_to_repositories_imports_all_sections(tmp_path):
    task_directory = tmp_path / "tasks"
    session_directory = tmp_path / "sessions"
    trace_path = tmp_path / "traces" / "agent_trace.jsonl"
    save_defense_task(create_task(), task_directory)
    save_agent_session(create_session(), session_directory)
    JsonlTraceRepository(trace_path).append(
        {"event_type": "agent_run", "success": True}
    )
    repositories = RepositoryBundle(
        task_repository=FakeTaskRepository(),
        session_repository=FakeSessionRepository(),
        trace_repository=FakeTraceRepository(),
        storage_backend="postgres",
    )

    report = import_json_storage_to_repositories(
        repositories=repositories,
        task_directory=task_directory,
        session_directory=session_directory,
        trace_file_path=trace_path,
    )

    assert report.total_source_count == 3
    assert report.total_imported_count == 3
    assert report.tasks.imported_count == 1
    assert report.sessions.imported_count == 1
    assert report.traces.imported_count == 1


def test_import_json_storage_to_repositories_supports_dry_run(tmp_path):
    task_directory = tmp_path / "tasks"
    session_directory = tmp_path / "sessions"
    trace_path = tmp_path / "traces" / "agent_trace.jsonl"
    save_defense_task(create_task(), task_directory)
    save_agent_session(create_session(), session_directory)
    JsonlTraceRepository(trace_path).append(
        {"event_type": "agent_run", "success": True}
    )
    task_repository = FakeTaskRepository()
    session_repository = FakeSessionRepository()
    trace_repository = FakeTraceRepository()
    repositories = RepositoryBundle(
        task_repository=task_repository,
        session_repository=session_repository,
        trace_repository=trace_repository,
        storage_backend="postgres",
    )

    report = import_json_storage_to_repositories(
        repositories=repositories,
        task_directory=task_directory,
        session_directory=session_directory,
        trace_file_path=trace_path,
        dry_run=True,
    )

    assert report.dry_run is True
    assert report.total_source_count == 3
    assert report.total_imported_count == 0
    assert task_repository.saved == []
    assert session_repository.saved == []
    assert trace_repository.records == []


def test_import_json_storage_to_repositories_can_skip_sections(tmp_path):
    repositories = RepositoryBundle(
        task_repository=FakeTaskRepository(),
        session_repository=FakeSessionRepository(),
        trace_repository=FakeTraceRepository(),
        storage_backend="postgres",
    )

    report = import_json_storage_to_repositories(
        repositories=repositories,
        task_directory=tmp_path / "tasks",
        session_directory=tmp_path / "sessions",
        trace_file_path=tmp_path / "trace.jsonl",
        include_tasks=False,
        include_sessions=False,
        include_traces=False,
    )

    assert report.to_dict() == {
        "tasks": {
            "source_count": 0,
            "imported_count": 0,
            "saved_identifiers": [],
        },
        "sessions": {
            "source_count": 0,
            "imported_count": 0,
            "saved_identifiers": [],
        },
        "traces": {
            "source_count": 0,
            "imported_count": 0,
            "saved_identifiers": [],
        },
        "dry_run": False,
        "total_source_count": 0,
        "total_imported_count": 0,
    }
