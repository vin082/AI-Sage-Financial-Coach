"""
Goal-Based Budget Planner — Phase 2, Epic 2.1 (P0)

Produces a deterministic, personalised budget plan based on:
  1. Customer's verified spending data (from TransactionAnalyser)
  2. Customer's stated goals (from CustomerMemory)
  3. 50/30/20 framework as the baseline allocation model

ANTI-HALLUCINATION PRINCIPLE:
  All budget allocations and goal projections are computed from
  verified income/spend figures. The LLM only narrates the plan.

FCA NOTE:
  Budget guidance only. Not regulated financial advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any


# ---------------------------------------------------------------------------
# 50/30/20 reference allocations
# ---------------------------------------------------------------------------

FRAMEWORK_ALLOCATIONS = {
    "needs":   Decimal("0.50"),   # essentials: housing, utilities, groceries, transport
    "wants":   Decimal("0.30"),   # discretionary: eating out, entertainment, shopping
    "savings": Decimal("0.20"),   # savings + debt repayment
}

ESSENTIAL_CATEGORIES = {"groceries", "utilities", "transport", "health"}
DISCRETIONARY_CATEGORIES = {"eating_out", "entertainment", "shopping",
                             "subscriptions", "cash_withdrawal", "other"}


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BudgetAllocation:
    bucket: str                     # "needs" | "wants" | "savings"
    recommended_monthly: Decimal    # 50/30/20 target
    actual_monthly: Decimal         # from transaction data
    variance: Decimal               # actual - recommended (positive = overspending)
    variance_pct: Decimal           # variance as % of recommended
    status: str                     # "on_track" | "over" | "under"
    categories_included: list[str]


@dataclass(frozen=True)
class GoalPlan:
    goal_id: str
    description: str
    target_amount: Decimal
    target_date: date | None
    monthly_required: Decimal       # amount needed per month to hit goal
    months_to_target: int | None
    achievable: bool                # can be funded from current surplus
    shortfall_monthly: Decimal      # 0 if achievable
    on_current_trajectory: bool     # will they hit it at current savings rate?


@dataclass
class BudgetPlan:
    net_monthly_income: Decimal
    framework: str                  # "50/30/20"

    # Allocations
    allocations: list[BudgetAllocation]

    # Goal plans
    goal_plans: list[GoalPlan]

    # Overall surplus/deficit after goals
    total_goal_monthly_required: Decimal
    discretionary_surplus_after_goals: Decimal
    budget_is_viable: bool

    # Recommendations (pre-computed, not LLM-generated)
    recommendations: list[str]


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

def _months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def build_budget_plan(
    net_monthly_income: Decimal,
    category_monthly_actuals: dict[str, Decimal],
    goals: list[dict[str, Any]],    # from CustomerMemory.goals serialised to dict
) -> BudgetPlan:
    """
    Build a complete budget plan from verified income and spending data.
    All arithmetic is deterministic — zero LLM involvement.

    Args:
        net_monthly_income: verified average monthly income from TransactionAnalyser
        category_monthly_actuals: {category: avg_monthly_spend} from TransactionAnalyser
        goals: list of goal dicts with keys: goal_id, description,
               target_amount, target_date (optional)
    """
    today = date.today()

    # --- Bucket actuals from transaction categories ---
    needs_actual = sum(
        category_monthly_actuals.get(c, Decimal("0"))
        for c in ESSENTIAL_CATEGORIES
    )
    wants_actual = sum(
        category_monthly_actuals.get(c, Decimal("0"))
        for c in DISCRETIONARY_CATEGORIES
    )
    # Savings = income - needs - wants (residual)
    savings_actual = max(
        Decimal("0"),
        net_monthly_income - needs_actual - wants_actual,
    )

    actuals = {
        "needs":   needs_actual.quantize(Decimal("0.01")),
        "wants":   wants_actual.quantize(Decimal("0.01")),
        "savings": savings_actual.quantize(Decimal("0.01")),
    }

    bucket_categories = {
        "needs":   list(ESSENTIAL_CATEGORIES),
        "wants":   list(DISCRETIONARY_CATEGORIES),
        "savings": ["savings_transfer", "debt_repayment"],
    }

    # --- Build allocations ---
    allocations: list[BudgetAllocation] = []
    for bucket, pct in FRAMEWORK_ALLOCATIONS.items():
        recommended = (net_monthly_income * pct).quantize(Decimal("0.01"))
        actual = actuals[bucket]
        variance = (actual - recommended).quantize(Decimal("0.01"))
        variance_pct = (
            (variance / recommended * 100).quantize(Decimal("0.1"))
            if recommended > 0 else Decimal("0")
        )
        if abs(variance_pct) <= Decimal("5"):
            status = "on_track"
        elif variance > 0:
            status = "over"
        else:
            status = "under"

        allocations.append(BudgetAllocation(
            bucket=bucket,
            recommended_monthly=recommended,
            actual_monthly=actual,
            variance=variance,
            variance_pct=variance_pct,
            status=status,
            categories_included=bucket_categories[bucket],
        ))

    # --- Goal planning ---
    available_for_goals = savings_actual  # what's actually left each month
    goal_plans: list[GoalPlan] = []
    total_goal_required = Decimal("0")

    for g in goals:
        target = Decimal(str(g.get("target_amount") or 0))
        if target <= 0:
            continue

        target_date_raw = g.get("target_date")
        months_to_target = None
        monthly_required = Decimal("0")

        if target_date_raw:
            if isinstance(target_date_raw, str):
                target_date = date.fromisoformat(target_date_raw)
            else:
                target_date = target_date_raw
            months_to_target = max(1, _months_between(today, target_date))
            monthly_required = (target / months_to_target).quantize(Decimal("0.01"))
        else:
            # No date: suggest a default 12-month timeline
            months_to_target = 12
            monthly_required = (target / 12).quantize(Decimal("0.01"))

        achievable = monthly_required <= available_for_goals
        shortfall = max(
            Decimal("0"),
            (monthly_required - available_for_goals).quantize(Decimal("0.01")),
        )
        on_trajectory = savings_actual >= monthly_required
        total_goal_required += monthly_required

        goal_plans.append(GoalPlan(
            goal_id=g.get("goal_id", ""),
            description=g.get("description", ""),
            target_amount=target,
            target_date=target_date_raw if isinstance(target_date_raw, date) else None,
            monthly_required=monthly_required,
            months_to_target=months_to_target,
            achievable=achievable,
            shortfall_monthly=shortfall,
            on_current_trajectory=on_trajectory,
        ))

    discretionary_surplus = (
        savings_actual - total_goal_required
    ).quantize(Decimal("0.01"))
    budget_viable = discretionary_surplus >= Decimal("0")

    # --- Pre-computed recommendations (no LLM) ---
    recommendations: list[str] = []

    wants_alloc = next(a for a in allocations if a.bucket == "wants")
    needs_alloc = next(a for a in allocations if a.bucket == "needs")
    savings_alloc = next(a for a in allocations if a.bucket == "savings")

    if wants_alloc.status == "over":
        monthly_overspend = wants_alloc.variance
        recommendations.append(
            f"Discretionary spending is £{monthly_overspend:.2f}/mo over the 30% target. "
            f"Reducing this would free up £{(monthly_overspend*12):.2f} per year."
        )
    if savings_alloc.status == "under":
        gap = abs(savings_alloc.variance)
        recommendations.append(
            f"Savings are £{gap:.2f}/mo below the 20% target. "
            f"Even a small standing order increase on payday would close this gap."
        )
    if not budget_viable:
        recommendations.append(
            f"Your goals require £{total_goal_required:.2f}/mo but your current surplus "
            f"is £{savings_actual:.2f}/mo. Consider extending goal timelines or "
            f"reducing discretionary spend."
        )
    if needs_alloc.status == "over" and needs_alloc.variance_pct > Decimal("15"):
        recommendations.append(
            f"Essential spending is {needs_alloc.variance_pct}% above target. "
            f"Review fixed costs like utilities and subscriptions for savings."
        )
    if not recommendations:
        recommendations.append(
            "Your budget is well-balanced. Keep up the consistent approach."
        )

    return BudgetPlan(
        net_monthly_income=net_monthly_income,
        framework="50/30/20",
        allocations=allocations,
        goal_plans=goal_plans,
        total_goal_monthly_required=total_goal_required.quantize(Decimal("0.01")),
        discretionary_surplus_after_goals=discretionary_surplus,
        budget_is_viable=budget_viable,
        recommendations=recommendations,
    )
