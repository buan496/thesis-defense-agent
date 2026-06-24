from dataclasses import asdict, dataclass
from uuid import uuid4

from app.sub_agent_permissions import validate_sub_agent_tool_call
from app.sub_agent_specs import get_sub_agent_spec


@dataclass(frozen=True)
class SubAgentExecutionPlan:
    plan_id: str
    sub_agent_name: str
    role: str
    tool_name: str
    tool_arguments: dict
    expected_output_fields: list[str]
    max_steps: int
    status: str = "planned"

    def to_dict(self) -> dict:
        return asdict(self)


def validate_sub_agent_plan_input(
    sub_agent_name: str,
    tool_name: str,
    tool_arguments: dict,
) -> None:
    spec = get_sub_agent_spec(sub_agent_name)
    validate_sub_agent_tool_call(
        sub_agent_name=sub_agent_name,
        tool_name=tool_name,
    )

    missing_fields = [
        field
        for field in spec.input_fields
        if field not in tool_arguments
    ]

    if missing_fields:
        raise ValueError(
            f"{sub_agent_name} 缺少输入字段：{', '.join(missing_fields)}"
        )


def create_sub_agent_execution_plan(
    sub_agent_name: str,
    tool_name: str,
    tool_arguments: dict,
    plan_id: str | None = None,
) -> SubAgentExecutionPlan:
    if not isinstance(tool_arguments, dict):
        raise ValueError("tool_arguments 必须是 dict")

    validate_sub_agent_plan_input(
        sub_agent_name=sub_agent_name,
        tool_name=tool_name,
        tool_arguments=tool_arguments,
    )

    spec = get_sub_agent_spec(sub_agent_name)

    return SubAgentExecutionPlan(
        plan_id=plan_id or uuid4().hex,
        sub_agent_name=spec.name,
        role=spec.role,
        tool_name=tool_name,
        tool_arguments=dict(tool_arguments),
        expected_output_fields=list(spec.output_fields),
        max_steps=spec.max_steps,
    )
