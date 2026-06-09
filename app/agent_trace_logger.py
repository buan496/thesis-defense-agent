import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from app.agent_models import AgentResult


def save_agent_trace(
    user_message: str,
    result: AgentResult,
    file_path: str = "data/traces/agent_trace.jsonl",
) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    trace = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "user_message": user_message,
        "result": asdict(result),
    }

    with path.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(trace, ensure_ascii=False) + "\n"
        )

    return path