# Prometheus Alerts

## Purpose

Prometheus already scrapes the FastAPI service metrics endpoint:

```text
GET /metrics/prometheus
```

This document defines the first alerting layer for the local learning
deployment. The goal is not full incident management yet; the goal is to move
from "metrics can be viewed" to "common failures can be detected".

## Files

```text
observability/prometheus/prometheus.yml
observability/prometheus/alert_rules.yml
observability/alertmanager/alertmanager.yml
docker-compose.yml
```

`prometheus.yml` loads the rule file:

```yaml
rule_files:
  - /etc/prometheus/alert_rules.yml
```

`docker-compose.yml` mounts both files into the Prometheus container.

Prometheus also routes firing alerts to Alertmanager:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - "alertmanager:9093"
```

## Alerts

### ThesisDefenseAgentApiDown

Expression:

```promql
up{job="thesis-defense-agent-api"} == 0
```

Meaning:

```text
Prometheus cannot scrape the API target for more than 1 minute.
```

Severity:

```text
critical
```

### ThesisDefenseAgentHigh5xxRate

Expression:

```promql
(
  sum(rate(thesis_defense_api_request_status_total{status_code=~"5.."}[5m]))
  /
  clamp_min(sum(rate(thesis_defense_api_requests_total[5m])), 1)
) > 0.05
```

Meaning:

```text
More than 5% of API requests returned 5xx responses during the last 5 minutes.
```

Severity:

```text
warning
```

### ThesisDefenseAgentHighAverageLatency

Expression:

```promql
thesis_defense_api_request_duration_ms_average > 2000
```

Meaning:

```text
Average API request latency is above 2000 ms for more than 5 minutes.
```

Severity:

```text
warning
```

## Local Validation

Start the API, Alertmanager, and Prometheus:

```powershell
docker compose up -d api alertmanager prometheus
```

Open Prometheus:

```text
http://127.0.0.1:9090
```

Open Alertmanager:

```text
http://127.0.0.1:9093
```

Check loaded targets:

```text
Status -> Targets
```

Check loaded rules:

```text
Alerts
```

Stop the API to trigger the down alert:

```powershell
docker compose stop api
```

Wait at least 1 minute, then check:

```text
ThesisDefenseAgentApiDown
```

Restart the API:

```powershell
docker compose up -d api
```

## Current Boundary

Completed:

```text
Prometheus scrape config
Prometheus text metrics endpoint
API down alert
5xx rate alert
average latency alert
Compose rule file mount
Prometheus to Alertmanager routing
local Alertmanager webhook receiver
offline config tests
```

Not completed:

```text
external notification channels
on-call routing
log-based alerts
distributed tracing alerts
production SLOs
```

## Next Step

After local Alertmanager routing is stable, the next operations step is K8s
manifest preparation or external notification provider integration.
