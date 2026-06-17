import json
import os
import re

from dataclasses import asdict
from pathlib import Path

from app.task_models import DefenseTask, TaskStep


DEFAULT_TASK_DIRECTORY = Path("data/defense_tasks")
TASK_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def validate_task_id(task_id: str) -> None:
    if not task_id:
        raise ValueError("task_id 不能为空")

    if not TASK_ID_PATTERN.fullmatch(task_id):
        raise ValueError(
            "task_id 只能包含字母、数字、下划线和连字符"
        )


def save_defense_task(
    task: DefenseTask,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
) -> Path:
    validate_task_id(task.task_id)

    directory_path = Path(directory)
    directory_path.mkdir(parents=True, exist_ok=True)

    task_path = directory_path / f"{task.task_id}.json"
    temporary_path = directory_path / f"{task.task_id}.tmp"

    task_text = json.dumps(
        asdict(task),
        ensure_ascii=False,
        indent=2,
    )

    try:
        temporary_path.write_text(
            task_text,
            encoding="utf-8",
        )

        os.replace(temporary_path, task_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    return task_path


def load_defense_task(
    task_id: str,
    directory: str | Path = DEFAULT_TASK_DIRECTORY,
) -> DefenseTask:
    validate_task_id(task_id)

    task_path = Path(directory) / f"{task_id}.json"

    if not task_path.exists():
        raise FileNotFoundError(
            f"答辩任务文件不存在：{task_path}"
        )

    try:
        task_data = json.loads(
            task_path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            f"答辩任务文件不是合法 JSON：{task_path}"
        ) from error

    required_fields = {
        "task_id",
        "topic",
        "status",
        "current_step_id",
        "steps",
        "metadata",
        "created_at",
        "updated_at",
    }

    missing_fields = required_fields - task_data.keys()

    if missing_fields:
        raise ValueError(
            f"答辩任务缺少字段：{sorted(missing_fields)}"
        )

    if task_data["task_id"] != task_id:
        raise ValueError(
            "文件中的 task_id 与请求的 task_id 不一致"
        )

    if not isinstance(task_data["steps"], list):
        raise ValueError("steps 必须是列表")

    steps = [
        TaskStep(**step_data)
        for step_data in task_data["steps"]
    ]

    return DefenseTask(
        task_id=task_data["task_id"],
        topic=task_data["topic"],
        status=task_data["status"],
        current_step_id=task_data["current_step_id"],
        steps=steps,
        metadata=task_data["metadata"],
        created_at=task_data["created_at"],
        updated_at=task_data["updated_at"],
    )