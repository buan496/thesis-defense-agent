from dataclasses import dataclass

from app.agent_models import CostEstimate, TokenUsage

def estimate_llm_cost(
    token_usage: TokenUsage,
    input_price_per_1m_tokens: float,
    output_price_per_1m_tokens: float,
    currency: str = "CNY",
) -> CostEstimate:
    if input_price_per_1m_tokens < 0:
        raise ValueError(
            "input_price_per_1m_tokens 不能小于 0"
        )

    if output_price_per_1m_tokens < 0:
        raise ValueError(
            "output_price_per_1m_tokens 不能小于 0"
        )

    input_cost = (
        token_usage.prompt_tokens
        / 1_000_000
        * input_price_per_1m_tokens
    )
    output_cost = (
        token_usage.completion_tokens
        / 1_000_000
        * output_price_per_1m_tokens
    )

    total_cost = input_cost + output_cost

    return CostEstimate(
        input_cost=input_cost,
        output_cost=output_cost,
        total_cost=total_cost,
        currency=currency,
    )