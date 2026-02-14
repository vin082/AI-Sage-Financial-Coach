"""
Product Eligibility Guidance — Phase 2, Epic 2.1 (P2)

Checks whether a customer's verified financial profile meets the
indicative eligibility criteria for banking products.

CRITICAL FCA DISTINCTION:
  This tool returns INDICATIVE ELIGIBILITY GUIDANCE only.
  It does NOT constitute:
    - A product offer
    - A Decision in Principle
    - Regulated financial advice
    - A credit assessment or credit decision

  All outputs use "may qualify" / "appears to meet" language,
  never "you qualify" or "you will be approved".

  Actual eligibility is determined by the lender's full underwriting
  process, credit checks and affordability assessment.

In production: eligibility rules would be maintained by product teams
and version-controlled separately from agent code.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


# ---------------------------------------------------------------------------
# Product eligibility rule registry
# ---------------------------------------------------------------------------
# Each rule is purely deterministic — income/surplus/balance thresholds.
# Rules are illustrative of typical banking criteria; not actual live criteria.

PRODUCT_RULES: dict[str, dict[str, Any]] = {
    "club_sage_account": {
        "name": "Club Sage Current Account",
        "type": "current_account",
        "description": "Earn lifestyle benefits and preferential savings rates",
        "indicative_criteria": {
            "min_monthly_income": Decimal("1500"),
            "min_monthly_pay_in": Decimal("1500"),
        },
        "benefit_summary": "Lifestyle benefit (cinema tickets, magazine subscription or dining card) + preferential savings rates",
        "disclaimer_required": True,
    },
    "easy_saver": {
        "name": "Easy Saver Account",
        "type": "savings",
        "description": "Flexible easy-access savings",
        "indicative_criteria": {
            "min_monthly_surplus": Decimal("50"),
        },
        "benefit_summary": "Accessible savings pot for short-term goals and emergency funds",
        "disclaimer_required": True,
    },
    "monthly_saver": {
        "name": "Monthly Saver",
        "type": "savings",
        "description": "Regular monthly savings with attractive rate",
        "indicative_criteria": {
            "min_monthly_surplus": Decimal("25"),
            "max_monthly_surplus": Decimal("400"),   # max deposit limit
        },
        "benefit_summary": "Save £25–£400/month at a preferential rate",
        "disclaimer_required": True,
    },
    "cash_isa": {
        "name": "Cash ISA",
        "type": "isa",
        "description": "Tax-free savings up to £20,000 per tax year",
        "indicative_criteria": {
            "min_monthly_surplus": Decimal("50"),
        },
        "benefit_summary": "Tax-free interest on savings — ideal if you pay income tax on savings interest",
        "disclaimer_required": True,
    },
    "personal_loan": {
        "name": "Personal Loan",
        "type": "credit",
        "description": "Fixed-rate personal loan",
        "indicative_criteria": {
            "min_monthly_income": Decimal("1000"),
            "min_monthly_surplus_after_committed": Decimal("100"),
            "max_debt_to_income_ratio": Decimal("0.40"),
        },
        "benefit_summary": "Fixed monthly repayments — predictable cost",
        "disclaimer_required": True,
        "regulated": True,
    },
}


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EligibilityOutcome:
    product_id: str
    product_name: str
    product_type: str
    description: str
    appears_eligible: bool
    eligibility_indicators: list[str]    # which criteria met
    eligibility_gaps: list[str]          # which criteria not met
    benefit_summary: str
    caveat: str                          # always present — FCA requirement


STANDARD_CAVEAT = (
    "This is indicative guidance only, based on your transaction data. "
    "It is not a product offer or guarantee of eligibility. "
    "Actual eligibility is subject to a full application, credit check "
    "and affordability assessment by the bank. "
    "Terms and conditions apply."
)


# ---------------------------------------------------------------------------
# Eligibility checker
# ---------------------------------------------------------------------------

def check_product_eligibility(
    net_monthly_income: Decimal,
    average_monthly_surplus: Decimal,
    current_balance: Decimal,
    product_ids: list[str] | None = None,
) -> list[EligibilityOutcome]:
    """
    Check indicative eligibility for banking products based on verified figures.
    All logic is deterministic — no LLM involved.

    Args:
        net_monthly_income:      from TransactionAnalyser
        average_monthly_surplus: from TransactionAnalyser
        current_balance:         from TransactionAnalyser
        product_ids:             subset of products to check (None = all)
    """
    products_to_check = (
        {k: v for k, v in PRODUCT_RULES.items() if k in product_ids}
        if product_ids
        else PRODUCT_RULES
    )

    outcomes: list[EligibilityOutcome] = []

    for product_id, rules in products_to_check.items():
        criteria = rules["indicative_criteria"]
        met: list[str] = []
        gaps: list[str] = []

        # Min monthly income
        if "min_monthly_income" in criteria:
            threshold = criteria["min_monthly_income"]
            if net_monthly_income >= threshold:
                met.append(f"Monthly income (£{net_monthly_income:.2f}) meets £{threshold:.2f} minimum")
            else:
                gaps.append(f"Monthly income (£{net_monthly_income:.2f}) is below £{threshold:.2f} minimum")

        # Min monthly surplus
        if "min_monthly_surplus" in criteria:
            threshold = criteria["min_monthly_surplus"]
            if average_monthly_surplus >= threshold:
                met.append(f"Monthly surplus (£{average_monthly_surplus:.2f}) meets £{threshold:.2f} minimum")
            else:
                gaps.append(f"Monthly surplus (£{average_monthly_surplus:.2f}) is below £{threshold:.2f} minimum")

        # Max monthly surplus (for regular saver deposit limit)
        if "max_monthly_surplus" in criteria:
            ceiling = criteria["max_monthly_surplus"]
            if average_monthly_surplus <= ceiling:
                met.append(f"Monthly surplus within £{ceiling:.2f} deposit limit")
            # Being over the ceiling is fine — customer can choose deposit amount

        # Debt-to-income ratio
        if "max_debt_to_income_ratio" in criteria:
            # We don't have actual debt data in this MVP — flag as unverifiable
            gaps.append("Debt-to-income ratio requires credit assessment — cannot be verified from transactions alone")

        appears_eligible = len(gaps) == 0 or (
            len(met) > 0 and all("credit assessment" in g for g in gaps)
        )

        outcomes.append(EligibilityOutcome(
            product_id=product_id,
            product_name=rules["name"],
            product_type=rules["type"],
            description=rules["description"],
            appears_eligible=appears_eligible,
            eligibility_indicators=met,
            eligibility_gaps=gaps,
            benefit_summary=rules["benefit_summary"],
            caveat=STANDARD_CAVEAT,
        ))

    # Sort: eligible products first
    outcomes.sort(key=lambda o: (not o.appears_eligible, o.product_type))
    return outcomes


def get_recommended_products(
    net_monthly_income: Decimal,
    average_monthly_surplus: Decimal,
    current_balance: Decimal,
) -> dict[str, Any]:
    """
    Return only the products the customer appears eligible for,
    filtered to the most relevant 3 based on their surplus profile.
    """
    all_outcomes = check_product_eligibility(
        net_monthly_income, average_monthly_surplus, current_balance
    )
    eligible = [o for o in all_outcomes if o.appears_eligible]

    return {
        "eligible_count": len(eligible),
        "products": [
            {
                "name": o.product_name,
                "type": o.product_type,
                "description": o.description,
                "benefit": o.benefit_summary,
                "why_eligible": o.eligibility_indicators[:2],
                "caveat": o.caveat,
            }
            for o in eligible[:3]
        ],
        "disclaimer": (
            "Product suggestions are based on your spending profile only. "
            "They are not personalised financial advice. "
            "Speak to an adviser for a full product assessment."
        ),
    }
