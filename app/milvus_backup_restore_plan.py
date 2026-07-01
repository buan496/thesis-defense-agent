from dataclasses import dataclass


@dataclass(frozen=True)
class MilvusBackupRestoreStep:
    name: str
    phase: str
    command: str
    requires_milvus: bool
    description: str


@dataclass(frozen=True)
class MilvusBackupRestorePlan:
    uri: str
    collection: str
    restore_collection: str
    source: str
    backup_dir: str
    vector_size: int
    metric_type: str
    volume_name: str
    backup_file_name: str
    steps: list[MilvusBackupRestoreStep]


def build_milvus_backup_restore_plan(
    uri: str = "http://127.0.0.1:19530",
    collection: str = "thesis_chunks",
    restore_collection: str = "thesis_chunks_restore",
    source: str = "data/vector_store.json",
    backup_dir: str = "data/milvus_backups",
    vector_size: int = 1024,
    metric_type: str = "COSINE",
    volume_name: str = "thesis-defense-agent_milvus_data",
    backup_file_name: str = "milvus_data_backup.tar.gz",
) -> MilvusBackupRestorePlan:
    normalized_uri = uri.strip().rstrip("/")
    normalized_collection = collection.strip()
    normalized_restore_collection = restore_collection.strip()
    normalized_source = source.strip()
    normalized_backup_dir = backup_dir.strip()
    normalized_metric_type = metric_type.strip().upper()
    normalized_volume_name = volume_name.strip()
    normalized_backup_file_name = backup_file_name.strip()

    if not normalized_uri:
        raise ValueError("uri must not be empty")

    if not normalized_collection:
        raise ValueError("collection must not be empty")

    if not normalized_restore_collection:
        raise ValueError("restore_collection must not be empty")

    if normalized_restore_collection == normalized_collection:
        raise ValueError("restore_collection must be different from collection")

    if not normalized_source:
        raise ValueError("source must not be empty")

    if not normalized_backup_dir:
        raise ValueError("backup_dir must not be empty")

    if vector_size <= 0:
        raise ValueError("vector_size must be greater than 0")

    if not normalized_metric_type:
        raise ValueError("metric_type must not be empty")

    if not normalized_volume_name:
        raise ValueError("volume_name must not be empty")

    if not normalized_backup_file_name:
        raise ValueError("backup_file_name must not be empty")

    restore_import_command = (
        "uv run python -m app.cli import-vector-store-to-milvus "
        f"--source {normalized_source} "
        f"--uri {normalized_uri} "
        f"--collection {normalized_restore_collection} "
        f"--vector-size {vector_size} "
        f"--metric-type {normalized_metric_type}"
    )
    restore_compare_command = (
        "uv run python -m app.cli compare-vector-store-backends "
        f"--source {normalized_source} "
        "--include-milvus "
        f"--milvus-uri {normalized_uri} "
        f"--milvus-collection {normalized_restore_collection} "
        f"--milvus-vector-size {vector_size} "
        f"--milvus-metric-type {normalized_metric_type}"
    )
    volume_backup_command = (
        f"New-Item -ItemType Directory -Force {normalized_backup_dir}; "
        f"$backupDir = (Resolve-Path {normalized_backup_dir}).Path; "
        "docker run --rm "
        f"-v {normalized_volume_name}:/volume:ro "
        '-v "${backupDir}:/backup" '
        "alpine sh -c "
        f'"cd /volume && tar czf /backup/{normalized_backup_file_name} ."'
    )

    steps = [
        MilvusBackupRestoreStep(
            name="ensure_backup_dir",
            phase="local",
            command=f"New-Item -ItemType Directory -Force {normalized_backup_dir}",
            requires_milvus=False,
            description="Create the local gitignored directory used to store Milvus backup artifacts.",
        ),
        MilvusBackupRestoreStep(
            name="verify_milvus_health",
            phase="milvus",
            command="docker compose ps milvus",
            requires_milvus=True,
            description="Confirm the local Milvus standalone service is running and healthy.",
        ),
        MilvusBackupRestoreStep(
            name="verify_json_baseline",
            phase="local",
            command=f"Test-Path {normalized_source}",
            requires_milvus=False,
            description="Confirm the JSON vector store baseline exists before treating Milvus as rebuildable state.",
        ),
        MilvusBackupRestoreStep(
            name="rebuild_restore_collection_from_json",
            phase="application",
            command=restore_import_command,
            requires_milvus=True,
            description="Rebuild a disposable Milvus restore collection from the JSON vector store baseline.",
        ),
        MilvusBackupRestoreStep(
            name="compare_restore_collection",
            phase="application",
            command=restore_compare_command,
            requires_milvus=True,
            description="Compare the restored Milvus collection with the JSON baseline through the retrieval benchmark.",
        ),
        MilvusBackupRestoreStep(
            name="optional_volume_backup",
            phase="local",
            command=volume_backup_command,
            requires_milvus=False,
            description="Create a local tar.gz backup of the Milvus standalone Docker volume for single-host recovery drills.",
        ),
        MilvusBackupRestoreStep(
            name="restore_boundary_check",
            phase="manual",
            command=(
                "Do not restore a volume backup over the active Milvus volume. "
                "Use a disposable environment or rebuild from JSON baseline first."
            ),
            requires_milvus=False,
            description="Record the destructive-operation boundary before any volume-level restore attempt.",
        ),
    ]

    return MilvusBackupRestorePlan(
        uri=normalized_uri,
        collection=normalized_collection,
        restore_collection=normalized_restore_collection,
        source=normalized_source,
        backup_dir=normalized_backup_dir,
        vector_size=vector_size,
        metric_type=normalized_metric_type,
        volume_name=normalized_volume_name,
        backup_file_name=normalized_backup_file_name,
        steps=steps,
    )


