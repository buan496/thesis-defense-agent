from app.task_models import DefenseTask, TaskStep
from app.task_runner import (
    complete_current_step,
    create_next_step,
    get_next_step_type,
)


def test_get_first_step_type_for_new_task():
    task = DefenseTask(topic="系统架构")

    assert get_next_step_type(task) == "retrieve_context"


def test_create_next_step_for_new_task():
    task = DefenseTask(topic="系统架构")

    step = create_next_step(
        task,
        input={
            "topic": "系统架构",
        },
    )

    assert step is not None
    assert step.step_type == "retrieve_context"
    assert step.input["topic"] == "系统架构"
    assert task.current_step_id == step.step_id
    assert task.status == "running"


def test_running_step_blocks_next_step():
    task = DefenseTask(topic="系统架构")
    step = create_next_step(task)

    assert step is not None
    assert get_next_step_type(task) is None
    assert create_next_step(task) is None


def test_completed_step_allows_next_step():
    task = DefenseTask(topic="系统架构")

    first_step = create_next_step(task)
    assert first_step is not None

    first_step.mark_completed(
        output={
            "context": "系统架构相关论文片段",
        }
    )

    next_step = create_next_step(task)

    assert next_step is not None
    assert next_step.step_type == "generate_question"


def test_complete_current_step_updates_output():
    task = DefenseTask(topic="系统架构")

    create_next_step(task)

    completed_step = complete_current_step(
        task,
        output={
            "context": "检索到的论文上下文",
        },
    )

    assert completed_step.status == "completed"
    assert completed_step.output["context"] == "检索到的论文上下文"


def test_task_marks_completed_after_last_step():
    task = DefenseTask(topic="系统架构")

    for step_type in [
        "retrieve_context",
        "generate_question",
        "wait_for_answer",
        "evaluate_answer",
        "rewrite_answer",
        "generate_follow_up",
        "wait_for_follow_up_answer",
        "evaluate_follow_up_answer",
        "summarize_training",
    ]:
        step = TaskStep(step_type=step_type)
        step.mark_completed()
        task.add_step(step)

    complete_current_step(
        task,
        output={
            "summary": "本轮训练完成",
        },
    )

    assert task.status == "completed"


def test_complete_current_step_without_step_raises_error():
    task = DefenseTask(topic="系统架构")

    try:
        complete_current_step(task)
    except ValueError as error:
        assert "没有可完成的步骤" in str(error)
    else:
        raise AssertionError("应该抛出 ValueError")