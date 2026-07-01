import pytest

from app import cli
from app.qdrant_backup_retention import (
    QdrantBackupFile,
    QdrantBackupRetentionPlan,
    QdrantBackupRetentionResult,
)
from app.qdrant_snapshot_client import QdrantSnapshotInfo
from app.qdrant_snapshot_scheduler import (
    build_qdrant_snapshot_drill_plan,
    execute_qdrant_snapshot_drill,
    render_qdrant_snapshot_drill_plan,
    render_qdrant_snapshot_drill_report,
)


class FakeSnapshotClient:
    def __init__(self):
        self.calls = []

    def create_snapshot(self, collection):
        self.calls.append(("create_snapshot", collection))
        return QdrantSnapshotInfo(
            name="snapshot-1.snapshot",
            creation_time="2026-07-01T10:00:00Z",
            size=123,
        )

    def download_snapshot(self, collection, snapshot_name, output_path):
        self.calls.append(
            ("download_snapshot", collection, snapshot_name, str(output_path))
        )
        output_path.write_bytes(b"snapshot-bytes")
        return str(output_path)

    def restore_snapshot(self, restore_collection, snapshot_path):
        self.calls.append(
            ("restore_snapshot", restore_collection, str(snapshot_path))
        )
        return {"result": True}


def fake_retention_plan_builder(backup_dir, keep_last):
    retained = [
        QdrantBackupFile(
            path=f"{backup_dir}/snapshot-1.snapshot",
            name="snapshot-1.snapshot",
            size_bytes=123,
            modified_timestamp=1,
        )
    ]
    return QdrantBackupRetentionPlan(
        backup_dir=backup_dir,
        keep_last=keep_last,
        patterns=["*.snapshot"],
        retained=retained,
        deletion_candidates=[],
    )


def fake_retention_executor(plan, dry_run):
    return QdrantBackupRetentionResult(
        plan=plan,
        dry_run=dry_run,
        deleted=[],
        skipped=[],
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


def test_execute_qdrant_snapshot_drill_runs_full_sequence(tmp_path):
    client = FakeSnapshotClient()
    compared_collections = []
    plan = build_qdrant_snapshot_drill_plan(
        backup_dir=str(tmp_path),
        keep_last=2,
        apply_retention=True,
    )

    def fake_compare(collection):
        compared_collections.append(collection)
        return {
            "best_repository": "qdrant",
            "score_delta_qdrant_minus_json": 0.0,
            "duration_delta_ms_qdrant_minus_json": 1.2,
        }

    report = execute_qdrant_snapshot_drill(
        plan=plan,
        snapshot_client=client,
        retention_plan_builder=fake_retention_plan_builder,
        retention_executor=fake_retention_executor,
        compare_restored_collection=fake_compare,
    )

    assert report.snapshot_name == "snapshot-1.snapshot"
    assert report.snapshot_path == str(tmp_path / "snapshot-1.snapshot")
    assert report.retention_result.dry_run is False
    assert report.restore_result == {"result": True}
    assert report.compare_report["best_repository"] == "qdrant"
    assert compared_collections == ["thesis_chunks_restore"]
    assert [step.name for step in report.steps] == [
        "ensure_backup_dir",
        "create_snapshot",
        "download_snapshot",
        "apply_retention",
        "restore_to_disposable_collection",
        "compare_restored_collection",
    ]
    assert [call[0] for call in client.calls] == [
        "create_snapshot",
        "download_snapshot",
        "restore_snapshot",
    ]


def test_execute_qdrant_snapshot_drill_can_skip_restore(tmp_path):
    client = FakeSnapshotClient()
    plan = build_qdrant_snapshot_drill_plan(
        backup_dir=str(tmp_path),
        run_restore_drill=False,
    )

    report = execute_qdrant_snapshot_drill(
        plan=plan,
        snapshot_client=client,
        retention_plan_builder=fake_retention_plan_builder,
        retention_executor=fake_retention_executor,
    )

    assert report.restore_result is None
    assert report.compare_report is None
    assert [step.name for step in report.steps] == [
        "ensure_backup_dir",
        "create_snapshot",
        "download_snapshot",
        "apply_retention",
    ]
    assert "restore_snapshot" not in [call[0] for call in client.calls]


def test_execute_qdrant_snapshot_drill_skips_compare_when_not_provided(
    tmp_path,
):
    client = FakeSnapshotClient()
    plan = build_qdrant_snapshot_drill_plan(backup_dir=str(tmp_path))

    report = execute_qdrant_snapshot_drill(
        plan=plan,
        snapshot_client=client,
        retention_plan_builder=fake_retention_plan_builder,
        retention_executor=fake_retention_executor,
    )

    compare_step = report.steps[-1]

    assert compare_step.name == "compare_restored_collection"
    assert compare_step.status == "skipped"
    assert report.compare_report is None


def test_render_qdrant_snapshot_drill_report_contains_summary(tmp_path):
    client = FakeSnapshotClient()
    plan = build_qdrant_snapshot_drill_plan(backup_dir=str(tmp_path))
    report = execute_qdrant_snapshot_drill(
        plan=plan,
        snapshot_client=client,
        retention_plan_builder=fake_retention_plan_builder,
        retention_executor=fake_retention_executor,
        compare_restored_collection=lambda collection: {
            "best_repository": "qdrant",
            "score_delta_qdrant_minus_json": 0.0,
            "duration_delta_ms_qdrant_minus_json": 1.2,
        },
    )

    rendered = render_qdrant_snapshot_drill_report(report)

    assert "# Qdrant Snapshot Drill Report" in rendered
    assert "- Snapshot name: `snapshot-1.snapshot`" in rendered
    assert "`create_snapshot`: `completed`" in rendered
    assert "- Best repository: `qdrant`" in rendered


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


def test_qdrant_snapshot_drill_run_cli_executes_with_fake_client(
    monkeypatch,
    capsys,
    tmp_path,
):
    class FakeQdrantSnapshotClient(FakeSnapshotClient):
        def __init__(self, url, api_key):
            super().__init__()
            self.url = url
            self.api_key = api_key

    monkeypatch.setattr(cli, "QdrantSnapshotClient", FakeQdrantSnapshotClient)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-drill-run",
            "--backup-dir",
            str(tmp_path),
            "--restore-collection",
            "restore_chunks",
            "--confirm-restore-collection",
            "restore_chunks",
            "--skip-compare",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Qdrant Snapshot Drill Report" in output
    assert "- Snapshot name: `snapshot-1.snapshot`" in output
    assert "`restore_to_disposable_collection`: `completed`" in output
    assert "`compare_restored_collection`: `skipped`" in output


def test_qdrant_snapshot_drill_run_cli_requires_restore_confirmation(
    monkeypatch,
    capsys,
    tmp_path,
):
    created = []

    class FakeQdrantSnapshotClient:
        def __init__(self, url, api_key):
            created.append({"url": url, "api_key": api_key})

    monkeypatch.setattr(cli, "QdrantSnapshotClient", FakeQdrantSnapshotClient)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-drill-run",
            "--backup-dir",
            str(tmp_path),
            "--restore-collection",
            "restore_chunks",
            "--confirm-restore-collection",
            "wrong_chunks",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 2
    assert "QDRANT SNAPSHOT DRILL RUN ERROR:" in output
    assert created == []
