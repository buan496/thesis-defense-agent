from dataclasses import asdict, dataclass

from app.config import SUB_AGENT_PLAN_TRACE_PATH
from app.sub_agent_permissions import check_sub_agent_tool_permission
from app.sub_agent_plan import SubAgentExecutionPlan, create_sub_agent_execution_plan
from app.sub_agent_plan_trace import save_sub_agent_plan_trace


@dataclass(frozen=True)
class SubAgentDryRunReport:
    sub_agent_name: str
    tool_name: str
    allowed: bool
    will_execute: bool
    plan: SubAgentExecutionPlan
    trace_saved: bool
    trace_path: str | None
    reason: str

    def to_dict(self) -> dict:
        data = asdict(self)
        data["plan"] = self.plan.to_dict()
        return data


def dry_run_sub_agent_tool_call(
    sub_agent_name: str,
    tool_name: str,
    tool_arguments: dict,
    save_trace: bool = False,
    trace_file: str = SUB_AGENT_PLAN_TRACE_PATH,
) -> SubAgentDryRunReport:
    permission = check_sub_agent_tool_permission(
        sub_agent_name=sub_agent_name,
        tool_name=tool_name,
    )
    plan = create_sub_agent_execution_plan(
        sub_agent_name=sub_agent_name,
        tool_name=tool_name,
        tool_arguments=tool_arguments,
    )
    trace_path = None

    if save_trace:
        trace_path = str(
            save_sub_agent_plan_trace(
                plan,
                file_path=trace_file,
            )
        )

    return SubAgentDryRunReport(
        sub_agent_name=sub_agent_name,
        tool_name=tool_name,
        allowed=permission.allowed,
        will_execute=False,
        plan=plan,
        trace_saved=save_trace,
        trace_path=trace_path,
        reason=(
            "dry-run only; tool was not executed"
        ),
    )
