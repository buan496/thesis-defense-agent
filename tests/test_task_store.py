import json

import pytest

from app.task_models import DefenseTask, TaskStep
from app.task_store import (
    load_defense_task,
    save_defense_task,
    validate_task_id,
)


def test_save_and_load_defense_task(tmp_path):
    task = DefenseTask(
        task_id="task-001",
        topic="系统架构",
        metadata={
            "student": "测试学生",
        },
    )

    step = TaskStep(
        step_type="generate_question",
        input={
            "topic": "系统架构",
        },
    )

    step.mark_completed(
        output={
            "question": "系统架构包括哪些模块？",
        }
    )

    task.add_step(step)

    task_path = save_defense_task(
        task,
        directory=tmp_path,
    )

    assert task_path.exists()
    assert task_path.name == "task-001.json"

    loaded_task = load_defense_task(
        "task-001",
        directory=tmp_path,
    )

    assert loaded_task == task
    assert loaded_task.steps[0].output["question"] == (
        "系统架构包括哪些模块？"
    )


def test_save_defense_task_writes_json(tmp_path):
    task = DefenseTask(
        task_id="task-002",
        topic="研究方法",
    )

    task_path = save_defense_task(
        task,
        directory=tmp_path,
    )

    saved_data = json.loads(
        task_path.read_text(encoding="utf-8")
    )

    assert saved_data["task_id"] == "task-002"
    assert saved_data["topic"] == "研究方法"
    assert saved_data["steps"] == []


def test_load_missing_defense_task(tmp_path):
    with pytest.raises(
        FileNotFoundError,
        match="答辩任务文件不存在",
    ):
        load_defense_task(
            "missing-task",
            directory=tmp_path,
        )


def test_validate_invalid_task_id():
    invalid_task_ids = [
        "",
        "../secret",
        "folder/task",
        "task.json",
        "中文任务",
    ]

    for task_id in invalid_task_ids:
        with pytest.raises(ValueError):
            validate_task_id(task_id)


def test_load_invalid_json(tmp_path):
    task_path = tmp_path / "broken-task.json"
    task_path.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="不是合法 JSON",
    ):
        load_defense_task(
            "broken-task",
            directory=tmp_path,
        )


def test_load_rejects_mismatched_task_id(tmp_path):
    task_path = tmp_path / "task-003.json"
    task_path.write_text(
        json.dumps(
            {
                "task_id": "another-task",
                "topic": "系统架构",
                "status": "created",
                "current_step_id": None,
                "steps": [],
                "metadata": {},
                "created_at": "2026-06-17T00:00:00+00:00",
                "updated_at": "2026-06-17T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="task_id 不一致",
    ):
        load_defense_task(
            "task-003",
            directory=tmp_path,
        )


def test_save_does_not_leave_temporary_file(tmp_path):
    task = DefenseTask(
        task_id="task-004",
        topic="系统架构",
    )

    save_defense_task(
        task,
        directory=tmp_path,
    )

    assert not (tmp_path / "task-004.tmp").exists()