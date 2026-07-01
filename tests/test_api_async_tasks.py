import time

from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes import async_tasks
from app.async_task_runner import AsyncTaskRunner


client = TestClient(app)


def clear_overrides():
    app.dependency_overrides.clear()


def test_create_async_task_returns_task_id():
    runner = AsyncTaskRunner()
    app.dependency_overrides[
        async_tasks.get_async_task_runner
    ] = lambda: runner

    try:
        response = client.post(
            "/async-tasks",
            json={
                "name": "demo",
                "delay_seconds": 0,
                "result": "done",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()
    task = body["task"]

    assert task["task_id"]
    assert task["name"] == "demo"
    assert task["status"] in {"pending", "running", "completed"}


def test_get_async_task_returns_completed_status():
    runner = AsyncTaskRunner()
    app.dependency_overrides[
        async_tasks.get_async_task_runner
    ] = lambda: runner

    try:
        create_response = client.post(
            "/async-tasks",
            json={
                "name": "demo",
                "delay_seconds": 0,
                "result": "done",
            },
        )
        task_id = create_response.json()["task"]["task_id"]

        response = None
        for _ in range(20):
            response = client.get(f"/async-tasks/{task_id}")
            if response.json()["task"]["status"] == "completed":
                break
            time.sleep(0.01)
    finally:
        clear_overrides()

    assert response is not None
    assert response.status_code == 200
    task = response.json()["task"]

    assert task["task_id"] == task_id
    assert task["status"] == "completed"
    assert task["result"] == {
        "result": "done",
        "delay_seconds": 0.0,
    }


def test_cancel_async_task_marks_task_cancelled():
    runner = AsyncTaskRunner()
    app.dependency_overrides[
        async_tasks.get_async_task_runner
    ] = lambda: runner

    try:
        create_response = client.post(
            "/async-tasks",
            json={
                "name": "slow",
                "delay_seconds": 5,
                "result": "done",
            },
        )
        task_id = create_response.json()["task"]["task_id"]

        response = client.delete(f"/async-tasks/{task_id}")
    finally:
        clear_overrides()

    assert response.status_code == 200
    task = response.json()["task"]

    assert task["task_id"] == task_id
    assert task["status"] == "cancelled"
    assert task["error_type"] == "CancelledError"


def test_get_async_task_returns_404_for_missing_task():
    runner = AsyncTaskRunner()
    app.dependency_overrides[
        async_tasks.get_async_task_runner
    ] = lambda: runner

    try:
        response = client.get("/async-tasks/missing")
    finally:
        clear_overrides()

    assert response.status_code == 404


def test_cancel_async_task_returns_404_for_missing_task():
    runner = AsyncTaskRunner()
    app.dependency_overrides[
        async_tasks.get_async_task_runner
    ] = lambda: runner

    try:
        response = client.delete("/async-tasks/missing")
    finally:
        clear_overrides()

    assert response.status_code == 404


def test_create_async_task_rejects_blank_name():
    runner = AsyncTaskRunner()
    app.dependency_overrides[
        async_tasks.get_async_task_runner
    ] = lambda: runner

    try:
        response = client.post(
            "/async-tasks",
            json={
                "name": "   ",
                "delay_seconds": 0,
                "result": "done",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 422
