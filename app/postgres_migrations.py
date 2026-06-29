from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path


DEFAULT_POSTGRES_MIGRATIONS_DIRECTORY = (
    Path(__file__).resolve().parents[1] / "db" / "migrations" / "postgres"
)


@dataclass(frozen=True)
class PostgresMigration:
    version: str
    name: str
    path: str
    checksum: str
    sql: str


def list_postgres_migration_paths(
    directory: str | Path = DEFAULT_POSTGRES_MIGRATIONS_DIRECTORY,
) -> list[Path]:
    migration_directory = Path(directory)

    if not migration_directory.exists():
        raise FileNotFoundError(f"PostgreSQL migration directory not found: {directory}")

    return sorted(migration_directory.glob("*.sql"))


def load_postgres_migrations(
    directory: str | Path = DEFAULT_POSTGRES_MIGRATIONS_DIRECTORY,
) -> list[PostgresMigration]:
    migrations = []

    for path in list_postgres_migration_paths(directory):
        version, name = _parse_migration_file_name(path.name)
        sql = path.read_text(encoding="utf-8")

        migrations.append(
            PostgresMigration(
                version=version,
                name=name,
                path=str(path),
                checksum=sha256(sql.encode("utf-8")).hexdigest(),
                sql=sql,
            )
        )

    return migrations


def build_postgres_migration_plan(
    directory: str | Path = DEFAULT_POSTGRES_MIGRATIONS_DIRECTORY,
) -> list[dict]:
    return [
        {
            "version": migration.version,
            "name": migration.name,
            "path": migration.path,
            "checksum": migration.checksum,
        }
        for migration in load_postgres_migrations(directory)
    ]


def _parse_migration_file_name(file_name: str) -> tuple[str, str]:
    if not file_name.endswith(".sql"):
        raise ValueError(f"PostgreSQL migration file must end with .sql: {file_name}")

    stem = file_name.removesuffix(".sql")
    parts = stem.split("_", 1)

    if len(parts) != 2 or not parts[0].isdigit() or not parts[1]:
        raise ValueError(
            "PostgreSQL migration file name must use '<number>_<name>.sql': "
            f"{file_name}"
        )

    return parts[0], parts[1]
