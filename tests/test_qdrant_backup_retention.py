import os
from pathlib import Path

import pytest

from app import cli
from app.qdrant_backup_retention import (
    build_qdrant_backup_retention_plan,
    execute_qdrant_backup_retention,
    render_qdrant_backup_retention_report,
)


def create_backup_file(
    directory: Path,
    name: str,
    modified_timestamp: float,
) -> Path:
    path = directory / name
    path.write_text(name, encoding="utf-8")
    os.utime(path, (modified_timestamp, modified_timestamp))
    return path


def test_build_qdrant_backup_retention_plan_keeps_newest_files(tmp_path):
    create_backup_file(tmp_path, "old.snapshot", 100)
    create_backup_file(tmp_path, "middle.snapshot", 200)
    create_backup_file(tmp_path, "new.snapshot", 300)
    create_backup_file(tmp_path, "ignored.txt", 400)

    plan = build_qdrant_backup_retention_plan(
        backup_dir=str(tmp_path),
        keep_last=2,
    )

    assert [item.name for item in plan.retained] == [
        "new.snapshot",
        "middle.snapshot",
    ]
    assert [item.name for item in plan.deletion_candidates] == [
        "old.snapshot",
    ]


def test_build_qdrant_backup_retention_plan_supports_custom_patterns(tmp_path):
    create_backup_file(tmp_path, "a.snapshot", 100)
    create_backup_file(tmp_path, "b.tar.gz", 200)

    plan = build_qdrant_backup_retention_plan(
        backup_dir=str(tmp_path),
        keep_last=1,
        patterns=["*.snapshot", "*.tar.gz"],
    )

    assert [item.name for item in plan.retained] == ["b.tar.gz"]
    assert [item.name for item in plan.deletion_candidates] == ["a.snapshot"]


def test_execute_qdrant_backup_retention_dry_run_does_not_delete(tmp_path):
    old_backup = create_backup_file(tmp_path, "old.snapshot", 100)
    new_backup = create_backup_file(tmp_path, "new.snapshot", 200)
    plan = build_qdrant_backup_retention_plan(
        backup_dir=str(tmp_path),
        keep_last=1,
    )

    result = execute_qdrant_backup_retention(plan, dry_run=True)

    assert result.dry_run is True
    assert result.deleted == []
    assert [item.name for item in result.skipped] == ["old.snapshot"]
    assert old_backup.exists()
    assert new_backup.exists()


def test_execute_qdrant_backup_retention_apply_deletes_candidates(tmp_path):
    old_backup = create_backup_file(tmp_path, "old.snapshot", 100)
    new_backup = create_backup_file(tmp_path, "new.snapshot", 200)
    plan = build_qdrant_backup_retention_plan(
        backup_dir=str(tmp_path),
        keep_last=1,
    )

    result = execute_qdrant_backup_retention(plan, dry_run=False)

    assert result.dry_run is False
    assert [item.name for item in result.deleted] == ["old.snapshot"]
    assert result.skipped == []
    assert not old_backup.exists()
    assert new_backup.exists()


def test_build_qdrant_backup_retention_plan_validates_inputs(tmp_path):
    with pytest.raises(ValueError, match="keep_last"):
        build_qdrant_backup_retention_plan(str(tmp_path), keep_last=-1)

    with pytest.raises(ValueError, match="patterns"):
        build_qdrant_backup_retention_plan(str(tmp_path), patterns=[])

    with pytest.raises(ValueError, match="patterns"):
        build_qdrant_backup_retention_plan(str(tmp_path), patterns=[" "])

    with pytest.raises(FileNotFoundError, match="backup_dir"):
        build_qdrant_backup_retention_plan(str(tmp_path / "missing"))

    file_path = tmp_path / "not-a-directory"
    file_path.write_text("x", encoding="utf-8")

    with pytest.raises(NotADirectoryError, match="backup_dir"):
        build_qdrant_backup_retention_plan(str(file_path))


def test_render_qdrant_backup_retention_report_contains_counts(tmp_path):
    create_backup_file(tmp_path, "old.snapshot", 100)
    create_backup_file(tmp_path, "new.snapshot", 200)
    plan = build_qdrant_backup_retention_plan(
        backup_dir=str(tmp_path),
        keep_last=1,
    )
    result = execute_qdrant_backup_retention(plan, dry_run=True)

    rendered = render_qdrant_backup_retention_report(result)

    assert "# Qdrant Backup Retention Report" in rendered
    assert "- Dry run: `True`" in rendered
    assert "- Retained count: `1`" in rendered
    assert "- Deletion candidate count: `1`" in rendered
    assert "`new.snapshot`" in rendered
    assert "`old.snapshot`" in rendered


def test_qdrant_backup_retention_cli_defaults_to_dry_run(
    monkeypatch,
    capsys,
    tmp_path,
):
    old_backup = create_backup_file(tmp_path, "old.snapshot", 100)
    create_backup_file(tmp_path, "new.snapshot", 200)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-backup-retention",
            "--backup-dir",
            str(tmp_path),
            "--keep-last",
            "1",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "# Qdrant Backup Retention Report" in output
    assert "- Dry run: `True`" in output
    assert old_backup.exists()


def test_qdrant_backup_retention_cli_apply_deletes_candidates(
    monkeypatch,
    capsys,
    tmp_path,
):
    old_backup = create_backup_file(tmp_path, "old.snapshot", 100)
    create_backup_file(tmp_path, "new.snapshot", 200)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-backup-retention",
            "--backup-dir",
            str(tmp_path),
            "--keep-last",
            "1",
            "--apply",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "- Dry run: `False`" in output
    assert "- Deleted count: `1`" in output
    assert not old_backup.exists()


def test_qdrant_backup_retention_cli_writes_report(
    monkeypatch,
    capsys,
    tmp_path,
):
    output_path = tmp_path / "retention.md"
    create_backup_file(tmp_path, "backup.snapshot", 100)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-backup-retention",
            "--backup-dir",
            str(tmp_path),
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    saved = output_path.read_text(encoding="utf-8")

    assert "OUTPUT:" in output
    assert "# Qdrant Backup Retention Report" in saved


def test_qdrant_backup_retention_cli_rejects_missing_directory(
    monkeypatch,
    capsys,
    tmp_path,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-backup-retention",
            "--backup-dir",
            str(tmp_path / "missing"),
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 2
    assert "QDRANT BACKUP RETENTION ERROR:" in output
