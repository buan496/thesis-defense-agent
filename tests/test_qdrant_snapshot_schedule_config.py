import pytest

from app import cli
from app.qdrant_snapshot_scheduler import (
    build_qdrant_snapshot_schedule_config,
    render_qdrant_snapshot_schedule_config,
)


def test_build_qdrant_snapshot_schedule_config_defaults_to_all_platforms():
    config = build_qdrant_snapshot_schedule_config()
    rendered = render_qdrant_snapshot_schedule_config(config)

    assert config.platform == "all"
    assert config.task_name == "thesis-defense-qdrant-snapshot-drill"
    assert config.cron_schedule == "0 3 * * *"
    assert config.windows_start_time == "03:00"
    assert "qdrant-snapshot-drill-run" in config.runner_command
    assert "--confirm-restore-collection thesis_chunks_restore" in config.runner_command
    assert "## Cron" in rendered
    assert "## Windows Task Scheduler" in rendered
    assert "## Kubernetes CronJob" in rendered


def test_build_qdrant_snapshot_schedule_config_supports_platform_filter():
    config = build_qdrant_snapshot_schedule_config(platform="cron")
    rendered = render_qdrant_snapshot_schedule_config(config)

    assert "## Cron" in rendered
    assert "## Windows Task Scheduler" not in rendered
    assert "## Kubernetes CronJob" not in rendered


def test_build_qdrant_snapshot_schedule_config_accepts_custom_values():
    config = build_qdrant_snapshot_schedule_config(
        platform="kubernetes_cronjob",
        task_name="qdrant-drill",
        cron_schedule="30 2 * * 1",
        windows_start_time="02:30",
        working_directory="E:/project",
        log_path="data/reports/drill.log",
        namespace="agent",
        image="ghcr.io/example/app:sha",
        collection="source_chunks",
        restore_collection="restore_chunks",
        backup_dir="tmp/backups",
        keep_last=3,
        apply_retention=True,
        run_restore_drill=False,
        run_compare=False,
    )
    rendered = render_qdrant_snapshot_schedule_config(config)

    assert config.platform == "kubernetes_cronjob"
    assert "--collection source_chunks" in config.runner_command
    assert "--restore-collection restore_chunks" in config.runner_command
    assert "--apply-retention" in config.runner_command
    assert "--skip-restore-drill" in config.runner_command
    assert "--skip-compare" in config.runner_command
    assert "namespace: agent" in rendered
    assert "image: ghcr.io/example/app:sha" in rendered
    assert "schedule: \"30 2 * * 1\"" in rendered


def test_build_qdrant_snapshot_schedule_config_validates_inputs():
    with pytest.raises(ValueError, match="platform"):
        build_qdrant_snapshot_schedule_config(platform="bad")

    with pytest.raises(ValueError, match="task_name"):
        build_qdrant_snapshot_schedule_config(task_name=" ")

    with pytest.raises(ValueError, match="cron_schedule"):
        build_qdrant_snapshot_schedule_config(cron_schedule="0 3 * *")

    with pytest.raises(ValueError, match="windows_start_time"):
        build_qdrant_snapshot_schedule_config(windows_start_time="25:00")

    with pytest.raises(ValueError, match="working_directory"):
        build_qdrant_snapshot_schedule_config(working_directory=" ")

    with pytest.raises(ValueError, match="log_path"):
        build_qdrant_snapshot_schedule_config(log_path="")

    with pytest.raises(ValueError, match="namespace"):
        build_qdrant_snapshot_schedule_config(namespace="")

    with pytest.raises(ValueError, match="image"):
        build_qdrant_snapshot_schedule_config(image=" ")

    with pytest.raises(ValueError, match="different"):
        build_qdrant_snapshot_schedule_config(
            collection="same",
            restore_collection="same",
        )


def test_qdrant_snapshot_schedule_config_cli_prints_config(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-schedule-config",
            "--platform",
            "cron",
            "--collection",
            "source_chunks",
            "--restore-collection",
            "restore_chunks",
            "--skip-compare",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "# Qdrant Snapshot Schedule Config" in output
    assert "- Platform: `cron`" in output
    assert "## Cron" in output
    assert "--collection source_chunks" in output
    assert "--skip-compare" in output


def test_qdrant_snapshot_schedule_config_cli_writes_markdown(
    monkeypatch,
    capsys,
    tmp_path,
):
    output_path = tmp_path / "schedule.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-schedule-config",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    saved = output_path.read_text(encoding="utf-8")

    assert "OUTPUT:" in output
    assert "# Qdrant Snapshot Schedule Config" in saved


def test_qdrant_snapshot_schedule_config_cli_rejects_invalid_input(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "qdrant-snapshot-schedule-config",
            "--platform",
            "bad",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 2
    assert "QDRANT SNAPSHOT SCHEDULE CONFIG ERROR:" in output
