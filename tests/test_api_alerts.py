from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_alertmanager_webhook_returns_received_summary():
    response = client.post(
        "/alerts/alertmanager",
        json={
            "receiver": "local-webhook",
            "status": "firing",
            "groupKey": "{}:{alertname=\"ThesisDefenseAgentApiDown\"}",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "ThesisDefenseAgentApiDown",
                        "severity": "critical",
                    },
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "received"
    assert body["receiver"] == "local-webhook"
    assert body["alert_status"] == "firing"
    assert body["alerts_received"] == 1
    assert body["alert_names"] == ["ThesisDefenseAgentApiDown"]
    assert body["group_key"] == "{}:{alertname=\"ThesisDefenseAgentApiDown\"}"
    assert body["notifications_created"] == 1
    assert len(body["notification_deliveries"]) == 1
    assert body["notification_deliveries"][0]["target"] == "primary-on-call"
    assert body["notification_deliveries"][0]["success"] is True


def test_alertmanager_webhook_tolerates_missing_alerts():
    response = client.post(
        "/alerts/alertmanager",
        json={
            "receiver": "local-webhook",
            "status": "resolved",
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "received"
    assert body["receiver"] == "local-webhook"
    assert body["alert_status"] == "resolved"
    assert body["alerts_received"] == 0
    assert body["alert_names"] == []
    assert body["notifications_created"] == 0
    assert body["notification_deliveries"] == []
