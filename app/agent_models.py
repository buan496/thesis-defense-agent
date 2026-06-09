from dataclasses import dataclass, field


@dataclass
class ToolTrace:
    step: int
    tool_name: str
    arguments: str
    result: str
    success: bool
    duration_ms: float


@dataclass
class AgentResult:
    final_output: str
    steps: int
    tool_traces: list[ToolTrace] = field(default_factory=list)
    
    
