from dataclasses import asdict, dataclass

from app.sub_agent_specs import get_sub_agent_spec


@dataclass(frozen=True)
class SubAgentToolPermissionResult:
    sub_agent_name: str
    tool_name: str
    allowed: bool
    reason: str
    allowed_tools: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def check_sub_agent_tool_permission(
    sub_agent_name: str,
    tool_name: str,
) -> SubAgentToolPermissionResult:
    spec = get_sub_agent_spec(sub_agent_name)
    allowed = tool_name in spec.allowed_tools

    if allowed:
        reason = (
            f"{sub_agent_name} is allowed to use {tool_name}"
        )
    else:
        reason = (
            f"{sub_agent_name} is not allowed to use {tool_name}"
        )

    return SubAgentToolPermissionResult(
        sub_agent_name=sub_agent_name,
        tool_name=tool_name,
        allowed=allowed,
        reason=reason,
        allowed_tools=list(spec.allowed_tools),
    )


def can_sub_agent_use_tool(
    sub_agent_name: str,
    tool_name: str,
) -> bool:
    return check_sub_agent_tool_permission(
        sub_agent_name,
        tool_name,
    ).allowed


def validate_sub_agent_tool_call(
    sub_agent_name: str,
    tool_name: str,
) -> None:
    result = check_sub_agent_tool_permission(
        sub_agent_name,
        tool_name,
    )

    if not result.allowed:
        raise ValueError(result.reason)
