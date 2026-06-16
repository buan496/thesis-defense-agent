from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.agent import run_agent
from app.agent_models import AgentResult
from app.session_models import AgentSession
from app.session_store import (
    DEFAULT_SESSION_DIRECTORY,
    load_agent_session,
    save_agent_session,
)
from app.tool_executor import execute_tool_call
from app.budget_guard import raise_if_cost_exceeded


def run_agent_session(
    user_message: str,
    session_id: str | None = None,
    directory: str | Path = DEFAULT_SESSION_DIRECTORY,
    max_steps: int = 5,
    max_history_turns: int = 6,
    max_history_characters: int = 12000,
    max_run_cost: float | None = None,
    llm_call: Callable[[list[dict]], Any] | None = None,
    tool_executor: Callable[[Any], str] = execute_tool_call,
) -> tuple[AgentResult, AgentSession, Path]:
    if session_id is None:
        session = AgentSession()
    else:
        session = load_agent_session(
            session_id=session_id,
            directory=directory,
        )

    result = run_agent(
        user_message=user_message,
        max_steps=max_steps,
        max_history_turns=max_history_turns,
        max_history_characters=max_history_characters,
        session=session,
        llm_call=llm_call,
        tool_executor=tool_executor,
    )
    if max_run_cost is not None:
        raise_if_cost_exceeded(
            cost_estimate=result.cost_estimate,
            max_cost=max_run_cost,
        )

    session_path = save_agent_session(
        session=session,
        directory=directory,
    )

    return result, session, session_path