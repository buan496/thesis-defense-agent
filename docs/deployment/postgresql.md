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

## Local Docker Compose Service

The local Docker Compose stack now includes a PostgreSQL service for integration
testing and future repository implementation work.

```powershell
docker compose up -d postgres
docker compose ps postgres
docker compose exec postgres pg_isready -U thesis_agent -d thesis_defense_agent
docker compose down
```

Default local environment variables:

```env
STORAGE_BACKEND=json
DATABASE_URL=postgresql://thesis_agent:thesis_agent_dev_password@localhost:5432/thesis_defense_agent
POSTGRES_DB=thesis_defense_agent
POSTGRES_USER=thesis_agent
POSTGRES_PASSWORD=thesis_agent_dev_password
POSTGRES_PORT=5432
```

`STORAGE_BACKEND=json` remains the default. The application still uses JSON /
JSONL storage unless future code explicitly selects PostgreSQL repositories.
The Compose database is a preparation step for schema migrations and repository
implementation, not a behavior change for the current API.

## Migration Files

PostgreSQL migration SQL files live in:

```text
db/migrations/postgres/
```

Current migration:

```text
001_initial_schema.sql
```

It defines:

- `schema_migrations`
- `defense_tasks`
- `agent_sessions`
- `trace_records`
- `feedback_records`
- `benchmark_candidates`

The migration is idempotent and uses `CREATE TABLE IF NOT EXISTS` / `CREATE
INDEX IF NOT EXISTS` so it can be used for local integration testing before a
full migration runner is introduced.

To inspect migration metadata without executing SQL:

```powershell
uv run python -m app.cli postgres-migrations
```

This command prints version, name, path, and checksum. It does not connect to
PostgreSQL and does not modify the database.

## Running Migrations

The migration runner uses `psycopg` and applies only pending migrations. It
checks `schema_migrations` first:

- matching version and checksum: skip
- matching version with different checksum: fail
- missing version: execute SQL and record version / name / checksum

Run against the local Compose database:

```powershell
docker compose up -d postgres

uv run python -m app.cli run-postgres-migrations `
  --database-url "postgresql://thesis_agent:thesis_agent_dev_password@localhost:5432/thesis_defense_agent"
```

Or use `.env`:

```powershell
uv run python -m app.cli run-postgres-migrations
```

The CLI intentionally prints only `DATABASE URL: configured`; it does not echo
the full connection string.

Current boundary: the runner prepares the database schema only. The API still
uses JSON / JSONL repositories until PostgreSQL repository implementations are
added and selected through configuration.

## Task Repository

`PostgresTaskRepository` lives in:

```text
app/postgres_task_repository.py
```

It implements the same `save(task)` and `load(task_id)` behavior as the
`TaskRepository` protocol:

- validates `task_id`
- serializes the full `DefenseTask` payload to PostgreSQL `JSONB`
- writes denormalized query fields: `task_id`, `topic`, `status`,
  `current_step_id`, `created_at`, `updated_at`
- uses `INSERT ... ON CONFLICT (task_id) DO UPDATE`
- loads a `DefenseTask` back from the `payload` column
- commits on success and rolls back on save failure

Current boundary: `PostgresTaskRepository` is implemented and tested, but the
API service still uses the existing JSON task store unless a future repository
factory selects PostgreSQL through configuration.

## Session Repository

`PostgresSessionRepository` lives in:

```text
app/postgres_session_repository.py
```

It implements the same `save(session)` and `load(session_id)` behavior as the
`SessionRepository` protocol:

- validates `session_id`
- serializes the full `AgentSession` payload to PostgreSQL `JSONB`
- writes `session_id`, `payload`, and `created_at`
- uses `INSERT ... ON CONFLICT (session_id) DO UPDATE`
- updates `updated_at` with `now()` on conflict
- loads an `AgentSession` back from the `payload` column
- commits on success and rolls back on save failure

Current boundary: `PostgresSessionRepository` is implemented and tested, but the
API service still uses the existing JSON session store unless a future
repository factory selects PostgreSQL through configuration.

## Trace Repository

`PostgresTraceRepository` lives in:

```text
app/postgres_trace_repository.py
```

It implements the same `append(record)` and `load_all()` behavior as the
`TraceRepository` protocol:

- appends trace records to `trace_records`
- stores the full original trace as PostgreSQL `JSONB`
- fills query columns: `source_type`, `source_id`, `event_type`, `success`
- infers common Agent and Sub-Agent trace fields when explicit metadata is not
  present
- returns `postgres:trace_records:<id>` for appended records
- loads payloads back in insertion order
- commits on success and rolls back on append failure

Current boundary: `PostgresTraceRepository` is implemented and tested, but the
application still writes JSONL traces unless a future repository factory selects
PostgreSQL through configuration.

## Repository Factory

Repository selection lives in:

```text
app/repository_factory.py
```

It creates a `RepositoryBundle` containing:

- `task_repository`
- `session_repository`
- `trace_repository`
- `storage_backend`

Supported backends:

```text
json
postgres
```

Default behavior remains:

```env
STORAGE_BACKEND=json
```

Inspect the selected repository implementations without connecting to
PostgreSQL:

```powershell
uv run python -m app.cli show-repositories
uv run python -m app.cli show-repositories --storage-backend postgres --database-url "postgresql://..."
```

The CLI prints repository class names only. It does not print the full
`DATABASE_URL`.

Current boundary: the factory can construct JSON or PostgreSQL repositories, but
the API service still uses the existing JSON-oriented service functions until a
future integration step wires repositories into runtime services.

## JSON-to-PostgreSQL Import

Local JSON / JSONL storage can be imported into PostgreSQL repositories through:

```text
app/postgres_json_importer.py
```

CLI:

```powershell
uv run python -m app.cli import-json-to-postgres `
  --database-url "postgresql://thesis_agent:thesis_agent_dev_password@localhost:5432/thesis_defense_agent"
```

