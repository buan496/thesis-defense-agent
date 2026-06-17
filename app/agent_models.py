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
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def add(
        self,
        other: "TokenUsage",
    ) -> None:
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens


@dataclass
class CostEstimate:
    input_cost: float = 0
    output_cost: float = 0
    total_cost: float = 0
    currency: str = "CNY"


@dataclass
class AgentResult:
    final_output: str
    steps: int
    tool_traces: list[ToolTrace] = field(default_factory=list)
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    cost_estimate: CostEstimate = field(default_factory=CostEstimate)