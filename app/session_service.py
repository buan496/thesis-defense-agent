from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.agent import build_agent_messages, run_agent
from app.agent_models import AgentResult
from app.session_models import AgentSession
from app.session_store import (
    DEFAULT_SESSION_DIRECTORY,
    load_agent_session,
    save_agent_session,
)
from app.tool_executor import execute_tool_call
from app.budget_guard import (
    PreflightBudgetExceededError,
    raise_if_cost_exceeded,
)
from app.config import ( 
    LLM_INPUT_PRICE_PER_1M_TOKENS,
    LLM_MAX_TOKENS,
    LLM_OUTPUT_PRICE_PER_1M_TOKENS,
    LLM_PRICE_CURRENCY,
)
from app.preflight_budget import estimate_preflight_budget

def run_agent_session(
    user_message: str,
    session_id: str | None = None,
    directory: str | Path = DEFAULT_SESSION_DIRECTORY,
    max_steps: int = 5,
    max_history_turns: int = 6,
    max_history_characters: int = 12000,
    max_run_cost: float | None = None,
    preflight_max_run_cost: float | None = None,
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
    
    session.add_message(
        role="user",
        content=user_message,
    )

    if preflight_max_run_cost is not None:
        messages = build_agent_messages(
            session=session,
            max_history_turns=max_history_turns,
            max_history_characters=max_history_characters,
        )

        estimate = estimate_preflight_budget(
            messages=messages,
            max_completion_tokens=LLM_MAX_TOKENS,
            input_price_per_1m_tokens=LLM_INPUT_PRICE_PER_1M_TOKENS,
            output_price_per_1m_tokens=LLM_OUTPUT_PRICE_PER_1M_TOKENS,
            currency=LLM_PRICE_CURRENCY,
        )

        if estimate.cost_estimate.total_cost > preflight_max_run_cost:
            raise PreflightBudgetExceededError(
                estimated_cost=estimate.cost_estimate.total_cost,
                max_cost=preflight_max_run_cost,
                currency=estimate.cost_estimate.currency,
                estimated_total_tokens=estimate.estimated_total_tokens,
            )

    result = run_agent(
        user_message=user_message,
        max_steps=max_steps,
        max_history_turns=max_history_turns,
        max_history_characters=max_history_characters,
        append_user_message=False,
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