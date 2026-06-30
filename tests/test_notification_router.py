from app.notification_channels import JsonlNotificationChannel
from app.notification_models import NotificationEvent
from app.notification_router import NotificationRouter


def test_notification_router_routes_by_severity_to_jsonl(tmp_path):
    notification_path = tmp_path / "notifications.jsonl"
    router = NotificationRouter(
        channels=[JsonlNotificationChannel(str(notification_path))],
        severity_targets={
            "critical": ["primary-on-call"],
            "unknown": ["ops-log"],
        },
    )
    event = NotificationEvent(
        event_id="evt-1",
        source="alertmanager",
        status="firing",
        severity="critical",
        title="ApiDown",
        message="API is down",
        labels={"alertname": "ApiDown", "severity": "critical"},
    )

    deliveries = router.route(event)

    assert len(deliveries) == 1
    assert deliveries[0].success is True
    assert deliveries[0].channel == "jsonl"
    assert deliveries[0].target == "primary-on-call"
    assert "ApiDown" in notification_path.read_text(encoding="utf-8")


def test_notification_router_uses_unknown_target_for_unknown_severity(tmp_path):
    notification_path = tmp_path / "notifications.jsonl"
    router = NotificationRouter(
        channels=[JsonlNotificationChannel(str(notification_path))],
        severity_targets={
            "critical": ["primary-on-call"],
            "unknown": ["ops-log"],
        },
    )
    event = NotificationEvent(
        event_id="evt-2",
        source="alertmanager",
        status="firing",
        severity="minor",
        title="MinorAlert",
        message="minor alert",
    )

    deliveries = router.route(event)

    assert deliveries[0].target == "ops-log"


def test_notification_router_deduplicates_events(tmp_path):
    notification_path = tmp_path / "notifications.jsonl"
    router = NotificationRouter(
        channels=[JsonlNotificationChannel(str(notification_path))],
        severity_targets={
            "critical": ["primary-on-call"],
            "unknown": ["ops-log"],
        },
    )
    event = NotificationEvent(
        event_id="evt-3",
        source="alertmanager",
        status="firing",
        severity="critical",
        title="ApiDown",
        message="API is down",
        fingerprint="same-fingerprint",
    )

    first = router.route(event)
    second = router.route(event)

    assert first[0].channel == "jsonl"
    assert second[0].channel == "router"
    assert second[0].target == "dedupe"
    assert second[0].message == "duplicate notification skipped"


def test_notification_router_reports_channel_error():
    class BrokenChannel:
        name = "broken"

        def send(self, event, target):
            raise RuntimeError("send failed")

    router = NotificationRouter(
        channels=[BrokenChannel()],
        severity_targets={
            "critical": ["primary-on-call"],
            "unknown": ["ops-log"],
        },
    )
    event = NotificationEvent(
        event_id="evt-4",
        source="alertmanager",
        status="firing",
        severity="critical",
        title="ApiDown",
        message="API is down",
    )

    deliveries = router.route(event)

    assert deliveries[0].success is False
    assert deliveries[0].channel == "broken"
    assert deliveries[0].error_type == "RuntimeError"
