# Runtime Repository Integration Design

## Purpose

This document defines how runtime services should move from direct JSON / JSONL
file storage to the repository abstraction introduced by `RepositoryBundle`.

The goal is not to immediately switch the whole application to PostgreSQL. The
goal is to define a safe migration path that preserves the current local JSON
workflow while making PostgreSQL selectable through configuration.

## Current State

The project currently has two storage paths:

```text
JSON / JSONL runtime path
-> task_store.py
-> session_store.py
-> trace JSONL helpers
-> current CLI and API runtime behavior
```

```text
Repository path
-> app.repository_factory.create_repositories()
-> JsonTaskRepository / JsonSessionRepository / JsonlTraceRepository
-> PostgresTaskRepository / PostgresSessionRepository / PostgresTraceRepository
```

The repository path can construct both JSON and PostgreSQL adapters, and the
JSON-to-PostgreSQL import command can copy existing local records into
PostgreSQL. Task workflow runtime now uses the task repository abstraction.
Chat session runtime now uses the session repository abstraction. Trace runtime
integration remains a later step.

## Target Direction

Runtime services should depend on repository interfaces instead of directly
calling storage files.

Target dependency direction:

```text
CLI / API
-> service layer
-> RepositoryBundle
-> concrete repository selected by STORAGE_BACKEND
```

Allowed concrete backends:

```text
STORAGE_BACKEND=json
STORAGE_BACKEND=postgres
```

Default behavior remains:

```text
STORAGE_BACKEND=json
```

## Integration Boundary

Repository injection should happen at service entry points, not inside low-level
domain models.

Keep these modules storage-agnostic:

```text
app.task_models
app.session_models
app.agent_models
app.task_executor
app.agent
```

Migrate these modules gradually:

```text
app.task_service
app.cli
app.api
session chat command handlers
trace append/read entry points
```

## RepositoryBundle Usage

`RepositoryBundle` is the runtime dependency container for storage:

```text
RepositoryBundle.task_repository
RepositoryBundle.session_repository
RepositoryBundle.trace_repository
RepositoryBundle.storage_backend
```

Runtime callers should create it once near the boundary:

```text
create_repositories(
    storage_backend=STORAGE_BACKEND,
    database_url=DATABASE_URL,
)
```

Do not call `create_repositories()` inside every small function. That would make
tests harder and hide database connection behavior.

## Migration Order

### Step 1: Task Runtime Pilot

Use task workflow as the first integration target because it already has a clear
state model and repository interface.

Scope:

```text
create-task
start-task-step
execute-task-step
submit-task-answer
submit-follow-up-answer
resume-task
analyze-task
export-task-markdown
show-task
```

Expected change:

```text
Task service accepts task_repository dependency.
CLI creates RepositoryBundle once.
Task CLI commands use repositories.task_repository.
```

Status:

```text
Implemented.
Task service functions accept task_repository.
Task CLI commands create the task repository through RepositoryBundle.
Default JSON behavior is preserved through JsonTaskRepository.
```

Rollback:

```text
Set STORAGE_BACKEND=json.
The same repository interface writes to local JSON again.
```

### Step 2: Session Runtime

Session commands should use `session_repository` after task runtime is stable.

Scope:

```text
chat
session creation
session resume
session metadata updates
memory-related session reads
```

Status:

```text
Implemented for chat runtime.
run_agent_session accepts session_repository.
The chat CLI creates the session repository through RepositoryBundle.
Default JSON behavior is preserved through JsonSessionRepository.
```

Rollback:

```text
Set STORAGE_BACKEND=json.
Existing JSON session files remain readable.
```

### Step 3: Trace Runtime

Trace runtime should move last because trace writing is cross-cutting and should
not block task/session migration.

Scope:

```text
Agent trace append
Sub-Agent trace append
trace analysis
trace replay
tool audit
```

Rollback:

```text
Set STORAGE_BACKEND=json.
Trace writes return to JSONL.
```

## Configuration Strategy

Required environment variables:

```text
STORAGE_BACKEND=json|postgres
DATABASE_URL=...
```

Rules:

```text
If STORAGE_BACKEND=json:
  DATABASE_URL is optional.

If STORAGE_BACKEND=postgres:
  DATABASE_URL is required.
  PostgreSQL migrations must have already run.
```

CLI commands must never print the full `DATABASE_URL`.

## Rollback Strategy

Runtime migration must preserve an immediate rollback path:

```text
1. Keep JSON as the default backend.
2. Import local JSON records into PostgreSQL explicitly.
3. Run smoke tests with STORAGE_BACKEND=postgres.
4. If anything fails, switch STORAGE_BACKEND=json.
5. Do not delete JSON source files during migration.
```

This keeps local development and CI stable while PostgreSQL support matures.

## Testing Strategy

Each integration step should include:

```text
fake repository tests
JSON backend behavior tests
PostgreSQL repository construction tests
CLI output tests
error-path tests for missing DATABASE_URL
```

Do not require a real PostgreSQL server for normal unit tests. Real database
checks should remain explicit integration tests or local manual checks.

## Risks

### Risk: Hidden Direct File Access

Some commands may still call `load_defense_task()` or `save_defense_task()`
directly after repository integration starts.

Mitigation:

```text
Search call sites before each migration step.
Move one command group at a time.
Add tests that inject fake repositories.
```

### Risk: Partial Backend Switching

Task records may be written to PostgreSQL while traces still go to JSONL.

Mitigation:

```text
Document mixed-backend behavior.
Move trace runtime only after task and session runtime are stable.
```

### Risk: PostgreSQL Schema Drift

Runtime may expect fields that migrations have not created.

Mitigation:

```text
Always run migration runner before enabling STORAGE_BACKEND=postgres.
Keep payload JSONB as the source of truth.
Use denormalized columns only for query convenience.
```

## Acceptance Criteria

The runtime repository integration phase is complete when:

```text
Task CLI can run with STORAGE_BACKEND=json.
Task CLI can run with STORAGE_BACKEND=postgres after migrations.
Session runtime can run through repository injection.
Trace runtime can write through repository injection.
JSON remains the default backend.
Full test suite passes without a real PostgreSQL server.
Docs clearly state rollback and backend selection behavior.
```

## Next Implementation Step

Start with Task runtime pilot:

```text
Refactor task service entry points to accept a task_repository dependency.
Keep JSON behavior as default.
Use fake repositories in tests.
Do not migrate session or trace runtime in the same PR.
```
