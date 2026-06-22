from types import SimpleNamespace

import pytest

import app.cli as cli
from app.budget_guard import BudgetExceededError, PreflightBudgetExceededError


def build_fake_agent_result(final_output: str):
    return SimpleNamespace(
        final_output=final_output,
        token_usage=SimpleNamespace(
            prompt_tokens=100,
            completion_tokens=20,
            total_tokens=120,
        ),
        cost_estimate=SimpleNamespace(
            input_cost=0.001,
            output_cost=0.002,
            total_cost=0.003,
            currency="CNY",
        ),
    )


def test_chat_command_creates_new_session(monkeypatch, capsys, tmp_path):
    received_arguments = {}

    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
        max_history_characters=12000,
        max_run_cost=None,
        preflight_max_run_cost=None,
        use_long_term_memory=True,
        max_memory_weaknesses=5,
        max_memory_summaries=3,
        compact_session=True,
        compact_summary_max_characters=4000,
    ):
        received_arguments.update(
            {
                "user_message": user_message,
                "session_id": session_id,
                "max_history_turns": max_history_turns,
                "max_history_characters": max_history_characters,
                "max_run_cost": max_run_cost,
                "preflight_max_run_cost": preflight_max_run_cost,
                "use_long_term_memory": use_long_term_memory,
                "max_memory_weaknesses": max_memory_weaknesses,
                "max_memory_summaries": max_memory_summaries,
                "compact_session": compact_session,
                "compact_summary_max_characters": (
                    compact_summary_max_characters
                ),
            }
        )

        return (
            build_fake_agent_result("saved thesis direction"),
            SimpleNamespace(session_id="new-session-001"),
            tmp_path / "new-session-001.json",
        )

    monkeypatch.setattr(cli, "run_agent_session", fake_run_agent_session)
    monkeypatch.setattr(
        "sys.argv",
        ["app.cli", "chat", "--message", "remember my thesis direction"],
    )

    cli.main()

    output = capsys.readouterr().out

    assert received_arguments == {
        "user_message": "remember my thesis direction",
        "session_id": None,
        "max_history_turns": 6,
        "max_history_characters": 12000,
        "max_run_cost": None,
        "preflight_max_run_cost": None,
        "use_long_term_memory": True,
        "max_memory_weaknesses": 5,
        "max_memory_summaries": 3,
        "compact_session": True,
        "compact_summary_max_characters": 4000,
    }
    assert "saved thesis direction" in output
    assert "TOKEN USAGE" in output
    assert "PROMPT TOKENS: 100" in output
    assert "COMPLETION TOKENS: 20" in output
    assert "TOTAL TOKENS: 120" in output
    assert "COST ESTIMATE" in output
    assert "INPUT COST: 0.001" in output
    assert "OUTPUT COST: 0.002" in output
    assert "TOTAL COST: 0.003" in output
    assert "CURRENCY: CNY" in output
    assert "new-session-001" in output
    assert "new-session-001.json" in output


def test_chat_command_resumes_existing_session(monkeypatch, capsys, tmp_path):
    received_arguments = {}

    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
        max_history_characters=12000,
        max_run_cost=None,
        preflight_max_run_cost=None,
        use_long_term_memory=True,
        max_memory_weaknesses=5,
        max_memory_summaries=3,
        compact_session=True,
        compact_summary_max_characters=4000,
    ):
        received_arguments.update(
            {
                "user_message": user_message,
                "session_id": session_id,
                "max_history_turns": max_history_turns,
                "max_history_characters": max_history_characters,
                "max_run_cost": max_run_cost,
                "preflight_max_run_cost": preflight_max_run_cost,
                "use_long_term_memory": use_long_term_memory,
                "max_memory_weaknesses": max_memory_weaknesses,
                "max_memory_summaries": max_memory_summaries,
                "compact_session": compact_session,
                "compact_summary_max_characters": (
                    compact_summary_max_characters
                ),
            }
        )

        return (
            build_fake_agent_result("existing session answer"),
            SimpleNamespace(session_id="existing-session"),
            tmp_path / "existing-session.json",
        )

    monkeypatch.setattr(cli, "run_agent_session", fake_run_agent_session)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--session-id",
            "existing-session",
            "--message",
            "what is my thesis direction?",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert received_arguments == {
        "user_message": "what is my thesis direction?",
        "session_id": "existing-session",
        "max_history_turns": 6,
        "max_history_characters": 12000,
        "max_run_cost": None,
        "preflight_max_run_cost": None,
        "use_long_term_memory": True,
        "max_memory_weaknesses": 5,
        "max_memory_summaries": 3,
        "compact_session": True,
        "compact_summary_max_characters": 4000,
    }
    assert "existing session answer" in output
    assert "existing-session" in output


