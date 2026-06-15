import json

import pytest

from app.session_models import AgentSession
from app.session_store import (
    load_agent_session,
    save_agent_session,
    validate_session_id,
)


def test_save_agent_session(tmp_path):
    session = AgentSession(
        session_id="session-001",
        metadata={"student_name": "测试学生"},
    )

    session.add_message(
        role="user",
        content="系统架构包括哪些模块？",
    )

    session_path = save_agent_session(
        session,
        directory=tmp_path,
    )

    assert session_path.exists()
    assert session_path.name == "session-001.json"

    saved_data = json.loads(
        session_path.read_text(encoding="utf-8")
    )

    assert saved_data["session_id"] == "session-001"
    assert saved_data["metadata"]["student_name"] == "测试学生"
    assert saved_data["messages"][0]["role"] == "user"


def test_load_agent_session(tmp_path):
    original_session = AgentSession(
        session_id="session-002",
        metadata={"thesis_path": "data/thesis.pdf"},
    )

    original_session.add_message(
        role="user",
        content="论文使用了哪些数据集？",
    )
    original_session.add_message(
        role="assistant",
        content="论文使用了 AISHELL-1 和 LibriSpeech。",
    )

    save_agent_session(
        original_session,
        directory=tmp_path,
    )

    loaded_session = load_agent_session(
        "session-002",
        directory=tmp_path,
    )

    assert loaded_session == original_session


def test_load_missing_agent_session(tmp_path):
    with pytest.raises(
        FileNotFoundError,
        match="Agent 会话文件不存在",
    ):
        load_agent_session(
            "not-exist",
            directory=tmp_path,
        )


def test_validate_invalid_session_id():
    invalid_session_ids = [
        "",
        "../secret",
        "folder/session",
        "session.json",
        "带中文的会话",
    ]

    for session_id in invalid_session_ids:
        with pytest.raises(ValueError):
            validate_session_id(session_id)


def test_load_invalid_json(tmp_path):
    session_path = tmp_path / "broken-session.json"
    session_path.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="不是合法 JSON",
    ):
        load_agent_session(
            "broken-session",
            directory=tmp_path,
        )


def test_load_rejects_mismatched_session_id(tmp_path):
    session_path = tmp_path / "session-003.json"
    session_path.write_text(
        json.dumps(
            {
                "session_id": "another-session",
                "created_at": "2026-06-15T00:00:00+00:00",
                "messages": [],
                "metadata": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="session_id 不一致",
    ):
        load_agent_session(
            "session-003",
            directory=tmp_path,
        )


def test_save_does_not_leave_temporary_file(tmp_path):
    session = AgentSession(session_id="session-004")

    save_agent_session(
        session,
        directory=tmp_path,
    )

    assert not (tmp_path / "session-004.tmp").exists()