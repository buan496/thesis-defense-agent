import time

from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes import async_tasks
from app.api.routes import tasks
from app.async_task_runner import AsyncTaskRunner
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
    assert task["metadata"]["correlation_id"] == response.headers[
        "X-Correlation-ID"
    ]
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
    assert body["step"]["input"]["topic"] == "系统架构"
    assert body["step"]["input"]["correlation_id"] == response.headers[
        "X-Correlation-ID"
    ]


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

    def fake_execute_task_step_service(
        task_id,
        directory,
        correlation_id=None,
    ):
        assert task_id == "task-1"
        assert directory == tmp_path
        assert correlation_id
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


def test_execute_task_step_async_creates_background_task(
    monkeypatch,
    tmp_path,
):
    runner = AsyncTaskRunner()
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path
    app.dependency_overrides[
        tasks.get_async_task_runner
    ] = lambda: runner
    app.dependency_overrides[
        async_tasks.get_async_task_runner
    ] = lambda: runner

    def fake_execute_task_step_service(
        task_id,
        directory,
        correlation_id=None,
    ):
        assert directory == tmp_path
        assert correlation_id

        fake_task = DefenseTask(
            topic="系统架构",
            task_id=task_id,
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
        return fake_task, fake_step, tmp_path / f"{task_id}.json"

    monkeypatch.setattr(
        tasks,
        "execute_task_step_service",
        fake_execute_task_step_service,
    )

    try:
        create_response = client.post(
            "/tasks",
            json={
                "topic": "系统架构",
            },
        )
        task_id = create_response.json()["task"]["task_id"]

        response = client.post(f"/tasks/{task_id}/steps/execute-async")
        async_task_id = response.json()["async_task"]["task_id"]

        status_response = None
        for _ in range(20):
            status_response = client.get(f"/async-tasks/{async_task_id}")
            if status_response.json()["task"]["status"] == "completed":
                break
            time.sleep(0.01)
    finally:
        clear_overrides()

    assert response.status_code == 200
    async_task = response.json()["async_task"]
    assert async_task["name"] == f"execute_task_step:{task_id}"
    assert async_task["status"] in {"pending", "running", "completed"}

    assert status_response is not None
    assert status_response.status_code == 200
    completed_task = status_response.json()["task"]
    assert completed_task["status"] == "completed"
    assert completed_task["result"]["task"]["task_id"] == task_id
    assert completed_task["result"]["step"]["step_type"] == "retrieve_context"
    assert completed_task["result"]["step"]["output"] == {
        "context": "系统架构上下文",
    }


def test_execute_task_step_async_records_background_failure(
    monkeypatch,
    tmp_path,
):
    runner = AsyncTaskRunner()
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path
    app.dependency_overrides[
        tasks.get_async_task_runner
    ] = lambda: runner
    app.dependency_overrides[
        async_tasks.get_async_task_runner
    ] = lambda: runner

    def fake_execute_task_step_service(
        task_id,
        directory,
        correlation_id=None,
    ):
        raise ValueError("invalid current step")

    monkeypatch.setattr(
        tasks,
        "execute_task_step_service",
        fake_execute_task_step_service,
    )

    try:
        create_response = client.post(
            "/tasks",
            json={
                "topic": "系统架构",
            },
        )
        task_id = create_response.json()["task"]["task_id"]

        response = client.post(f"/tasks/{task_id}/steps/execute-async")
        async_task_id = response.json()["async_task"]["task_id"]

        status_response = None
        for _ in range(20):
            status_response = client.get(f"/async-tasks/{async_task_id}")
            if status_response.json()["task"]["status"] == "failed":
                break
            time.sleep(0.01)
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert status_response is not None
    failed_task = status_response.json()["task"]

    assert failed_task["status"] == "failed"
    assert failed_task["error_type"] == "ValueError"
    assert failed_task["error_message"] == "invalid current step"


def test_execute_task_step_async_returns_404_when_task_missing(tmp_path):
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.post("/tasks/not-exist/steps/execute-async")
    finally:
        clear_overrides()

    assert response.status_code == 404


def test_execute_task_step_maps_value_error_to_400(monkeypatch, tmp_path):
    def fake_execute_task_step_service(
        task_id,
        directory,
        correlation_id=None,
    ):
        assert correlation_id
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
def test_submit_answer_returns_completed_wait_step(monkeypatch, tmp_path):
    fake_task = DefenseTask(
        topic="系统架构",
        task_id="task-1",
        status="running",
    )
    fake_step = TaskStep(
        step_type="wait_for_answer",
        status="completed",
        output={
            "answer": "模块拆分便于定位问题",
        },
    )
    fake_task.add_step(fake_step)
    fake_path = tmp_path / "task-1.json"

    def fake_submit_task_answer_service(
        task_id,
        answer,
        directory,
        correlation_id=None,
    ):
        assert task_id == "task-1"
        assert answer == "模块拆分便于定位问题"
        assert directory == tmp_path
        assert correlation_id
        return fake_task, fake_step, fake_path

    monkeypatch.setattr(
        tasks,
        "submit_task_answer_service",
        fake_submit_task_answer_service,
    )
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.post(
            "/tasks/task-1/answer",
            json={
                "answer": " 模块拆分便于定位问题 ",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["task"]["task_id"] == "task-1"
    assert body["step"]["step_type"] == "wait_for_answer"
    assert body["step"]["output"] == {
        "answer": "模块拆分便于定位问题",
    }


def test_submit_follow_up_answer_returns_completed_wait_step(
    monkeypatch,
    tmp_path,
):
    fake_task = DefenseTask(
        topic="系统架构",
        task_id="task-1",
        status="running",
    )
    fake_step = TaskStep(
        step_type="wait_for_follow_up_answer",
        status="completed",
        output={
            "follow_up_answer": "特征处理模块负责音频读取",
        },
    )
    fake_task.add_step(fake_step)
    fake_path = tmp_path / "task-1.json"

    def fake_submit_follow_up_answer_service(
        task_id,
        answer,
        directory,
        correlation_id=None,
    ):
        assert task_id == "task-1"
        assert answer == "特征处理模块负责音频读取"
        assert directory == tmp_path
        assert correlation_id
        return fake_task, fake_step, fake_path

    monkeypatch.setattr(
        tasks,
        "submit_follow_up_answer_service",
        fake_submit_follow_up_answer_service,
    )
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.post(
            "/tasks/task-1/follow-up-answer",
            json={
                "answer": " 特征处理模块负责音频读取 ",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["task"]["task_id"] == "task-1"
    assert body["step"]["step_type"] == "wait_for_follow_up_answer"
    assert body["step"]["output"] == {
        "follow_up_answer": "特征处理模块负责音频读取",
    }


def test_submit_answer_rejects_blank_answer(tmp_path):
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.post(
            "/tasks/task-1/answer",
            json={
                "answer": "   ",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 422


def test_submit_answer_maps_invalid_state_to_400(monkeypatch, tmp_path):
    def fake_submit_task_answer_service(
        task_id,
        answer,
        directory,
        correlation_id=None,
    ):
        assert correlation_id
        raise ValueError("当前步骤不是 wait_for_answer")

    monkeypatch.setattr(
        tasks,
        "submit_task_answer_service",
        fake_submit_task_answer_service,
    )
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.post(
            "/tasks/task-1/answer",
            json={
                "answer": "回答",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 400
    assert response.json()["detail"] == "当前步骤不是 wait_for_answer"


def test_analyze_task_returns_trace_summary(monkeypatch, tmp_path):
    def fake_analyze_task_service(task_id, directory):
        assert task_id == "task-1"
        assert directory == tmp_path
        return {
            "task_id": "task-1",
            "step_count": 2,
            "completed_step_count": 1,
        }

    monkeypatch.setattr(
        tasks,
        "analyze_task_service",
        fake_analyze_task_service,
    )
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.get("/tasks/task-1/analysis")
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert response.json() == {
        "analysis": {
            "task_id": "task-1",
            "step_count": 2,
            "completed_step_count": 1,
        }
    }


def test_analyze_task_maps_missing_task_to_404(monkeypatch, tmp_path):
    def fake_analyze_task_service(task_id, directory):
        raise FileNotFoundError("task missing")

    monkeypatch.setattr(
        tasks,
        "analyze_task_service",
        fake_analyze_task_service,
    )
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.get("/tasks/missing/analysis")
    finally:
        clear_overrides()

    assert response.status_code == 404
    assert response.json()["detail"] == "task missing"


def test_export_task_report_returns_path_and_markdown(monkeypatch, tmp_path):
    def fake_export_task_report_service(task_id, directory):
        assert task_id == "task-1"
        assert directory == tmp_path
        return tmp_path / "task-1.md", "# 论文答辩训练报告\n"

    monkeypatch.setattr(
        tasks,
        "export_task_report_service",
        fake_export_task_report_service,
    )
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.post("/tasks/task-1/report/export")
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["path"].endswith("task-1.md")
    assert body["markdown"] == "# 论文答辩训练报告\n"


def test_export_task_report_maps_invalid_task_to_400(monkeypatch, tmp_path):
    def fake_export_task_report_service(task_id, directory):
        raise ValueError("invalid task")

    monkeypatch.setattr(
        tasks,
        "export_task_report_service",
        fake_export_task_report_service,
    )
    app.dependency_overrides[tasks.get_task_directory] = lambda: tmp_path

    try:
        response = client.post("/tasks/task-1/report/export")
    finally:
        clear_overrides()

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid task"