def test_chat_command_reads_interactive_input(monkeypatch, capsys, tmp_path):
    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
        max_history_characters=12000,
        max_run_cost=None,
        preflight_max_run_cost=None,
        use_long_term_memory=True,
        max_memory_weaknesses=5,
        max_memory_summaries=3,
        compact_session=True,
        compact_summary_max_characters=4000,
    ):
        assert user_message == "interactive question"
        assert session_id is None

        return (
            build_fake_agent_result("interactive answer"),
            SimpleNamespace(session_id="interactive-session"),
            tmp_path / "interactive-session.json",
        )

    monkeypatch.setattr(cli, "run_agent_session", fake_run_agent_session)
    monkeypatch.setattr("builtins.input", lambda prompt: "interactive question")
    monkeypatch.setattr("sys.argv", ["app.cli", "chat"])

    cli.main()

    output = capsys.readouterr().out

    assert "interactive answer" in output
    assert "interactive-session" in output


def test_chat_command_handles_missing_session(monkeypatch, capsys):
    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
        max_history_characters=12000,
        max_run_cost=None,
        preflight_max_run_cost=None,
        use_long_term_memory=True,
        max_memory_weaknesses=5,
        max_memory_summaries=3,
        compact_session=True,
        compact_summary_max_characters=4000,
    ):
        raise FileNotFoundError("missing-session.json")

    monkeypatch.setattr(cli, "run_agent_session", fake_run_agent_session)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--session-id",
            "missing-session",
            "--message",
            "continue chat",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "SESSION ERROR" in output
    assert "missing-session.json" in output


def test_chat_command_passes_max_history_turns(monkeypatch, capsys, tmp_path):
    received_arguments = {}

    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
        max_history_characters=12000,
        max_run_cost=None,
        preflight_max_run_cost=None,
        use_long_term_memory=True,
        max_memory_weaknesses=5,
        max_memory_summaries=3,
        compact_session=True,
        compact_summary_max_characters=4000,
    ):
        received_arguments["max_history_turns"] = max_history_turns

        return (
            build_fake_agent_result("history window answer"),
            SimpleNamespace(session_id="window-session"),
            tmp_path / "window-session.json",
        )

    monkeypatch.setattr(cli, "run_agent_session", fake_run_agent_session)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test history window",
            "--max-history-turns",
            "3",
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert received_arguments["max_history_turns"] == 3
    assert "history window answer" in output


def test_chat_command_rejects_invalid_history_turns(monkeypatch, capsys):
    def run_agent_session_should_not_run(*args, **kwargs):
        raise AssertionError("invalid arguments should not run Agent")

    monkeypatch.setattr(cli, "run_agent_session", run_agent_session_should_not_run)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test",
            "--max-history-turns",
            "0",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2
    output = capsys.readouterr().out
    assert "ARGUMENT ERROR" in output
    assert "--max-history-turns" in output


def test_chat_command_passes_max_history_characters(monkeypatch, capsys, tmp_path):
    received_arguments = {}

    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
        max_history_characters=12000,
        max_run_cost=None,
        preflight_max_run_cost=None,
        use_long_term_memory=True,
        max_memory_weaknesses=5,
        max_memory_summaries=3,
        compact_session=True,
        compact_summary_max_characters=4000,
    ):
        received_arguments["max_history_characters"] = max_history_characters

        return (
            build_fake_agent_result("character budget answer"),
            SimpleNamespace(session_id="character-session"),
            tmp_path / "character-session.json",
        )

    monkeypatch.setattr(cli, "run_agent_session", fake_run_agent_session)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test character budget",
            "--max-history-characters",
            "3000",
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert received_arguments["max_history_characters"] == 3000
    assert "character budget answer" in output


