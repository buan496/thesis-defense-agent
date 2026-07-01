# Qdrant Local Service

## Purpose

Qdrant is introduced as the next vector database candidate after the local JSON
vector store repository abstraction.

The first stage prepared local infrastructure:

```text
docker-compose qdrant service
Qdrant environment variables
documentation and offline config tests
```

The current implementation also includes a minimal `QdrantVectorStoreRepository`
behind the existing vector store repository protocol.

## Local Compose Service

The Compose service uses the official Qdrant Docker image pinned to
`qdrant/qdrant:v1.18.2` and stores data in a named Docker volume:

```text
qdrant_data -> /qdrant/storage
```

Start Qdrant:

```powershell
docker compose up -d qdrant
```

Check service status:

```powershell
docker compose ps qdrant
```

Check the HTTP API:

```powershell
Invoke-RestMethod http://127.0.0.1:6333
```

Stop Qdrant without deleting the volume:

```powershell
docker compose stop qdrant
```

Delete the local Qdrant volume only when you intentionally want to reset vector
database state:

```powershell
docker compose down -v
```

## Local Environment

Default `.env.example` values:

```env
VECTOR_STORE_BACKEND=json
QDRANT_URL=http://127.0.0.1:6333
QDRANT_COLLECTION=thesis_chunks
QDRANT_VECTOR_SIZE=1024
QDRANT_DISTANCE=Cosine
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_API_KEY=
```

`VECTOR_STORE_BACKEND=json` remains the default. Set
`VECTOR_STORE_BACKEND=qdrant` explicitly when testing Qdrant retrieval.

`QDRANT_VECTOR_SIZE=1024` matches the current `BAAI/bge-m3` embedding output
used by the project.

## Current Boundary

Completed:

```text
Qdrant Compose service
Qdrant image pinned to v1.18.2
Qdrant named volume
Qdrant REST and gRPC port configuration
Qdrant config variables
offline tests for compose/env/config
local REST smoke test
QdrantVectorStoreRepository minimal implementation
Qdrant collection ensure/create
Qdrant upsert
Qdrant query_points search
import-vector-store-to-qdrant CLI
local import smoke test: 70 chunks imported from data/vector_store.json
local repository search smoke test
compare-vector-store-backends CLI
JSON vs Qdrant benchmark comparison path
delete-qdrant-collection CLI with explicit confirmation
Qdrant snapshot backup/restore SOP
vector-db-governance-report CLI
Qdrant / Milvus production-governance comparison report
qdrant-backup-retention CLI
local backup retention dry-run / apply execution
qdrant-snapshot-smoke-plan CLI
qdrant-snapshot-smoke-report-template CLI
qdrant-snapshot-create CLI
qdrant-snapshot-list CLI
qdrant-snapshot-download CLI
qdrant-snapshot-restore CLI with explicit confirmation
qdrant-snapshot-drill-plan CLI
qdrant-snapshot-drill-run CLI
qdrant-snapshot-schedule-config CLI
qdrant-snapshot-schedule-install-plan CLI
qdrant-snapshot-schedule-verify-plan CLI
```

Not completed:

```text
Automated scheduled Qdrant backup job
Automated scheduled Qdrant snapshot creation
Automated scheduled restore smoke drill
Actual cron / Windows Task Scheduler / Kubernetes CronJob installation
Actual scheduled run evidence collection
MilvusVectorStoreRepository
Milvus runtime benchmark
```

## Production Governance Report

The project includes an offline vector database governance report. It does not
connect to Qdrant or Milvus. Its purpose is to keep production-promotion
criteria explicit before changing the default runtime backend.

Generate the report:

```powershell
uv run python -m app.cli vector-db-governance-report
```

Save the report:

```powershell
uv run python -m app.cli vector-db-governance-report `
  --output data/reports/vector_db_governance.md
```

Evaluate Milvus as the target comparison backend without implementing it:

```powershell
uv run python -m app.cli vector-db-governance-report `
  --target-backend milvus `
  --output data/reports/vector_db_governance_milvus.md
```

The report covers:

```text
JSON baseline role
Qdrant promotion gates
Milvus comparison boundary
quality regression gate
latency recording gate
backup / restore gate
destructive-operation guardrails
rollback requirement
```

Current decision:

```text
JSON remains the default local fallback.
Qdrant remains the primary production candidate.
Milvus remains a future comparison candidate, not an implemented runtime backend.
```

## Import JSON Vector Store Into Qdrant

Start Qdrant:

```powershell
docker compose up -d qdrant
```

Import the current JSON vector store:

```powershell
uv run python -m app.cli import-vector-store-to-qdrant `
  --source data/vector_store.json `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks `
  --vector-size 1024 `
  --distance Cosine
