import pytest
import tempfile
from pathlib import Path

from app import cli
from app.qdrant_snapshot_scheduler import (
    QdrantSnapshotScheduleInstallExecutionReport,
    QdrantSnapshotScheduleInstallExecutionResult,
    build_qdrant_snapshot_schedule_config,
    build_qdrant_snapshot_schedule_install_plan,
    execute_qdrant_snapshot_schedule_install_plan,
    render_qdrant_snapshot_schedule_install_execution_report,
)


def test_execute_qdrant_snapshot_schedule_install_plan_uses_runner():
    config = build_qdrant_snapshot_schedule_config(platform="cron")
    plan = build_qdrant_snapshot_schedule_install_plan(
        config,
        apply=True,
        confirm_task_name=config.task_name,
    )
    seen = {}

    def fake_runner(command: str, timeout_seconds: int):
        seen["command"] = command
        seen["timeout_seconds"] = timeout_seconds
        return QdrantSnapshotScheduleInstallExecutionResult(
            platform="cron",
            command=command,
            return_code=0,
            stdout="installed",
            stderr="",
            success=True,
        )

    report = execute_qdrant_snapshot_schedule_install_plan(
        plan,
        command_runner=fake_runner,
        timeout_seconds=10,
    )
    rendered = render_qdrant_snapshot_schedule_install_execution_report(report)

    assert seen["command"] == plan.commands[0].command
    assert seen["timeout_seconds"] == 10
    assert report.result.success is True
    assert "installed" in rendered
    assert "# Qdrant Snapshot Schedule Install Execution Report" in rendered


def test_execute_qdrant_snapshot_schedule_install_plan_records_failure():
    config = build_qdrant_snapshot_schedule_config(platform="cron")
    plan = build_qdrant_snapshot_schedule_install_plan(
        config,
        apply=True,
        confirm_task_name=config.task_name,
    )

    def fake_runner(command: str, timeout_seconds: int):
        return QdrantSnapshotScheduleInstallExecutionResult(
            platform="cron",
            command=command,
            return_code=1,
            stdout="",
            stderr="failed",
            success=False,
        )

    report = execute_qdrant_snapshot_schedule_install_plan(
        plan,
        command_runner=fake_runner,
    )

    assert report.result.success is False
    assert report.result.return_code == 1
    assert report.result.stderr == "failed"


def test_execute_qdrant_snapshot_schedule_install_plan_writes_windows_script(
    tmp_path,
):
    config = build_qdrant_snapshot_schedule_config(
        platform="windows_task_scheduler",
        task_name="qdrant-drill",
        working_directory=str(tmp_path),
        log_path="data/reports/drill.log",
    )
    plan = build_qdrant_snapshot_schedule_install_plan(
        config,
        apply=True,
        confirm_task_name=config.task_name,
    )

    def fake_runner(command: str, timeout_seconds: int):
        return QdrantSnapshotScheduleInstallExecutionResult(
            platform="windows_task_scheduler",
            command=command,
            return_code=0,
            stdout="created",
            stderr="",
            success=True,
        )

    execute_qdrant_snapshot_schedule_install_plan(
        plan,
        command_runner=fake_runner,
    )

    script_path = (
        Path(tempfile.gettempdir())
        / "thesis-defense-agent"
        / "scheduled_tasks"
        / "qdrant-drill.ps1"
    )
    script = script_path.read_text(encoding="utf-8")

    assert script_path.exists()
    assert script_path.read_bytes().startswith(b"\xef\xbb\xbf")
    assert "Set-Location -LiteralPath" in script
    assert "qdrant-snapshot-drill-run" in script
    assert "data/reports/drill.log" in script


def test_execute_qdrant_snapshot_schedule_install_plan_rejects_dry_run():
    config = build_qdrant_snapshot_schedule_config(platform="cron")
    plan = build_qdrant_snapshot_schedule_install_plan(config)

    with pytest.raises(ValueError, match="apply"):
        execute_qdrant_snapshot_schedule_install_plan(plan)


def test_execute_qdrant_snapshot_schedule_install_plan_rejects_all_platform():
    config = build_qdrant_snapshot_schedule_config(platform="all")

    with pytest.raises(ValueError, match="platform"):
        build_qdrant_snapshot_schedule_install_plan(
            config,
            apply=True,
            confirm_task_name=config.task_name,
        )


def test_execute_qdrant_snapshot_schedule_install_plan_rejects_bad_timeout():
    config = build_qdrant_snapshot_schedule_config(platform="cron")
    plan = build_qdrant_snapshot_schedule_install_plan(
        config,
        apply=True,
        confirm_task_name=config.task_name,
    )

    with pytest.raises(ValueError, match="timeout_seconds"):
        execute_qdrant_snapshot_schedule_install_plan(
            plan,
            command_runner=lambda command, timeout: QdrantSnapshotScheduleInstallExecutionResult(
                platform="cron",
                command=command,
                return_code=0,
                stdout="",
                stderr="",
                success=True,
            ),
            timeout_seconds=0,
        )


def test_qdrant_snapshot_schedule_install_execute_cli_prints_report(
    monkeypatch,
    capsys,
):
    def fake_execute(plan, timeout_seconds):
        return QdrantSnapshotScheduleInstallExecutionReport(
            plan=plan,
            result=QdrantSnapshotScheduleInstallExecutionResult(
                platform=plan.config.platform,
                command=plan.commands[0].command,
                return_code=0,
                stdout="installed",
                stderr="",
                success=True,
            ),
        )

    monkeypatch.setattr(
        cli,
        "execute_qdrant_snapshot_schedule_install_plan",
        fake_execute,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-schedule-install-execute",
            "--platform",
            "cron",
            "--task-name",
            "qdrant-drill",
            "--confirm-task-name",
            "qdrant-drill",
            "--timeout-seconds",
            "5",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Qdrant Snapshot Schedule Install Execution Report" in output
    assert "- Platform: `cron`" in output
    assert "- Success: `True`" in output
    assert "installed" in output


def test_qdrant_snapshot_schedule_install_execute_cli_rejects_bad_confirmation(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-schedule-install-execute",
            "--platform",
            "cron",
            "--task-name",
            "qdrant-drill",
            "--confirm-task-name",
            "wrong",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 2
    assert "QDRANT SNAPSHOT SCHEDULE INSTALL EXECUTE ERROR:" in output