def test_chat_command_rejects_invalid_history_characters(monkeypatch, capsys):
    def run_agent_session_should_not_run(*args, **kwargs):
        raise AssertionError("invalid arguments should not run Agent")

    monkeypatch.setattr(cli, "run_agent_session", run_agent_session_should_not_run)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test",
            "--max-history-characters",
            "0",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2
    output = capsys.readouterr().out
    assert "ARGUMENT ERROR" in output
    assert "--max-history-characters" in output


def test_chat_command_passes_max_run_cost(monkeypatch, capsys, tmp_path):
    received_arguments = {}

    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
        max_history_characters=12000,
        max_run_cost=None,
        preflight_max_run_cost=None,
        use_long_term_memory=True,
        max_memory_weaknesses=5,
        max_memory_summaries=3,
        compact_session=True,
        compact_summary_max_characters=4000,
    ):
        received_arguments["max_run_cost"] = max_run_cost

        return (
            build_fake_agent_result("budget answer"),
            SimpleNamespace(session_id="budget-session"),
            tmp_path / "budget-session.json",
        )

    monkeypatch.setattr(cli, "run_agent_session", fake_run_agent_session)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test budget",
            "--max-run-cost",
            "0.05",
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert received_arguments["max_run_cost"] == 0.05
    assert "budget answer" in output


def test_chat_command_rejects_negative_max_run_cost(monkeypatch, capsys):
    def run_agent_session_should_not_run(*args, **kwargs):
        raise AssertionError("invalid arguments should not run Agent")

    monkeypatch.setattr(cli, "run_agent_session", run_agent_session_should_not_run)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test",
            "--max-run-cost",
            "-0.01",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2
    output = capsys.readouterr().out
    assert "ARGUMENT ERROR" in output
    assert "--max-run-cost" in output


def test_chat_command_handles_budget_exceeded(monkeypatch, capsys):
    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
        max_history_characters=12000,
        max_run_cost=None,
        preflight_max_run_cost=None,
        use_long_term_memory=True,
        max_memory_weaknesses=5,
        max_memory_summaries=3,
        compact_session=True,
        compact_summary_max_characters=4000,
    ):
        raise BudgetExceededError(
            actual_cost=0.06,
            max_cost=0.05,
            currency="CNY",
        )

    monkeypatch.setattr(cli, "run_agent_session", fake_run_agent_session)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test budget exceeded",
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


def test_chat_command_passes_preflight_max_run_cost(monkeypatch, capsys, tmp_path):
    received_arguments = {}

    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
        max_history_characters=12000,
        max_run_cost=None,
        preflight_max_run_cost=None,
        use_long_term_memory=True,
        max_memory_weaknesses=5,
        max_memory_summaries=3,
        compact_session=True,
        compact_summary_max_characters=4000,
    ):
        received_arguments["preflight_max_run_cost"] = preflight_max_run_cost

        return (
            build_fake_agent_result("preflight budget answer"),
            SimpleNamespace(session_id="preflight-session"),
            tmp_path / "preflight-session.json",
        )

    monkeypatch.setattr(cli, "run_agent_session", fake_run_agent_session)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test preflight budget",
            "--preflight-max-run-cost",
            "0.02",
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert received_arguments["preflight_max_run_cost"] == 0.02
    assert "preflight budget answer" in output


def test_chat_command_rejects_negative_preflight_max_run_cost(monkeypatch, capsys):
    def run_agent_session_should_not_run(*args, **kwargs):
        raise AssertionError("invalid arguments should not run Agent")

    monkeypatch.setattr(cli, "run_agent_session", run_agent_session_should_not_run)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test",
            "--preflight-max-run-cost",
            "-0.01",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2
    output = capsys.readouterr().out
    assert "ARGUMENT ERROR" in output
    assert "--preflight-max-run-cost" in output


def test_chat_command_handles_preflight_budget_exceeded(monkeypatch, capsys):
    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
        max_history_characters=12000,
        max_run_cost=None,
        preflight_max_run_cost=None,
        use_long_term_memory=True,
        max_memory_weaknesses=5,
        max_memory_summaries=3,
        compact_session=True,
        compact_summary_max_characters=4000,
    ):
        raise PreflightBudgetExceededError(
            estimated_cost=0.06,
            max_cost=0.05,
            currency="CNY",
            estimated_total_tokens=20000,
        )

    monkeypatch.setattr(cli, "run_agent_session", fake_run_agent_session)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test preflight budget exceeded",
            "--preflight-max-run-cost",
            "0.05",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "PREFLIGHT BUDGET ERROR" in output
    assert "0.060000 CNY" in output
    assert "0.050000 CNY" in output


