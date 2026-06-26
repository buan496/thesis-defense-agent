import json
import logging

from fastapi.testclient import TestClient

from app.api.main import app
from app.api.metrics import reset_api_metrics


client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "thesis-defense-agent",
    }


def test_version_returns_service_and_version():
    response = client.get("/version")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "thesis-defense-agent"
    assert body["version"]


def test_rag_status_returns_file_flags():
    response = client.get("/rag/status")

    assert response.status_code == 200
    body = response.json()
    assert body["vector_store_path"] == "data\\vector_store.json" or body[
        "vector_store_path"
    ] == "data/vector_store.json"
    assert isinstance(body["vector_store_exists"], bool)
    assert body["metadata_path"] == "data\\vector_store_meta.json" or body[
        "metadata_path"
    ] == "data/vector_store_meta.json"
    assert isinstance(body["metadata_exists"], bool)


def test_request_logging_middleware_records_request(caplog):
    caplog.set_level(
        logging.INFO,
        logger="app.api.request",
    )

    response = client.get("/health")

    assert response.status_code == 200

    records = [
        record
        for record in caplog.records
        if record.name == "app.api.request"
    ]
    assert records

    log_payload = json.loads(records[-1].message)

    assert log_payload["event"] == "api_request"
    assert log_payload["method"] == "GET"
    assert log_payload["path"] == "/health"
    assert log_payload["status_code"] == 200
    assert log_payload["duration_ms"] >= 0


def test_metrics_records_api_requests():
    reset_api_metrics()

    health_response = client.get("/health")
    metrics_response = client.get("/metrics")

    assert health_response.status_code == 200
    assert metrics_response.status_code == 200

    metrics = metrics_response.json()

    assert metrics["request_count"] >= 1
    assert metrics["status_counts"]["200"] >= 1
    assert metrics["total_duration_ms"] >= 0
    assert metrics["average_duration_ms"] >= 0