```

Run retrieval with Qdrant explicitly:

```powershell
$env:VECTOR_STORE_BACKEND = "qdrant"
uv run python -m app.cli create-task --topic "系统架构"
```

Clean the variable when finished:

```powershell
Remove-Item Env:VECTOR_STORE_BACKEND -ErrorAction SilentlyContinue
```

## Compare JSON and Qdrant Backends

The benchmark comparison uses the same RAG benchmark questions and compares
quality plus query latency across the JSON repository and Qdrant repository.

```powershell
uv run python -m app.cli compare-vector-store-backends `
  --source data/vector_store.json `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks `
  --vector-size 1024 `
  --distance Cosine
```

The report includes:

```text
average_score
average_duration_ms
score_delta_qdrant_minus_json
duration_delta_ms_qdrant_minus_json
missing keywords per query
cache hits / misses
```

## Delete a Qdrant Collection

Collection deletion is destructive, so the CLI requires explicit confirmation.
The value passed to `--confirm-collection` must exactly match `--collection`.

```powershell
uv run python -m app.cli delete-qdrant-collection `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks `
  --vector-size 1024 `
  --distance Cosine `
  --confirm-collection thesis_chunks
```

If the collection does not exist, the command succeeds with:

```text
DELETED: False
```

If the confirmation does not match, the command exits before contacting
Qdrant.

## Backup and Restore SOP

Qdrant's native backup unit is a snapshot. For this project, snapshots are the
preferred operational backup path because they preserve vectors, payloads, and
the collection storage structures needed for efficient restore.

Official reference:

```text
https://qdrant.tech/documentation/snapshots/
```

Important local Docker detail:

```text
Qdrant Docker snapshots path: /qdrant/snapshots
Project Qdrant volume: qdrant_data -> /qdrant/storage
```

### Create a Collection Snapshot

Start Qdrant first:

```powershell
docker compose up -d qdrant
```

Create a snapshot for the current thesis collection:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:6333/collections/thesis_chunks/snapshots"
```

The response contains the snapshot file name. Save that name before continuing.

### List Collection Snapshots

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:6333/collections/thesis_chunks/snapshots"
```

### Download a Snapshot

Replace `<snapshot_name>` with the name returned by the create or list command:

```powershell
New-Item -ItemType Directory -Force data/qdrant_backups

Invoke-WebRequest `
  -Uri "http://127.0.0.1:6333/collections/thesis_chunks/snapshots/<snapshot_name>" `
  -OutFile "data/qdrant_backups/<snapshot_name>"
```

The `data/qdrant_backups/` directory is a local operational backup target. Do
not commit snapshot files to Git.

### Restore from an Uploaded Snapshot

Restoring can overwrite collection data. Use a disposable collection first when
testing restore.

```powershell
curl.exe -X POST `
  "http://127.0.0.1:6333/collections/thesis_chunks_restore/snapshots/upload?priority=snapshot" `
  -H "Content-Type: multipart/form-data" `
  -F "snapshot=@data/qdrant_backups/<snapshot_name>"
```

After restore, compare retrieval behavior before switching application traffic:

```powershell
uv run python -m app.cli compare-vector-store-backends `
  --source data/vector_store.json `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks_restore `
  --vector-size 1024 `
  --distance Cosine
```

### Rebuild from JSON Baseline

Because JSON remains the default source of truth in this learning project, a
Qdrant collection can also be rebuilt from `data/vector_store.json`:

```powershell
uv run python -m app.cli delete-qdrant-collection `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks `
  --vector-size 1024 `
  --distance Cosine `
  --confirm-collection thesis_chunks

uv run python -m app.cli import-vector-store-to-qdrant `
  --source data/vector_store.json `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks `
  --vector-size 1024 `
  --distance Cosine
```

Use snapshot restore when preserving the exact Qdrant collection state matters.
Use JSON rebuild when the goal is to regenerate the collection from the current
local vector store artifact.

## Snapshot API Runner

The project provides manual CLI wrappers around Qdrant's collection snapshot
HTTP APIs. These commands are useful for local operational drills and scripted
maintenance, but they do not create a scheduler by themselves.

Create a snapshot:

```powershell
uv run python -m app.cli qdrant-snapshot-create `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks
```

List snapshots:

```powershell
uv run python -m app.cli qdrant-snapshot-list `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks
```

Download a snapshot:

```powershell
uv run python -m app.cli qdrant-snapshot-download `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks `
  --snapshot-name <snapshot_name> `
  --backup-dir data/qdrant_backups
```

Restore a snapshot into a disposable collection:

```powershell
uv run python -m app.cli qdrant-snapshot-restore `
  --url http://127.0.0.1:6333 `
  --restore-collection thesis_chunks_restore `
  --confirm-restore-collection thesis_chunks_restore `
  --snapshot-path data/qdrant_backups/<snapshot_name>