def test_chat_command_passes_memory_controls(monkeypatch, capsys, tmp_path):
    received_arguments = {}

    def fake_run_agent_session(
        user_message,
        session_id=None,
        max_history_turns=6,
        max_history_characters=12000,
        max_run_cost=None,
        preflight_max_run_cost=None,
        use_long_term_memory=True,
        max_memory_weaknesses=5,
        max_memory_summaries=3,
        compact_session=True,
        compact_summary_max_characters=4000,
    ):
        received_arguments["user_message"] = user_message
        received_arguments["use_long_term_memory"] = use_long_term_memory
        received_arguments["max_memory_weaknesses"] = max_memory_weaknesses
        received_arguments["max_memory_summaries"] = max_memory_summaries

        return (
            build_fake_agent_result("memory controls answer"),
            SimpleNamespace(session_id="memory-control-session"),
            tmp_path / "memory-control-session.json",
        )

    monkeypatch.setattr(cli, "run_agent_session", fake_run_agent_session)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test memory controls",
            "--disable-memory",
            "--max-memory-weaknesses",
            "2",
            "--max-memory-summaries",
            "1",
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert received_arguments == {
        "user_message": "test memory controls",
        "use_long_term_memory": False,
        "max_memory_weaknesses": 2,
        "max_memory_summaries": 1,
    }
    assert "memory controls answer" in output


def test_chat_command_rejects_negative_max_memory_weaknesses(monkeypatch, capsys):
    def run_agent_session_should_not_run(*args, **kwargs):
        raise AssertionError("invalid arguments should not run Agent")

    monkeypatch.setattr(cli, "run_agent_session", run_agent_session_should_not_run)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test",
            "--max-memory-weaknesses",
            "-1",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2
    output = capsys.readouterr().out
    assert "ARGUMENT ERROR" in output
    assert "--max-memory-weaknesses" in output


def test_chat_command_rejects_negative_max_memory_summaries(monkeypatch, capsys):
    def run_agent_session_should_not_run(*args, **kwargs):
        raise AssertionError("invalid arguments should not run Agent")

    monkeypatch.setattr(cli, "run_agent_session", run_agent_session_should_not_run)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test",
            "--max-memory-summaries",
            "-1",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2
    output = capsys.readouterr().out
    assert "ARGUMENT ERROR" in output
    assert "--max-memory-summaries" in output


def test_chat_command_passes_session_compaction_controls(
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
        preflight_max_run_cost=None,
        use_long_term_memory=True,
        max_memory_weaknesses=5,
        max_memory_summaries=3,
        compact_session=True,
        compact_summary_max_characters=4000,
    ):
        received_arguments["compact_session"] = compact_session
        received_arguments["compact_summary_max_characters"] = (
            compact_summary_max_characters
        )

        return (
            build_fake_agent_result("compaction controls answer"),
            SimpleNamespace(session_id="compaction-control-session"),
            tmp_path / "compaction-control-session.json",
        )

    monkeypatch.setattr(cli, "run_agent_session", fake_run_agent_session)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test compaction controls",
            "--disable-session-compaction",
            "--compact-summary-max-characters",
            "1200",
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert received_arguments == {
        "compact_session": False,
        "compact_summary_max_characters": 1200,
    }
    assert "compaction controls answer" in output


def test_chat_command_rejects_invalid_compact_summary_characters(
    monkeypatch,
    capsys,
):
    def run_agent_session_should_not_run(*args, **kwargs):
        raise AssertionError("invalid arguments should not run Agent")

    monkeypatch.setattr(cli, "run_agent_session", run_agent_session_should_not_run)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "chat",
            "--message",
            "test",
            "--compact-summary-max-characters",
            "0",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2
    output = capsys.readouterr().out
    assert "ARGUMENT ERROR" in output
    assert "--compact-summary-max-characters" in output

