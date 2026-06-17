from app.task_service import (
    complete_task_step,
    create_defense_task,
    get_defense_task,
    start_next_task_step,
)


def test_create_defense_task_saves_task(tmp_path):
    task, task_path = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    assert task.task_id
    assert task.topic == "系统架构"
    assert task.status == "created"
    assert task_path.exists()

    loaded_task = get_defense_task(
        task.task_id,
        directory=tmp_path,
    )

    assert loaded_task == task


def test_start_next_task_step_loads_updates_and_saves_task(tmp_path):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    updated_task, step, task_path = start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
        input={
            "topic": "系统架构",
        },
    )

    assert step is not None
    assert step.step_type == "retrieve_context"
    assert step.input["topic"] == "系统架构"
    assert updated_task.status == "running"
    assert task_path.exists()

    loaded_task = get_defense_task(
        task.task_id,
        directory=tmp_path,
    )

    assert loaded_task == updated_task


def test_start_next_task_step_returns_none_when_current_step_not_completed(
    tmp_path,
):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )

    updated_task, step, _ = start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )

    assert step is None
    assert len(updated_task.steps) == 1


def test_complete_task_step_loads_updates_and_saves_task(tmp_path):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )

    updated_task, step, task_path = complete_task_step(
        task_id=task.task_id,
        directory=tmp_path,
        output={
            "context": "系统架构相关上下文",
        },
    )

    assert step.status == "completed"
    assert step.output["context"] == "系统架构相关上下文"
    assert task_path.exists()

    loaded_task = get_defense_task(
        task.task_id,
        directory=tmp_path,
    )

    assert loaded_task == updated_task


def test_task_service_can_advance_two_steps(tmp_path):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    _, first_step, _ = start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )

    assert first_step is not None
    assert first_step.step_type == "retrieve_context"

    complete_task_step(
        task_id=task.task_id,
        directory=tmp_path,
        output={
            "context": "系统架构上下文",
        },
    )

    updated_task, second_step, _ = start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
        input={
            "context": "系统架构上下文",
        },
    )

    assert second_step is not None
    assert second_step.step_type == "generate_question"
    assert len(updated_task.steps) == 2