from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class DefenseSession:
    training_query: str
    retrieved_context: str
    question: str
    student_answer: str
    evaluation: str
    rewritten_answer: str
    follow_up_question: str
    follow_up_answer: str
    follow_up_evaluation: str


@dataclass
class AgentSession:
    session_id: str = field(
        default_factory=lambda: uuid4().hex
    )
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    messages: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(
        self,
        role: str,
        content: str,
    ) -> dict[str, Any]:
        message = {
            "role": role,
            "content": content,
        }

        self.messages.append(message)
        return message