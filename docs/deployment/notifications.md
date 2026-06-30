# External Notification Routing

## Purpose

Alertmanager local routing already proves that alerts can reach the API.
This stage adds an internal notification layer:

```text
Alertmanager webhook
-> NotificationEvent
-> NotificationRouter
-> NotificationChannel
-> local JSONL audit record
```

The implementation is still a local learning version. It does not require
Feishu, WeCom, email, SMS, PagerDuty, or any secret-bearing external provider.

## Files

```text
app/notification_models.py
app/notification_channels.py
app/notification_router.py
app/alert_notification_adapter.py
app/api/routes/alerts.py
tests/test_notification_router.py
tests/test_alert_notification_adapter.py
docs/deployment/notifications.md
```

## Concepts

### NotificationEvent

Normalized alert event used by the application. It contains:

```text
event_id
source
status
severity
title
message
labels
annotations
receiver
group_key
fingerprint
```

### NotificationRouter

Routes events by severity:

```text
critical -> primary-on-call
warning  -> platform-triage
info     -> ops-log
unknown  -> ops-log
```

The router also performs in-memory deduplication by event fingerprint or stable
event identity. This avoids repeatedly sending the same notification inside one
API process.

### NotificationChannel

Current local channels:

```text
ConsoleNotificationChannel
JsonlNotificationChannel
```

The API uses `JsonlNotificationChannel` by default, so every routed alert is
written as an audit line.

## Runtime Output

Default path:

```text
data/notifications/notifications.jsonl
```

Override through:

```text
NOTIFICATION_JSONL_PATH=data/notifications/notifications.jsonl
```

The directory is ignored by Git because it is runtime data.

## Alertmanager Webhook Response

`POST /alerts/alertmanager` still returns the original intake summary, and now
also returns notification routing information:

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
      "event_id": "...",
      "channel": "jsonl",
      "target": "primary-on-call",
      "success": true,
      "message": "written to data/notifications/notifications.jsonl",
      "error_type": null,
      "delivered_at": "..."
    }
  ]
}
```

## Direct Test

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
        "fingerprint": "demo-fingerprint",
        "labels": {
          "alertname": "ThesisDefenseAgentApiDown",
          "severity": "critical"
        },
        "annotations": {
          "summary": "API is unreachable"
        }
      }
    ]
  }'
```

Check the audit file:

```powershell
Get-Content data\notifications\notifications.jsonl -Tail 5
```

## Boundary

Completed:

```text
Alertmanager payload -> NotificationEvent conversion
severity-based routing
local JSONL notification channel
console notification channel
in-memory deduplication
delivery result reporting
offline unit tests
FastAPI alert route integration
```

Not completed:

```text
Feishu / WeCom / email provider
production on-call schedule
cross-process deduplication
notification silence management
notification escalation policy
secret management for external providers
```
