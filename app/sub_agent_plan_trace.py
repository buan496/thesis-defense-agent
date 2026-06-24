import json
from datetime import datetime
from pathlib import Path

from app.config import SUB_AGENT_PLAN_TRACE_PATH
from app.sub_agent_plan import SubAgentExecutionPlan


def build_sub_agent_plan_trace_record(
    plan: SubAgentExecutionPlan,
) -> dict:
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "event_type": "sub_agent_plan_created",
        "plan": plan.to_dict(),
        "audit": {
            "sub_agent_name": plan.sub_agent_name,
            "tool_name": plan.tool_name,
            "status": plan.status,
            "max_steps": plan.max_steps,
            "expected_output_fields": plan.expected_output_fields,
        },
    }


def save_sub_agent_plan_trace(
    plan: SubAgentExecutionPlan,
    file_path: str = SUB_AGENT_PLAN_TRACE_PATH,
) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    record = build_sub_agent_plan_trace_record(plan)

    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return path


def load_sub_agent_plan_traces(
    file_path: str = SUB_AGENT_PLAN_TRACE_PATH,
) -> list[dict]:
    path = Path(file_path)

    if not path.exists():
        return []

    records = []

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))

    return records


def summarize_sub_agent_plan_traces(
    records: list[dict],
) -> dict:
    by_sub_agent = {}
    by_tool = {}

    for record in records:
        audit = record["audit"]
        sub_agent_name = audit["sub_agent_name"]
        tool_name = audit["tool_name"]

        by_sub_agent[sub_agent_name] = (
            by_sub_agent.get(sub_agent_name, 0) + 1
        )
        by_tool[tool_name] = by_tool.get(tool_name, 0) + 1

    return {
        "total": len(records),
        "by_sub_agent": dict(sorted(by_sub_agent.items())),
        "by_tool": dict(sorted(by_tool.items())),
    }
