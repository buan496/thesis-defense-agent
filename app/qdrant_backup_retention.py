from dataclasses import dataclass
from pathlib import Path


DEFAULT_QDRANT_BACKUP_PATTERNS = ["*.snapshot"]


@dataclass(frozen=True)
class QdrantBackupFile:
    path: str
    name: str
    size_bytes: int
    modified_timestamp: float


@dataclass(frozen=True)
class QdrantBackupRetentionPlan:
    backup_dir: str
    keep_last: int
    patterns: list[str]
    retained: list[QdrantBackupFile]
    deletion_candidates: list[QdrantBackupFile]


@dataclass(frozen=True)
class QdrantBackupRetentionResult:
    plan: QdrantBackupRetentionPlan
    dry_run: bool
    deleted: list[QdrantBackupFile]
    skipped: list[QdrantBackupFile]


def build_qdrant_backup_retention_plan(
    backup_dir: str,
    keep_last: int = 5,
    patterns: list[str] | None = None,
) -> QdrantBackupRetentionPlan:
    if keep_last < 0:
        raise ValueError("keep_last must be greater than or equal to 0")

    normalized_patterns = (
        DEFAULT_QDRANT_BACKUP_PATTERNS
        if patterns is None
        else patterns
    )

    if not normalized_patterns:
        raise ValueError("patterns must not be empty")

    for pattern in normalized_patterns:
        if not pattern.strip():
            raise ValueError("patterns must not contain empty values")

    backup_path = Path(backup_dir)

    if not backup_path.exists():
        raise FileNotFoundError(f"backup_dir does not exist: {backup_dir}")

    if not backup_path.is_dir():
        raise NotADirectoryError(f"backup_dir is not a directory: {backup_dir}")

    backups = _list_backup_files(backup_path, normalized_patterns)
    backups = sorted(
        backups,
        key=lambda item: (item.modified_timestamp, item.name),
        reverse=True,
    )

    retained = backups[:keep_last]
    deletion_candidates = backups[keep_last:]

    return QdrantBackupRetentionPlan(
        backup_dir=str(backup_path),
        keep_last=keep_last,
        patterns=normalized_patterns,
        retained=retained,
        deletion_candidates=deletion_candidates,
    )


def execute_qdrant_backup_retention(
    plan: QdrantBackupRetentionPlan,
    dry_run: bool = True,
) -> QdrantBackupRetentionResult:
    deleted = []
    skipped = []
    backup_dir = Path(plan.backup_dir).resolve()

    for backup in plan.deletion_candidates:
        backup_path = Path(backup.path).resolve()
        _ensure_path_inside_directory(backup_path, backup_dir)

        if dry_run:
            skipped.append(backup)
            continue

        if backup_path.exists():
            backup_path.unlink()
            deleted.append(backup)
        else:
            skipped.append(backup)

    return QdrantBackupRetentionResult(
        plan=plan,
        dry_run=dry_run,
        deleted=deleted,
        skipped=skipped,
    )


def render_qdrant_backup_retention_report(
    result: QdrantBackupRetentionResult,
) -> str:
    plan = result.plan
    lines = [
        "# Qdrant Backup Retention Report",
        "",
        f"- Backup directory: `{plan.backup_dir}`",
        f"- Keep last: `{plan.keep_last}`",
        f"- Patterns: `{', '.join(plan.patterns)}`",
        f"- Dry run: `{result.dry_run}`",
        f"- Retained count: `{len(plan.retained)}`",
        f"- Deletion candidate count: `{len(plan.deletion_candidates)}`",
        f"- Deleted count: `{len(result.deleted)}`",
        f"- Skipped count: `{len(result.skipped)}`",
        "",
        "## Retained",
        "",
    ]

    lines.extend(_render_backup_items(plan.retained))
    lines.extend(["", "## Deletion Candidates", ""])
    lines.extend(_render_backup_items(plan.deletion_candidates))
    lines.extend(["", "## Deleted", ""])
    lines.extend(_render_backup_items(result.deleted))
    lines.extend(["", "## Skipped", ""])
    lines.extend(_render_backup_items(result.skipped))

    return "\n".join(lines).rstrip() + "\n"


def _list_backup_files(
    backup_dir: Path,
    patterns: list[str],
) -> list[QdrantBackupFile]:
    seen_paths = set()
    backups = []

    for pattern in patterns:
        for path in backup_dir.glob(pattern):
            if not path.is_file():
                continue

            resolved_path = path.resolve()

            if resolved_path in seen_paths:
                continue

            seen_paths.add(resolved_path)
            stat = path.stat()
            backups.append(
                QdrantBackupFile(
                    path=str(path),
                    name=path.name,
                    size_bytes=stat.st_size,
                    modified_timestamp=stat.st_mtime,
                )
            )

    return backups


def _ensure_path_inside_directory(path: Path, directory: Path) -> None:
    try:
        path.relative_to(directory)
    except ValueError as error:
        raise ValueError(
            f"Refusing to delete file outside backup_dir: {path}"
        ) from error


def _render_backup_items(items: list[QdrantBackupFile]) -> list[str]:
    if not items:
        return ["- none"]

    return [
        (
            f"- `{item.name}` "
            f"(size={item.size_bytes}, modified={item.modified_timestamp})"
        )
        for item in items
    ]
