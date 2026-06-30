import pytest

from app import cli
from app.qdrant_snapshot_smoke_plan import (
    build_qdrant_snapshot_smoke_plan,
    render_qdrant_snapshot_smoke_plan,
    render_qdrant_snapshot_smoke_report_template,
)


def test_build_qdrant_snapshot_smoke_plan_contains_expected_steps():
    plan = build_qdrant_snapshot_smoke_plan()

    assert plan.url == "http://127.0.0.1:6333"
    assert plan.collection == "thesis_chunks"
    assert plan.restore_collection == "thesis_chunks_restore"
    assert plan.backup_dir == "data/qdrant_backups"

    assert [step.name for step in plan.steps] == [
        "ensure_backup_dir",
        "create_snapshot",
        "list_snapshots",
        "download_snapshot",
        "restore_to_disposable_collection",
        "compare_restored_collection",
        "retention_dry_run",
    ]
    assert plan.steps[0].requires_qdrant is False
    assert all(step.requires_qdrant for step in plan.steps[1:6])
    assert plan.steps[6].requires_qdrant is False
    assert "/collections/thesis_chunks/snapshots" in plan.steps[1].command
    assert "thesis_chunks_restore/snapshots/upload" in plan.steps[4].command
    assert "compare-vector-store-backends" in plan.steps[5].command
    assert "qdrant-backup-retention" in plan.steps[6].command


def test_build_qdrant_snapshot_smoke_plan_accepts_custom_values():
    plan = build_qdrant_snapshot_smoke_plan(
        url="http://qdrant.local:6333/",
        collection="source_chunks",
        restore_collection="restore_chunks",
        backup_dir="tmp/backups",
        snapshot_name_placeholder="snapshot-1.snapshot",
    )

    rendered = render_qdrant_snapshot_smoke_plan(plan)

    assert "- Qdrant URL: `http://qdrant.local:6333`" in rendered
    assert "- Source collection: `source_chunks`" in rendered
    assert "- Restore collection: `restore_chunks`" in rendered
    assert "tmp/backups/snapshot-1.snapshot" in rendered


def test_build_qdrant_snapshot_smoke_plan_validates_inputs():
    with pytest.raises(ValueError, match="url"):
        build_qdrant_snapshot_smoke_plan(url=" ")

    with pytest.raises(ValueError, match="collection"):
        build_qdrant_snapshot_smoke_plan(collection="")

    with pytest.raises(ValueError, match="restore_collection"):
        build_qdrant_snapshot_smoke_plan(restore_collection="")

    with pytest.raises(ValueError, match="different"):
        build_qdrant_snapshot_smoke_plan(
            collection="same",
            restore_collection="same",
        )

    with pytest.raises(ValueError, match="backup_dir"):
        build_qdrant_snapshot_smoke_plan(backup_dir="")

    with pytest.raises(ValueError, match="snapshot_name_placeholder"):
        build_qdrant_snapshot_smoke_plan(snapshot_name_placeholder=" ")


def test_render_qdrant_snapshot_smoke_report_template_contains_evidence_fields():
    plan = build_qdrant_snapshot_smoke_plan(
        restore_collection="restore_chunks",
    )

    rendered = render_qdrant_snapshot_smoke_report_template(
        plan,
        environment="local-compose",
        operator="tester",
    )

    assert "# Qdrant Snapshot Smoke Execution Report" in rendered
    assert "- Environment: `local-compose`" in rendered
    assert "- Operator: `tester`" in rendered
    assert "- Result: `[ ] PASS  [ ] FAIL  [ ] SKIPPED`" in rendered
    assert "Evidence:" in rendered
    assert "restore_chunks/snapshots/upload" in rendered


def test_render_qdrant_snapshot_smoke_report_template_rejects_empty_environment():
    plan = build_qdrant_snapshot_smoke_plan()

    with pytest.raises(ValueError, match="environment"):
        render_qdrant_snapshot_smoke_report_template(plan, environment=" ")


def test_qdrant_snapshot_smoke_plan_cli_prints_plan(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-smoke-plan",
            "--restore-collection",
            "restore_chunks",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Qdrant Snapshot Smoke Plan" in output
    assert "Invoke-RestMethod" in output
    assert "restore_chunks/snapshots/upload" in output
    assert "qdrant-backup-retention" in output


def test_qdrant_snapshot_smoke_plan_cli_writes_markdown(
    monkeypatch,
    capsys,
    tmp_path,
):
    output_path = tmp_path / "snapshot-plan.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-smoke-plan",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    saved = output_path.read_text(encoding="utf-8")

    assert "OUTPUT:" in output
    assert "# Qdrant Snapshot Smoke Plan" in saved


def test_qdrant_snapshot_smoke_report_cli_prints_template(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-smoke-report-template",
            "--environment",
            "local-compose",
            "--operator",
            "tester",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Qdrant Snapshot Smoke Execution Report" in output
    assert "- Environment: `local-compose`" in output
    assert "- Operator: `tester`" in output
    assert "Paste sanitized command output here." in output


def test_qdrant_snapshot_smoke_cli_rejects_invalid_restore_collection(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-smoke-plan",
            "--collection",
            "same",
            "--restore-collection",
            "same",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 2
    assert "QDRANT SNAPSHOT SMOKE PLAN ERROR:" in output
