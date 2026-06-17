from dataclasses import dataclass

from app.agent_models import CostEstimate, TokenUsage
from app.cost_estimator import estimate_llm_cost
from app.token_estimator import estimate_messages_tokens


@dataclass
class PreflightBudgetEstimate:
    estimated_prompt_tokens: int
    reserved_completion_tokens: int
    estimated_total_tokens: int
    cost_estimate: CostEstimate


def estimate_preflight_budget(
    messages: list[dict],
    max_completion_tokens: int,
    input_price_per_1m_tokens: float,
    output_price_per_1m_tokens: float,
    currency: str = "CNY",
    characters_per_token: int = 4,
) -> PreflightBudgetEstimate:
    if max_completion_tokens < 0:
        raise ValueError("max_completion_tokens 不能小于 0")

    estimated_prompt_tokens = estimate_messages_tokens(
        messages=messages,
        characters_per_token=characters_per_token,
    )

    token_usage = TokenUsage(
        prompt_tokens=estimated_prompt_tokens,
        completion_tokens=max_completion_tokens,
        total_tokens=estimated_prompt_tokens + max_completion_tokens,
    )

    cost_estimate = estimate_llm_cost(
        token_usage=token_usage,
        input_price_per_1m_tokens=input_price_per_1m_tokens,
        output_price_per_1m_tokens=output_price_per_1m_tokens,
        currency=currency,
    )

    return PreflightBudgetEstimate(
        estimated_prompt_tokens=estimated_prompt_tokens,
        reserved_completion_tokens=max_completion_tokens,
        estimated_total_tokens=token_usage.total_tokens,
        cost_estimate=cost_estimate,
    )