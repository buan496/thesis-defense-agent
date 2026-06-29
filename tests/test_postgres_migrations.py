from pathlib import Path

import pytest

from app.postgres_migrations import (
    build_postgres_migration_plan,
    list_postgres_migration_paths,
    load_postgres_migrations,
)


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIRECTORY = ROOT / "db" / "migrations" / "postgres"
INITIAL_SCHEMA = MIGRATIONS_DIRECTORY / "001_initial_schema.sql"


def test_postgres_initial_schema_file_exists():
    assert INITIAL_SCHEMA.exists()


def test_postgres_initial_schema_defines_core_tables():
    sql = INITIAL_SCHEMA.read_text(encoding="utf-8").lower()

    assert "create table if not exists schema_migrations" in sql
    assert "create table if not exists defense_tasks" in sql
    assert "create table if not exists agent_sessions" in sql
    assert "create table if not exists trace_records" in sql
    assert "create table if not exists feedback_records" in sql
    assert "create table if not exists benchmark_candidates" in sql


def test_postgres_initial_schema_uses_jsonb_payloads():
    sql = INITIAL_SCHEMA.read_text(encoding="utf-8").lower()

    assert "payload jsonb not null" in sql


def test_postgres_initial_schema_defines_useful_indexes():
    sql = INITIAL_SCHEMA.read_text(encoding="utf-8").lower()

    assert "idx_defense_tasks_status" in sql
    assert "idx_trace_records_source" in sql
    assert "idx_feedback_records_source" in sql
    assert "idx_benchmark_candidates_status" in sql


def test_list_postgres_migration_paths_returns_sorted_sql_files():
    paths = list_postgres_migration_paths(MIGRATIONS_DIRECTORY)

    assert paths == [INITIAL_SCHEMA]


def test_load_postgres_migrations_returns_metadata_and_sql():
    migrations = load_postgres_migrations(MIGRATIONS_DIRECTORY)

    assert len(migrations) == 1

    migration = migrations[0]
    assert migration.version == "001"
    assert migration.name == "initial_schema"
    assert migration.path.endswith("001_initial_schema.sql")
    assert len(migration.checksum) == 64
    assert "CREATE TABLE IF NOT EXISTS defense_tasks" in migration.sql


def test_build_postgres_migration_plan_excludes_sql_body():
    plan = build_postgres_migration_plan(MIGRATIONS_DIRECTORY)

    assert plan == [
        {
            "version": "001",
            "name": "initial_schema",
            "path": str(INITIAL_SCHEMA),
            "checksum": load_postgres_migrations(MIGRATIONS_DIRECTORY)[0].checksum,
        }
    ]
    assert "sql" not in plan[0]


def test_list_postgres_migration_paths_rejects_missing_directory(tmp_path):
    missing_directory = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        list_postgres_migration_paths(missing_directory)


def test_load_postgres_migrations_rejects_invalid_file_name(tmp_path):
    (tmp_path / "invalid.sql").write_text("SELECT 1;", encoding="utf-8")

    with pytest.raises(ValueError):
        load_postgres_migrations(tmp_path)
