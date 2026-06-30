from dataclasses import dataclass


@dataclass(frozen=True)
class QdrantSnapshotSmokeStep:
    name: str
    phase: str
    command: str
    requires_qdrant: bool
    description: str


@dataclass(frozen=True)
class QdrantSnapshotSmokePlan:
    url: str
    collection: str
    restore_collection: str
    backup_dir: str
    snapshot_name_placeholder: str
    steps: list[QdrantSnapshotSmokeStep]


def build_qdrant_snapshot_smoke_plan(
    url: str = "http://127.0.0.1:6333",
    collection: str = "thesis_chunks",
    restore_collection: str = "thesis_chunks_restore",
    backup_dir: str = "data/qdrant_backups",
    snapshot_name_placeholder: str = "<snapshot_name>",
) -> QdrantSnapshotSmokePlan:
    normalized_url = url.strip().rstrip("/")
    normalized_collection = collection.strip()
    normalized_restore_collection = restore_collection.strip()
    normalized_backup_dir = backup_dir.strip()
    normalized_snapshot_name = snapshot_name_placeholder.strip()

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

    if not normalized_snapshot_name:
        raise ValueError("snapshot_name_placeholder must not be empty")

    snapshot_uri = (
        f"{normalized_url}/collections/"
        f"{normalized_collection}/snapshots/{normalized_snapshot_name}"
    )
    snapshot_path = f"{normalized_backup_dir}/{normalized_snapshot_name}"

    steps = [
        QdrantSnapshotSmokeStep(
            name="ensure_backup_dir",
            phase="local",
            command=f"New-Item -ItemType Directory -Force {normalized_backup_dir}",
            requires_qdrant=False,
            description="Create the local gitignored directory used to store downloaded snapshots.",
        ),
        QdrantSnapshotSmokeStep(
            name="create_snapshot",
            phase="qdrant",
            command=(
                "Invoke-RestMethod "
                "-Method Post "
                f'-Uri "{normalized_url}/collections/{normalized_collection}/snapshots"'
            ),
            requires_qdrant=True,
            description="Ask Qdrant to create a collection snapshot and return its file name.",
        ),
        QdrantSnapshotSmokeStep(
            name="list_snapshots",
            phase="qdrant",
            command=(
                "Invoke-RestMethod "
                "-Method Get "
                f'-Uri "{normalized_url}/collections/{normalized_collection}/snapshots"'
            ),
            requires_qdrant=True,
            description="Confirm the created snapshot is visible through the Qdrant API.",
        ),
        QdrantSnapshotSmokeStep(
            name="download_snapshot",
            phase="qdrant",
            command=(
                "Invoke-WebRequest "
                f'-Uri "{snapshot_uri}" '
                f'-OutFile "{snapshot_path}"'
            ),
            requires_qdrant=True,
            description="Download the snapshot file into the local backup directory.",
        ),
        QdrantSnapshotSmokeStep(
            name="restore_to_disposable_collection",
            phase="qdrant",
            command=(
                "curl.exe -X POST "
                f'"{normalized_url}/collections/'
                f'{normalized_restore_collection}/snapshots/upload?priority=snapshot" '
                '-H "Content-Type: multipart/form-data" '
                f'-F "snapshot=@{snapshot_path}"'
            ),
            requires_qdrant=True,
            description="Restore the snapshot into a disposable collection, never directly over the active collection.",
        ),
        QdrantSnapshotSmokeStep(
            name="compare_restored_collection",
            phase="application",
            command=(
                "uv run python -m app.cli compare-vector-store-backends "
                "--source data/vector_store.json "
                f"--url {normalized_url} "
                f"--collection {normalized_restore_collection}"
            ),
            requires_qdrant=True,
            description="Compare JSON baseline retrieval with the restored Qdrant collection.",
        ),
        QdrantSnapshotSmokeStep(
            name="retention_dry_run",
            phase="local",
            command=(
                "uv run python -m app.cli qdrant-backup-retention "
                f"--backup-dir {normalized_backup_dir} "
                "--keep-last 5"
            ),
            requires_qdrant=False,
            description="Preview old snapshot deletion candidates without deleting files.",
        ),
    ]

    return QdrantSnapshotSmokePlan(
        url=normalized_url,
        collection=normalized_collection,
        restore_collection=normalized_restore_collection,
        backup_dir=normalized_backup_dir,
        snapshot_name_placeholder=normalized_snapshot_name,
        steps=steps,
    )


def render_qdrant_snapshot_smoke_plan(
    plan: QdrantSnapshotSmokePlan,
) -> str:
    lines = [
        "# Qdrant Snapshot Smoke Plan",
        "",
        f"- Qdrant URL: `{plan.url}`",
        f"- Source collection: `{plan.collection}`",
        f"- Restore collection: `{plan.restore_collection}`",
        f"- Backup directory: `{plan.backup_dir}`",
        f"- Snapshot name placeholder: `{plan.snapshot_name_placeholder}`",
        "",
        "Replace the snapshot placeholder with the snapshot file name returned by `create_snapshot`.",
        "",
    ]

    for index, step in enumerate(plan.steps, start=1):
        scope = "requires qdrant" if step.requires_qdrant else "local"
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


def render_qdrant_snapshot_smoke_report_template(
    plan: QdrantSnapshotSmokePlan,
    environment: str = "local-qdrant",
    operator: str = "",
) -> str:
    normalized_environment = environment.strip()
    operator_text = operator.strip() or "TBD"

    if not normalized_environment:
        raise ValueError("environment must not be empty")

    lines = [
        "# Qdrant Snapshot Smoke Execution Report",
        "",
        f"- Environment: `{normalized_environment}`",
        f"- Qdrant URL: `{plan.url}`",
        f"- Source collection: `{plan.collection}`",
        f"- Restore collection: `{plan.restore_collection}`",
        f"- Backup directory: `{plan.backup_dir}`",
        f"- Operator: `{operator_text}`",
        "- Started at: `TBD`",
        "- Finished at: `TBD`",
        "- Overall status: `TBD`",
        "",
        "Do not paste API keys, kubeconfig content, private URLs, or other secrets into this report.",
        "",
    ]

    for index, step in enumerate(plan.steps, start=1):
        scope = "requires qdrant" if step.requires_qdrant else "local"
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
