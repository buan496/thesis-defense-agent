from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


def current_utc_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass
class NotificationEvent:
    event_id: str
    source: str
    status: str
    severity: str
    title: str
    message: str
    labels: dict[str, Any] = field(default_factory=dict)
    annotations: dict[str, Any] = field(default_factory=dict)
    receiver: str | None = None
    group_key: str | None = None
    fingerprint: str | None = None
    starts_at: str | None = None
    ends_at: str | None = None
    created_at: str = field(default_factory=current_utc_iso)

    @property
    def dedupe_key(self) -> str:
        if self.fingerprint:
            return f"{self.source}:{self.fingerprint}:{self.status}"

        alert_name = self.labels.get("alertname", self.title)
        instance = self.labels.get("instance", "")
        return f"{self.source}:{alert_name}:{instance}:{self.status}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NotificationDelivery:
    event_id: str
    channel: str
    target: str
    success: bool
    message: str
    error_type: str | None = None
    delivered_at: str = field(default_factory=current_utc_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
