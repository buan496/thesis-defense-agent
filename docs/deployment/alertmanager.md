# Alertmanager Local Routing

## Purpose

This project already exposes Prometheus metrics and alert rules. Alertmanager
adds the next operational layer:

```text
Prometheus alert rule
-> Alertmanager route
-> local webhook receiver
-> FastAPI alert intake endpoint
```

The current implementation is a local learning setup. It verifies routing,
grouping, repeat intervals, and webhook delivery without depending on email,
SMS, Feishu, WeCom, or a server-side notification provider.

## Files

```text
observability/prometheus/prometheus.yml
observability/prometheus/alert_rules.yml
observability/alertmanager/alertmanager.yml
docker-compose.yml
app/api/routes/alerts.py
app/alert_notification_adapter.py
app/notification_router.py
app/notification_channels.py
```

## Local Services

Start API, Prometheus, and Alertmanager:

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

The Alertmanager port can be changed through:

```text
ALERTMANAGER_PORT=9093
```

## Prometheus Alertmanager Target

Prometheus sends alerts to Alertmanager through:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - "alertmanager:9093"
```

## Alertmanager Route

The local route groups alerts by:

```text
alertname
service
severity
```

Default timing:

```text
group_wait: 10s
group_interval: 1m
repeat_interval: 30m
```

Critical alerts use a shorter repeat interval:

```text
repeat_interval: 10m
```

## Local Webhook Receiver

Alertmanager sends notifications to the API:

```text
POST http://api:8000/alerts/alertmanager
```

The API returns a summary:

```json
{
  "status": "received",
  "receiver": "local-webhook",
  "alert_status": "firing",
  "alerts_received": 1,
  "alert_names": ["ThesisDefenseAgentApiDown"],
  "group_key": "...",
  "notifications_created": 1,
  "notification_deliveries": [
    {
      "channel": "jsonl",
      "target": "primary-on-call",
      "success": true
    }
  ]
}
```

The receiver also converts Alertmanager alerts into local notification events
and writes delivery audit records through the JSONL notification channel.
Production notification providers remain outside this local learning stage.

## Trigger ApiDown Locally

Start the stack:

```powershell
docker compose up -d api alertmanager prometheus
```

Stop the API:

```powershell
docker compose stop api
```

Wait at least 1 minute, then check:

```text
Prometheus -> Alerts
Alertmanager -> Alerts
```

Restart the API:

```powershell
docker compose up -d api
```

## Direct Webhook Test

You can test the receiver without waiting for a real alert:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/alerts/alertmanager `
  -ContentType "application/json" `
  -Body '{
    "receiver": "local-webhook",
    "status": "firing",
    "groupKey": "{}:{alertname=\"ThesisDefenseAgentApiDown\"}",
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "ThesisDefenseAgentApiDown",
          "severity": "critical"
        }
      }
    ]
  }'
```

## Boundary

Completed:

```text
Alertmanager Docker Compose service
Prometheus -> Alertmanager routing
Alertmanager local webhook receiver
FastAPI alert intake endpoint
Alertmanager payload -> NotificationEvent adapter
severity-based NotificationRouter
local JSONL notification audit channel
offline config tests
API webhook tests
```

Not completed:

```text
email / Feishu / WeCom notification provider
Alertmanager silence management SOP
production on-call schedule
K8s Alertmanager deployment
log-based alerting
distributed tracing alerts
```
