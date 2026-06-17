from dataclasses import dataclass

from app.task_models import DefenseTask
from app.task_runner import get_next_step_type


AUTO_EXECUTABLE_STEP_TYPES = {
    "retrieve_context",
    "generate_question",
}

HUMAN_INPUT_STEP_TYPES = {
    "wait_for_answer",
    "wait_for_follow_up_answer",
}


@dataclass
class TaskResumeStatus:
    action: str
    task_status: str
    current_step_id: str | None = None
    current_step_type: str | None = None
    current_step_status: str | None = None
    next_step_type: str | None = None
    can_execute_current_step: bool = False
    needs_human_input: bool = False
    message: str = ""


def get_resumable_task_status(task: DefenseTask) -> TaskResumeStatus:
    current_step = task.get_current_step()

    if task.status == "completed":
        return TaskResumeStatus(
            action="completed",
            task_status=task.status,
            message="任务已经完成",
        )

    if task.status == "failed":
        return TaskResumeStatus(
            action="failed",
            task_status=task.status,
            current_step_id=(
                current_step.step_id if current_step is not None else None
            ),
            current_step_type=(
                current_step.step_type if current_step is not None else None
            ),
            current_step_status=(
                current_step.status if current_step is not None else None
            ),
            message="任务已经失败，需要人工检查错误后再恢复",
        )

    if current_step is None:
        next_step_type = get_next_step_type(task)

        return TaskResumeStatus(
            action="create_next_step",
            task_status=task.status,
            next_step_type=next_step_type,
            message="任务尚未开始，可以创建第一个步骤",
        )

    if current_step.status in {"pending", "running"}:
        if current_step.step_type in AUTO_EXECUTABLE_STEP_TYPES:
            return TaskResumeStatus(
                action="execute_current_step",
                task_status=task.status,
                current_step_id=current_step.step_id,
                current_step_type=current_step.step_type,
                current_step_status=current_step.status,
                can_execute_current_step=True,
                message="当前步骤可以自动执行",
            )

        if current_step.step_type in HUMAN_INPUT_STEP_TYPES:
            return TaskResumeStatus(
                action="wait_for_human_input",
                task_status=task.status,
                current_step_id=current_step.step_id,
                current_step_type=current_step.step_type,
                current_step_status=current_step.status,
                needs_human_input=True,
                message="当前步骤需要人工输入",
            )

        return TaskResumeStatus(
            action="manual_review",
            task_status=task.status,
            current_step_id=current_step.step_id,
            current_step_type=current_step.step_type,
            current_step_status=current_step.status,
            message="当前步骤尚未接入自动执行，需要人工处理",
        )

    if current_step.status == "failed":
        return TaskResumeStatus(
            action="failed_step",
            task_status=task.status,
            current_step_id=current_step.step_id,
            current_step_type=current_step.step_type,
            current_step_status=current_step.status,
            message="当前步骤失败，需要人工检查错误后再恢复",
        )

    if current_step.status == "completed":
        next_step_type = get_next_step_type(task)

        if next_step_type is None:
            return TaskResumeStatus(
                action="completed",
                task_status=task.status,
                current_step_id=current_step.step_id,
                current_step_type=current_step.step_type,
                current_step_status=current_step.status,
                message="任务已经没有后续步骤",
            )

        return TaskResumeStatus(
            action="create_next_step",
            task_status=task.status,
            current_step_id=current_step.step_id,
            current_step_type=current_step.step_type,
            current_step_status=current_step.status,
            next_step_type=next_step_type,
            message="当前步骤已完成，可以创建下一步",
        )

    return TaskResumeStatus(
        action="unknown",
        task_status=task.status,
        current_step_id=current_step.step_id,
        current_step_type=current_step.step_type,
        current_step_status=current_step.status,
        message="未知任务恢复状态",
    )
