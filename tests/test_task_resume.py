from app.task_models import DefenseTask, TaskStep
from app.task_resume import get_resumable_task_status
from app.task_runner import create_next_step


def test_resume_status_for_new_task_creates_first_step():
    task = DefenseTask(topic="系统架构")

    status = get_resumable_task_status(task)

    assert status.action == "create_next_step"
    assert status.next_step_type == "retrieve_context"
    assert status.can_execute_current_step is False
    assert status.needs_human_input is False


def test_resume_status_for_pending_auto_step_executes_current_step():
    task = DefenseTask(topic="系统架构")
    step = create_next_step(
        task,
        input={
            "topic": "系统架构",
        },
    )

    status = get_resumable_task_status(task)

    assert step is not None
    assert status.action == "execute_current_step"
    assert status.current_step_id == step.step_id
    assert status.current_step_type == "retrieve_context"
    assert status.current_step_status == "pending"
    assert status.can_execute_current_step is True


def test_resume_status_for_running_auto_step_executes_current_step():
    task = DefenseTask(topic="系统架构")
    step = create_next_step(task)
    assert step is not None
    step.mark_running()

    status = get_resumable_task_status(task)

    assert status.action == "execute_current_step"
    assert status.current_step_status == "running"
    assert status.can_execute_current_step is True


def test_resume_status_for_completed_step_creates_next_step():
    task = DefenseTask(topic="系统架构")
    step = create_next_step(task)
    assert step is not None
    step.mark_completed(
        output={
            "context": "系统架构上下文",
        }
    )

    status = get_resumable_task_status(task)

    assert status.action == "create_next_step"
    assert status.current_step_type == "retrieve_context"
    assert status.next_step_type == "generate_question"


def test_resume_status_for_human_input_step_waits_for_user():
    task = DefenseTask(topic="系统架构")
    step = TaskStep(step_type="wait_for_answer")
    task.add_step(step)

    status = get_resumable_task_status(task)

    assert status.action == "wait_for_human_input"
    assert status.current_step_type == "wait_for_answer"
    assert status.needs_human_input is True


def test_resume_status_for_unimplemented_pending_step_requires_manual_review():
    task = DefenseTask(topic="系统架构")
    step = TaskStep(step_type="evaluate_answer")
    task.add_step(step)

    status = get_resumable_task_status(task)

    assert status.action == "manual_review"
    assert status.current_step_type == "evaluate_answer"
    assert status.can_execute_current_step is False


def test_resume_status_for_failed_task_requires_manual_check():
    task = DefenseTask(topic="系统架构")
    step = create_next_step(task)
    assert step is not None
    task.mark_failed("工具调用失败")

    status = get_resumable_task_status(task)

    assert status.action == "failed"
    assert status.task_status == "failed"
    assert "人工检查" in status.message


def test_resume_status_for_failed_step_requires_manual_check():
    task = DefenseTask(topic="系统架构")
    step = create_next_step(task)
    assert step is not None
    step.mark_failed("模型返回空内容")

    status = get_resumable_task_status(task)

    assert status.action == "failed_step"
    assert status.current_step_status == "failed"
    assert "人工检查" in status.message


def test_resume_status_for_completed_task():
    task = DefenseTask(topic="系统架构")
    task.mark_completed()

    status = get_resumable_task_status(task)

    assert status.action == "completed"
    assert status.task_status == "completed"
