import pytest

from types import SimpleNamespace

import app.cli as cli
from app.budget_guard import BudgetExceededError

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
        max_history_characters=12000,
        max_run_cost=None,
    ):
        received_arguments["user_message"] = user_message
        received_arguments["session_id"] = session_id
        received_arguments["max_history_turns"] = (
            max_history_turns
        )
        received_arguments["max_history_characters"] = (
            max_history_characters
        )
        received_arguments["max_run_cost"] = max_run_cost
        
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
        "max_history_characters": 12000,
        "max_run_cost": None,
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
        max_history_characters=12000,
        max_run_cost=None,
    ):
        received_arguments["user_message"] = user_message
        received_arguments["session_id"] = session_id
        received_arguments["max_history_turns"] = (
            max_history_turns
        )
        received_arguments["max_history_characters"] = (
            max_history_characters
        )
        received_arguments["max_run_cost"] = max_run_cost
        
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
        "max_history_characters": 12000,
        "max_run_cost": None,
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
        max_history_characters=12000,
        max_run_cost=None,
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
        max_history_characters=12000,
        max_run_cost=None,
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
        max_history_characters=12000,
        max_run_cost=None,
    ):
        received_arguments["user_message"] = user_message
        received_arguments["session_id"] = session_id
        received_arguments["max_history_turns"] = (
            max_history_turns
        )
        received_arguments["max_history_characters"] = (
            max_history_characters
        )
        received_arguments["max_run_cost"] = max_run_cost

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
        "max_history_characters": 12000,
        "max_run_cost": None,
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
    
    
def test_chat_command_passes_max_history_characters(
    monkeypatch,
    capsys,
    tmp_path,
):
    received_arguments = {}

    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
        max_history_characters=12000,
        max_run_cost=None,
    ):
        received_arguments["user_message"] = user_message
        received_arguments["session_id"] = session_id
        received_arguments["max_history_turns"] = max_history_turns
        received_arguments["max_history_characters"] = (
            max_history_characters
        )
        received_arguments["max_run_cost"] = max_run_cost

        return (
            SimpleNamespace(final_output="字符预算测试回答"),
            SimpleNamespace(session_id="character-session"),
            tmp_path / "character-session.json",
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
            "测试字符预算",
            "--max-history-characters",
            "3000",
        ],
    )

    cli.main()

    assert received_arguments == {
        "user_message": "测试字符预算",
        "session_id": None,
        "max_history_turns": 6,
        "max_history_characters": 3000,
        "max_run_cost": None,
    }

    output = capsys.readouterr().out

    assert "字符预算测试回答" in output
    
def test_chat_command_rejects_invalid_history_characters(
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
            "--max-history-characters",
            "0",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2

    output = capsys.readouterr().out

    assert "--max-history-characters 必须大于 0" in output
    
def test_chat_command_passes_max_run_cost(
    monkeypatch,
    capsys,
    tmp_path,
):
    received_arguments = {}

    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
        max_history_characters=12000,
        max_run_cost=None,
    ):
        received_arguments["user_message"] = user_message
        received_arguments["session_id"] = session_id
        received_arguments["max_history_turns"] = max_history_turns
        received_arguments["max_history_characters"] = (
            max_history_characters
        )
        received_arguments["max_run_cost"] = max_run_cost

        return (
            SimpleNamespace(final_output="预算测试回答"),
            SimpleNamespace(session_id="budget-session"),
            tmp_path / "budget-session.json",
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
            "测试预算",
            "--max-run-cost",
            "0.05",
        ],
    )

    cli.main()

    assert received_arguments == {
        "user_message": "测试预算",
        "session_id": None,
        "max_history_turns": 6,
        "max_history_characters": 12000,
        "max_run_cost": 0.05,
    }

    output = capsys.readouterr().out
    assert "预算测试回答" in output
    
def test_chat_command_rejects_negative_max_run_cost(
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
            "--max-run-cost",
            "-0.01",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2

    output = capsys.readouterr().out

    assert "--max-run-cost 不能小于 0" in output
    
def test_chat_command_handles_budget_exceeded(
    monkeypatch,
    capsys,
):
    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
        max_history_characters=12000,
        max_run_cost=None,
    ):
        raise BudgetExceededError(
            actual_cost=0.06,
            max_cost=0.05,
            currency="CNY",
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
            "测试预算超限",
            "--max-run-cost",
            "0.05",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 1

    output = capsys.readouterr().out

    assert "BUDGET ERROR" in output
    assert "0.060000 CNY" in output
    assert "0.050000 CNY" in output