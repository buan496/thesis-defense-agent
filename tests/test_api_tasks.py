from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes import tasks


client = TestClient(app)


def clear_overrides():
    app.dependency_overrides.clear()


def test_create_task_saves_task_in_configured_directory(tmp_path):
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.post(
            "/tasks",
            json={
                "topic": "系统架构",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()
    task = body["task"]

    assert task["topic"] == "系统架构"
    assert task["status"] == "created"
    assert task["task_id"]
    assert body["path"].endswith(f"{task['task_id']}.json")
    assert (tmp_path / f"{task['task_id']}.json").exists()


def test_get_task_returns_saved_task(tmp_path):
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        create_response = client.post(
            "/tasks",
            json={
                "topic": "系统架构",
            },
        )
        task_id = create_response.json()["task"]["task_id"]

        response = client.get(f"/tasks/{task_id}")
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["task"]["task_id"] == task_id
    assert body["task"]["topic"] == "系统架构"
    assert body["task"]["status"] == "created"


def test_create_task_rejects_blank_topic(tmp_path):
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.post(
            "/tasks",
            json={
                "topic": "   ",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 422


def test_get_task_returns_404_when_missing(tmp_path):
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.get("/tasks/not-exist")
    finally:
        clear_overrides()

    assert response.status_code == 404


def test_get_task_rejects_invalid_task_id(tmp_path):
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.get("/tasks/../bad")
    finally:
        clear_overrides()

    assert response.status_code in {400, 404}
