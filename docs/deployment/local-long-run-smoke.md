# Local Long-Run Smoke

## Purpose

This document defines the local Docker Compose long-run smoke workflow.

It is the local substitute for server long-run validation when the server is
temporarily unreachable. The goal is to verify that the local stack can remain
observable and healthy for a defined window before moving the same procedure to
a server.

## Prerequisites

Start the local stack first:

```powershell
docker compose up -d --build
```

If host port `8000` is already used by another local service, start the API on
another host port and pass the same URL to the smoke command:

```powershell
$env:API_PORT = "8001"
docker compose up -d --build

uv run python -m app.cli local-long-run-smoke `
  --api-url http://127.0.0.1:8001
```

Recommended baseline checks:

```powershell
docker compose ps
curl.exe -f http://127.0.0.1:8000/health
curl.exe -f http://127.0.0.1:8000/version
curl.exe -f http://127.0.0.1:9090/-/ready
curl.exe -f http://127.0.0.1:9093/-/ready
curl.exe -f http://127.0.0.1:6333/readyz
```

## One-Cycle Smoke

Run one immediate observation cycle:

```powershell
uv run python -m app.cli local-long-run-smoke `
  --markdown-output data/reports/local_long_run_smoke.md `
  --output data/reports/local_long_run_smoke.json
```

This probes:

```text
docker compose ps
API /health
API /version
API /metrics/prometheus
Prometheus /-/ready
Alertmanager /-/ready
Qdrant /readyz
```

## Timed Observation

Run a 10-minute local observation:

```powershell
uv run python -m app.cli local-long-run-smoke `
  --duration-seconds 600 `
  --interval-seconds 60 `
  --markdown-output data/reports/local_long_run_smoke_10m.md `
  --output data/reports/local_long_run_smoke_10m.json
```

Run a 1-hour local observation:

```powershell
uv run python -m app.cli local-long-run-smoke `
  --duration-seconds 3600 `
  --interval-seconds 300 `
  --markdown-output data/reports/local_long_run_smoke_1h.md `
  --output data/reports/local_long_run_smoke_1h.json
```

The command exits with code `1` if any cycle fails. Use `--allow-fail` only when
you want to keep collecting the report without failing the shell command.

## Acceptance Criteria

A local long-run smoke passes when:

- `docker compose ps` exits successfully.
- Compose status output does not contain `exited`, `dead`, `unhealthy`, or `restarting`.
- API health, version, and Prometheus metrics endpoints return 2xx.
- Prometheus and Alertmanager readiness endpoints return 2xx.
- Qdrant readiness endpoint returns 2xx.

## Evidence

Save generated evidence under `data/reports/`:

```text
data/reports/local_long_run_smoke.md
data/reports/local_long_run_smoke.json
```

`data/reports/` is ignored by Git, because reports may contain local runtime
paths, endpoint details, or operational output.

## Boundary

This is not a replacement for server validation. It validates the same health
and observability assumptions on Windows + Docker Desktop first, so the later
server step only needs to prove runtime environment stability rather than
redesigning the validation flow.