def render_milvus_backup_restore_plan(
    plan: MilvusBackupRestorePlan,
) -> str:
    lines = [
        "# Milvus Backup / Restore Plan",
        "",
        f"- Milvus URI: `{plan.uri}`",
        f"- Source collection: `{plan.collection}`",
        f"- Restore collection: `{plan.restore_collection}`",
        f"- JSON baseline: `{plan.source}`",
        f"- Backup directory: `{plan.backup_dir}`",
        f"- Vector size: `{plan.vector_size}`",
        f"- Metric type: `{plan.metric_type}`",
        f"- Docker volume: `{plan.volume_name}`",
        f"- Backup file name: `{plan.backup_file_name}`",
        "",
        "Current project boundary: Milvus is a rebuildable vector backend derived from the JSON vector store baseline.",
        "Prefer rebuilding a disposable restore collection before considering volume-level recovery.",
        "",
    ]

    for index, step in enumerate(plan.steps, start=1):
        scope = "requires milvus" if step.requires_milvus else "local/manual"
        lines.extend(
            [
                f"## {index}. {step.name}",
                "",
                f"- Phase: `{step.phase}`",
                f"- Scope: `{scope}`",
                f"- Purpose: {step.description}",
                "",
                "```powershell",
                step.command,
                "```",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def render_milvus_restore_report_template(
    plan: MilvusBackupRestorePlan,
    environment: str = "local-milvus",
    operator: str = "",
) -> str:
    normalized_environment = environment.strip()
    operator_text = operator.strip() or "TBD"

    if not normalized_environment:
        raise ValueError("environment must not be empty")

    lines = [
        "# Milvus Backup / Restore Execution Report",
        "",
        f"- Environment: `{normalized_environment}`",
        f"- Milvus URI: `{plan.uri}`",
        f"- Source collection: `{plan.collection}`",
        f"- Restore collection: `{plan.restore_collection}`",
        f"- JSON baseline: `{plan.source}`",
        f"- Backup directory: `{plan.backup_dir}`",
        f"- Docker volume: `{plan.volume_name}`",
        f"- Backup file name: `{plan.backup_file_name}`",
        f"- Operator: `{operator_text}`",
        "- Started at: `TBD`",
        "- Finished at: `TBD`",
        "- Overall status: `TBD`",
        "",
        "Do not paste API keys, tokens, private URLs, or other secrets into this report.",
        "",
        "## Verification Summary",
        "",
        "- Restore collection row count: `TBD`",
        "- Retrieval benchmark average score: `TBD`",
        "- Retrieval benchmark status: `[ ] PASS  [ ] FAIL  [ ] SKIPPED`",
        "- Volume backup artifact exists: `[ ] PASS  [ ] FAIL  [ ] SKIPPED`",
        "",
    ]

    for index, step in enumerate(plan.steps, start=1):
        scope = "requires milvus" if step.requires_milvus else "local/manual"
        lines.extend(
            [
                f"## {index}. {step.name}",
                "",
                f"- Phase: `{step.phase}`",
                f"- Scope: `{scope}`",
                f"- Expected result: {step.description}",
                "- Result: `[ ] PASS  [ ] FAIL  [ ] SKIPPED`",
                "- Notes: `TBD`",
                "",
                "Command:",
                "",
                "```powershell",
                step.command,
                "```",
                "",
                "Evidence:",
                "",
                "```text",
                "Paste sanitized command output here.",
                "```",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"
