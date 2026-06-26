from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes import tasks
from app.task_models import DefenseTask, TaskStep


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


def test_start_task_step_creates_next_step(tmp_path):
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        create_response = client.post(
            "/tasks",
            json={
                "topic": "系统架构",
            },
        )
        task_id = create_response.json()["task"]["task_id"]

        response = client.post(
            f"/tasks/{task_id}/steps/start",
            json={
                "input": {
                    "topic": "系统架构",
                },
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["task"]["task_id"] == task_id
    assert body["task"]["status"] == "running"
    assert body["step"]["step_type"] == "retrieve_context"
    assert body["step"]["input"] == {
        "topic": "系统架构",
    }


def test_start_task_step_returns_404_when_task_missing(tmp_path):
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.post(
            "/tasks/not-exist/steps/start",
            json={
                "input": {},
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 404


def test_execute_task_step_returns_step_output(monkeypatch, tmp_path):
    fake_task = DefenseTask(
        topic="系统架构",
        task_id="task-1",
        status="running",
    )
    fake_step = TaskStep(
        step_type="retrieve_context",
        status="completed",
        output={
            "context": "系统架构上下文",
        },
    )
    fake_task.add_step(fake_step)
    fake_path = tmp_path / "task-1.json"

    def fake_execute_task_step_service(task_id, directory):
        assert task_id == "task-1"
        assert directory == tmp_path
        return fake_task, fake_step, fake_path

    monkeypatch.setattr(
        tasks,
        "execute_task_step_service",
        fake_execute_task_step_service,
    )
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.post("/tasks/task-1/steps/execute")
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["task"]["task_id"] == "task-1"
    assert body["step"]["step_type"] == "retrieve_context"
    assert body["step"]["output"] == {
        "context": "系统架构上下文",
    }
    assert body["path"].endswith("task-1.json")


def test_execute_task_step_maps_value_error_to_400(monkeypatch, tmp_path):
    def fake_execute_task_step_service(task_id, directory):
        raise ValueError("当前任务没有可执行步骤")

    monkeypatch.setattr(
        tasks,
        "execute_task_step_service",
        fake_execute_task_step_service,
    )
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.post("/tasks/task-1/steps/execute")
    finally:
        clear_overrides()

    assert response.status_code == 400
    assert response.json()["detail"] == "当前任务没有可执行步骤"
