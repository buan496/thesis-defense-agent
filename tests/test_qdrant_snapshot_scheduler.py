import pytest

from app import cli
from app.qdrant_snapshot_scheduler import (
    build_qdrant_snapshot_drill_plan,
    render_qdrant_snapshot_drill_plan,
)


def test_build_qdrant_snapshot_drill_plan_contains_expected_steps():
    plan = build_qdrant_snapshot_drill_plan()

    assert plan.url == "http://127.0.0.1:6333"
    assert plan.collection == "thesis_chunks"
    assert plan.restore_collection == "thesis_chunks_restore"
    assert plan.backup_dir == "data/qdrant_backups"
    assert plan.keep_last == 5
    assert plan.apply_retention is False
    assert plan.run_restore_drill is True
    assert [step.name for step in plan.steps] == [
        "ensure_backup_dir",
        "create_snapshot",
        "download_snapshot",
        "apply_retention",
        "restore_to_disposable_collection",
        "compare_restored_collection",
    ]


def test_build_qdrant_snapshot_drill_plan_can_disable_restore_drill():
    plan = build_qdrant_snapshot_drill_plan(run_restore_drill=False)

    assert plan.run_restore_drill is False
    assert [step.name for step in plan.steps] == [
        "ensure_backup_dir",
        "create_snapshot",
        "download_snapshot",
        "apply_retention",
    ]


def test_build_qdrant_snapshot_drill_plan_accepts_custom_values():
    plan = build_qdrant_snapshot_drill_plan(
        url="http://qdrant.local:6333/",
        collection="source_chunks",
        restore_collection="restore_chunks",
        backup_dir="tmp/backups",
        keep_last=3,
        apply_retention=True,
    )
    rendered = render_qdrant_snapshot_drill_plan(plan)

    assert "- Qdrant URL: `http://qdrant.local:6333`" in rendered
    assert "- Source collection: `source_chunks`" in rendered
    assert "- Restore collection: `restore_chunks`" in rendered
    assert "- Backup directory: `tmp/backups`" in rendered
    assert "- Keep last: `3`" in rendered
    assert "- Apply retention: `True`" in rendered
    assert "apply retention keep_last=3" in rendered


def test_build_qdrant_snapshot_drill_plan_validates_inputs():
    with pytest.raises(ValueError, match="url"):
        build_qdrant_snapshot_drill_plan(url=" ")

    with pytest.raises(ValueError, match="collection"):
        build_qdrant_snapshot_drill_plan(collection="")

    with pytest.raises(ValueError, match="restore_collection"):
        build_qdrant_snapshot_drill_plan(restore_collection="")

    with pytest.raises(ValueError, match="different"):
        build_qdrant_snapshot_drill_plan(
            collection="same",
            restore_collection="same",
        )

    with pytest.raises(ValueError, match="backup_dir"):
        build_qdrant_snapshot_drill_plan(backup_dir=" ")

    with pytest.raises(ValueError, match="keep_last"):
        build_qdrant_snapshot_drill_plan(keep_last=-1)


def test_qdrant_snapshot_drill_plan_cli_prints_plan(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-drill-plan",
            "--collection",
            "source_chunks",
            "--restore-collection",
            "restore_chunks",
            "--keep-last",
            "3",
            "--apply-retention",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Qdrant Snapshot Drill Plan" in output
    assert "- Source collection: `source_chunks`" in output
    assert "- Restore collection: `restore_chunks`" in output
    assert "- Keep last: `3`" in output
    assert "- Apply retention: `True`" in output


def test_qdrant_snapshot_drill_plan_cli_writes_markdown(
    monkeypatch,
    capsys,
    tmp_path,
):
    output_path = tmp_path / "drill-plan.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-drill-plan",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    saved = output_path.read_text(encoding="utf-8")

    assert "OUTPUT:" in output
    assert "# Qdrant Snapshot Drill Plan" in saved


def test_qdrant_snapshot_drill_plan_cli_rejects_invalid_restore_collection(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-drill-plan",
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
    assert "QDRANT SNAPSHOT DRILL PLAN ERROR:" in output
