import os
from collections.abc import Iterable

from app.notification_channels import JsonlNotificationChannel, NotificationChannel
from app.notification_models import NotificationDelivery, NotificationEvent


DEFAULT_NOTIFICATION_JSONL_PATH = os.getenv(
    "NOTIFICATION_JSONL_PATH",
    "data/notifications/notifications.jsonl",
)

DEFAULT_SEVERITY_TARGETS = {
    "critical": ["primary-on-call"],
    "warning": ["platform-triage"],
    "info": ["ops-log"],
    "unknown": ["ops-log"],
}


class NotificationRouter:
    def __init__(
        self,
        channels: Iterable[NotificationChannel],
        severity_targets: dict[str, list[str]] | None = None,
        deduplicate: bool = True,
    ):
        self.channels = list(channels)
        self.severity_targets = severity_targets or DEFAULT_SEVERITY_TARGETS
        self.deduplicate = deduplicate
        self._delivered_keys: set[str] = set()

    def targets_for(self, event: NotificationEvent) -> list[str]:
        severity = event.severity.lower() if event.severity else "unknown"
        return self.severity_targets.get(
            severity,
            self.severity_targets["unknown"],
        )

    def route(self, event: NotificationEvent) -> list[NotificationDelivery]:
        if self.deduplicate and event.dedupe_key in self._delivered_keys:
            return [
                NotificationDelivery(
                    event_id=event.event_id,
                    channel="router",
                    target="dedupe",
                    success=True,
                    message="duplicate notification skipped",
                )
            ]

        deliveries: list[NotificationDelivery] = []
        for target in self.targets_for(event):
            for channel in self.channels:
                try:
                    deliveries.append(channel.send(event, target))
                except Exception as error:
                    deliveries.append(
                        NotificationDelivery(
                            event_id=event.event_id,
                            channel=channel.name,
                            target=target,
                            success=False,
                            message=str(error),
                            error_type=type(error).__name__,
                        )
                    )

        if self.deduplicate:
            self._delivered_keys.add(event.dedupe_key)

        return deliveries


def build_default_notification_router() -> NotificationRouter:
    return NotificationRouter(
        channels=[
            JsonlNotificationChannel(DEFAULT_NOTIFICATION_JSONL_PATH),
        ],
    )
