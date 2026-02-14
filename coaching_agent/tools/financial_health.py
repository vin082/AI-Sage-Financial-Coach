"""
Financial Health Score Calculator — 100% deterministic, zero LLM involvement.

Scoring is rule-based and fully auditable, critical for FCA compliance
and customer trust.  Every score can be traced back to a specific
transaction-derived metric.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from coaching_agent.tools.transaction_analyser import SpendingInsights


# ---------------------------------------------------------------------------
# Scoring components (max points per pillar)
# ---------------------------------------------------------------------------

MAX_SCORE = 100

PILLAR_WEIGHTS = {
    "savings_rate":       30,   # % of income saved each month
    "spend_stability":    20,   # consistency of month-on-month spend
    "essentials_ratio":   20,   # essentials vs discretionary balance
    "subscription_load":  15,   # subscription overhead as % of income
    "surplus_buffer":     15,   # months of expenses covered by current balance
}


@dataclass(frozen=True)
class HealthPillar:
    name: str
    score: int
    max_score: int
    grade: str          # A / B / C / D
    explanation: str    # plain-English, data-backed explanation (no LLM)


@dataclass(frozen=True)
class FinancialHealthReport:
    customer_id: str
    overall_score: int
    overall_grade: str
    summary: str
    pillars: list[HealthPillar]
    # Raw metrics surfaced for full auditability
    savings_rate_pct: Decimal
    essentials_pct: Decimal
    subscription_pct: Decimal
    months_buffer: Decimal


ESSENTIAL_CATEGORIES = {"groceries", "utilities", "transport", "health"}
DISCRETIONARY_CATEGORIES = {"eating_out", "entertainment", "shopping", "subscriptions", "cash_withdrawal"}


def _grade(score: int, max_score: int) -> str:
    ratio = score / max_score
    if ratio >= 0.85:
        return "A"
    if ratio >= 0.70:
        return "B"
    if ratio >= 0.50:
        return "C"
    return "D"


def compute_health_score(insights: SpendingInsights) -> FinancialHealthReport:
    """
    Compute a fully deterministic financial health score.

    All inputs come from pre-verified SpendingInsights — no LLM can
    alter the numbers at this stage.
    """
    pillars: list[HealthPillar] = []

    income = insights.average_monthly_income
    spend = insights.average_monthly_spend

    # ----------------------------------------------------------------
    # 1. Savings Rate (0-30 pts)
    # ----------------------------------------------------------------
    savings_rate = (
        (income - spend) / income
        if income > 0
        else Decimal("0")
    )
    savings_rate_pct = (savings_rate * 100).quantize(Decimal("0.1"))

    if savings_rate >= Decimal("0.20"):
        sr_score = 30
        sr_explanation = f"Excellent — saving {savings_rate_pct}% of income (target: ≥20%)."
    elif savings_rate >= Decimal("0.10"):
        sr_score = 20
        sr_explanation = f"Good — saving {savings_rate_pct}% of income. Aim for 20% to score higher."
    elif savings_rate >= Decimal("0.05"):
        sr_score = 10
        sr_explanation = f"Fair — saving {savings_rate_pct}% of income. Small increases make a big difference."
    else:
        sr_score = max(0, int(float(savings_rate * 100)))
        sr_explanation = f"Needs attention — saving only {savings_rate_pct}% of income. Consider a savings pot."

    pillars.append(HealthPillar(
        name="Savings Rate",
        score=sr_score,
        max_score=30,
        grade=_grade(sr_score, 30),
        explanation=sr_explanation,
    ))

    # ----------------------------------------------------------------
    # 2. Spend Stability (0-20 pts)
    # ----------------------------------------------------------------
    monthly_spends = [s.total_debit for s in insights.monthly_summaries]
    if len(monthly_spends) >= 2:
        avg = sum(monthly_spends) / len(monthly_spends)
        variance = sum((x - avg) ** 2 for x in monthly_spends) / len(monthly_spends)
        std_dev = variance.sqrt()
        cv = (std_dev / avg * 100).quantize(Decimal("0.1")) if avg > 0 else Decimal("0")
    else:
        cv = Decimal("0")

    if cv < Decimal("10"):
        ss_score = 20
        ss_explanation = f"Very stable spending (variation: {cv}%). Great budgeting consistency."
    elif cv < Decimal("20"):
        ss_score = 15
        ss_explanation = f"Mostly stable (variation: {cv}%). Minor month-to-month swings."
    elif cv < Decimal("35"):
        ss_score = 8
        ss_explanation = f"Moderate variation ({cv}%) — some months spend significantly more."
    else:
        ss_score = 3
        ss_explanation = f"High variation ({cv}%) — spending is unpredictable. A monthly budget could help."

    pillars.append(HealthPillar(
        name="Spend Stability",
        score=ss_score,
        max_score=20,
        grade=_grade(ss_score, 20),
        explanation=ss_explanation,
    ))

    # ----------------------------------------------------------------
    # 3. Essentials Ratio (0-20 pts)
    # ----------------------------------------------------------------
    total_spend_all = sum(
        c.total_spend for c in insights.top_categories
    )
    essentials_total = sum(
        c.total_spend for c in insights.top_categories
        if c.category in ESSENTIAL_CATEGORIES
    )
    essentials_pct = (
        (essentials_total / total_spend_all * 100).quantize(Decimal("0.1"))
        if total_spend_all > 0
        else Decimal("0")
    )

    if essentials_pct <= Decimal("60"):
        er_score = 20
        er_explanation = f"Healthy balance — {essentials_pct}% on essentials, leaving room for savings."
    elif essentials_pct <= Decimal("75"):
        er_score = 13
        er_explanation = f"{essentials_pct}% of spend on essentials — limited discretionary headroom."
    else:
        er_score = 5
        er_explanation = f"{essentials_pct}% on essentials is high. Review fixed costs where possible."

    pillars.append(HealthPillar(
        name="Essentials Balance",
        score=er_score,
        max_score=20,
        grade=_grade(er_score, 20),
        explanation=er_explanation,
    ))

    # ----------------------------------------------------------------
    # 4. Subscription Load (0-15 pts)
    # ----------------------------------------------------------------
    sub_pct = (
        (insights.subscription_monthly_cost / income * 100).quantize(Decimal("0.1"))
        if income > 0
        else Decimal("0")
    )

    if sub_pct <= Decimal("3"):
        sub_score = 15
        sub_explanation = f"Low subscription load ({sub_pct}% of income = £{insights.subscription_monthly_cost}/mo)."
    elif sub_pct <= Decimal("6"):
        sub_score = 10
        sub_explanation = f"Moderate subscriptions ({sub_pct}% of income = £{insights.subscription_monthly_cost}/mo). Worth an annual review."
    else:
        sub_score = 4
        sub_explanation = f"High subscription load ({sub_pct}% of income = £{insights.subscription_monthly_cost}/mo). Consider consolidating."

    pillars.append(HealthPillar(
        name="Subscription Load",
        score=sub_score,
        max_score=15,
        grade=_grade(sub_score, 15),
        explanation=sub_explanation,
    ))

    # ----------------------------------------------------------------
    # 5. Surplus Buffer (0-15 pts)
    # ----------------------------------------------------------------
    months_buffer = (
        (insights.current_balance_estimate / spend).quantize(Decimal("0.1"))
        if spend > 0
        else Decimal("0")
    )

    if months_buffer >= Decimal("3"):
        buf_score = 15
        buf_explanation = f"Strong buffer — {months_buffer} months of expenses in account (target: ≥3 months)."
    elif months_buffer >= Decimal("1"):
        buf_score = 8
        buf_explanation = f"{months_buffer} months buffer. Building to 3 months provides a solid safety net."
    else:
        buf_score = 3
        buf_explanation = f"Low buffer ({months_buffer} months). Priority: build an emergency fund."

    pillars.append(HealthPillar(
        name="Emergency Buffer",
        score=buf_score,
        max_score=15,
        grade=_grade(buf_score, 15),
        explanation=buf_explanation,
    ))

    # ----------------------------------------------------------------
    # Overall
    # ----------------------------------------------------------------
    overall = sum(p.score for p in pillars)
    grade = _grade(overall, MAX_SCORE)

    grade_summaries = {
        "A": "Your finances are in great shape. Keep it up.",
        "B": "Good financial health with a few areas to optimise.",
        "C": "Some improvements could significantly boost your position.",
        "D": "Your finances need attention — let's identify quick wins.",
    }

    return FinancialHealthReport(
        customer_id=insights.customer_id,
        overall_score=overall,
        overall_grade=grade,
        summary=grade_summaries[grade],
        pillars=pillars,
        savings_rate_pct=savings_rate_pct,
        essentials_pct=essentials_pct,
        subscription_pct=sub_pct,
        months_buffer=months_buffer,
    )
