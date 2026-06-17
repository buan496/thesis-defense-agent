from dataclasses import dataclass

from app.agent_models import CostEstimate


@dataclass
class BudgetCheckResult:
    passed: bool
    actual_cost: float
    max_cost: float
    currency: str


class BudgetExceededError(RuntimeError):
    def __init__(
        self,
        actual_cost: float,
        max_cost: float,
        currency: str,
    ):
        self.actual_cost = actual_cost
        self.max_cost = max_cost
        self.currency = currency

        super().__init__(
            f"本轮 Agent 成本超出预算："
            f"{actual_cost:.6f} {currency} > "
            f"{max_cost:.6f} {currency}"
        )


def check_cost_budget(
    cost_estimate: CostEstimate,
    max_cost: float,
) -> BudgetCheckResult:
    if max_cost < 0:
        raise ValueError("max_cost 不能小于 0")

    passed = cost_estimate.total_cost <= max_cost

    return BudgetCheckResult(
        passed=passed,
        actual_cost=cost_estimate.total_cost,
        max_cost=max_cost,
        currency=cost_estimate.currency,
    )


def raise_if_cost_exceeded(
    cost_estimate: CostEstimate,
    max_cost: float,
) -> None:
    result = check_cost_budget(
        cost_estimate=cost_estimate,
        max_cost=max_cost,
    )

    if not result.passed:
        raise BudgetExceededError(
            actual_cost=result.actual_cost,
            max_cost=result.max_cost,
            currency=result.currency,
        )
        
class PreflightBudgetExceededError(RuntimeError):
    def __init__(
        self,
        estimated_cost: float,
        max_cost: float,
        currency: str,
        estimated_total_tokens: int,
    ):
        self.estimated_cost = estimated_cost
        self.max_cost = max_cost
        self.currency = currency
        self.estimated_total_tokens = estimated_total_tokens

        super().__init__(
            f"调用前预算预估超限："
            f"{estimated_cost:.6f} {currency} > "
            f"{max_cost:.6f} {currency}，"
            f"预计 tokens：{estimated_total_tokens}"
        )