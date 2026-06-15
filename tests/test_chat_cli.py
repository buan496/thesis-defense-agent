import pytest

from types import SimpleNamespace

import app.cli as cli


def test_chat_command_creates_new_session(
    monkeypatch,
    capsys,
    tmp_path,
):
    received_arguments = {}

    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
    ):
        received_arguments["user_message"] = user_message
        received_arguments["session_id"] = session_id
        received_arguments["max_history_turns"] = (
            max_history_turns
        )
        
        result = SimpleNamespace(
            final_output="我已经记住你的研究方向。",
        )
        session = SimpleNamespace(
            session_id="new-session-001",
        )
        session_path = (
            tmp_path / "new-session-001.json"
        )

        return result, session, session_path

    monkeypatch.setattr(
        cli,
        "run_agent_session",
        fake_run_agent_session,
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "我的论文研究语音识别。",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert received_arguments == {
        "user_message": "我的论文研究语音识别。",
        "session_id": None,
        "max_history_turns": 6,
    }

    assert "我已经记住你的研究方向。" in output
    assert "new-session-001" in output
    assert "new-session-001.json" in output


def test_chat_command_resumes_existing_session(
    monkeypatch,
    capsys,
    tmp_path,
):
    received_arguments = {}

    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
    ):
        received_arguments["user_message"] = user_message
        received_arguments["session_id"] = session_id
        received_arguments["max_history_turns"] = (
            max_history_turns
        )

        result = SimpleNamespace(
            final_output="你的论文研究语音识别。",
        )
        session = SimpleNamespace(
            session_id="existing-session",
        )
        session_path = (
            tmp_path / "existing-session.json"
        )

        return result, session, session_path

    monkeypatch.setattr(
        cli,
        "run_agent_session",
        fake_run_agent_session,
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--session-id",
            "existing-session",
            "--message",
            "我的论文研究方向是什么？",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert received_arguments == {
        "user_message": "我的论文研究方向是什么？",
        "session_id": "existing-session",
        "max_history_turns": 6,
    }

    assert "你的论文研究语音识别。" in output
    assert "existing-session" in output


def test_chat_command_reads_interactive_input(
    monkeypatch,
    capsys,
    tmp_path,
):
    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
    ):
        assert user_message == "交互输入的问题"
        assert session_id is None

        return (
            SimpleNamespace(final_output="交互回答"),
            SimpleNamespace(session_id="interactive-session"),
            tmp_path / "interactive-session.json",
        )

    monkeypatch.setattr(
        cli,
        "run_agent_session",
        fake_run_agent_session,
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt: "交互输入的问题",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "交互回答" in output
    assert "interactive-session" in output


def test_chat_command_handles_missing_session(
    monkeypatch,
    capsys,
):
    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
    ):
        raise FileNotFoundError(
            "Agent 会话文件不存在：missing-session.json"
        )

    monkeypatch.setattr(
        cli,
        "run_agent_session",
        fake_run_agent_session,
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--session-id",
            "missing-session",
            "--message",
            "继续对话",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("CLI 应该以状态码 1 退出")

    output = capsys.readouterr().out

    assert "SESSION ERROR" in output
    assert "missing-session.json" in output
    
    
def test_chat_command_passes_max_history_turns(
    monkeypatch,
    capsys,
    tmp_path,
):
    received_arguments = {}

    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
    ):
        received_arguments["user_message"] = user_message
        received_arguments["session_id"] = session_id
        received_arguments["max_history_turns"] = (
            max_history_turns
        )

        return (
            SimpleNamespace(final_output="测试回答"),
            SimpleNamespace(session_id="window-session"),
            tmp_path / "window-session.json",
        )

    monkeypatch.setattr(
        cli,
        "run_agent_session",
        fake_run_agent_session,
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "测试短期记忆窗口",
            "--max-history-turns",
            "3",
        ],
    )

    cli.main()

    assert received_arguments == {
        "user_message": "测试短期记忆窗口",
        "session_id": None,
        "max_history_turns": 3,
    }

    output = capsys.readouterr().out
    assert "测试回答" in output
    
    
def test_chat_command_rejects_invalid_history_turns(
    monkeypatch,
    capsys,
):
    def run_agent_session_should_not_run(*args, **kwargs):
        raise AssertionError("参数非法时不应运行 Agent")

    monkeypatch.setattr(
        cli,
        "run_agent_session",
        run_agent_session_should_not_run,
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "测试",
            "--max-history-turns",
            "0",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2

    output = capsys.readouterr().out

    assert "--max-history-turns 必须大于 0" in output