import json

from app.agent_models import AgentResult, ToolTrace
from app.agent_trace_logger import save_agent_trace


class InMemoryTraceRepository:
    def __init__(self):
        self.records = []

    def append(self, record):
        self.records.append(record)
        return f"repository:{len(self.records)}"

    def load_all(self):
        return list(self.records)


def test_save_agent_trace(tmp_path):
    trace_path = tmp_path / "agent_trace.jsonl"

    result = AgentResult(
        final_output="系统包含多个模块。",
        steps=2,
        tool_traces=[
            ToolTrace(
                step=1,
                tool_name="search_thesis",
                arguments='{"query": "系统架构"}',
                result='[{"text": "论文内容"}]',
                success=True,
                duration_ms=100.0,
            )
        ],
    )

    saved_path = save_agent_trace(
        user_message="系统架构是什么？",
        result=result,
        file_path=str(trace_path),
    )

    line = saved_path.read_text(encoding="utf-8").strip()
    data = json.loads(line)

    assert data["user_message"] == "系统架构是什么？"
    assert data["result"]["steps"] == 2
    assert data["result"]["tool_traces"][0]["success"] is True


def test_save_agent_trace_can_use_trace_repository(tmp_path):
    repository = InMemoryTraceRepository()
    result = AgentResult(
        final_output="系统包含多个模块。",
        steps=1,
        tool_traces=[],
    )

    saved_identifier = save_agent_trace(
        user_message="系统架构是什么？",
        result=result,
        file_path=str(tmp_path / "agent_trace.jsonl"),
        trace_repository=repository,
    )

    assert saved_identifier == "repository:1"
    assert len(repository.records) == 1
    assert repository.records[0]["user_message"] == "系统架构是什么？"
    assert repository.records[0]["result"]["steps"] == 1
    assert not (tmp_path / "agent_trace.jsonl").exists()
