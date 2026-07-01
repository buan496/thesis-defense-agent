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


QDRANT_SNAPSHOT_SCHEDULE_PLATFORMS = [
    "all",
    "cron",
    "windows_task_scheduler",
    "kubernetes_cronjob",
]


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
class QdrantSnapshotScheduleConfig:
    platform: str
    task_name: str
    cron_schedule: str
    windows_start_time: str
    working_directory: str
    log_path: str
    namespace: str
    image: str
    runner_command: str


@dataclass(frozen=True)
class QdrantSnapshotScheduleInstallCommand:
    platform: str
    command: str
    description: str
    applies_system_change: bool


@dataclass(frozen=True)
class QdrantSnapshotScheduleInstallPlan:
    config: QdrantSnapshotScheduleConfig
    apply: bool
    commands: list[QdrantSnapshotScheduleInstallCommand]


@dataclass(frozen=True)
class QdrantSnapshotScheduleVerificationCommand:
    platform: str
    purpose: str
    command: str
    destructive: bool


@dataclass(frozen=True)
class QdrantSnapshotScheduleVerificationPlan:
    config: QdrantSnapshotScheduleConfig
    commands: list[QdrantSnapshotScheduleVerificationCommand]


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


def build_qdrant_snapshot_schedule_config(
    platform: str = "all",
    task_name: str = "thesis-defense-qdrant-snapshot-drill",
    cron_schedule: str = "0 3 * * *",
    windows_start_time: str = "03:00",
    working_directory: str = ".",
    log_path: str = "data/reports/qdrant_snapshot_drill_scheduled.log",
    namespace: str = "default",
    image: str = "ghcr.io/buan496/thesis-defense-agent:latest",
    collection: str = "thesis_chunks",
    restore_collection: str = "thesis_chunks_restore",
    backup_dir: str = "data/qdrant_backups",
    keep_last: int = 5,
    apply_retention: bool = False,
    run_restore_drill: bool = True,
    run_compare: bool = True,
) -> QdrantSnapshotScheduleConfig:
    normalized_platform = platform.strip()
    normalized_task_name = task_name.strip()
    normalized_cron_schedule = " ".join(cron_schedule.strip().split())
    normalized_windows_start_time = windows_start_time.strip()
    normalized_working_directory = working_directory.strip()
    normalized_log_path = log_path.strip()
    normalized_namespace = namespace.strip()
    normalized_image = image.strip()

    if normalized_platform not in QDRANT_SNAPSHOT_SCHEDULE_PLATFORMS:
        raise ValueError(
            "platform must be one of: "
            + ", ".join(QDRANT_SNAPSHOT_SCHEDULE_PLATFORMS)
        )

    if not normalized_task_name:
        raise ValueError("task_name must not be empty")

    _validate_cron_schedule(normalized_cron_schedule)
    _validate_windows_start_time(normalized_windows_start_time)

    if not normalized_working_directory:
        raise ValueError("working_directory must not be empty")

    if not normalized_log_path:
        raise ValueError("log_path must not be empty")

    if not normalized_namespace:
        raise ValueError("namespace must not be empty")

    if not normalized_image:
        raise ValueError("image must not be empty")

    drill_plan = build_qdrant_snapshot_drill_plan(
        collection=collection,
        restore_collection=restore_collection,
        backup_dir=backup_dir,
        keep_last=keep_last,
        apply_retention=apply_retention,
        run_restore_drill=run_restore_drill,
    )

    runner_command = _build_qdrant_snapshot_drill_runner_command(
        plan=drill_plan,
        run_compare=run_compare,
    )

    return QdrantSnapshotScheduleConfig(
        platform=normalized_platform,
        task_name=normalized_task_name,
        cron_schedule=normalized_cron_schedule,
        windows_start_time=normalized_windows_start_time,
        working_directory=normalized_working_directory,
        log_path=normalized_log_path,
        namespace=normalized_namespace,
        image=normalized_image,
        runner_command=runner_command,
    )


