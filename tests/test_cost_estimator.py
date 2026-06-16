import pytest

from app.agent_models import TokenUsage
from app.cost_estimator import estimate_llm_cost


def test_estimate_llm_cost():
    token_usage = TokenUsage(
        prompt_tokens=2_000_000,
        completion_tokens=500_000,
        total_tokens=2_500_000,
    )

    estimate = estimate_llm_cost(
        token_usage=token_usage,
        input_price_per_1m_tokens=1.0,
        output_price_per_1m_tokens=2.0,
        currency="CNY",
    )

    assert estimate.input_cost == 2.0
    assert estimate.output_cost == 1.0
    assert estimate.total_cost == 3.0
    assert estimate.currency == "CNY"


def test_estimate_llm_cost_with_zero_tokens():
    token_usage = TokenUsage()

    estimate = estimate_llm_cost(
        token_usage=token_usage,
        input_price_per_1m_tokens=1.0,
        output_price_per_1m_tokens=2.0,
    )

    assert estimate.input_cost == 0
    assert estimate.output_cost == 0
    assert estimate.total_cost == 0


@pytest.mark.parametrize(
    "input_price, output_price",
    [
        (-1.0, 2.0),
        (1.0, -2.0),
    ],
)
def test_estimate_llm_cost_rejects_negative_price(
    input_price,
    output_price,
):
    token_usage = TokenUsage(
        prompt_tokens=100,
        completion_tokens=100,
        total_tokens=200,
    )

    with pytest.raises(ValueError):
        estimate_llm_cost(
            token_usage=token_usage,
            input_price_per_1m_tokens=input_price,
            output_price_per_1m_tokens=output_price,
        )