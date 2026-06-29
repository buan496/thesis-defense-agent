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
```

Not completed:

```text
Automated scheduled Qdrant backup job
Qdrant backup retention policy enforcement
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

### Backup Safety Rules

```text
1. Do not commit snapshot files or Qdrant volumes to Git.
2. Always restore into a disposable collection first.
3. Run compare-vector-store-backends after restore.
4. Keep JSON vector store as the local fallback until Qdrant is promoted as the primary backend.
5. Use delete-qdrant-collection only with explicit --confirm-collection.
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
