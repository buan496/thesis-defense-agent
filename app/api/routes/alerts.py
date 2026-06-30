import logging
from typing import Any

from fastapi import APIRouter, Body


router = APIRouter(prefix="/alerts", tags=["alerts"])
logger = logging.getLogger("app.api.alerts")


@router.post("/alertmanager")
def receive_alertmanager_webhook(
    payload: dict[str, Any] = Body(...),
) -> dict[str, object]:
    alerts = payload.get("alerts", [])
    if not isinstance(alerts, list):
        alerts = []

    alert_names = []
    for alert in alerts:
        if not isinstance(alert, dict):
            continue

        labels = alert.get("labels", {})
        if not isinstance(labels, dict):
            continue

        alert_name = labels.get("alertname")
        if isinstance(alert_name, str) and alert_name:
            alert_names.append(alert_name)

    result = {
        "status": "received",
        "receiver": payload.get("receiver"),
        "alert_status": payload.get("status"),
        "alerts_received": len(alerts),
        "alert_names": alert_names,
        "group_key": payload.get("groupKey"),
    }
    logger.info("alertmanager_webhook_received: %s", result)

    return result
