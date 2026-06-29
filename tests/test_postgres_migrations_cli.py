from types import SimpleNamespace

from app import cli


def test_postgres_migrations_command_prints_plan(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "postgres-migrations",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "POSTGRES MIGRATION PLAN" in output
    assert "COUNT: 1" in output
    assert "VERSION: 001" in output
    assert "NAME: initial_schema" in output
    assert "CHECKSUM:" in output


def test_postgres_migrations_command_rejects_missing_directory(
    monkeypatch,
    capsys,
    tmp_path,
):
    missing_directory = tmp_path / "missing"
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "postgres-migrations",
            "--directory",
            str(missing_directory),
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("Expected postgres-migrations to fail")

    output = capsys.readouterr().out

    assert "POSTGRES MIGRATION ERROR:" in output


def test_run_postgres_migrations_command_applies_migrations(
    monkeypatch,
    capsys,
):
    captured = {}

    def fake_run_postgres_migrations(database_url, migrations_directory=None):
        captured["database_url"] = database_url
        captured["migrations_directory"] = migrations_directory
        return SimpleNamespace(
            total_count=1,
            applied_count=1,
            skipped_count=0,
            applied=[
                {
                    "version": "001",
                    "name": "initial_schema",
                    "path": "db/migrations/postgres/001_initial_schema.sql",
                    "checksum": "abc123",
                }
            ],
            skipped=[],
        )

    monkeypatch.setattr(
        cli,
        "run_postgres_migrations",
        fake_run_postgres_migrations,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "run-postgres-migrations",
            "--database-url",
            "postgresql://user:secret@localhost/db",
            "--directory",
            "db/migrations/postgres",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured == {
        "database_url": "postgresql://user:secret@localhost/db",
        "migrations_directory": "db/migrations/postgres",
    }
    assert "POSTGRES MIGRATION RUN" in output
    assert "DATABASE URL: configured" in output
    assert "TOTAL: 1" in output
    assert "APPLIED: 1" in output
    assert "SKIPPED: 0" in output
    assert "secret" not in output


def test_run_postgres_migrations_command_requires_database_url(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(cli, "DATABASE_URL", "")
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "run-postgres-migrations",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("Expected run-postgres-migrations to fail")

    output = capsys.readouterr().out

    assert "DATABASE_URL is required" in output
