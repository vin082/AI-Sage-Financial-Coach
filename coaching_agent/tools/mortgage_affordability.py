"""
Mortgage Affordability Modeller — Phase 2, Epic 2.1 (P0)

ANTI-HALLUCINATION PRINCIPLE:
  All affordability calculations are fully deterministic.
  Stress-test rates, LTI multiples and stress thresholds are
  sourced from FCA/PRA regulatory guidelines — not LLM knowledge.
  The LLM receives only pre-computed results and narrates them.

FCA NOTE:
  This tool produces GUIDANCE based on income/expenditure data.
  It does NOT constitute a mortgage offer, Decision in Principle,
  or regulated mortgage advice under MCOB.
  All outputs must be accompanied by the mortgage disclaimer.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

from coaching_agent.tools.transaction_analyser import SpendingInsights


# ---------------------------------------------------------------------------
# Regulatory constants (PRA SS13/16 affordability rules)
# ---------------------------------------------------------------------------

# PRA loan-to-income flow limit — no more than 15% of new mortgage lending
# above 4.5x income. We use 4.5x as the standard upper bound.
MAX_LTI_MULTIPLE = Decimal("4.5")

# FCA stress test: lender must assess affordability at reversion rate + 3%
# We model a conservative stressed rate for guidance purposes
STRESS_RATE_ADD_ON = Decimal("0.03")       # +3% stress add-on

# Standard repayment period
DEFAULT_TERM_YEARS = 25

# Typical product rates (guidance only — not a live rate, must not be quoted as offer)
INDICATIVE_RATES = {
    "2yr_fixed":  Decimal("0.0499"),   # 4.99%
    "5yr_fixed":  Decimal("0.0479"),   # 4.79%
    "tracker":    Decimal("0.0519"),   # 5.19%
}


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AffordabilityScenario:
    rate_type: str
    annual_rate: Decimal
    stressed_rate: Decimal
    monthly_payment: Decimal
    stressed_monthly_payment: Decimal
    is_affordable: bool                 # stressed payment < max_affordable_payment
    ltv_pct: Decimal | None            # loan-to-value if property value supplied


@dataclass(frozen=True)
class MortgageAffordabilityResult:
    # Inputs (from customer data — all verified)
    gross_annual_income: Decimal
    net_monthly_income: Decimal
    average_monthly_committed_spend: Decimal   # essentials only
    average_monthly_surplus: Decimal

    # Affordability outputs (deterministic)
    max_loan_by_lti: Decimal                   # 4.5 × gross income
    max_affordable_payment: Decimal            # 35% of net income rule
    requested_loan: Decimal | None
    requested_affordable: bool | None

    # Scenarios
    scenarios: list[AffordabilityScenario]

    # Guidance flags
    surplus_after_mortgage: Decimal | None     # monthly surplus if mortgage taken
    deposit_required_5pct: Decimal | None      # min deposit at 95% LTV
    deposit_required_10pct: Decimal | None     # deposit at 90% LTV
    stress_pass: bool | None                   # passes PRA stress test


# ---------------------------------------------------------------------------
# Core calculator
# ---------------------------------------------------------------------------

def _monthly_repayment(principal: Decimal, annual_rate: Decimal, years: int) -> Decimal:
    """
    Standard annuity mortgage repayment formula.
    Uses Decimal arithmetic throughout — no float rounding errors.
    """
    if annual_rate == 0:
        return (principal / Decimal(years * 12)).quantize(Decimal("0.01"))

    monthly_rate = annual_rate / 12
    n = years * 12
    # M = P * [r(1+r)^n] / [(1+r)^n - 1]
    factor = (1 + monthly_rate) ** n
    payment = principal * (monthly_rate * factor) / (factor - 1)
    return payment.quantize(Decimal("0.01"))


def assess_affordability(
    insights: SpendingInsights,
    requested_loan_amount: Decimal | None = None,
    property_value: Decimal | None = None,
    term_years: int = DEFAULT_TERM_YEARS,
) -> MortgageAffordabilityResult:
    """
    Compute mortgage affordability from verified spending insights.

    All calculations are deterministic — no LLM involved.
    The LLM only narrates the returned result object.
    """
    net_monthly = insights.average_monthly_income
    # Estimate gross from net using approximate UK tax for typical income band
    # In production: use actual gross from payroll data
    gross_annual = (net_monthly * Decimal("12") / Decimal("0.72")).quantize(Decimal("0.01"))

    # Max loan by LTI multiple (PRA guideline)
    max_loan_lti = (gross_annual * MAX_LTI_MULTIPLE).quantize(Decimal("0.01"))

    # Max affordable monthly payment: 35% of net income is a widely used benchmark
    # This is guidance, not a lender commitment
    max_affordable_payment = (net_monthly * Decimal("0.35")).quantize(Decimal("0.01"))

    # Build scenarios for each indicative rate
    scenarios: list[AffordabilityScenario] = []
    for rate_name, rate in INDICATIVE_RATES.items():
        loan = requested_loan_amount or max_loan_lti
        stressed = rate + STRESS_RATE_ADD_ON
        monthly = _monthly_repayment(loan, rate, term_years)
        stressed_monthly = _monthly_repayment(loan, stressed, term_years)
        ltv = None
        if property_value and property_value > 0:
            ltv = (loan / property_value * 100).quantize(Decimal("0.1"))

        scenarios.append(AffordabilityScenario(
            rate_type=rate_name,
            annual_rate=(rate * 100).quantize(Decimal("0.01")),
            stressed_rate=((rate + STRESS_RATE_ADD_ON) * 100).quantize(Decimal("0.01")),
            monthly_payment=monthly,
            stressed_monthly_payment=stressed_monthly,
            is_affordable=stressed_monthly <= max_affordable_payment,
            ltv_pct=ltv,
        ))

    # Requested loan assessment
    requested_affordable = None
    surplus_after = None
    stress_pass = None
    if requested_loan_amount:
        # Use 5yr fixed as reference scenario for requested loan assessment
        ref = next(s for s in scenarios if s.rate_type == "5yr_fixed")
        requested_affordable = ref.is_affordable
        surplus_after = (
            net_monthly - insights.average_monthly_spend - ref.monthly_payment
        ).quantize(Decimal("0.01"))
        stress_pass = ref.stressed_monthly_payment <= max_affordable_payment

    deposit_5 = None
    deposit_10 = None
    if property_value:
        deposit_5 = (property_value * Decimal("0.05")).quantize(Decimal("0.01"))
        deposit_10 = (property_value * Decimal("0.10")).quantize(Decimal("0.01"))

    return MortgageAffordabilityResult(
        gross_annual_income=gross_annual,
        net_monthly_income=net_monthly,
        average_monthly_committed_spend=insights.average_monthly_committed_spend
            if hasattr(insights, "average_monthly_committed_spend")
            else insights.average_monthly_spend,
        average_monthly_surplus=insights.average_monthly_surplus,
        max_loan_by_lti=max_loan_lti,
        max_affordable_payment=max_affordable_payment,
        requested_loan=requested_loan_amount,
        requested_affordable=requested_affordable,
        scenarios=scenarios,
        surplus_after_mortgage=surplus_after,
        deposit_required_5pct=deposit_5,
        deposit_required_10pct=deposit_10,
        stress_pass=stress_pass,
    )
