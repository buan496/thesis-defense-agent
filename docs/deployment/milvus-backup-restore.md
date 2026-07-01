# Milvus Backup / Restore SOP

## Purpose

This project currently treats Milvus as a rebuildable vector database backend.
The authoritative local baseline is still `data/vector_store.json`; Milvus can
be rebuilt from that JSON file through `import-vector-store-to-milvus`.

This SOP therefore has two layers:

```text
Primary restore path:
JSON vector store baseline -> disposable Milvus restore collection -> benchmark comparison

Supplemental local recovery path:
Docker volume tar.gz backup -> isolated restore environment -> smoke verification
```

Do not restore a Milvus Docker volume directly over the active local service
unless the environment is disposable and the restore target is explicitly
confirmed.

## Generate The Plan

Generate a dry-run backup / restore plan:

```powershell
uv run python -m app.cli milvus-backup-restore-plan
```

Save the plan as Markdown:

```powershell
uv run python -m app.cli milvus-backup-restore-plan `
  --output data/reports/milvus_backup_restore_plan.md
```

Use a disposable restore collection:

```powershell
uv run python -m app.cli milvus-backup-restore-plan `
  --restore-collection thesis_chunks_restore
```

## Generate The Execution Report Template

```powershell
uv run python -m app.cli milvus-restore-report-template `
  --environment local-milvus `
  --operator "<your-name>"
```

Save the report template:

```powershell
uv run python -m app.cli milvus-restore-report-template `
  --output data/reports/milvus_restore_report.md
```

## Restore Smoke Test

The safe restore smoke test rebuilds a disposable Milvus collection from the JSON
baseline:

```powershell
uv run python -m app.cli import-vector-store-to-milvus `
  --source data/vector_store.json `
  --uri http://127.0.0.1:19530 `
  --collection thesis_chunks_restore `
  --vector-size 1024 `
  --metric-type COSINE
```

Then compare the restored collection with the JSON baseline:

```powershell
uv run python -m app.cli compare-vector-store-backends `
  --source data/vector_store.json `
  --include-milvus `
  --milvus-uri http://127.0.0.1:19530 `
  --milvus-collection thesis_chunks_restore `
  --milvus-vector-size 1024 `
  --milvus-metric-type COSINE
```

Expected acceptance criteria:

```text
Milvus restore collection is created.
Milvus restored search returns benchmark results.
Average benchmark score does not regress against the JSON baseline.
No production collection is overwritten.
```

After the restore smoke test, delete only the disposable restore collection with
explicit confirmation:

```powershell
uv run python -m app.cli delete-milvus-collection `
  --uri http://127.0.0.1:19530 `
  --collection thesis_chunks_restore `
  --confirm-collection thesis_chunks_restore
```

## Optional Local Volume Backup

For the local standalone Milvus Compose service, the persistent data lives in the
Docker volume:

```text
thesis-defense-agent_milvus_data
```

The generated plan includes a PowerShell command that creates a `tar.gz` archive
from that volume into `data/milvus_backups`.

This is a single-host learning backup. It is not a production Milvus cluster
backup strategy.

## Boundaries

Completed in this project stage:

```text
Milvus backup / restore SOP document
milvus-backup-restore-plan CLI
milvus-restore-report-template CLI
safe restore path through JSON baseline rebuild
optional local Docker volume backup command preview
delete-milvus-collection CLI with explicit confirmation
```

Not completed:

```text
Milvus Backup Tool integration
Milvus object storage backup
Milvus cluster-level restore drill
automatic destructive volume restore execution
```