```

Restore requires `--confirm-restore-collection` to exactly match
`--restore-collection`. This prevents accidental restore into the wrong
collection. Do not restore over the active collection during smoke testing.

## Snapshot Drill Plan

The project also provides a scheduled-drill plan generator. It does not contact
Qdrant. Its purpose is to make the future scheduled runner explicit before
adding cron, Windows Task Scheduler, or Kubernetes CronJob integration.

Generate the default drill plan:

```powershell
uv run python -m app.cli qdrant-snapshot-drill-plan
```

Generate a plan that previews retention only:

```powershell
uv run python -m app.cli qdrant-snapshot-drill-plan `
  --collection thesis_chunks `
  --restore-collection thesis_chunks_restore `
  --backup-dir data/qdrant_backups `
  --keep-last 5
```

Generate a plan that marks retention as an apply step:

```powershell
uv run python -m app.cli qdrant-snapshot-drill-plan `
  --collection thesis_chunks `
  --restore-collection thesis_chunks_restore `
  --backup-dir data/qdrant_backups `
  --keep-last 5 `
  --apply-retention
```

Save the plan:

```powershell
uv run python -m app.cli qdrant-snapshot-drill-plan `
  --output data/reports/qdrant_snapshot_drill_plan.md
```

Current boundary:

```text
The drill plan is implemented.
The one-time drill runner is implemented.
Scheduled execution is not implemented yet.
```

## Snapshot Drill Runner

The project provides a one-time Qdrant snapshot drill runner. It executes the
manual runner steps as one command:

```text
create snapshot
download snapshot
run local retention policy
optionally restore into a disposable collection
optionally compare restored collection against JSON baseline
```

Run a drill without restored-collection comparison:

```powershell
uv run python -m app.cli qdrant-snapshot-drill-run `
  --collection thesis_chunks `
  --restore-collection thesis_chunks_restore `
  --confirm-restore-collection thesis_chunks_restore `
  --backup-dir data/qdrant_backups `
  --keep-last 5 `
  --skip-compare
```

Run a drill and save a Markdown report:

```powershell
uv run python -m app.cli qdrant-snapshot-drill-run `
  --collection thesis_chunks `
  --restore-collection thesis_chunks_restore `
  --confirm-restore-collection thesis_chunks_restore `
  --backup-dir data/qdrant_backups `
  --keep-last 5 `
  --skip-compare `
  --output data/reports/qdrant_snapshot_drill_report.md
```

When restore drill is enabled, `--confirm-restore-collection` must exactly
match `--restore-collection`. Use `--skip-restore-drill` to run only snapshot
creation, download, and retention.

Current boundary:

```text
The runner is an explicit one-time command.
It does not create cron, Windows Task Scheduler, or Kubernetes CronJob resources.
Retention remains dry-run unless --apply-retention is passed.
Restore must target a disposable collection.
```

## Snapshot Schedule Config

The project provides a schedule configuration preview generator for the
one-time snapshot drill runner. It renders scheduler snippets for local cron,
Windows Task Scheduler, and Kubernetes CronJob, but it does not install or
apply any scheduled task.

Generate all supported schedule previews:

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-config
```

Generate only a cron preview:

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-config `
  --platform cron `
  --cron-schedule "0 3 * * *" `
  --collection thesis_chunks `
  --restore-collection thesis_chunks_restore
```

Save the generated Markdown:

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-config `
  --platform cron `
  --output data/reports/qdrant_snapshot_schedule_config.md
```

Generate a Kubernetes CronJob preview:

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-config `
  --platform kubernetes_cronjob `
  --namespace thesis-defense `
  --image ghcr.io/buan496/thesis-defense-agent:latest
```

Current boundary:

```text
The schedule config generator is implemented.
It renders cron, Windows Task Scheduler, and Kubernetes CronJob previews.
It does not install cron entries.
It does not create Windows scheduled tasks.
It does not apply Kubernetes CronJob manifests.
Review and run generated scheduler commands manually before enabling automation.
```

## Snapshot Schedule Install Plan

The project also provides a schedule install plan generator. It converts the
schedule config preview into explicit install commands, while preserving safety
guards.

Generate dry-run install commands for all supported platforms:

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-install-plan
```

Generate a dry-run Windows Task Scheduler install command:

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-install-plan `
  --platform windows_task_scheduler `
  --task-name thesis-defense-qdrant-snapshot-drill
```

Generate a real cron install command preview with explicit confirmation:

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-install-plan `
  --platform cron `
  --task-name thesis-defense-qdrant-snapshot-drill `
  --confirm-task-name thesis-defense-qdrant-snapshot-drill `
  --apply
```

