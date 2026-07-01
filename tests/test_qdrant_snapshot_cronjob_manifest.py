import pytest

from app import cli
from app.qdrant_snapshot_cronjob_manifest import (
    render_qdrant_snapshot_cronjob_manifest,
)
from app.qdrant_snapshot_scheduler import build_qdrant_snapshot_schedule_config


def test_render_qdrant_snapshot_cronjob_manifest_contains_runtime_controls():
    config = build_qdrant_snapshot_schedule_config(
        platform="kubernetes_cronjob",
        task_name="qdrant-drill",
        cron_schedule="*/5 * * * *",
        namespace="agent",
        image="ghcr.io/example/app:sha",
        collection="source_chunks",
        restore_collection="restore_chunks",
        backup_dir="/app/data/qdrant_backups",
        keep_last=2,
        apply_retention=True,
    )

    rendered = render_qdrant_snapshot_cronjob_manifest(config)

    assert "apiVersion: batch/v1" in rendered
    assert "kind: CronJob" in rendered
    assert "  name: qdrant-drill" in rendered
    assert "  namespace: agent" in rendered
    assert '  schedule: "*/5 * * * *"' in rendered
    assert "  concurrencyPolicy: Forbid" in rendered
    assert "      backoffLimit: 0" in rendered
    assert "      ttlSecondsAfterFinished: 86400" in rendered
    assert "              image: ghcr.io/example/app:sha" in rendered
    assert "                - \"qdrant-snapshot-drill-run\"" in rendered
    assert "                - \"--collection\"" in rendered
    assert "                - \"source_chunks\"" in rendered
    assert "                - \"--restore-collection\"" in rendered
    assert "                - \"restore_chunks\"" in rendered
    assert "                - \"--apply-retention\"" in rendered
    assert "                - \"--confirm-restore-collection\"" in rendered
    assert "                    name: thesis-defense-agent-api-config" in rendered
    assert "                    name: thesis-defense-agent-api-secret" in rendered
    assert "                    optional: true" in rendered
    assert "            runAsNonRoot: true" in rendered
    assert "                allowPrivilegeEscalation: false" in rendered
    assert "              emptyDir: {}" in rendered


def test_render_qdrant_snapshot_cronjob_manifest_supports_custom_env_sources():
    config = build_qdrant_snapshot_schedule_config(
        platform="kubernetes_cronjob",
    )

    rendered = render_qdrant_snapshot_cronjob_manifest(
        config,
        config_map_name="agent-config",
        secret_name="agent-secret",
    )

    assert "                    name: agent-config" in rendered
    assert "                    name: agent-secret" in rendered


def test_render_qdrant_snapshot_cronjob_manifest_preserves_spaced_args():
    config = build_qdrant_snapshot_schedule_config(
        platform="kubernetes_cronjob",
        backup_dir="/app/data/qdrant backups",
    )

    rendered = render_qdrant_snapshot_cronjob_manifest(config)

    assert "                - \"/app/data/qdrant backups\"" in rendered
    assert "                - \"/app/data/qdrant\"" not in rendered


def test_render_qdrant_snapshot_cronjob_manifest_rejects_non_kubernetes_platform():
    config = build_qdrant_snapshot_schedule_config(platform="cron")

    with pytest.raises(ValueError, match="platform"):
        render_qdrant_snapshot_cronjob_manifest(config)


def test_render_qdrant_snapshot_cronjob_manifest_validates_env_sources():
    config = build_qdrant_snapshot_schedule_config(
        platform="kubernetes_cronjob",
    )

    with pytest.raises(ValueError, match="config_map_name"):
        render_qdrant_snapshot_cronjob_manifest(config, config_map_name=" ")

    with pytest.raises(ValueError, match="secret_name"):
        render_qdrant_snapshot_cronjob_manifest(config, secret_name="")


def test_qdrant_snapshot_cronjob_manifest_cli_prints_yaml(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-cronjob-manifest",
            "--task-name",
            "qdrant-drill",
            "--namespace",
            "agent",
            "--cron-schedule",
            "*/10 * * * *",
            "--collection",
            "source_chunks",
            "--restore-collection",
            "restore_chunks",
            "--skip-compare",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "kind: CronJob" in output
    assert "  name: qdrant-drill" in output
    assert "  namespace: agent" in output
    assert '  schedule: "*/10 * * * *"' in output
    assert "                - \"--skip-compare\"" in output


def test_qdrant_snapshot_cronjob_manifest_cli_writes_yaml(
    monkeypatch,
    capsys,
    tmp_path,
):
    output_path = tmp_path / "cronjob.yaml"
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-cronjob-manifest",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    saved = output_path.read_text(encoding="utf-8")

    assert "OUTPUT:" in output
    assert "kind: CronJob" in saved


def test_qdrant_snapshot_cronjob_manifest_cli_rejects_invalid_input(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-cronjob-manifest",
            "--cron-schedule",
            "bad schedule",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 2
    assert "QDRANT SNAPSHOT CRONJOB MANIFEST ERROR:" in output
