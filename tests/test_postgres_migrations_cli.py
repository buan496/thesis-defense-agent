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