Save the install plan:

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-install-plan `
  --platform cron `
  --output data/reports/qdrant_snapshot_schedule_install_plan.md
```

Safety rules:

```text
Dry-run is the default.
--apply requires --confirm-task-name to match --task-name.
--apply cannot be used with --platform all.
The CLI renders install commands; it does not execute them.
Review commands before running them in a shell or cluster.
```

## Snapshot Schedule Verification Plan

After installing a scheduler manually, generate a verification plan for the
specific platform. The plan includes status checks, log checks, and rollback
commands.

Generate a cron verification plan:

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-verify-plan `
  --platform cron
```

Generate a Windows Task Scheduler verification plan:

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-verify-plan `
  --platform windows_task_scheduler `
  --task-name thesis-defense-qdrant-snapshot-drill
```

Generate a Kubernetes CronJob verification plan:

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-verify-plan `
  --platform kubernetes_cronjob `
  --task-name thesis-defense-qdrant-snapshot-drill `
  --namespace thesis-defense
```

Save the verification plan:

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-verify-plan `
  --platform cron `
  --output data/reports/qdrant_snapshot_schedule_verify_plan.md
```

Verification scope:

```text
The CLI generates status, log, and rollback commands.
It does not query cron, Windows Task Scheduler, or Kubernetes directly.
It does not execute rollback commands.
Run the generated commands manually and save evidence before enabling long-term automation.
```

## Snapshot Smoke Plan

The project provides an offline snapshot smoke-test plan generator. It does not
contact Qdrant. It creates a repeatable sequence for manually validating:

```text
create snapshot
list snapshot
download snapshot
restore into disposable collection
compare restored collection against JSON baseline
run backup retention dry-run
```

Generate the plan:

```powershell
uv run python -m app.cli qdrant-snapshot-smoke-plan
```

Save the plan:

```powershell
uv run python -m app.cli qdrant-snapshot-smoke-plan `
  --output data/reports/qdrant_snapshot_smoke_plan.md
```

Generate an execution report template:

```powershell
uv run python -m app.cli qdrant-snapshot-smoke-report-template `
  --environment local-compose `
  --operator "<your-name>" `
  --output data/reports/qdrant_snapshot_smoke_report.md
```

Use a disposable restore collection. Do not restore directly over the active
collection:

```powershell
uv run python -m app.cli qdrant-snapshot-smoke-plan `
  --collection thesis_chunks `
  --restore-collection thesis_chunks_restore
```

Current boundary:

```text
The plan and report template are implemented.
The Qdrant snapshot API runner is implemented as manual CLI commands.
The project does not yet include scheduled backup or scheduled restore drill automation.
```

### Backup Safety Rules

```text
1. Do not commit snapshot files or Qdrant volumes to Git.
2. Always restore into a disposable collection first.
3. Run compare-vector-store-backends after restore.
4. Keep JSON vector store as the local fallback until Qdrant is promoted as the primary backend.
5. Use delete-qdrant-collection only with explicit --confirm-collection.
```

## Backup Retention Policy

Downloaded Qdrant snapshot files are stored under:

```text
data/qdrant_backups/
```

This directory is ignored by Git. The project provides a local retention CLI
that can be used manually or scheduled later. By default it is dry-run and does
not delete files.

Preview deletion candidates while keeping the newest 5 snapshots:

```powershell
New-Item -ItemType Directory -Force data/qdrant_backups

uv run python -m app.cli qdrant-backup-retention `
  --backup-dir data/qdrant_backups `
  --keep-last 5
```

Actually delete older snapshots:

```powershell
uv run python -m app.cli qdrant-backup-retention `
  --backup-dir data/qdrant_backups `
  --keep-last 5 `
  --apply
```

Save a retention report:

```powershell
uv run python -m app.cli qdrant-backup-retention `
  --backup-dir data/qdrant_backups `
  --keep-last 5 `
  --output data/reports/qdrant_backup_retention.md
```

The default file pattern is:

```text
*.snapshot
```

Use additional patterns only if your backup process produces different file
names:

```powershell
uv run python -m app.cli qdrant-backup-retention `
  --backup-dir data/qdrant_backups `
  --pattern "*.snapshot" `
  --pattern "*.tar.gz"
```

Current boundary:

```text
Retention execution is implemented for local downloaded backup files.
Qdrant snapshot creation / list / download / restore can be run through manual CLI commands.
No cron, Task Scheduler, or Kubernetes CronJob is created yet.
```

## Current Runtime Boundary

The default remains:

```text
VECTOR_STORE_BACKEND=json
```

This keeps local JSON retrieval as the stable baseline while Qdrant is tested
side-by-side.

## Next Step

Automate only after the SOP is stable: scheduled snapshot creation, retention
cleanup, and restore smoke checks are future production-readiness work.
