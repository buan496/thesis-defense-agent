from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol

from app.postgres_migrations import (
    DEFAULT_POSTGRES_MIGRATIONS_DIRECTORY,
    PostgresMigration,
    load_postgres_migrations,
)


SCHEMA_MIGRATIONS_BOOTSTRAP_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


class CursorProtocol(Protocol):
    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> Any:
        ...

    def fetchall(self) -> list[tuple[Any, ...]]:
        ...

    def close(self) -> Any:
        ...


class ConnectionProtocol(Protocol):
    def cursor(self) -> CursorProtocol:
        ...

    def commit(self) -> Any:
        ...

    def rollback(self) -> Any:
        ...

    def close(self) -> Any:
        ...


ConnectFn = Callable[[str], ConnectionProtocol]


class PostgresMigrationError(RuntimeError):
    pass


class PostgresMigrationChecksumMismatch(PostgresMigrationError):
    pass


@dataclass(frozen=True)
class PostgresMigrationRunReport:
    applied: list[dict] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)

    @property
    def applied_count(self) -> int:
        return len(self.applied)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    @property
    def total_count(self) -> int:
        return self.applied_count + self.skipped_count

    def to_dict(self) -> dict:
        return {
            "applied": self.applied,
            "skipped": self.skipped,
            "applied_count": self.applied_count,
            "skipped_count": self.skipped_count,
            "total_count": self.total_count,
        }


def run_postgres_migrations(
    database_url: str,
    migrations_directory: str | Path = DEFAULT_POSTGRES_MIGRATIONS_DIRECTORY,
    connect_fn: ConnectFn | None = None,
) -> PostgresMigrationRunReport:
    if not database_url.strip():
        raise ValueError("database_url is required")

    migrations = load_postgres_migrations(migrations_directory)
    connection = _connect(database_url, connect_fn)
    cursor = connection.cursor()

    try:
        cursor.execute(SCHEMA_MIGRATIONS_BOOTSTRAP_SQL)
        applied_migrations = _load_applied_migrations(cursor)
        report = _apply_pending_migrations(
            cursor=cursor,
            migrations=migrations,
            applied_migrations=applied_migrations,
        )
        connection.commit()
        return report
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def _connect(
    database_url: str,
    connect_fn: ConnectFn | None,
) -> ConnectionProtocol:
    if connect_fn is not None:
        return connect_fn(database_url)

    import psycopg

    return psycopg.connect(database_url)


def _load_applied_migrations(cursor: CursorProtocol) -> dict[str, str]:
    cursor.execute("SELECT version, checksum FROM schema_migrations")

    return {
        str(version): str(checksum)
        for version, checksum in cursor.fetchall()
    }


def _apply_pending_migrations(
    cursor: CursorProtocol,
    migrations: list[PostgresMigration],
    applied_migrations: dict[str, str],
) -> PostgresMigrationRunReport:
    applied = []
    skipped = []

    for migration in migrations:
        existing_checksum = applied_migrations.get(migration.version)

        if existing_checksum is not None:
            if existing_checksum != migration.checksum:
                raise PostgresMigrationChecksumMismatch(
                    "Applied PostgreSQL migration checksum mismatch: "
                    f"{migration.version} {migration.name}"
                )

            skipped.append(_migration_summary(migration))
            continue

        cursor.execute(migration.sql)
        cursor.execute(
            (
                "INSERT INTO schema_migrations (version, name, checksum) "
                "VALUES (%s, %s, %s)"
            ),
            (migration.version, migration.name, migration.checksum),
        )
        applied.append(_migration_summary(migration))

    return PostgresMigrationRunReport(
        applied=applied,
        skipped=skipped,
    )


def _migration_summary(migration: PostgresMigration) -> dict:
    return {
        "version": migration.version,
        "name": migration.name,
        "path": migration.path,
        "checksum": migration.checksum,
    }
