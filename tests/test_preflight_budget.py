import pytest

from app.preflight_budget import estimate_preflight_budget


def test_estimate_preflight_budget():
    messages = [
        {
            "role": "user",
            "content": "abcd",
        }
    ]

    estimate = estimate_preflight_budget(
        messages=messages,
        max_completion_tokens=100,
        input_price_per_1m_tokens=1.0,
        output_price_per_1m_tokens=2.0,
        currency="CNY",
        characters_per_token=4,
    )

    assert estimate.estimated_prompt_tokens > 0
    assert estimate.reserved_completion_tokens == 100
    assert estimate.estimated_total_tokens == (
        estimate.estimated_prompt_tokens + 100
    )
    assert estimate.cost_estimate.input_cost > 0
    assert estimate.cost_estimate.output_cost == pytest.approx(
        100 / 1_000_000 * 2.0
    )
    assert estimate.cost_estimate.total_cost == pytest.approx(
        estimate.cost_estimate.input_cost
        + estimate.cost_estimate.output_cost
    )
    assert estimate.cost_estimate.currency == "CNY"


def test_estimate_preflight_budget_allows_zero_completion_tokens():
    estimate = estimate_preflight_budget(
        messages=[],
        max_completion_tokens=0,
        input_price_per_1m_tokens=1.0,
        output_price_per_1m_tokens=2.0,
    )

    assert estimate.estimated_prompt_tokens == 0
    assert estimate.reserved_completion_tokens == 0
    assert estimate.estimated_total_tokens == 0
    assert estimate.cost_estimate.total_cost == 0


def test_estimate_preflight_budget_rejects_negative_completion_tokens():
    with pytest.raises(
        ValueError,
        match="max_completion_tokens 不能小于 0",
    ):
        estimate_preflight_budget(
            messages=[],
            max_completion_tokens=-1,
            input_price_per_1m_tokens=1.0,
            output_price_per_1m_tokens=2.0,
        )