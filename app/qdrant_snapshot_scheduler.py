from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from app.qdrant_backup_retention import (
    QdrantBackupRetentionPlan,
    QdrantBackupRetentionResult,
    build_qdrant_backup_retention_plan,
    execute_qdrant_backup_retention,
)
from app.qdrant_snapshot_client import QdrantSnapshotInfo


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


@dataclass(frozen=True)
class QdrantSnapshotDrillStepResult:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class QdrantSnapshotDrillReport:
    plan: QdrantSnapshotDrillPlan
    snapshot_name: str | None
    snapshot_path: str | None
    retention_result: QdrantBackupRetentionResult | None
    restore_result: dict | None
    compare_report: dict | None
    steps: list[QdrantSnapshotDrillStepResult]


class QdrantSnapshotDrillClient(Protocol):
    def create_snapshot(self, collection: str) -> QdrantSnapshotInfo:
        ...

    def download_snapshot(
        self,
        collection: str,
        snapshot_name: str,
        output_path: str | Path,
    ) -> str:
        ...

    def restore_snapshot(
        self,
        restore_collection: str,
        snapshot_path: str | Path,
    ) -> dict:
        ...


RetentionPlanBuilder = Callable[
    [str, int],
    QdrantBackupRetentionPlan,
]
RetentionExecutor = Callable[
    [QdrantBackupRetentionPlan, bool],
    QdrantBackupRetentionResult,
]
CompareRestoredCollection = Callable[[str], dict]


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


def execute_qdrant_snapshot_drill(
    plan: QdrantSnapshotDrillPlan,
    snapshot_client: QdrantSnapshotDrillClient,
    retention_plan_builder: RetentionPlanBuilder = build_qdrant_backup_retention_plan,
    retention_executor: RetentionExecutor = execute_qdrant_backup_retention,
    compare_restored_collection: CompareRestoredCollection | None = None,
) -> QdrantSnapshotDrillReport:
    step_results = []
    backup_path = Path(plan.backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)
    step_results.append(
        QdrantSnapshotDrillStepResult(
            name="ensure_backup_dir",
            status="completed",
            detail=str(backup_path),
        )
    )

    snapshot = snapshot_client.create_snapshot(plan.collection)
    step_results.append(
        QdrantSnapshotDrillStepResult(
            name="create_snapshot",
            status="completed",
            detail=snapshot.name,
        )
    )

    snapshot_path = backup_path / snapshot.name
    saved_path = snapshot_client.download_snapshot(
        collection=plan.collection,
        snapshot_name=snapshot.name,
        output_path=snapshot_path,
    )
    step_results.append(
        QdrantSnapshotDrillStepResult(
            name="download_snapshot",
            status="completed",
            detail=saved_path,
        )
    )

    retention_plan = retention_plan_builder(
        plan.backup_dir,
        plan.keep_last,
    )
    retention_result = retention_executor(
        retention_plan,
        not plan.apply_retention,
    )
    step_results.append(
        QdrantSnapshotDrillStepResult(
            name="apply_retention",
            status="completed",
            detail=(
                f"dry_run={retention_result.dry_run}, "
                f"deleted={len(retention_result.deleted)}, "
                f"skipped={len(retention_result.skipped)}"
            ),
        )
    )

    restore_result = None
    compare_report = None

    if plan.run_restore_drill:
        restore_result = snapshot_client.restore_snapshot(
            restore_collection=plan.restore_collection,
            snapshot_path=saved_path,
        )
        step_results.append(
            QdrantSnapshotDrillStepResult(
                name="restore_to_disposable_collection",
                status="completed",
                detail=str(restore_result),
            )
        )

        if compare_restored_collection is None:
            step_results.append(
                QdrantSnapshotDrillStepResult(
                    name="compare_restored_collection",
                    status="skipped",
                    detail="compare_restored_collection was not provided",
                )
            )
        else:
            compare_report = compare_restored_collection(plan.restore_collection)
            step_results.append(
                QdrantSnapshotDrillStepResult(
                    name="compare_restored_collection",
                    status="completed",
                    detail=(
                        "best_repository="
                        f"{compare_report.get('best_repository')}"
                    ),
                )
            )

    return QdrantSnapshotDrillReport(
        plan=plan,
        snapshot_name=snapshot.name,
        snapshot_path=saved_path,
        retention_result=retention_result,
        restore_result=restore_result,
        compare_report=compare_report,
        steps=step_results,
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


def render_qdrant_snapshot_drill_report(
    report: QdrantSnapshotDrillReport,
) -> str:
    plan = report.plan
    lines = [
        "# Qdrant Snapshot Drill Report",
        "",
        f"- Qdrant URL: `{plan.url}`",
        f"- Source collection: `{plan.collection}`",
        f"- Restore collection: `{plan.restore_collection}`",
        f"- Backup directory: `{plan.backup_dir}`",
        f"- Keep last: `{plan.keep_last}`",
        f"- Apply retention: `{plan.apply_retention}`",
        f"- Run restore drill: `{plan.run_restore_drill}`",
        f"- Snapshot name: `{report.snapshot_name or 'None'}`",
        f"- Snapshot path: `{report.snapshot_path or 'None'}`",
        "",
        "## Steps",
        "",
    ]

    for step in report.steps:
        lines.append(
            f"- `{step.name}`: `{step.status}` - {step.detail}"
        )

    lines.extend(["", "## Retention", ""])

    if report.retention_result is None:
        lines.append("- none")
    else:
        result = report.retention_result
        lines.extend(
            [
                f"- Dry run: `{result.dry_run}`",
                f"- Retained count: `{len(result.plan.retained)}`",
                f"- Deletion candidate count: `{len(result.plan.deletion_candidates)}`",
                f"- Deleted count: `{len(result.deleted)}`",
                f"- Skipped count: `{len(result.skipped)}`",
            ]
        )

    lines.extend(["", "## Restore", ""])
    lines.append(f"- Result: `{report.restore_result or 'None'}`")

    lines.extend(["", "## Compare Restored Collection", ""])

    if report.compare_report is None:
        lines.append("- none")
    else:
        lines.extend(
            [
                f"- Best repository: `{report.compare_report.get('best_repository')}`",
                (
                    "- Score delta Qdrant-JSON: "
                    f"`{report.compare_report.get('score_delta_qdrant_minus_json')}`"
                ),
                (
                    "- Duration delta ms Qdrant-JSON: "
                    f"`{report.compare_report.get('duration_delta_ms_qdrant_minus_json')}`"
                ),
            ]
        )

    return "\n".join(lines).rstrip() + "\n"
