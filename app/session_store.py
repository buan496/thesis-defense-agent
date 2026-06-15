import json
import os
import re

from dataclasses import asdict
from pathlib import Path

from app.session_models import AgentSession


DEFAULT_SESSION_DIRECTORY = Path("data/agent_sessions")
SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def validate_session_id(session_id: str) -> None:
    if not session_id:
        raise ValueError("session_id 不能为空")

    if not SESSION_ID_PATTERN.fullmatch(session_id):
        raise ValueError(
            "session_id 只能包含字母、数字、下划线和连字符"
        )


def save_agent_session(
    session: AgentSession,
    directory: str | Path = DEFAULT_SESSION_DIRECTORY,
) -> Path:
    validate_session_id(session.session_id)

    directory_path = Path(directory)
    directory_path.mkdir(parents=True, exist_ok=True)

    session_path = directory_path / f"{session.session_id}.json"
    temporary_path = directory_path / f"{session.session_id}.tmp"

    session_data = asdict(session)
    session_text = json.dumps(
        session_data,
        ensure_ascii=False,
        indent=2,
    )

    try:
        temporary_path.write_text(
            session_text,
            encoding="utf-8",
        )

        os.replace(temporary_path, session_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    return session_path


def load_agent_session(
    session_id: str,
    directory: str | Path = DEFAULT_SESSION_DIRECTORY,
) -> AgentSession:
    validate_session_id(session_id)

    session_path = Path(directory) / f"{session_id}.json"

    if not session_path.exists():
        raise FileNotFoundError(
            f"Agent 会话文件不存在：{session_path}"
        )

    try:
        session_data = json.loads(
            session_path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Agent 会话文件不是合法 JSON：{session_path}"
        ) from error

    required_fields = {
        "session_id",
        "created_at",
        "messages",
        "metadata",
    }

    missing_fields = required_fields - session_data.keys()

    if missing_fields:
        raise ValueError(
            f"Agent 会话缺少字段：{sorted(missing_fields)}"
        )

    if session_data["session_id"] != session_id:
        raise ValueError(
            "文件中的 session_id 与请求的 session_id 不一致"
        )

    if not isinstance(session_data["messages"], list):
        raise ValueError("messages 必须是列表")

    if not isinstance(session_data["metadata"], dict):
        raise ValueError("metadata 必须是字典")

    return AgentSession(
        session_id=session_data["session_id"],
        created_at=session_data["created_at"],
        messages=session_data["messages"],
        metadata=session_data["metadata"],
    )