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
```

Not completed:

```text
Qdrant operational backup/restore
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

## Current Runtime Boundary

The default remains:

```text
VECTOR_STORE_BACKEND=json
```

This keeps local JSON retrieval as the stable baseline while Qdrant is tested
side-by-side.

## Next Step

Define backup/restore guidance before using Qdrant as a long-running
production dependency.
