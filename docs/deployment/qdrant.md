# Qdrant Local Service

## Purpose

Qdrant is introduced as the next vector database candidate after the local JSON
vector store repository abstraction.

This stage prepares local infrastructure only:

```text
docker-compose qdrant service
Qdrant environment variables
documentation and offline config tests
```

It does not implement `QdrantVectorStoreRepository` yet, and it does not switch
runtime retrieval away from the JSON vector store.

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

`VECTOR_STORE_BACKEND=json` remains the default until the Qdrant repository is
implemented and tested.

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
```

Not completed:

```text
Qdrant Python client dependency
Qdrant collection creation
JSON vector store import into Qdrant
QdrantVectorStoreRepository
runtime retrieval through Qdrant
Qdrant benchmark comparison against JSON vector store
```

## Next Step

Implement a Qdrant repository adapter behind the existing vector store
repository protocol:

```text
JsonVectorStoreRepository
QdrantVectorStoreRepository
```

The expected migration path is:

```text
1. Add Qdrant client dependency
2. Implement collection ensure/create logic
3. Import existing JSON vector store items into Qdrant
4. Implement search(query, top_k, embedding_fn)
5. Run RAG benchmark against both JSON and Qdrant backends
```
