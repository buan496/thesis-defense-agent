import hashlib
import json
from typing import Any

from app.notification_models import NotificationDelivery, NotificationEvent
from app.notification_router import NotificationRouter


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _stable_event_id(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def build_notification_events_from_alertmanager_payload(
    payload: dict[str, Any],
) -> list[NotificationEvent]:
    alerts = payload.get("alerts", [])
    if not isinstance(alerts, list):
        return []

    events: list[NotificationEvent] = []
    for alert in alerts:
        if not isinstance(alert, dict):
            continue

        labels = _safe_dict(alert.get("labels"))
        annotations = _safe_dict(alert.get("annotations"))
        alert_name = labels.get("alertname", "unknown-alert")
        severity = labels.get("severity", "unknown")
        status = alert.get("status", payload.get("status", "unknown"))
        fingerprint = alert.get("fingerprint")

        title = str(alert_name)
        summary = annotations.get("summary") or annotations.get("description")
        message = str(summary) if summary else f"{status}: {title}"

        events.append(
            NotificationEvent(
                event_id=str(fingerprint) if fingerprint else _stable_event_id(alert),
                source="alertmanager",
                status=str(status),
                severity=str(severity),
                title=title,
                message=message,
                labels=labels,
                annotations=annotations,
                receiver=payload.get("receiver"),
                group_key=payload.get("groupKey"),
                fingerprint=str(fingerprint) if fingerprint else None,
                starts_at=alert.get("startsAt"),
                ends_at=alert.get("endsAt"),
            )
        )

    return events


def route_alertmanager_payload(
    payload: dict[str, Any],
    router: NotificationRouter,
) -> dict[str, Any]:
    events = build_notification_events_from_alertmanager_payload(payload)
    deliveries: list[NotificationDelivery] = []

    for event in events:
        deliveries.extend(router.route(event))

    return {
        "notifications_created": len(events),
        "notification_deliveries": [
            delivery.to_dict() for delivery in deliveries
        ],
    }
