import pytest

from app import cli
from app.qdrant_snapshot_scheduler import (
    build_qdrant_snapshot_schedule_config,
    build_qdrant_snapshot_schedule_install_plan,
    render_qdrant_snapshot_schedule_install_plan,
)


def test_build_qdrant_snapshot_schedule_install_plan_defaults_to_dry_run():
    config = build_qdrant_snapshot_schedule_config()
    plan = build_qdrant_snapshot_schedule_install_plan(config)
    rendered = render_qdrant_snapshot_schedule_install_plan(plan)

    assert plan.apply is False
    assert len(plan.commands) == 3
    assert all(not command.applies_system_change for command in plan.commands)
    assert "# Qdrant Snapshot Schedule Install Plan" in rendered
    assert "- Mode: `dry-run`" in rendered
    assert "## cron" in rendered
    assert "## windows_task_scheduler" in rendered
    assert "## kubernetes_cronjob" in rendered


def test_build_qdrant_snapshot_schedule_install_plan_apply_single_platform():
    config = build_qdrant_snapshot_schedule_config(platform="cron")
    plan = build_qdrant_snapshot_schedule_install_plan(
        config,
        apply=True,
        confirm_task_name=config.task_name,
    )

    assert plan.apply is True
    assert len(plan.commands) == 1
    assert plan.commands[0].platform == "cron"
    assert plan.commands[0].applies_system_change is True
    assert "crontab -" in plan.commands[0].command
    assert not plan.commands[0].command.startswith("echo")


def test_build_qdrant_snapshot_schedule_install_plan_uses_script_file_for_windows():
    config = build_qdrant_snapshot_schedule_config(
        platform="windows_task_scheduler",
        working_directory="E:/project with spaces",
    )
    plan = build_qdrant_snapshot_schedule_install_plan(
        config,
        apply=True,
        confirm_task_name=config.task_name,
    )

    command = plan.commands[0].command

    assert "powershell.exe -NoProfile -ExecutionPolicy Bypass -File" in command
    assert "thesis-defense-agent" in command
    assert "scheduled_tasks" in command
    assert " -Command " not in command
    assert "Set-Location" not in command


def test_build_qdrant_snapshot_schedule_install_plan_rejects_apply_all():
    config = build_qdrant_snapshot_schedule_config(platform="all")

    with pytest.raises(ValueError, match="platform"):
        build_qdrant_snapshot_schedule_install_plan(
            config,
            apply=True,
            confirm_task_name=config.task_name,
        )


def test_build_qdrant_snapshot_schedule_install_plan_requires_confirmation():
    config = build_qdrant_snapshot_schedule_config(platform="cron")

    with pytest.raises(ValueError, match="confirm_task_name"):
        build_qdrant_snapshot_schedule_install_plan(
            config,
            apply=True,
            confirm_task_name="wrong-name",
        )


def test_qdrant_snapshot_schedule_install_plan_cli_prints_plan(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-schedule-install-plan",
            "--platform",
            "windows_task_scheduler",
            "--task-name",
            "qdrant-drill",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Qdrant Snapshot Schedule Install Plan" in output
    assert "- Mode: `dry-run`" in output
    assert "- Platform: `windows_task_scheduler`" in output
    assert "qdrant-drill" in output
    assert "Write-Output" in output


def test_qdrant_snapshot_schedule_install_plan_cli_writes_markdown(
    monkeypatch,
    capsys,
    tmp_path,
):
    output_path = tmp_path / "install-plan.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-schedule-install-plan",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    saved = output_path.read_text(encoding="utf-8")

    assert "OUTPUT:" in output
    assert "# Qdrant Snapshot Schedule Install Plan" in saved


def test_qdrant_snapshot_schedule_install_plan_cli_rejects_apply_without_confirm(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-schedule-install-plan",
            "--platform",
            "cron",
            "--apply",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 2
    assert "QDRANT SNAPSHOT SCHEDULE INSTALL PLAN ERROR:" in output