def render_qdrant_snapshot_schedule_config(
    config: QdrantSnapshotScheduleConfig,
) -> str:
    lines = [
        "# Qdrant Snapshot Schedule Config",
        "",
        f"- Platform: `{config.platform}`",
        f"- Task name: `{config.task_name}`",
        f"- Cron schedule: `{config.cron_schedule}`",
        f"- Windows start time: `{config.windows_start_time}`",
        f"- Working directory: `{config.working_directory}`",
        f"- Log path: `{config.log_path}`",
        f"- Namespace: `{config.namespace}`",
        f"- Image: `{config.image}`",
        "",
        "This output is a schedule configuration preview. It does not install or apply a scheduled task.",
        "",
        "## Runner Command",
        "",
        "```powershell",
        config.runner_command,
        "```",
        "",
    ]

    if config.platform in ("all", "cron"):
        lines.extend(_render_cron_config(config))

    if config.platform in ("all", "windows_task_scheduler"):
        lines.extend(_render_windows_task_scheduler_config(config))

    if config.platform in ("all", "kubernetes_cronjob"):
        lines.extend(_render_kubernetes_cronjob_config(config))

    lines.extend(
        [
            "## Safety Boundary",
            "",
            "- Review the generated command before installing it.",
            "- Keep restore target as a disposable collection.",
            "- Keep retention dry-run unless deletion is explicitly required.",
            "- Do not paste API keys into generated Markdown.",
            "",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def build_qdrant_snapshot_schedule_install_plan(
    config: QdrantSnapshotScheduleConfig,
    apply: bool = False,
    confirm_task_name: str | None = None,
) -> QdrantSnapshotScheduleInstallPlan:
    if apply and config.platform == "all":
        raise ValueError("platform must not be all when apply is true")

    if apply and confirm_task_name != config.task_name:
        raise ValueError("confirm_task_name must match task_name when apply is true")

    commands = []

    if config.platform in ("all", "cron"):
        commands.append(_build_cron_install_command(config, apply))

    if config.platform in ("all", "windows_task_scheduler"):
        commands.append(_build_windows_install_command(config, apply))

    if config.platform in ("all", "kubernetes_cronjob"):
        commands.append(_build_kubernetes_install_command(config, apply))

    return QdrantSnapshotScheduleInstallPlan(
        config=config,
        apply=apply,
        commands=commands,
    )


def render_qdrant_snapshot_schedule_install_plan(
    plan: QdrantSnapshotScheduleInstallPlan,
) -> str:
    mode = "apply" if plan.apply else "dry-run"
    lines = [
        "# Qdrant Snapshot Schedule Install Plan",
        "",
        f"- Mode: `{mode}`",
        f"- Platform: `{plan.config.platform}`",
        f"- Task name: `{plan.config.task_name}`",
        f"- Cron schedule: `{plan.config.cron_schedule}`",
        f"- Windows start time: `{plan.config.windows_start_time}`",
        f"- Working directory: `{plan.config.working_directory}`",
        f"- Log path: `{plan.config.log_path}`",
        f"- Namespace: `{plan.config.namespace}`",
        f"- Image: `{plan.config.image}`",
        "",
        "This plan shows install commands for the snapshot drill scheduler.",
        "Dry-run mode does not modify cron, Windows Task Scheduler, or Kubernetes.",
        "",
    ]

    for command in plan.commands:
        lines.extend(
            [
                f"## {command.platform}",
                "",
                f"- Description: {command.description}",
                f"- Applies system change: `{command.applies_system_change}`",
                "",
                "```powershell",
                command.command,
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Safety Boundary",
            "",
            "- Review generated commands before applying them.",
            "- Apply only one scheduler platform at a time.",
            "- Keep restore target as a disposable collection.",
            "- Run a manual drill successfully before installing a schedule.",
            "",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def build_qdrant_snapshot_schedule_verification_plan(
    config: QdrantSnapshotScheduleConfig,
) -> QdrantSnapshotScheduleVerificationPlan:
    if config.platform == "all":
        raise ValueError("platform must not be all for verification plan")

    commands = []

    if config.platform == "cron":
        commands.extend(_build_cron_verification_commands(config))
    elif config.platform == "windows_task_scheduler":
        commands.extend(_build_windows_verification_commands(config))
    elif config.platform == "kubernetes_cronjob":
        commands.extend(_build_kubernetes_verification_commands(config))
    else:
        raise ValueError(
            "platform must be one of: cron, windows_task_scheduler, kubernetes_cronjob"
        )

    return QdrantSnapshotScheduleVerificationPlan(
        config=config,
        commands=commands,
    )


def render_qdrant_snapshot_schedule_verification_plan(
    plan: QdrantSnapshotScheduleVerificationPlan,
) -> str:
    lines = [
        "# Qdrant Snapshot Schedule Verification Plan",
        "",
        f"- Platform: `{plan.config.platform}`",
        f"- Task name: `{plan.config.task_name}`",
        f"- Log path: `{plan.config.log_path}`",
        f"- Namespace: `{plan.config.namespace}`",
        "",
        "Use this plan after installing the scheduler. It separates status checks, log checks, and rollback commands.",
        "",
    ]

    for command in plan.commands:
        lines.extend(
            [
                f"## {command.purpose}",
                "",
                f"- Platform: `{command.platform}`",
                f"- Destructive: `{command.destructive}`",
                "",
                "```powershell",
                command.command,
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Verification Rules",
            "",
            "- Confirm the schedule exists before waiting for a timed run.",
            "- Confirm logs are written after the first scheduled run.",
            "- Confirm restore still targets a disposable collection.",
            "- Keep rollback commands ready before enabling apply mode.",
            "",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


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


def _build_qdrant_snapshot_drill_runner_command(
    plan: QdrantSnapshotDrillPlan,
    run_compare: bool,
) -> str:
    parts = [
        "uv",
        "run",
        "python",
        "-m",
        "app.cli",
        "qdrant-snapshot-drill-run",
        "--collection",
        plan.collection,
        "--restore-collection",
        plan.restore_collection,
        "--backup-dir",
        plan.backup_dir,
        "--keep-last",
        str(plan.keep_last),
    ]

    if plan.apply_retention:
        parts.append("--apply-retention")

    if plan.run_restore_drill:
        parts.extend(
            [
                "--confirm-restore-collection",
                plan.restore_collection,
            ]
        )
    else:
        parts.append("--skip-restore-drill")

    if not run_compare:
        parts.append("--skip-compare")

    return " ".join(parts)


def _render_cron_config(
    config: QdrantSnapshotScheduleConfig,
) -> list[str]:
    return [
        "## Cron",
        "",
        "Preview entry:",
        "",
        "```cron",
        (
            f"{config.cron_schedule} cd {config.working_directory} "
            f"&& {config.runner_command} >> {config.log_path} 2>&1"
        ),
        "```",
        "",
    ]


def _render_windows_task_scheduler_config(
    config: QdrantSnapshotScheduleConfig,
) -> list[str]:
    command = (
        "powershell -NoProfile -ExecutionPolicy Bypass "
        f"-Command \"Set-Location '{config.working_directory}'; "
        f"{config.runner_command} *> '{config.log_path}'\""
    )

    return [
        "## Windows Task Scheduler",
        "",
        "Preview command:",
        "",
        "```powershell",
        (
            f'schtasks /Create /TN "{config.task_name}" '
            f"/SC DAILY /ST {config.windows_start_time} "
            f'/TR "{command}"'
        ),
        "```",
        "",
    ]


def _render_kubernetes_cronjob_config(
    config: QdrantSnapshotScheduleConfig,
) -> list[str]:
    args = config.runner_command.split()

    lines = [
        "## Kubernetes CronJob",
        "",
        "Preview manifest:",
        "",
        "```yaml",
        "apiVersion: batch/v1",
        "kind: CronJob",
        "metadata:",
        f"  name: {config.task_name}",
        f"  namespace: {config.namespace}",
        "spec:",
        f"  schedule: \"{config.cron_schedule}\"",
        "  concurrencyPolicy: Forbid",
        "  successfulJobsHistoryLimit: 3",
        "  failedJobsHistoryLimit: 3",
        "  jobTemplate:",
        "    spec:",
        "      template:",
        "        spec:",
        "          restartPolicy: Never",
        "          containers:",
        "            - name: qdrant-snapshot-drill",
        f"              image: {config.image}",
        "              args:",
    ]

    for arg in args:
        lines.append(f"                - {arg}")

    lines.extend(["```", ""])
    return lines


def _build_cron_install_command(
    config: QdrantSnapshotScheduleConfig,
    apply: bool,
) -> QdrantSnapshotScheduleInstallCommand:
    cron_entry = (
        f"{config.cron_schedule} cd {config.working_directory} "
        f"&& {config.runner_command} >> {config.log_path} 2>&1"
    )
    command = f"(crontab -l 2>/dev/null; echo '{cron_entry}') | crontab -"

    if not apply:
        command = f"echo \"{command}\""

    return QdrantSnapshotScheduleInstallCommand(
        platform="cron",
        command=command,
        description="Install a local crontab entry for the snapshot drill runner.",
        applies_system_change=apply,
    )


def _build_windows_install_command(
    config: QdrantSnapshotScheduleConfig,
    apply: bool,
) -> QdrantSnapshotScheduleInstallCommand:
    task_command = (
        "powershell -NoProfile -ExecutionPolicy Bypass "
        f"-Command \"Set-Location '{config.working_directory}'; "
        f"{config.runner_command} *> '{config.log_path}'\""
    )
    command = (
        f'schtasks /Create /F /TN "{config.task_name}" '
        f"/SC DAILY /ST {config.windows_start_time} "
        f'/TR "{task_command}"'
    )

    if not apply:
        command = f'Write-Output "{command}"'

    return QdrantSnapshotScheduleInstallCommand(
        platform="windows_task_scheduler",
        command=command,
        description="Install a Windows Task Scheduler daily task.",
        applies_system_change=apply,
    )


def _build_kubernetes_install_command(
    config: QdrantSnapshotScheduleConfig,
    apply: bool,
) -> QdrantSnapshotScheduleInstallCommand:
    command = (
        "kubectl apply -f "
        f"{config.task_name}-cronjob.yaml"
    )

    if not apply:
        command = f'echo "{command}"'

    return QdrantSnapshotScheduleInstallCommand(
        platform="kubernetes_cronjob",
        command=command,
        description=(
            "Apply a reviewed Kubernetes CronJob manifest generated from "
            "the schedule config preview."
        ),
        applies_system_change=apply,
    )


def _build_cron_verification_commands(
    config: QdrantSnapshotScheduleConfig,
) -> list[QdrantSnapshotScheduleVerificationCommand]:
    escaped_runner = config.runner_command.replace("/", "\\/")
    return [
        QdrantSnapshotScheduleVerificationCommand(
            platform="cron",
            purpose="Check scheduled command",
            command=f"crontab -l | Select-String \"{config.runner_command}\"",
            destructive=False,
        ),
        QdrantSnapshotScheduleVerificationCommand(
            platform="cron",
            purpose="Check scheduler log",
            command=f"Get-Content {config.log_path} -Tail 80",
            destructive=False,
        ),
        QdrantSnapshotScheduleVerificationCommand(
            platform="cron",
            purpose="Rollback scheduled command",
            command=f"crontab -l | sed '/{escaped_runner}/d' | crontab -",
            destructive=True,
        ),
    ]


def _build_windows_verification_commands(
    config: QdrantSnapshotScheduleConfig,
) -> list[QdrantSnapshotScheduleVerificationCommand]:
    return [
        QdrantSnapshotScheduleVerificationCommand(
            platform="windows_task_scheduler",
            purpose="Check scheduled task",
            command=f'schtasks /Query /TN "{config.task_name}" /V /FO LIST',
            destructive=False,
        ),
        QdrantSnapshotScheduleVerificationCommand(
            platform="windows_task_scheduler",
            purpose="Check scheduler log",
            command=f"Get-Content {config.log_path} -Tail 80",
            destructive=False,
        ),
        QdrantSnapshotScheduleVerificationCommand(
            platform="windows_task_scheduler",
            purpose="Rollback scheduled task",
            command=f'schtasks /Delete /TN "{config.task_name}" /F',
            destructive=True,
        ),
    ]


def _build_kubernetes_verification_commands(
    config: QdrantSnapshotScheduleConfig,
) -> list[QdrantSnapshotScheduleVerificationCommand]:
    return [
        QdrantSnapshotScheduleVerificationCommand(
            platform="kubernetes_cronjob",
            purpose="Check CronJob",
            command=(
                "kubectl get cronjob "
                f"{config.task_name} -n {config.namespace} -o wide"
            ),
            destructive=False,
        ),
        QdrantSnapshotScheduleVerificationCommand(
            platform="kubernetes_cronjob",
            purpose="Check recent Jobs",
            command=(
                "kubectl get jobs -n "
                f"{config.namespace} --sort-by=.metadata.creationTimestamp"
            ),
            destructive=False,
        ),
        QdrantSnapshotScheduleVerificationCommand(
            platform="kubernetes_cronjob",
            purpose="Check scheduler logs",
            command=(
                "kubectl logs -n "
                f"{config.namespace} "
                f"-l job-name={config.task_name} --tail=80"
            ),
            destructive=False,
        ),
        QdrantSnapshotScheduleVerificationCommand(
            platform="kubernetes_cronjob",
            purpose="Rollback CronJob",
            command=(
                "kubectl delete cronjob "
                f"{config.task_name} -n {config.namespace}"
            ),
            destructive=True,
        ),
    ]


def _validate_cron_schedule(cron_schedule: str) -> None:
    if not cron_schedule:
        raise ValueError("cron_schedule must not be empty")

    if len(cron_schedule.split()) != 5:
        raise ValueError("cron_schedule must contain exactly 5 fields")


def _validate_windows_start_time(windows_start_time: str) -> None:
    parts = windows_start_time.split(":")

    if len(parts) != 2:
        raise ValueError("windows_start_time must use HH:MM format")

    hour_text, minute_text = parts

    if not hour_text.isdigit() or not minute_text.isdigit():
        raise ValueError("windows_start_time must use HH:MM format")

    hour = int(hour_text)
    minute = int(minute_text)

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("windows_start_time must use HH:MM format")


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
