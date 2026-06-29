from app import cli
from app.postgres_json_importer import (
    ImportJsonStorageReport,
    ImportSectionReport,
)


def test_import_json_to_postgres_command_runs_import(
    monkeypatch,
    capsys,
):
    captured = {}

    def fake_create_repositories(**kwargs):
        captured["create_repositories"] = kwargs
        return "repositories"

    def fake_import_json_storage_to_repositories(**kwargs):
        captured["import"] = kwargs
        return ImportJsonStorageReport(
            tasks=ImportSectionReport(source_count=2, imported_count=2),
            sessions=ImportSectionReport(source_count=1, imported_count=1),
            traces=ImportSectionReport(source_count=3, imported_count=3),
            dry_run=False,
        )

    monkeypatch.setattr(cli, "create_repositories", fake_create_repositories)
    monkeypatch.setattr(
        cli,
        "import_json_storage_to_repositories",
        fake_import_json_storage_to_repositories,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "import-json-to-postgres",
            "--database-url",
            "postgresql://user:secret@localhost/db",
            "--task-directory",
            "data/tasks",
            "--session-directory",
            "data/sessions",
            "--trace-file",
            "data/traces/agent_trace.jsonl",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["create_repositories"] == {
        "storage_backend": "postgres",
        "database_url": "postgresql://user:secret@localhost/db",
    }
    assert captured["import"] == {
        "repositories": "repositories",
        "task_directory": "data/tasks",
        "session_directory": "data/sessions",
        "trace_file_path": "data/traces/agent_trace.jsonl",
        "include_tasks": True,
        "include_sessions": True,
        "include_traces": True,
        "dry_run": False,
    }
    assert "POSTGRES JSON IMPORT" in output
    assert "DATABASE URL: configured" in output
    assert "TASK SOURCE COUNT: 2" in output
    assert "SESSION IMPORTED COUNT: 1" in output
    assert "TRACE IMPORTED COUNT: 3" in output
    assert "TOTAL IMPORTED COUNT: 6" in output
    assert "secret" not in output


def test_import_json_to_postgres_command_supports_dry_run_and_skip_flags(
    monkeypatch,
    capsys,
):
    captured = {}

    def fake_create_repositories(**kwargs):
        return "repositories"

    def fake_import_json_storage_to_repositories(**kwargs):
        captured.update(kwargs)
        return ImportJsonStorageReport(
            tasks=ImportSectionReport(source_count=0, imported_count=0),
            sessions=ImportSectionReport(source_count=0, imported_count=0),
            traces=ImportSectionReport(source_count=0, imported_count=0),
            dry_run=True,
        )

    monkeypatch.setattr(cli, "create_repositories", fake_create_repositories)
    monkeypatch.setattr(
        cli,
        "import_json_storage_to_repositories",
        fake_import_json_storage_to_repositories,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "import-json-to-postgres",
            "--database-url",
            "postgresql://example",
            "--skip-tasks",
            "--skip-sessions",
            "--skip-traces",
            "--dry-run",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["include_tasks"] is False
    assert captured["include_sessions"] is False
    assert captured["include_traces"] is False
    assert captured["dry_run"] is True
    assert "DRY RUN: True" in output
    assert "TOTAL IMPORTED COUNT: 0" in output


def test_import_json_to_postgres_command_requires_database_url(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(cli, "DATABASE_URL", "")
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "import-json-to-postgres",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("Expected import-json-to-postgres to fail")

    output = capsys.readouterr().out

    assert "POSTGRES IMPORT ERROR:" in output
    assert "DATABASE_URL is required" in output
