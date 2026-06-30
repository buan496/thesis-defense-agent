import json
import logging
from pathlib import Path
from typing import Protocol

from app.notification_models import NotificationDelivery, NotificationEvent


logger = logging.getLogger(__name__)


class NotificationChannel(Protocol):
    name: str

    def send(
        self,
        event: NotificationEvent,
        target: str,
    ) -> NotificationDelivery:
        ...


class ConsoleNotificationChannel:
    name = "console"

    def send(
        self,
        event: NotificationEvent,
        target: str,
    ) -> NotificationDelivery:
        logger.warning(
            "notification target=%s severity=%s title=%s",
            target,
            event.severity,
            event.title,
        )
        return NotificationDelivery(
            event_id=event.event_id,
            channel=self.name,
            target=target,
            success=True,
            message="logged to console",
        )


class JsonlNotificationChannel:
    name = "jsonl"

    def __init__(self, file_path: str):
        self.file_path = file_path

    def send(
        self,
        event: NotificationEvent,
        target: str,
    ) -> NotificationDelivery:
        path = Path(self.file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "target": target,
            "event": event.to_dict(),
        }

        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

        return NotificationDelivery(
            event_id=event.event_id,
            channel=self.name,
            target=target,
            success=True,
            message=f"written to {self.file_path}",
        )
