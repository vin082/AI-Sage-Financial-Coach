"""
Savings vs Debt Trade-Off Modeller — Phase 2, Epic 2.1 (P0)

ANTI-HALLUCINATION PRINCIPLE:
  All projections use deterministic compound interest / amortisation maths.
  No LLM is involved in any numerical calculation.
  The LLM narrates the pre-computed comparison only.

FCA NOTE:
  This tool provides comparative GUIDANCE only.
  It does NOT constitute regulated financial advice.
  The optimal decision depends on individual tax position, risk
  appetite and full financial circumstances — a qualified adviser
  should be consulted for personalised recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DebtPaydownProjection:
    """Outcome of putting a fixed monthly amount toward debt repayment."""
    strategy: str                        # "minimum_only" | "overpay"
    extra_monthly_payment: Decimal
    months_to_payoff: int
    total_interest_paid: Decimal
    total_paid: Decimal
    interest_saved_vs_minimum: Decimal


@dataclass(frozen=True)
class SavingsProjection:
    """Outcome of putting the same monthly amount into savings."""
    monthly_amount: Decimal
    annual_rate: Decimal
    years: int
    final_balance: Decimal
    total_contributed: Decimal
    interest_earned: Decimal


@dataclass(frozen=True)
class TradeOffResult:
    """
    Side-by-side comparison: overpay debt vs save the same amount.
    Includes a clear recommendation based on the interest rate differential.
    """
    monthly_amount_available: Decimal    # surplus the customer can deploy

    # Debt scenario
    debt_balance: Decimal
    debt_interest_rate: Decimal          # annual %
    debt_paydown: DebtPaydownProjection
    debt_minimum_only: DebtPaydownProjection

    # Savings scenario (same monthly amount)
    savings_rate: Decimal                # annual % (indicative)
    savings_projection: SavingsProjection

    # Decision metrics
    net_benefit_of_debt_paydown: Decimal  # interest saved - interest earned
    rate_differential: Decimal            # debt rate - savings rate
    recommendation: str                   # "pay_debt_first" | "save_first" | "split"
    recommendation_reason: str

    # Mortgage overpayment specific (if applicable)
    is_mortgage: bool
    mortgage_term_reduction_months: int | None


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

def _months_to_payoff(
    balance: Decimal,
    annual_rate: Decimal,
    monthly_payment: Decimal,
) -> tuple[int, Decimal]:
    """
    Simulate loan amortisation month by month.
    Returns (months_to_payoff, total_interest_paid).
    """
    if annual_rate == 0:
        months = int((balance / monthly_payment).to_integral_value()) + 1
        return months, Decimal("0")

    monthly_rate = annual_rate / 12
    remaining = balance
    total_interest = Decimal("0")
    months = 0
    max_iterations = 600  # 50 years safety cap

    while remaining > 0 and months < max_iterations:
        interest = (remaining * monthly_rate).quantize(Decimal("0.01"))
        principal = monthly_payment - interest
        if principal <= 0:
            # Payment doesn't cover interest — infinite debt
            return 9999, Decimal("999999.99")
        total_interest += interest
        remaining -= principal
        months += 1

    return months, total_interest.quantize(Decimal("0.01"))


def _compound_savings(
    monthly: Decimal,
    annual_rate: Decimal,
    years: int,
) -> Decimal:
    """Standard future value of monthly contributions with compound interest."""
    if annual_rate == 0:
        return (monthly * years * 12).quantize(Decimal("0.01"))
    monthly_rate = annual_rate / 12
    n = years * 12
    fv = monthly * ((((1 + monthly_rate) ** n) - 1) / monthly_rate)
    return fv.quantize(Decimal("0.01"))


def analyse_tradeoff(
    debt_balance: Decimal,
    debt_annual_rate: Decimal,
    current_minimum_payment: Decimal,
    monthly_surplus: Decimal,
    savings_annual_rate: Decimal,
    is_mortgage: bool = False,
    mortgage_original_term_months: int | None = None,
) -> TradeOffResult:
    """
    Compare: apply monthly_surplus to debt vs put it into savings.
    All arithmetic is deterministic — zero LLM involvement.
    """
    # --- Debt scenarios ---
    # Scenario A: minimum payments only
    min_months, min_interest = _months_to_payoff(
        debt_balance, debt_annual_rate, current_minimum_payment
    )
    minimum_projection = DebtPaydownProjection(
        strategy="minimum_only",
        extra_monthly_payment=Decimal("0"),
        months_to_payoff=min_months,
        total_interest_paid=min_interest,
        total_paid=(current_minimum_payment * min_months).quantize(Decimal("0.01")),
        interest_saved_vs_minimum=Decimal("0"),
    )

    # Scenario B: minimum + monthly surplus overpayment
    overpay_payment = current_minimum_payment + monthly_surplus
    op_months, op_interest = _months_to_payoff(
        debt_balance, debt_annual_rate, overpay_payment
    )
    interest_saved = (min_interest - op_interest).quantize(Decimal("0.01"))
    overpay_projection = DebtPaydownProjection(
        strategy="overpay",
        extra_monthly_payment=monthly_surplus,
        months_to_payoff=op_months,
        total_interest_paid=op_interest,
        total_paid=(overpay_payment * op_months).quantize(Decimal("0.01")),
        interest_saved_vs_minimum=interest_saved,
    )

    # Mortgage term reduction
    term_reduction = None
    if is_mortgage and mortgage_original_term_months:
        term_reduction = mortgage_original_term_months - op_months

    # --- Savings scenario ---
    # Put the same monthly_surplus into savings for the same period as debt payoff
    years_equivalent = max(1, op_months // 12)
    savings_balance = _compound_savings(
        monthly_surplus, savings_annual_rate, years_equivalent
    )
    total_contributed = (monthly_surplus * years_equivalent * 12).quantize(Decimal("0.01"))
    interest_earned = (savings_balance - total_contributed).quantize(Decimal("0.01"))

    savings_proj = SavingsProjection(
        monthly_amount=monthly_surplus,
        annual_rate=(savings_annual_rate * 100).quantize(Decimal("0.02")),
        years=years_equivalent,
        final_balance=savings_balance,
        total_contributed=total_contributed,
        interest_earned=interest_earned,
    )

    # --- Decision logic ---
    rate_diff = (debt_annual_rate - savings_annual_rate).quantize(Decimal("0.01"))
    net_benefit = (interest_saved - interest_earned).quantize(Decimal("0.01"))

    if rate_diff > Decimal("0.02"):       # debt rate > savings rate by >2%
        recommendation = "pay_debt_first"
        reason = (
            f"Your debt rate ({(debt_annual_rate*100):.1f}%) is {(rate_diff*100):.1f}% higher "
            f"than the savings rate ({(savings_annual_rate*100):.1f}%). Overpaying saves "
            f"£{interest_saved:.2f} in interest — more than the £{interest_earned:.2f} "
            f"you'd earn saving the same amount."
        )
    elif rate_diff < Decimal("-0.005"):   # savings rate meaningfully beats debt rate
        recommendation = "save_first"
        reason = (
            f"The savings rate ({(savings_annual_rate*100):.1f}%) exceeds your debt rate "
            f"({(debt_annual_rate*100):.1f}%). Your money works harder in savings than "
            f"paying down this debt early."
        )
    else:
        recommendation = "split"
        reason = (
            f"Rates are close ({(debt_annual_rate*100):.1f}% debt vs "
            f"{(savings_annual_rate*100):.1f}% savings). A split approach — "
            f"half to debt overpayment, half to savings — balances flexibility "
            f"with cost reduction."
        )

    return TradeOffResult(
        monthly_amount_available=monthly_surplus,
        debt_balance=debt_balance,
        debt_interest_rate=(debt_annual_rate * 100).quantize(Decimal("0.01")),
        debt_paydown=overpay_projection,
        debt_minimum_only=minimum_projection,
        savings_rate=(savings_annual_rate * 100).quantize(Decimal("0.01")),
        savings_projection=savings_proj,
        net_benefit_of_debt_paydown=net_benefit,
        rate_differential=(rate_diff * 100).quantize(Decimal("0.02")),
        recommendation=recommendation,
        recommendation_reason=reason,
        is_mortgage=is_mortgage,
        mortgage_term_reduction_months=term_reduction,
    )
