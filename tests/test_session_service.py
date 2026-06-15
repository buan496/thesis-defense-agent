import pytest

from app.session_models import AgentSession
from app.session_service import run_agent_session
from app.session_store import (
    load_agent_session,
    save_agent_session,
)


class FakeMessage:
    def __init__(
        self,
        content: str = "",
        tool_calls=None,
    ):
        self.content = content
        self.tool_calls = tool_calls


def test_run_agent_session_creates_and_saves_new_session(
    tmp_path,
):
    def fake_llm_call(messages):
        return FakeMessage(
            content="你好，我可以帮助你准备答辩。",
            tool_calls=None,
        )

    result, session, session_path = run_agent_session(
        user_message="你好",
        directory=tmp_path,
        llm_call=fake_llm_call,
    )

    assert result.final_output == (
        "你好，我可以帮助你准备答辩。"
    )

    assert session.session_id
    assert session_path.exists()
    assert session_path.name == f"{session.session_id}.json"

    loaded_session = load_agent_session(
        session_id=session.session_id,
        directory=tmp_path,
    )

    assert loaded_session == session


def test_run_agent_session_resumes_existing_session(
    tmp_path,
):
    original_session = AgentSession(
        session_id="resume-session",
    )

    original_session.add_message(
        role="user",
        content="我的论文研究语音识别。",
    )
    original_session.add_message(
        role="assistant",
        content="好的，我已经记住了。",
    )

    save_agent_session(
        session=original_session,
        directory=tmp_path,
    )

    received_messages = []

    def fake_llm_call(messages):
        received_messages.extend(messages)

        return FakeMessage(
            content="你的论文研究方向是语音识别。",
            tool_calls=None,
        )

    result, session, session_path = run_agent_session(
        user_message="我的论文研究方向是什么？",
        session_id="resume-session",
        directory=tmp_path,
        llm_call=fake_llm_call,
    )

    assert result.final_output == (
        "你的论文研究方向是语音识别。"
    )

    assert session.session_id == "resume-session"
    assert session_path.name == "resume-session.json"

    assert received_messages[0]["role"] == "system"

    assert received_messages[1:] == [
        {
            "role": "user",
            "content": "我的论文研究语音识别。",
        },
        {
            "role": "assistant",
            "content": "好的，我已经记住了。",
        },
        {
            "role": "user",
            "content": "我的论文研究方向是什么？",
        },
    ]

    saved_session = load_agent_session(
        session_id="resume-session",
        directory=tmp_path,
    )

    assert saved_session.messages[-1] == {
        "role": "assistant",
        "content": "你的论文研究方向是语音识别。",
    }


def test_run_agent_session_rejects_missing_session(
    tmp_path,
):
    def fake_llm_call(messages):
        raise AssertionError("不应该调用模型")

    with pytest.raises(
        FileNotFoundError,
        match="Agent 会话文件不存在",
    ):
        run_agent_session(
            user_message="继续对话",
            session_id="missing-session",
            directory=tmp_path,
            llm_call=fake_llm_call,
        )


def test_failed_agent_run_does_not_overwrite_session(
    tmp_path,
):
    original_session = AgentSession(
        session_id="protected-session",
    )

    original_session.add_message(
        role="user",
        content="已经保存的问题",
    )
    original_session.add_message(
        role="assistant",
        content="已经保存的回答",
    )

    save_agent_session(
        session=original_session,
        directory=tmp_path,
    )

    def failing_llm_call(messages):
        raise RuntimeError("模拟模型调用失败")

    with pytest.raises(
        RuntimeError,
        match="模拟模型调用失败",
    ):
        run_agent_session(
            user_message="这条消息不应该保存",
            session_id="protected-session",
            directory=tmp_path,
            llm_call=failing_llm_call,
        )

    loaded_session = load_agent_session(
        session_id="protected-session",
        directory=tmp_path,
    )

    assert loaded_session == original_session
    assert len(loaded_session.messages) == 2