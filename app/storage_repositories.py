import json
from pathlib import Path
from typing import Any, Protocol

from app.session_models import AgentSession
from app.session_store import load_agent_session, save_agent_session
from app.task_models import DefenseTask
from app.task_store import load_defense_task, save_defense_task


class TaskRepository(Protocol):
    def save(self, task: DefenseTask) -> str:
        ...

    def load(self, task_id: str) -> DefenseTask:
        ...


class SessionRepository(Protocol):
    def save(self, session: AgentSession) -> str:
        ...

    def load(self, session_id: str) -> AgentSession:
        ...


class TraceRepository(Protocol):
    def append(self, record: dict[str, Any]) -> str:
        ...

    def load_all(self) -> list[dict[str, Any]]:
        ...


class JsonTaskRepository:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)

    def save(self, task: DefenseTask) -> str:
        return str(
            save_defense_task(
                task,
                directory=self.directory,
            )
        )

    def load(self, task_id: str) -> DefenseTask:
        return load_defense_task(
            task_id,
            directory=self.directory,
        )


class JsonSessionRepository:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)

    def save(self, session: AgentSession) -> str:
        return str(
            save_agent_session(
                session,
                directory=self.directory,
            )
        )

    def load(self, session_id: str) -> AgentSession:
        return load_agent_session(
            session_id,
            directory=self.directory,
        )


class JsonlTraceRepository:
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

    def append(self, record: dict[str, Any]) -> str:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with self.file_path.open("a", encoding="utf-8") as file:
            file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

        return str(self.file_path)

    def load_all(self) -> list[dict[str, Any]]:
        if not self.file_path.exists():
            return []

        records = []

        with self.file_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"trace line {line_number} is not valid JSON"
                    ) from error

        return records
