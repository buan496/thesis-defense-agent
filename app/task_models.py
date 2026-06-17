from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def current_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return uuid4().hex


@dataclass
class TaskStep:
    step_type: str
    step_id: str = field(default_factory=new_id)
    status: str = "pending"
    input: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    tool_traces: list[dict[str, Any]] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=dict)
    cost_estimate: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    created_at: str = field(default_factory=current_time)
    updated_at: str = field(default_factory=current_time)

    def mark_running(self) -> None:
        self.status = "running"
        self.updated_at = current_time()

    def mark_completed(
        self,
        output: dict[str, Any] | None = None,
    ) -> None:
        self.status = "completed"

        if output is not None:
            self.output = output

        self.updated_at = current_time()

    def mark_failed(
        self,
        error: str,
    ) -> None:
        self.status = "failed"
        self.error = error
        self.updated_at = current_time()


@dataclass
class DefenseTask:
    topic: str
    task_id: str = field(default_factory=new_id)
    status: str = "created"
    current_step_id: str | None = None
    steps: list[TaskStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=current_time)
    updated_at: str = field(default_factory=current_time)

    def add_step(
        self,
        step: TaskStep,
    ) -> TaskStep:
        self.steps.append(step)
        self.current_step_id = step.step_id

        if self.status == "created":
            self.status = "running"

        self.updated_at = current_time()

        return step

    def get_current_step(self) -> TaskStep | None:
        if self.current_step_id is None:
            return None

        for step in self.steps:
            if step.step_id == self.current_step_id:
                return step

        return None

    def mark_completed(self) -> None:
        self.status = "completed"
        self.updated_at = current_time()

    def mark_failed(
        self,
        error: str,
    ) -> None:
        self.status = "failed"
        self.metadata["error"] = error
        self.updated_at = current_time()