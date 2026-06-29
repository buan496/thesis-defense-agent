# PostgreSQL Storage Plan

## Purpose

The current project stores tasks, sessions, memory, and traces in local JSON or JSONL files. This is appropriate for the local learning version, but it is not enough for a long-running multi-user service.

PostgreSQL will be introduced as a durable storage backend for:

- DefenseTask records
- Agent sessions
- Agent and task trace records
- feedback and benchmark candidate records

This stage does not replace the existing JSON storage directly. The first step is to define repository boundaries so the current JSON implementation and a future PostgreSQL implementation can share the same interface.

## Current Abstraction

Repository interfaces live in:

```text
app/storage_repositories.py
```

Current JSON-backed implementations:

```text
JsonTaskRepository
JsonSessionRepository
JsonlTraceRepository
```

Future PostgreSQL-backed implementations should provide equivalent behavior:

```text
PostgresTaskRepository
PostgresSessionRepository
PostgresTraceRepository
```

## Proposed Tables

### defense_tasks

```sql
CREATE TABLE defense_tasks (
    task_id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    status TEXT NOT NULL,
    current_step_id TEXT,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
```

`payload` stores the full serialized `DefenseTask` object first. Later, steps can be normalized into a separate table if query requirements justify it.

### agent_sessions

```sql
CREATE TABLE agent_sessions (
    session_id TEXT PRIMARY KEY,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

`payload` stores the serialized `AgentSession`, including messages and metadata.

### trace_records

```sql
CREATE TABLE trace_records (
    id BIGSERIAL PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT,
    event_type TEXT,
    success BOOLEAN,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Trace records are append-only. They should not be updated in place.

## Migration Strategy

Recommended order:

1. Keep JSON storage as the default.
2. Add repository interfaces and JSON implementations.
3. Add PostgreSQL schema and migrations.
4. Add PostgreSQL repository implementations behind config flags.
5. Write one-time import scripts from JSON files to PostgreSQL.
6. Switch API service to PostgreSQL in server/runtime mode only.

## Why Not Replace JSON Immediately

Replacing storage directly would mix two changes:

- changing persistence semantics
- changing application behavior

The project should keep those concerns separate. The repository abstraction lets tests verify storage behavior before the service layer is switched.

## Next Steps

- Add `DATABASE_URL` configuration.
- Add PostgreSQL dependencies after selecting the client library.
- Add migration tooling.
- Add `PostgresTaskRepository`.
- Add `PostgresSessionRepository`.
- Add `PostgresTraceRepository`.
- Add Docker Compose PostgreSQL service for local integration testing.
