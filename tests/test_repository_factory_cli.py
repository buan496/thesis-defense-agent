from app import cli


def test_show_repositories_command_prints_json_repositories(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "show-repositories",
            "--storage-backend",
            "json",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "REPOSITORY CONFIG" in output
    assert "STORAGE BACKEND: json" in output
    assert "TASK REPOSITORY: JsonTaskRepository" in output
    assert "SESSION REPOSITORY: JsonSessionRepository" in output
    assert "TRACE REPOSITORY: JsonlTraceRepository" in output


def test_show_repositories_command_prints_postgres_repositories_without_url(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "show-repositories",
            "--storage-backend",
            "postgres",
            "--database-url",
            "postgresql://user:secret@localhost/db",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "STORAGE BACKEND: postgres" in output
    assert "TASK REPOSITORY: PostgresTaskRepository" in output
    assert "SESSION REPOSITORY: PostgresSessionRepository" in output
    assert "TRACE REPOSITORY: PostgresTraceRepository" in output
    assert "secret" not in output


def test_show_repositories_command_rejects_postgres_without_database_url(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(cli, "DATABASE_URL", "")
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "show-repositories",
            "--storage-backend",
            "postgres",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("Expected show-repositories to fail")

    output = capsys.readouterr().out

    assert "REPOSITORY CONFIG ERROR:" in output
    assert "DATABASE_URL is required" in output
