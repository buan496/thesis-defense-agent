import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from app.agent_models import AgentResult
from app.storage_repositories import TraceRepository


TraceSaveReference = str | Path


def build_agent_trace_record(
    user_message: str,
    result: AgentResult,
) -> dict:
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "user_message": user_message,
        "result": asdict(result),
    }


def save_agent_trace(
    user_message: str,
    result: AgentResult,
    file_path: str = "data/traces/agent_trace.jsonl",
    trace_repository: TraceRepository | None = None,
) -> TraceSaveReference:
    trace = build_agent_trace_record(
        user_message=user_message,
        result=result,
    )

    if trace_repository is not None:
        return trace_repository.append(trace)

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(trace, ensure_ascii=False) + "\n"
        )

    return path
