from pathlib import Path

import pytest

from app.postgres_migration_runner import (
    PostgresMigrationChecksumMismatch,
    run_postgres_migrations,
)
from app.postgres_migrations import load_postgres_migrations


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIRECTORY = ROOT / "db" / "migrations" / "postgres"


class FakeCursor:
    def __init__(self, applied_migrations=None):
        self.applied_migrations = applied_migrations or {}
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        return list(self.applied_migrations.items())

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_run_postgres_migrations_applies_pending_migration():
    cursor = FakeCursor()
    connection = FakeConnection(cursor)

    report = run_postgres_migrations(
        "postgresql://example",
        migrations_directory=MIGRATIONS_DIRECTORY,
        connect_fn=lambda database_url: connection,
    )

    assert report.applied_count == 1
    assert report.skipped_count == 0
    assert report.applied[0]["version"] == "001"
    assert connection.committed is True
    assert connection.rolled_back is False
    assert connection.closed is True
    assert cursor.closed is True
    assert any(
        "CREATE TABLE IF NOT EXISTS defense_tasks" in query
        for query, _ in cursor.executed
    )
    assert any(
        query.startswith("INSERT INTO schema_migrations")
        and params[:2] == ("001", "initial_schema")
        for query, params in cursor.executed
    )


def test_run_postgres_migrations_skips_applied_matching_checksum():
    migration = load_postgres_migrations(MIGRATIONS_DIRECTORY)[0]
    cursor = FakeCursor(
        applied_migrations={
            migration.version: migration.checksum,
        }
    )
    connection = FakeConnection(cursor)

    report = run_postgres_migrations(
        "postgresql://example",
        migrations_directory=MIGRATIONS_DIRECTORY,
        connect_fn=lambda database_url: connection,
    )

    assert report.applied_count == 0
    assert report.skipped_count == 1
    assert report.skipped[0]["version"] == "001"
    assert connection.committed is True
    assert not any(
        query.startswith("INSERT INTO schema_migrations")
        for query, _ in cursor.executed
    )


def test_run_postgres_migrations_rejects_checksum_mismatch():
    cursor = FakeCursor(
        applied_migrations={
            "001": "different-checksum",
        }
    )
    connection = FakeConnection(cursor)

    with pytest.raises(PostgresMigrationChecksumMismatch):
        run_postgres_migrations(
            "postgresql://example",
            migrations_directory=MIGRATIONS_DIRECTORY,
            connect_fn=lambda database_url: connection,
        )

    assert connection.committed is False
    assert connection.rolled_back is True
    assert connection.closed is True


def test_run_postgres_migrations_requires_database_url():
    with pytest.raises(ValueError):
        run_postgres_migrations(
            "",
            migrations_directory=MIGRATIONS_DIRECTORY,
            connect_fn=lambda database_url: FakeConnection(FakeCursor()),
        )