Preview without writing:

```powershell
uv run python -m app.cli import-json-to-postgres `
  --database-url "postgresql://thesis_agent:thesis_agent_dev_password@localhost:5432/thesis_defense_agent" `
  --dry-run
```

Optional source overrides:

```powershell
uv run python -m app.cli import-json-to-postgres `
  --task-directory data/defense_tasks `
  --session-directory data/agent_sessions `
  --trace-file data/traces/agent_trace.jsonl
```

Optional section skips:

```powershell
uv run python -m app.cli import-json-to-postgres `
  --skip-tasks `
  --skip-sessions `
  --skip-traces
```

The CLI prints counts only and intentionally does not print the full
`DATABASE_URL`.

Recommended order for a local PostgreSQL import:

```powershell
docker compose up -d postgres
uv run python -m app.cli run-postgres-migrations
uv run python -m app.cli import-json-to-postgres --dry-run
uv run python -m app.cli import-json-to-postgres
```

Current boundary: import scripts are explicit operational tools. They do not
change runtime storage behavior; `STORAGE_BACKEND=json` remains the default.

## Task Runtime Repository Pilot

Task workflow commands now create a task repository through the repository
factory and inject it into the task service layer.

Covered commands:

```text
create-task
start-task-step
complete-task-step
execute-task-step
submit-task-answer
submit-follow-up-answer
resume-task
analyze-task
export-task-markdown
export-task-memory
show-task
```

Default local behavior still uses JSON:

```env
STORAGE_BACKEND=json
```

PostgreSQL task runtime can be selected only after migrations and import have
been handled explicitly:

```powershell
uv run python -m app.cli run-postgres-migrations
uv run python -m app.cli import-json-to-postgres --dry-run
uv run python -m app.cli import-json-to-postgres
```

Current boundary: task runtime is the first repository-backed runtime pilot.
Session runtime and trace runtime still have separate migration steps.

## Session Runtime Repository Integration

Chat session runtime now creates a session repository through the repository
factory and injects it into `run_agent_session`.

Covered behavior:

```text
chat session creation
chat session resume
session metadata persistence
session compaction persistence
```

Default local behavior still uses JSON:

```env
STORAGE_BACKEND=json
```

Current boundary: task runtime and chat session runtime are repository-backed.
Trace runtime still writes through the existing JSONL path until its dedicated
migration step is implemented.

## Why Not Replace JSON Immediately

Replacing storage directly would mix two changes:

- changing persistence semantics
- changing application behavior

The project should keep those concerns separate. The repository abstraction lets tests verify storage behavior before the service layer is switched.

## Next Steps

- Wire repository factory into runtime services after import / rollback
  strategy is defined.
