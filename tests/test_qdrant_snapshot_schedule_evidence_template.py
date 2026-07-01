import pytest

from app import cli
from app.qdrant_snapshot_scheduler import (
    build_qdrant_snapshot_schedule_config,
    render_qdrant_snapshot_schedule_evidence_template,
)


def test_render_qdrant_snapshot_schedule_evidence_template_contains_sections():
    config = build_qdrant_snapshot_schedule_config(
        platform="cron",
        task_name="qdrant-drill",
    )

    rendered = render_qdrant_snapshot_schedule_evidence_template(
        config,
        environment="local",
        operator="tester",
    )

    assert "# Qdrant Snapshot Schedule Evidence Report" in rendered
    assert "- Environment: `local`" in rendered
    assert "- Operator: `tester`" in rendered
    assert "## 1. Pre-Install Manual Drill" in rendered
    assert "## 2. Install Command" in rendered
    assert "## 3. Check scheduled command" in rendered
    assert "## 5. Rollback scheduled command" in rendered
    assert "- Result: `[ ] PASS  [ ] FAIL  [ ] SKIPPED`" in rendered
    assert "Paste sanitized command output here." in rendered
    assert "## Safety Checklist" in rendered


def test_render_qdrant_snapshot_schedule_evidence_template_defaults_operator():
    config = build_qdrant_snapshot_schedule_config(platform="cron")

    rendered = render_qdrant_snapshot_schedule_evidence_template(config)

    assert "- Operator: `TBD`" in rendered


def test_render_qdrant_snapshot_schedule_evidence_template_rejects_empty_environment():
    config = build_qdrant_snapshot_schedule_config(platform="cron")

    with pytest.raises(ValueError, match="environment"):
        render_qdrant_snapshot_schedule_evidence_template(
            config,
            environment=" ",
        )


def test_render_qdrant_snapshot_schedule_evidence_template_rejects_all_platform():
    config = build_qdrant_snapshot_schedule_config(platform="all")

    with pytest.raises(ValueError, match="platform"):
        render_qdrant_snapshot_schedule_evidence_template(config)


def test_qdrant_snapshot_schedule_evidence_template_cli_prints_template(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-schedule-evidence-template",
            "--platform",
            "windows_task_scheduler",
            "--task-name",
            "qdrant-drill",
            "--environment",
            "windows-local",
            "--operator",
            "tester",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Qdrant Snapshot Schedule Evidence Report" in output
    assert "- Platform: `windows_task_scheduler`" in output
    assert "- Environment: `windows-local`" in output
    assert 'schtasks /Create /F /TN "qdrant-drill"' in output
    assert 'schtasks /Delete /TN "qdrant-drill" /F' in output


def test_qdrant_snapshot_schedule_evidence_template_cli_writes_markdown(
    monkeypatch,
    capsys,
    tmp_path,
):
    output_path = tmp_path / "evidence.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-schedule-evidence-template",
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
    assert "# Qdrant Snapshot Schedule Evidence Report" in saved


def test_qdrant_snapshot_schedule_evidence_template_cli_rejects_all(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-schedule-evidence-template",
            "--platform",
            "all",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 2
    assert "QDRANT SNAPSHOT SCHEDULE EVIDENCE TEMPLATE ERROR:" in output
