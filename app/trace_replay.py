import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class TraceReplayRecord:
    source_type: str
    source_path: str
    record_index: int
    created_at: str | None
    event_type: str
    status: str | None
    success: bool | None
    tool_names: list[str]
    tool_call_count: int
    failed_tool_call_count: int
    duration_ms: float
    raw: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_jsonl_trace_records(file_path: str) -> list[dict[str, Any]]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Trace file does not exist: {file_path}")

    records = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Trace line {line_number} is not valid JSON"
                ) from error

    return records


def replay_trace_file(
    file_path: str,
    source_type: str,
) -> dict[str, Any]:
    raw_records = load_jsonl_trace_records(file_path)

    records = [
        normalize_trace_record(
            raw=raw_record,
            source_type=source_type,
            source_path=file_path,
            record_index=index,
        )
        for index, raw_record in enumerate(raw_records, start=1)
    ]

    return summarize_trace_replay(records)


def normalize_trace_record(
    raw: dict[str, Any],
    source_type: str,
    source_path: str,
    record_index: int,
) -> TraceReplayRecord:
    if source_type == "agent":
        return normalize_agent_trace_record(
            raw=raw,
            source_path=source_path,
            record_index=record_index,
        )

    if source_type == "sub_agent_plan":
        return normalize_sub_agent_plan_trace_record(
            raw=raw,
            source_path=source_path,
            record_index=record_index,
        )

    if source_type == "sub_agent_execution":
        return normalize_sub_agent_execution_trace_record(
            raw=raw,
            source_path=source_path,
            record_index=record_index,
        )

    return TraceReplayRecord(
        source_type=source_type,
        source_path=source_path,
        record_index=record_index,
        created_at=raw.get("created_at"),
        event_type=raw.get("event_type", "unknown"),
        status=raw.get("status"),
        success=raw.get("success"),
        tool_names=[],
        tool_call_count=0,
        failed_tool_call_count=0,
        duration_ms=0.0,
        raw=raw,
    )


def normalize_agent_trace_record(
    raw: dict[str, Any],
    source_path: str,
    record_index: int,
) -> TraceReplayRecord:
    result = raw.get("result", {})
    tool_traces = result.get("tool_traces", [])
    failed_tool_call_count = sum(
        1
        for tool_trace in tool_traces
        if tool_trace.get("success") is False
    )
    duration_ms = sum(
        float(tool_trace.get("duration_ms", 0.0) or 0.0)
        for tool_trace in tool_traces
    )

    return TraceReplayRecord(
        source_type="agent",
        source_path=source_path,
        record_index=record_index,
        created_at=raw.get("created_at"),
        event_type="agent_run",
        status=None,
        success=failed_tool_call_count == 0,
        tool_names=[
            tool_trace.get("tool_name", "")
            for tool_trace in tool_traces
        ],
        tool_call_count=len(tool_traces),
        failed_tool_call_count=failed_tool_call_count,
        duration_ms=duration_ms,
        raw=raw,
    )


def normalize_sub_agent_plan_trace_record(
    raw: dict[str, Any],
    source_path: str,
    record_index: int,
) -> TraceReplayRecord:
    audit = raw.get("audit", {})
    tool_name = audit.get("tool_name")

    return TraceReplayRecord(
        source_type="sub_agent_plan",
        source_path=source_path,
        record_index=record_index,
        created_at=raw.get("created_at"),
        event_type=raw.get("event_type", "sub_agent_plan_created"),
        status=audit.get("status"),
        success=None,
        tool_names=[tool_name] if tool_name else [],
        tool_call_count=1 if tool_name else 0,
        failed_tool_call_count=0,
        duration_ms=0.0,
        raw=raw,
    )


def normalize_sub_agent_execution_trace_record(
    raw: dict[str, Any],
    source_path: str,
    record_index: int,
) -> TraceReplayRecord:
    audit = raw.get("audit", {})
    tool_name = audit.get("tool_name")
    success = audit.get("success")

    return TraceReplayRecord(
        source_type="sub_agent_execution",
        source_path=source_path,
        record_index=record_index,
        created_at=raw.get("created_at"),
        event_type=raw.get("event_type", "sub_agent_tool_executed"),
        status=None,
        success=success,
        tool_names=[tool_name] if tool_name else [],
        tool_call_count=1 if tool_name else 0,
        failed_tool_call_count=1 if success is False else 0,
        duration_ms=float(audit.get("duration_ms", 0.0) or 0.0),
        raw=raw,
    )


def summarize_trace_replay(
    records: list[TraceReplayRecord],
) -> dict[str, Any]:
    by_source_type: dict[str, int] = {}
    by_tool: dict[str, int] = {}
    failed_record_count = 0
    total_tool_call_count = 0
    total_failed_tool_call_count = 0
    total_duration_ms = 0.0

    for record in records:
        by_source_type[record.source_type] = (
            by_source_type.get(record.source_type, 0) + 1
        )

        for tool_name in record.tool_names:
            by_tool[tool_name] = by_tool.get(tool_name, 0) + 1

        if record.success is False or record.failed_tool_call_count > 0:
            failed_record_count += 1

        total_tool_call_count += record.tool_call_count
        total_failed_tool_call_count += record.failed_tool_call_count
        total_duration_ms += record.duration_ms

    return {
        "record_count": len(records),
        "failed_record_count": failed_record_count,
        "total_tool_call_count": total_tool_call_count,
        "total_failed_tool_call_count": total_failed_tool_call_count,
        "total_duration_ms": total_duration_ms,
        "by_source_type": dict(sorted(by_source_type.items())),
        "by_tool": dict(sorted(by_tool.items())),
        "records": [
            record.to_dict()
            for record in records
        ],
    }
