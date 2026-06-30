from app.alert_notification_adapter import (
    build_notification_events_from_alertmanager_payload,
    route_alertmanager_payload,
)
from app.notification_router import NotificationRouter


class RecordingChannel:
    name = "recording"

    def __init__(self):
        self.records = []

    def send(self, event, target):
        from app.notification_models import NotificationDelivery

        self.records.append((event, target))
        return NotificationDelivery(
            event_id=event.event_id,
            channel=self.name,
            target=target,
            success=True,
            message="recorded",
        )


def test_build_notification_events_from_alertmanager_payload():
    events = build_notification_events_from_alertmanager_payload(
        {
            "receiver": "local-webhook",
            "status": "firing",
            "groupKey": "group-1",
            "alerts": [
                {
                    "status": "firing",
                    "fingerprint": "fp-1",
                    "labels": {
                        "alertname": "ThesisDefenseAgentApiDown",
                        "severity": "critical",
                    },
                    "annotations": {
                        "summary": "API is not reachable",
                    },
                    "startsAt": "2026-06-30T00:00:00Z",
                }
            ],
        }
    )

    assert len(events) == 1
    assert events[0].event_id == "fp-1"
    assert events[0].source == "alertmanager"
    assert events[0].status == "firing"
    assert events[0].severity == "critical"
    assert events[0].title == "ThesisDefenseAgentApiDown"
    assert events[0].message == "API is not reachable"
    assert events[0].receiver == "local-webhook"
    assert events[0].group_key == "group-1"


def test_build_notification_events_ignores_invalid_alerts():
    events = build_notification_events_from_alertmanager_payload(
        {
            "alerts": [
                "not-a-dict",
                {
                    "labels": "not-a-dict",
                    "annotations": "not-a-dict",
                },
            ]
        }
    )

    assert len(events) == 1
    assert events[0].title == "unknown-alert"
    assert events[0].severity == "unknown"


def test_route_alertmanager_payload_returns_delivery_summary():
    channel = RecordingChannel()
    router = NotificationRouter(
        channels=[channel],
        severity_targets={
            "critical": ["primary-on-call"],
            "unknown": ["ops-log"],
        },
    )

    result = route_alertmanager_payload(
        {
            "alerts": [
                {
                    "status": "firing",
                    "fingerprint": "fp-2",
                    "labels": {
                        "alertname": "ApiDown",
                        "severity": "critical",
                    },
                }
            ]
        },
        router=router,
    )

    assert result["notifications_created"] == 1
    assert result["notification_deliveries"][0]["channel"] == "recording"
    assert result["notification_deliveries"][0]["target"] == "primary-on-call"
    assert channel.records[0][0].title == "ApiDown"


def test_route_alertmanager_payload_handles_empty_alerts():
    channel = RecordingChannel()
    router = NotificationRouter(channels=[channel])

    result = route_alertmanager_payload({"alerts": []}, router=router)

    assert result["notifications_created"] == 0
    assert result["notification_deliveries"] == []
