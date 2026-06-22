from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.agent import build_agent_messages, run_agent
from app.agent_models import AgentResult
from app.session_models import AgentSession
from app.session_compactor import compact_agent_session
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
    LONG_TERM_MEMORY_PATH,
)
from app.long_term_memory import (
    build_long_term_memory_context,
    load_long_term_memory,
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
    long_term_memory_path: str | Path = LONG_TERM_MEMORY_PATH,
    use_long_term_memory: bool = True,
    max_memory_weaknesses: int = 5,
    max_memory_summaries: int = 3,
    compact_session: bool = True,
    compact_summary_max_characters: int = 4000,
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
    
    if max_memory_weaknesses < 0:
        raise ValueError("max_memory_weaknesses must be greater than or equal to 0")

    if max_memory_summaries < 0:
        raise ValueError("max_memory_summaries must be greater than or equal to 0")
    
    if compact_summary_max_characters <= 0:
        raise ValueError(
            "compact_summary_max_characters must be greater than 0"
        )
    
    long_term_memory_context = ""

    if use_long_term_memory:
        long_term_memory = load_long_term_memory(long_term_memory_path)
        long_term_memory_context = build_long_term_memory_context(
            long_term_memory,
            max_weaknesses=max_memory_weaknesses,
            max_summaries=max_memory_summaries,
            query=user_message,
        )

    if preflight_max_run_cost is not None:
        messages = build_agent_messages(
            session=session,
            max_history_turns=max_history_turns,
            max_history_characters=max_history_characters,
            long_term_memory_context=long_term_memory_context,
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
        long_term_memory_context=long_term_memory_context,
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

    session.metadata["last_token_usage"] = {
        "prompt_tokens": result.token_usage.prompt_tokens,
        "completion_tokens": result.token_usage.completion_tokens,
        "total_tokens": result.token_usage.total_tokens,
    }
    session.metadata["last_cost_estimate"] = {
        "input_cost": result.cost_estimate.input_cost,
        "output_cost": result.cost_estimate.output_cost,
        "total_cost": result.cost_estimate.total_cost,
        "currency": result.cost_estimate.currency,
    }

    if compact_session:
        session = compact_agent_session(
            session=session,
            keep_recent_turns=max_history_turns,
            max_summary_characters=compact_summary_max_characters,
        )

    session_path = save_agent_session(
        session=session,
        directory=directory,
    )

    return result, session, session_path
