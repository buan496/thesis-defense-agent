# Server Long-Run Preflight

## Purpose

This document defines the preflight checklist before leaving the project
running on a server for a long observation window.

It does not deploy the server by itself. It creates a repeatable evidence
index so the operator knows what to verify, what output to save, and what must
not be pasted into reports.

## Generate The Checklist

Docker Compose runtime:

```powershell
uv run python -m app.cli server-long-run-preflight `
  --environment server-docker `
  --runtime docker_compose `
  --operator "<your-name>" `
  --output data/reports/server_long_run_preflight.md
```

Kubernetes runtime:

```powershell
uv run python -m app.cli server-long-run-preflight `
  --environment server-k8s `
  --runtime kubernetes `
  --operator "<your-name>" `
  --output data/reports/server_long_run_preflight_k8s.md
```

The generated Markdown report is operational evidence and should normally stay
under `data/reports/`, which is ignored by Git.

## Checklist Sections

The preflight report covers:

```text
release baseline
secret boundary
quality gate baseline
runtime data boundary
Docker Compose or Kubernetes runtime checks
Qdrant scheduler checks
observability baseline
long-run observation window
rollback and data recovery
```

## Required Evidence

Before starting a server long-run, collect sanitized evidence for:

```text
git status and release commit
secret boundary confirmation
pytest / CI status
runtime data inventory
service health checks
Prometheus / Alertmanager readiness
Qdrant readiness
Qdrant snapshot drill or CronJob schedule evidence
log tail samples
rollback command record
```

Never paste:

```text
real API keys
passwords
kubeconfig content
private server endpoints
raw .env contents
complete sensitive task/session/trace records
```

## Long-Run Window

For the first server experiment, define the window before starting:

```text
6 hours: first smoke-level long-run
24 hours: stronger single-day stability evidence
7 days: later production-style soak, not required for the current learning step
```

For each window, record:

```text
start timestamp
release commit
runtime mode
health samples
logs tail samples
scheduled backup / snapshot status
incident notes
final pass/fail decision
```

## Current Boundary

Completed locally:

```text
Docker Compose runtime checks
K8s kind smoke run
Qdrant StatefulSet runtime validation
Qdrant CronJob manual Job smoke
Qdrant CronJob one-cycle natural schedule observe
Qdrant CronJob multi-cycle natural schedule observe
server-long-run-preflight report generator
```

Not completed:

```text
server multi-hour / multi-day long-run evidence
reverse proxy / HTTPS
external notification provider
centralized log collection
production secret management
```
