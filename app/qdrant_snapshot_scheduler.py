from dataclasses import dataclass


@dataclass(frozen=True)
class QdrantSnapshotDrillStep:
    name: str
    phase: str
    action: str
    dry_run_safe: bool
    description: str


@dataclass(frozen=True)
class QdrantSnapshotDrillPlan:
    url: str
    collection: str
    restore_collection: str
    backup_dir: str
    keep_last: int
    apply_retention: bool
    run_restore_drill: bool
    steps: list[QdrantSnapshotDrillStep]


def build_qdrant_snapshot_drill_plan(
    url: str = "http://127.0.0.1:6333",
    collection: str = "thesis_chunks",
    restore_collection: str = "thesis_chunks_restore",
    backup_dir: str = "data/qdrant_backups",
    keep_last: int = 5,
    apply_retention: bool = False,
    run_restore_drill: bool = True,
) -> QdrantSnapshotDrillPlan:
    normalized_url = url.strip().rstrip("/")
    normalized_collection = collection.strip()
    normalized_restore_collection = restore_collection.strip()
    normalized_backup_dir = backup_dir.strip()

    if not normalized_url:
        raise ValueError("url must not be empty")

    if not normalized_collection:
        raise ValueError("collection must not be empty")

    if not normalized_restore_collection:
        raise ValueError("restore_collection must not be empty")

    if normalized_restore_collection == normalized_collection:
        raise ValueError("restore_collection must be different from collection")

    if not normalized_backup_dir:
        raise ValueError("backup_dir must not be empty")

    if keep_last < 0:
        raise ValueError("keep_last must be greater than or equal to 0")

    steps = [
        QdrantSnapshotDrillStep(
            name="ensure_backup_dir",
            phase="local",
            action="create local backup directory if missing",
            dry_run_safe=True,
            description="Prepare the gitignored directory used for downloaded Qdrant snapshots.",
        ),
        QdrantSnapshotDrillStep(
            name="create_snapshot",
            phase="qdrant",
            action=f"create snapshot for collection {normalized_collection}",
            dry_run_safe=False,
            description="Call Qdrant's create snapshot API for the active source collection.",
        ),
        QdrantSnapshotDrillStep(
            name="download_snapshot",
            phase="qdrant",
            action=f"download created snapshot into {normalized_backup_dir}",
            dry_run_safe=False,
            description="Persist the generated snapshot to the local backup directory.",
        ),
        QdrantSnapshotDrillStep(
            name="apply_retention",
            phase="local",
            action=(
                f"apply retention keep_last={keep_last}"
                if apply_retention
                else f"preview retention keep_last={keep_last}"
            ),
            dry_run_safe=not apply_retention,
            description="Run the local downloaded snapshot retention policy.",
        ),
    ]

    if run_restore_drill:
        steps.extend(
            [
                QdrantSnapshotDrillStep(
                    name="restore_to_disposable_collection",
                    phase="qdrant",
                    action=(
                        "restore downloaded snapshot into "
                        f"{normalized_restore_collection}"
                    ),
                    dry_run_safe=False,
                    description="Restore only into a disposable collection, never directly over the active collection.",
                ),
                QdrantSnapshotDrillStep(
                    name="compare_restored_collection",
                    phase="application",
                    action=(
                        "compare restored collection "
                        f"{normalized_restore_collection} against JSON baseline"
                    ),
                    dry_run_safe=False,
                    description="Run retrieval benchmark comparison before trusting the restored collection.",
                ),
            ]
        )

    return QdrantSnapshotDrillPlan(
        url=normalized_url,
        collection=normalized_collection,
        restore_collection=normalized_restore_collection,
        backup_dir=normalized_backup_dir,
        keep_last=keep_last,
        apply_retention=apply_retention,
        run_restore_drill=run_restore_drill,
        steps=steps,
    )


def render_qdrant_snapshot_drill_plan(
    plan: QdrantSnapshotDrillPlan,
) -> str:
    lines = [
        "# Qdrant Snapshot Drill Plan",
        "",
        f"- Qdrant URL: `{plan.url}`",
        f"- Source collection: `{plan.collection}`",
        f"- Restore collection: `{plan.restore_collection}`",
        f"- Backup directory: `{plan.backup_dir}`",
        f"- Keep last: `{plan.keep_last}`",
        f"- Apply retention: `{plan.apply_retention}`",
        f"- Run restore drill: `{plan.run_restore_drill}`",
        "",
        "This plan describes the scheduled drill sequence. It does not call Qdrant by itself.",
        "",
    ]

    for index, step in enumerate(plan.steps, start=1):
        lines.extend(
            [
                f"## {index}. {step.name}",
                "",
                f"- Phase: `{step.phase}`",
                f"- Dry-run safe: `{step.dry_run_safe}`",
                f"- Action: {step.action}",
                f"- Purpose: {step.description}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"
