import pytest

from app import cli
from app.milvus_backup_restore_plan import (
    build_milvus_backup_restore_plan,
    render_milvus_backup_restore_plan,
    render_milvus_restore_report_template,
)


def test_build_milvus_backup_restore_plan_contains_expected_steps():
    plan = build_milvus_backup_restore_plan()

    assert plan.uri == "http://127.0.0.1:19530"
    assert plan.collection == "thesis_chunks"
    assert plan.restore_collection == "thesis_chunks_restore"
    assert plan.source == "data/vector_store.json"
    assert plan.backup_dir == "data/milvus_backups"

    assert [step.name for step in plan.steps] == [
        "ensure_backup_dir",
        "verify_milvus_health",
        "verify_json_baseline",
        "rebuild_restore_collection_from_json",
        "compare_restore_collection",
        "optional_volume_backup",
        "restore_boundary_check",
    ]
    assert plan.steps[0].requires_milvus is False
    assert plan.steps[1].requires_milvus is True
    assert plan.steps[2].requires_milvus is False
    assert plan.steps[3].requires_milvus is True
    assert plan.steps[4].requires_milvus is True
    assert plan.steps[5].requires_milvus is False
    assert plan.steps[6].requires_milvus is False
    assert "import-vector-store-to-milvus" in plan.steps[3].command
    assert "--collection thesis_chunks_restore" in plan.steps[3].command
    assert "compare-vector-store-backends" in plan.steps[4].command
    assert "--include-milvus" in plan.steps[4].command
    assert "thesis-defense-agent_milvus_data" in plan.steps[5].command


def test_build_milvus_backup_restore_plan_accepts_custom_values():
    plan = build_milvus_backup_restore_plan(
        uri="http://milvus.local:19530/",
        collection="source_chunks",
        restore_collection="restore_chunks",
        source="tmp/vector_store.json",
        backup_dir="tmp/milvus_backups",
        vector_size=768,
        metric_type="ip",
        volume_name="custom_milvus_data",
        backup_file_name="custom_backup.tar.gz",
    )

    rendered = render_milvus_backup_restore_plan(plan)

    assert "- Milvus URI: `http://milvus.local:19530`" in rendered
    assert "- Source collection: `source_chunks`" in rendered
    assert "- Restore collection: `restore_chunks`" in rendered
    assert "- Vector size: `768`" in rendered
    assert "- Metric type: `IP`" in rendered
    assert "custom_milvus_data" in rendered
    assert "custom_backup.tar.gz" in rendered


def test_build_milvus_backup_restore_plan_validates_inputs():
    with pytest.raises(ValueError, match="uri"):
        build_milvus_backup_restore_plan(uri=" ")

    with pytest.raises(ValueError, match="collection"):
        build_milvus_backup_restore_plan(collection="")

    with pytest.raises(ValueError, match="restore_collection"):
        build_milvus_backup_restore_plan(restore_collection="")

    with pytest.raises(ValueError, match="different"):
        build_milvus_backup_restore_plan(
            collection="same",
            restore_collection="same",
        )

    with pytest.raises(ValueError, match="source"):
        build_milvus_backup_restore_plan(source="")

    with pytest.raises(ValueError, match="backup_dir"):
        build_milvus_backup_restore_plan(backup_dir="")

    with pytest.raises(ValueError, match="vector_size"):
        build_milvus_backup_restore_plan(vector_size=0)

    with pytest.raises(ValueError, match="metric_type"):
        build_milvus_backup_restore_plan(metric_type=" ")

    with pytest.raises(ValueError, match="volume_name"):
        build_milvus_backup_restore_plan(volume_name=" ")

    with pytest.raises(ValueError, match="backup_file_name"):
        build_milvus_backup_restore_plan(backup_file_name="")


def test_render_milvus_restore_report_template_contains_evidence_fields():
    plan = build_milvus_backup_restore_plan(
        restore_collection="restore_chunks",
    )

    rendered = render_milvus_restore_report_template(
        plan,
        environment="local-compose",
        operator="tester",
    )

    assert "# Milvus Backup / Restore Execution Report" in rendered
    assert "- Environment: `local-compose`" in rendered
    assert "- Operator: `tester`" in rendered
    assert "- Restore collection row count: `TBD`" in rendered
    assert "- Result: `[ ] PASS  [ ] FAIL  [ ] SKIPPED`" in rendered
    assert "Paste sanitized command output here." in rendered
    assert "--collection restore_chunks" in rendered


def test_render_milvus_restore_report_template_rejects_empty_environment():
    plan = build_milvus_backup_restore_plan()

    with pytest.raises(ValueError, match="environment"):
        render_milvus_restore_report_template(plan, environment=" ")


def test_milvus_backup_restore_plan_cli_prints_plan(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "milvus-backup-restore-plan",
            "--restore-collection",
            "restore_chunks",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Milvus Backup / Restore Plan" in output
    assert "import-vector-store-to-milvus" in output
    assert "--collection restore_chunks" in output
    assert "optional_volume_backup" in output


def test_milvus_backup_restore_plan_cli_writes_markdown(
    monkeypatch,
    capsys,
    tmp_path,
):
    output_path = tmp_path / "milvus-plan.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "milvus-backup-restore-plan",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    saved = output_path.read_text(encoding="utf-8")

    assert "OUTPUT:" in output
    assert "# Milvus Backup / Restore Plan" in saved


def test_milvus_restore_report_template_cli_prints_template(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "milvus-restore-report-template",
            "--environment",
            "local-compose",
            "--operator",
            "tester",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Milvus Backup / Restore Execution Report" in output
    assert "- Environment: `local-compose`" in output
    assert "- Operator: `tester`" in output
    assert "Paste sanitized command output here." in output


def test_milvus_backup_restore_cli_rejects_invalid_restore_collection(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "milvus-backup-restore-plan",
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
    assert "MILVUS BACKUP RESTORE PLAN ERROR:" in output
