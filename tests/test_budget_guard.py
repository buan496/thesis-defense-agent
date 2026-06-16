import pytest

from app.agent_models import CostEstimate
from app.budget_guard import (
    BudgetExceededError,
    check_cost_budget,
    raise_if_cost_exceeded,
)


def test_check_cost_budget_passes_when_under_limit():
    cost_estimate = CostEstimate(
        input_cost=0.01,
        output_cost=0.01,
        total_cost=0.02,
        currency="CNY",
    )

    result = check_cost_budget(
        cost_estimate=cost_estimate,
        max_cost=0.03,
    )

    assert result.passed is True
    assert result.actual_cost == 0.02
    assert result.max_cost == 0.03
    assert result.currency == "CNY"


def test_check_cost_budget_passes_when_equal_to_limit():
    cost_estimate = CostEstimate(
        total_cost=0.03,
        currency="CNY",
    )

    result = check_cost_budget(
        cost_estimate=cost_estimate,
        max_cost=0.03,
    )

    assert result.passed is True


def test_check_cost_budget_fails_when_over_limit():
    cost_estimate = CostEstimate(
        total_cost=0.05,
        currency="CNY",
    )

    result = check_cost_budget(
        cost_estimate=cost_estimate,
        max_cost=0.03,
    )

    assert result.passed is False
    assert result.actual_cost == 0.05
    assert result.max_cost == 0.03


def test_check_cost_budget_rejects_negative_limit():
    cost_estimate = CostEstimate(
        total_cost=0.01,
        currency="CNY",
    )

    with pytest.raises(
        ValueError,
        match="max_cost 不能小于 0",
    ):
        check_cost_budget(
            cost_estimate=cost_estimate,
            max_cost=-1,
        )


def test_raise_if_cost_exceeded_does_not_raise_when_under_limit():
    cost_estimate = CostEstimate(
        total_cost=0.02,
        currency="CNY",
    )

    raise_if_cost_exceeded(
        cost_estimate=cost_estimate,
        max_cost=0.03,
    )


def test_raise_if_cost_exceeded_raises_budget_error():
    cost_estimate = CostEstimate(
        total_cost=0.05,
        currency="CNY",
    )

    with pytest.raises(BudgetExceededError) as error:
        raise_if_cost_exceeded(
            cost_estimate=cost_estimate,
            max_cost=0.03,
        )

    assert error.value.actual_cost == 0.05
    assert error.value.max_cost == 0.03
    assert error.value.currency == "CNY"
    assert "本轮 Agent 成本超出预算" in str(error.value)