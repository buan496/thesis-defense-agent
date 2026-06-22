import pytest

from app.task_models import DefenseTask, TaskStep
from app.task_store import save_defense_task
from app.tools.training_record import query_training_record


def add_completed_step(
    task: DefenseTask,
    step_type: str,
    output: dict,
) -> None:
    step = TaskStep(step_type=step_type)
    step.mark_completed(output=output)
    task.add_step(step)


def test_query_training_record(tmp_path):
    task = DefenseTask(
        task_id="task-001",
        topic="系统架构",
    )

    add_completed_step(
        task,
        "generate_question",
        {"question": "系统架构包括哪些模块？"},
    )
    add_completed_step(
        task,
        "wait_for_answer",
        {"answer": "包括特征处理和训练模块。"},
    )
    add_completed_step(
        task,
        "evaluate_answer",
        {"evaluation": "回答基本正确，但不够完整。"},
    )
    add_completed_step(
        task,
        "rewrite_answer",
        {"rewritten_answer": "系统按职责拆分为多个模块。"},
    )
    add_completed_step(
        task,
        "generate_follow_up",
        {"follow_up_question": "模块拆分如何帮助定位问题？"},
    )
    add_completed_step(
        task,
        "wait_for_follow_up_answer",
        {"follow_up_answer": "可以按模块逐步排查。"},
    )
    add_completed_step(
        task,
        "evaluate_follow_up_answer",
        {"follow_up_evaluation": "追问回答方向正确。"},
    )
    add_completed_step(
        task,
        "summarize_training",
        {"summary": "本轮训练主要薄弱点是回答不够具体。"},
    )

    task.mark_completed()
    save_defense_task(task, directory=tmp_path)

    record = query_training_record(
        task_id="task-001",
        directory=tmp_path,
    )

    assert record == {
        "task_id": "task-001",
        "topic": "系统架构",
        "status": "completed",
        "step_count": 8,
        "completed_step_count": 8,
        "question": "系统架构包括哪些模块？",
        "student_answer": "包括特征处理和训练模块。",
        "evaluation": "回答基本正确，但不够完整。",
        "rewritten_answer": "系统按职责拆分为多个模块。",
        "follow_up_question": "模块拆分如何帮助定位问题？",
        "follow_up_answer": "可以按模块逐步排查。",
        "follow_up_evaluation": "追问回答方向正确。",
        "summary": "本轮训练主要薄弱点是回答不够具体。",
    }


def test_query_training_record_rejects_empty_task_id():
    with pytest.raises(ValueError, match="task_id 不能为空"):
        query_training_record(task_id="   ")


def test_query_training_record_loads_missing_optional_fields(tmp_path):
    task = DefenseTask(
        task_id="task-002",
        topic="系统架构",
    )
    add_completed_step(
        task,
        "generate_question",
        {"question": "系统架构包括哪些模块？"},
    )
    save_defense_task(task, directory=tmp_path)

    record = query_training_record(
        task_id="task-002",
        directory=tmp_path,
    )

    assert record["question"] == "系统架构包括哪些模块？"
    assert record["summary"] is None
    assert record["step_count"] == 1
