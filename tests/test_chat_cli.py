
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
    ):
        received_arguments["user_message"] = user_message
        received_arguments["session_id"] = session_id

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
    ):
        received_arguments["user_message"] = user_message
        received_arguments["session_id"] = session_id

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