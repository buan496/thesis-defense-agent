from fastapi.testclient import TestClient

from app.api.main import app


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
