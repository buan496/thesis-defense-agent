import pytest

from app.session_models import AgentSession
from app.storage_repositories import (
    JsonSessionRepository,
    JsonTaskRepository,
    JsonlTraceRepository,
    SessionRepository,
    TaskRepository,
    TraceRepository,
)
from app.task_models import DefenseTask, TaskStep


def test_json_task_repository_saves_and_loads_task(tmp_path):
    repository: TaskRepository = JsonTaskRepository(tmp_path)
    task = DefenseTask(
        task_id="task-1",
        topic="系统架构",
    )
    step = TaskStep(step_type="retrieve_context")
    step.mark_completed(
        output={
            "context": "模块化设计",
        }
    )
    task.add_step(step)

    saved_path = repository.save(task)
    loaded_task = repository.load("task-1")

    assert saved_path.endswith("task-1.json")
    assert loaded_task == task
    assert loaded_task.steps[0].output["context"] == "模块化设计"


def test_json_session_repository_saves_and_loads_session(tmp_path):
    repository: SessionRepository = JsonSessionRepository(tmp_path)
    session = AgentSession(
        session_id="session-1",
        metadata={
            "thesis_direction": "中英双语语音识别",
        },
    )
    session.add_message(
        role="user",
        content="请记住我的论文方向",
    )

    saved_path = repository.save(session)
    loaded_session = repository.load("session-1")

    assert saved_path.endswith("session-1.json")
    assert loaded_session == session
    assert loaded_session.metadata["thesis_direction"] == (
        "中英双语语音识别"
    )


def test_jsonl_trace_repository_appends_and_loads_records(tmp_path):
    repository: TraceRepository = JsonlTraceRepository(
        tmp_path / "traces" / "agent_trace.jsonl"
    )

    saved_path = repository.append(
        {
            "event_type": "agent_run",
            "success": True,
        }
    )
    repository.append(
        {
            "event_type": "tool_call",
            "success": False,
        }
    )

    records = repository.load_all()

    assert saved_path.endswith("agent_trace.jsonl")
    assert records == [
        {
            "event_type": "agent_run",
            "success": True,
        },
        {
            "event_type": "tool_call",
            "success": False,
        },
    ]


def test_jsonl_trace_repository_returns_empty_list_for_missing_file(tmp_path):
    repository = JsonlTraceRepository(
        tmp_path / "missing.jsonl"
    )

    assert repository.load_all() == []


def test_jsonl_trace_repository_rejects_invalid_json(tmp_path):
    trace_path = tmp_path / "broken.jsonl"
    trace_path.write_text(
        "{broken",
        encoding="utf-8",
    )
    repository = JsonlTraceRepository(trace_path)

    with pytest.raises(
        ValueError,
        match="trace line 1 is not valid JSON",
    ):
        repository.load_all()
