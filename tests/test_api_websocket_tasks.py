from pathlib import Path

from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes import websocket_tasks
from app.task_models import DefenseTask, TaskStep


client = TestClient(app)


def fake_task_and_step(step_type: str = "retrieve_context"):
    task = DefenseTask(
        topic="系统架构",
        task_id="task-1",
        status="running",
    )
    step = TaskStep(
        step_type=step_type,
        status="completed",
        output={
            "ok": True,
        },
    )
    task.add_step(step)
    return task, step, Path("task-1.json")


def test_handle_task_websocket_message_returns_pong(tmp_path):
    response = websocket_tasks.handle_task_websocket_message(
        task_id="task-1",
        message={
            "type": "ping",
        },
        directory=tmp_path,
    )

    assert response == {
        "type": "pong",
        "task_id": "task-1",
    }


def test_handle_task_websocket_message_starts_next_step(
    monkeypatch,
    tmp_path,
):
    def fake_start(task_id, directory, input):
        assert task_id == "task-1"
        assert directory == tmp_path
        assert input == {
            "topic": "系统架构",
        }
        return fake_task_and_step()

    monkeypatch.setattr(
        websocket_tasks,
        "start_task_step_service",
        fake_start,
    )

    response = websocket_tasks.handle_task_websocket_message(
        task_id="task-1",
        message={
            "type": "start_next_step",
            "input": {
                "topic": "系统架构",
            },
        },
        directory=tmp_path,
    )

    assert response["type"] == "step_started"
    assert response["task"]["task_id"] == "task-1"
    assert response["step"]["step_type"] == "retrieve_context"


def test_handle_task_websocket_message_submits_answer(
    monkeypatch,
    tmp_path,
):
    def fake_submit(task_id, answer, directory):
        assert task_id == "task-1"
        assert answer == "模块化便于定位问题"
        assert directory == tmp_path
        return fake_task_and_step("wait_for_answer")

    monkeypatch.setattr(
        websocket_tasks,
        "submit_task_answer_service",
        fake_submit,
    )

    response = websocket_tasks.handle_task_websocket_message(
        task_id="task-1",
        message={
            "type": "submit_answer",
            "answer": " 模块化便于定位问题 ",
        },
        directory=tmp_path,
    )

    assert response["type"] == "answer_submitted"
    assert response["step"]["step_type"] == "wait_for_answer"


def test_handle_task_websocket_message_rejects_blank_answer(tmp_path):
    try:
        websocket_tasks.handle_task_websocket_message(
            task_id="task-1",
            message={
                "type": "submit_answer",
                "answer": "   ",
            },
            directory=tmp_path,
        )
    except ValueError as error:
        assert str(error) == "answer must not be empty"
    else:
        raise AssertionError("expected ValueError")


def test_handle_task_websocket_message_rejects_unknown_type(tmp_path):
    try:
        websocket_tasks.handle_task_websocket_message(
            task_id="task-1",
            message={
                "type": "unknown",
            },
            directory=tmp_path,
        )
    except ValueError as error:
        assert "unsupported websocket message type" in str(error)
    else:
        raise AssertionError("expected ValueError")


def test_task_websocket_connects_and_handles_ping():
    with client.websocket_connect("/ws/tasks/task-1") as websocket:
        connected = websocket.receive_json()

        assert connected == {
            "type": "connected",
            "task_id": "task-1",
        }

        websocket.send_json(
            {
                "type": "ping",
            }
        )
        response = websocket.receive_json()

        assert response == {
            "type": "pong",
            "task_id": "task-1",
        }


def test_task_websocket_returns_error_for_unknown_message():
    with client.websocket_connect("/ws/tasks/task-1") as websocket:
        websocket.receive_json()

        websocket.send_json(
            {
                "type": "unknown",
            }
        )
        response = websocket.receive_json()

        assert response["type"] == "error"
        assert "unsupported websocket message type" in response["message"]
