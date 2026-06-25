import json

import pytest

from app.task_memory_exporter import (
    export_task_to_long_term_memory,
    extract_summary_weaknesses,
    find_latest_completed_step,
)
from app.task_models import DefenseTask, TaskStep


def build_completed_task() -> DefenseTask:
    task = DefenseTask(
        topic="系统架构",
        task_id="task-001",
    )

    summary_step = TaskStep(step_type="summarize_training")
    summary_step.mark_completed(
        output={
            "summary": "本轮训练回答较笼统，下一轮需要补充模块案例。",
            "weaknesses": [
                "回答缺少具体模块案例",
                "需要说明工程排查路径",
            ],
        }
    )
    task.add_step(summary_step)
    task.mark_completed()

    return task


def test_export_task_to_long_term_memory(tmp_path):
    memory_path = tmp_path / "memory.json"
    task = build_completed_task()

    report = export_task_to_long_term_memory(
        task=task,
        memory_path=memory_path,
    )

    memory = json.loads(memory_path.read_text(encoding="utf-8"))

    assert report == {
        "task_id": "task-001",
        "topic": "系统架构",
        "memory_path": str(memory_path),
        "summary_exported": True,
        "weakness_count": 2,
        "weaknesses": [
            "回答缺少具体模块案例",
            "需要说明工程排查路径",
        ],
    }
    assert memory["training_summaries"][0]["summary"] == (
        "本轮训练回答较笼统，下一轮需要补充模块案例。"
    )
    assert memory["training_summaries"][0]["task_id"] == "task-001"
    assert memory["training_summaries"][0]["topic"] == "系统架构"
    assert [
        item["weakness"] for item in memory["weaknesses"]
    ] == [
        "回答缺少具体模块案例",
        "需要说明工程排查路径",
    ]


def test_export_task_to_long_term_memory_rejects_unfinished_task(tmp_path):
    task = DefenseTask(topic="系统架构")

    with pytest.raises(ValueError, match="only completed tasks"):
        export_task_to_long_term_memory(
            task=task,
            memory_path=tmp_path / "memory.json",
        )


def test_export_task_to_long_term_memory_rejects_missing_summary_step(
    tmp_path,
):
    task = DefenseTask(topic="系统架构")
    task.mark_completed()

    with pytest.raises(ValueError, match="no completed summarize_training"):
        export_task_to_long_term_memory(
            task=task,
            memory_path=tmp_path / "memory.json",
        )


def test_export_task_to_long_term_memory_rejects_empty_summary(tmp_path):
    task = DefenseTask(topic="系统架构")
    summary_step = TaskStep(step_type="summarize_training")
    summary_step.mark_completed(output={"summary": " "})
    task.add_step(summary_step)
    task.mark_completed()

    with pytest.raises(ValueError, match="has no summary"):
        export_task_to_long_term_memory(
            task=task,
            memory_path=tmp_path / "memory.json",
        )


def test_find_latest_completed_step():
    task = DefenseTask(topic="系统架构")
    old_step = TaskStep(step_type="summarize_training")
    old_step.mark_completed(output={"summary": "old"})
    new_step = TaskStep(step_type="summarize_training")
    new_step.mark_completed(output={"summary": "new"})
    pending_step = TaskStep(step_type="summarize_training")
    task.add_step(old_step)
    task.add_step(new_step)
    task.add_step(pending_step)

    found = find_latest_completed_step(
        task,
        step_type="summarize_training",
    )

    assert found == new_step


def test_extract_summary_weaknesses():
    assert extract_summary_weaknesses(
        {
            "weaknesses": [
                "  回答过于笼统  ",
                "",
                123,
                "缺少例子",
            ]
        }
    ) == [
        "回答过于笼统",
        "缺少例子",
    ]

    assert extract_summary_weaknesses({"weaknesses": "单条薄弱点"}) == [
        "单条薄弱点",
    ]
    assert extract_summary_weaknesses({}) == []


def test_extract_summary_weaknesses_rejects_invalid_type():
    with pytest.raises(ValueError, match="weaknesses must be"):
        extract_summary_weaknesses({"weaknesses": {"bad": "type"}})
