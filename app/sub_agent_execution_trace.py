import json
from datetime import datetime
from pathlib import Path

from app.config import SUB_AGENT_EXECUTION_TRACE_PATH


def build_sub_agent_execution_trace_record(
    execution_result,
) -> dict:
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "event_type": "sub_agent_tool_executed",
        "execution": execution_result.to_dict(),
        "audit": {
            "sub_agent_name": execution_result.sub_agent_name,
            "tool_name": execution_result.tool_name,
            "success": execution_result.success,
            "duration_ms": execution_result.duration_ms,
            "plan_id": execution_result.plan.plan_id,
        },
    }


def save_sub_agent_execution_trace(
    execution_result,
    file_path: str = SUB_AGENT_EXECUTION_TRACE_PATH,
) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    record = build_sub_agent_execution_trace_record(execution_result)

    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return path


def load_sub_agent_execution_traces(
    file_path: str = SUB_AGENT_EXECUTION_TRACE_PATH,
) -> list[dict]:
    path = Path(file_path)

    if not path.exists():
        return []

    records = []

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))

    return records


def summarize_sub_agent_execution_traces(
    records: list[dict],
) -> dict:
    by_sub_agent = {}
    by_tool = {}
    successful = 0
    failed = 0

    for record in records:
        audit = record["audit"]
        sub_agent_name = audit["sub_agent_name"]
        tool_name = audit["tool_name"]

        by_sub_agent[sub_agent_name] = (
            by_sub_agent.get(sub_agent_name, 0) + 1
        )
        by_tool[tool_name] = by_tool.get(tool_name, 0) + 1

        if audit["success"]:
            successful += 1
        else:
            failed += 1

    return {
        "total": len(records),
        "successful": successful,
        "failed": failed,
        "by_sub_agent": dict(sorted(by_sub_agent.items())),
        "by_tool": dict(sorted(by_tool.items())),
    }
