# Milvus Local Service

## Purpose

Milvus is introduced as a comparison vector database backend after the JSON
baseline and Qdrant implementation. The goal is not to replace Qdrant
immediately. The goal is to validate that the existing `VectorStoreRepository`
protocol can support another vector database and can be evaluated with the same
retrieval benchmark.

## Local Compose Service

The Compose service uses Milvus standalone mode with embedded etcd and local
storage:

```text
milvusdb/milvus:v2.5.17
milvus_data -> /var/lib/milvus
```

Start Milvus:

```powershell
docker compose up -d milvus
```

Check service status:

```powershell
docker compose ps milvus
```

Stop Milvus without deleting the volume:

```powershell
docker compose stop milvus
```

Delete the local Milvus volume only when you intentionally want to reset vector
database state:

```powershell
docker compose down -v
```

## Local Environment

Default `.env.example` values:

```env
MILVUS_URI=http://127.0.0.1:19530
MILVUS_TOKEN=
MILVUS_COLLECTION=thesis_chunks
MILVUS_VECTOR_SIZE=1024
MILVUS_METRIC_TYPE=COSINE
MILVUS_PORT=19530
MILVUS_METRICS_PORT=9091
```

`VECTOR_STORE_BACKEND=json` remains the default. Set
`VECTOR_STORE_BACKEND=milvus` explicitly only when testing Milvus retrieval.

`MILVUS_VECTOR_SIZE=1024` matches the current `BAAI/bge-m3` embedding output
used by the project.

## Import JSON Vector Store

Import the current local JSON vector store into Milvus:

```powershell
uv run python -m app.cli import-vector-store-to-milvus `
  --source data/vector_store.json `
  --uri http://127.0.0.1:19530 `
  --collection thesis_chunks `
  --vector-size 1024 `
  --metric-type COSINE
```

## Backend Comparison

Compare JSON, Qdrant, and Milvus with the same benchmark:

```powershell
docker compose up -d qdrant milvus

uv run python -m app.cli compare-vector-store-backends `
  --source data/vector_store.json `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks `
  --include-milvus `
  --milvus-uri http://127.0.0.1:19530 `
  --milvus-collection thesis_chunks `
  --output data/reports/vector_store_backend_comparison_with_milvus.json
```

## Current Boundary

Completed:

```text
Milvus Compose service
Milvus environment variables
pymilvus dependency
MilvusVectorStoreRepository
Milvus collection ensure/create
Milvus insert
Milvus search
import-vector-store-to-milvus CLI
compare-vector-store-backends --include-milvus
fake-client unit tests
```

Not completed:

```text
local Milvus runtime smoke execution
JSON / Qdrant / Milvus benchmark result report
Milvus backup / restore SOP
Milvus production deployment topology
```

