import pytest

from app import cli
from app.qdrant_snapshot_scheduler import (
    build_qdrant_snapshot_schedule_config,
    build_qdrant_snapshot_schedule_verification_plan,
    render_qdrant_snapshot_schedule_verification_plan,
)


def test_build_qdrant_snapshot_schedule_verification_plan_for_cron():
    config = build_qdrant_snapshot_schedule_config(platform="cron")
    plan = build_qdrant_snapshot_schedule_verification_plan(config)
    rendered = render_qdrant_snapshot_schedule_verification_plan(plan)

    assert plan.config.platform == "cron"
    assert [command.purpose for command in plan.commands] == [
        "Check scheduled command",
        "Check scheduler log",
        "Rollback scheduled command",
    ]
    assert plan.commands[-1].destructive is True
    assert "crontab -l" in rendered
    assert "# Qdrant Snapshot Schedule Verification Plan" in rendered


def test_build_qdrant_snapshot_schedule_verification_plan_for_windows():
    config = build_qdrant_snapshot_schedule_config(
        platform="windows_task_scheduler",
        task_name="qdrant-drill",
    )
    plan = build_qdrant_snapshot_schedule_verification_plan(config)

    assert len(plan.commands) == 3
    assert plan.commands[0].platform == "windows_task_scheduler"
    assert 'schtasks /Query /TN "qdrant-drill"' in plan.commands[0].command
    assert 'schtasks /Delete /TN "qdrant-drill" /F' in plan.commands[-1].command
    assert plan.commands[-1].destructive is True


def test_build_qdrant_snapshot_schedule_verification_plan_for_kubernetes():
    config = build_qdrant_snapshot_schedule_config(
        platform="kubernetes_cronjob",
        task_name="qdrant-drill",
        namespace="agent",
    )
    plan = build_qdrant_snapshot_schedule_verification_plan(config)

    assert len(plan.commands) == 4
    assert plan.commands[0].command == (
        "kubectl get cronjob qdrant-drill -n agent -o wide"
    )
    assert plan.commands[-1].command == (
        "kubectl delete cronjob qdrant-drill -n agent"
    )
    assert plan.commands[-1].destructive is True


def test_build_qdrant_snapshot_schedule_verification_plan_rejects_all():
    config = build_qdrant_snapshot_schedule_config(platform="all")

    with pytest.raises(ValueError, match="platform"):
        build_qdrant_snapshot_schedule_verification_plan(config)


def test_qdrant_snapshot_schedule_verify_plan_cli_prints_plan(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-schedule-verify-plan",
            "--platform",
            "kubernetes_cronjob",
            "--task-name",
            "qdrant-drill",
            "--namespace",
            "agent",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Qdrant Snapshot Schedule Verification Plan" in output
    assert "- Platform: `kubernetes_cronjob`" in output
    assert "kubectl get cronjob qdrant-drill -n agent -o wide" in output
    assert "Rollback CronJob" in output


def test_qdrant_snapshot_schedule_verify_plan_cli_writes_markdown(
    monkeypatch,
    capsys,
    tmp_path,
):
    output_path = tmp_path / "verify-plan.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-schedule-verify-plan",
            "--platform",
            "cron",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    saved = output_path.read_text(encoding="utf-8")

    assert "OUTPUT:" in output
    assert "# Qdrant Snapshot Schedule Verification Plan" in saved


def test_qdrant_snapshot_schedule_verify_plan_cli_rejects_all(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-schedule-verify-plan",
            "--platform",
            "all",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 2
    assert "QDRANT SNAPSHOT SCHEDULE VERIFY PLAN ERROR:" in output
