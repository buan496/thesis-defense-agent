# Logging and Retention

## Purpose

This project already emits structured API request logs and Agent trace files.
This document defines how to view, filter, and retain logs in the local Docker
and server-style Compose runtime.

The current goal is operational clarity:

```text
Where are logs?
How do I query recent failures?
How long are container logs retained?
What is not centralized yet?
```

## Log Sources

### API Request Logs

FastAPI request logs are emitted by:

```text
app/api/middleware.py
logger name: app.api.request
event: api_request
```

Each request log is JSON text with:

```json
{
  "event": "api_request",
  "method": "GET",
  "path": "/health",
  "status_code": 200,
  "duration_ms": 12.34
}
```

### Agent Trace Logs

Agent traces are JSONL records saved under:

```text
data/traces/
```

These are not Docker stdout logs. They are application audit artifacts and are
queried through the existing trace replay/analyze commands.

### Task and Session Artifacts

Task/session artifacts are saved under:

```text
data/defense_tasks/
data/agent_sessions/
data/task_reports/
```

These are state/audit files, not process logs.

## Docker Log Retention

`docker-compose.yml` uses the Docker `json-file` logging driver with rotation
for all runtime services:

```yaml
logging:
  driver: json-file
  options:
    max-size: "${DOCKER_LOG_MAX_SIZE:-10m}"
    max-file: "${DOCKER_LOG_MAX_FILE:-5}"
```

Default retention:

```text
max-size: 10m
max-file: 5
```

This means each container keeps up to roughly 5 rotated JSON log files of 10 MB
each.

Override in `.env`:

```env
DOCKER_LOG_MAX_SIZE=20m
DOCKER_LOG_MAX_FILE=10
```

## Query Commands

Show current containers:

```powershell
docker compose ps
```

Follow API logs:

```powershell
docker compose logs -f api
```

Show recent API logs:

```powershell
docker compose logs --tail 100 api
```

Show Prometheus logs:

```powershell
docker compose logs --tail 100 prometheus
```

Filter API request logs by path:

```powershell
docker compose logs api |
  Select-String '"event": "api_request"' |
  Select-String '"path": "/tasks"'
```

Filter likely server errors:

```powershell
docker compose logs api |
  Select-String '"status_code": 5'
```

Show logs since a time window:

```powershell
docker compose logs --since 30m api
```

## Trace Query Commands

Analyze Agent traces:

```powershell
uv run python -m app.cli analyze-traces
```

Replay the latest Agent trace:

```powershell
uv run python -m app.cli replay-agent-trace
```

Analyze task trace:

```powershell
uv run python -m app.cli analyze-task --task-id <TASK_ID>
```

Export task report:

```powershell
uv run python -m app.cli export-task-markdown --task-id <TASK_ID>
```

## Current Boundary

Completed:

```text
structured API request logs
Docker Compose log rotation
basic Docker log query commands
Agent trace JSONL files
trace analyze/replay commands
task trace analysis
task Markdown export
```

Not completed:

```text
centralized log storage
Loki / Elasticsearch
log-based alerting
correlation IDs across request -> task -> tool call
PII redaction policy
long-term archive retention
```

## Next Step

After local log retention is documented, the next observability step is either:

```text
correlation IDs
or centralized log collection
```

Correlation IDs are recommended first because they improve every later logging
backend.
