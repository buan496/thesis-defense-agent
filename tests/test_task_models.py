from app.task_models import DefenseTask, TaskStep


def test_create_defense_task():
    task = DefenseTask(topic="系统架构")

    assert task.task_id
    assert task.topic == "系统架构"
    assert task.status == "created"
    assert task.current_step_id is None
    assert task.steps == []


def test_add_step_updates_task_state():
    task = DefenseTask(topic="系统架构")
    step = TaskStep(
        step_type="generate_question",
        input={
            "topic": "系统架构",
        },
    )

    task.add_step(step)

    assert task.status == "running"
    assert task.current_step_id == step.step_id
    assert task.steps == [step]


def test_get_current_step():
    task = DefenseTask(topic="系统架构")

    first_step = TaskStep(step_type="retrieve_context")
    second_step = TaskStep(step_type="generate_question")

    task.add_step(first_step)
    task.add_step(second_step)

    current_step = task.get_current_step()

    assert current_step == second_step
    assert current_step.step_type == "generate_question"


def test_task_step_can_mark_running_and_completed():
    step = TaskStep(
        step_type="evaluate_answer",
        input={
            "question": "系统架构包括哪些模块？",
            "answer": "包括特征处理和训练模块。",
        },
    )

    step.mark_running()

    assert step.status == "running"

    step.mark_completed(
        output={
            "score": 7,
            "feedback": "回答基本正确，但不够完整。",
        }
    )

    assert step.status == "completed"
    assert step.output["score"] == 7
    assert step.output["feedback"] == "回答基本正确，但不够完整。"


def test_task_step_can_mark_failed():
    step = TaskStep(step_type="generate_question")

    step.mark_failed("模型返回空内容")

    assert step.status == "failed"
    assert step.error == "模型返回空内容"


def test_defense_task_can_mark_completed():
    task = DefenseTask(topic="系统架构")

    task.mark_completed()

    assert task.status == "completed"


def test_defense_task_can_mark_failed():
    task = DefenseTask(topic="系统架构")

    task.mark_failed("工具调用失败")

    assert task.status == "failed"
    assert task.metadata["error"] == "工具调用失败"