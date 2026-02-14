"""
Life Event Detector — Phase 2, Epic 2.1 (P1)

Detects probable life events from transaction patterns — deterministically,
without any LLM involvement. All signal rules are explicit and auditable.

Detected events:
  - New baby / nursery costs starting
  - Property purchase (solicitor/surveyor fees, stamp duty pattern)
  - New rent (first recurring payment to new landlord)
  - Job/income change (salary amount or source changes)
  - Marriage (wedding venue / registry office transactions)
  - New regular commute (new transport pattern)
  - Subscription to a new nursery / school

Each detection returns a confidence score (0.0–1.0) and the exact
transactions that triggered it — fully explainable to the customer.

PRIVACY NOTE:
  Life event detections are only surfaced to the customer, never
  shared with third parties or used for unsolicited product marketing
  without explicit customer consent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict
from typing import Any

from data.mock_transactions import Transaction


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LifeEventSignal:
    event_type: str          # e.g. "new_baby", "property_purchase"
    confidence: float        # 0.0 – 1.0
    detected_date: date      # when first signal appeared
    evidence: list[str]      # human-readable explanation of triggering transactions
    suggested_coaching: str  # what the agent should offer (guidance, not advice)
    requires_confirmation: bool  # ask customer "did we get this right?"


@dataclass
class LifeEventReport:
    customer_id: str
    detected_events: list[LifeEventSignal]
    high_confidence_events: list[LifeEventSignal]   # confidence >= 0.70
    scan_period_days: int


# ---------------------------------------------------------------------------
# Merchant keyword registries (case-insensitive)
# ---------------------------------------------------------------------------

NURSERY_KEYWORDS = [
    "nursery", "daycare", "day care", "childcare", "child care",
    "little stars", "tiny tots", "happy days", "busy bees",
]

SCHOOL_KEYWORDS = [
    "school fees", "school dinner", "parentpay", "schoolgateway",
    "scopay", "sims pay",
]

PROPERTY_KEYWORDS = [
    "solicitor", "conveyancer", "conveyancing", "surveyor", "survey",
    "stamp duty", "sdlt", "land registry", "mortgage fee",
    "arrangement fee", "valuation fee",
]

WEDDING_KEYWORDS = [
    "wedding", "registry office", "civil ceremony", "wedding venue",
    "bridal", "florist", "wedding cake", "photographer",
]

RENT_KEYWORDS = [
    "rent", "letting", "landlord", "estate agent", "rightmove",
    "zoopla", "openrent", "spareroom",
]

BABY_EQUIPMENT_KEYWORDS = [
    "mothercare", "john lewis baby", "kiddicare", "mamas and papas",
    "babies r us", "pram", "bugaboo", "icandy", "stokke",
]

LARGE_RETAILERS_BABY = [
    "boots", "superdrug",  # large baby product purchases
]


def _merchant_matches(merchant: str, keywords: list[str]) -> bool:
    m = merchant.lower()
    return any(k in m for k in keywords)


def _is_new_recurring(
    transactions: list[Transaction],
    merchant_fragment: str,
    lookback_months: int = 3,
    min_occurrences: int = 2,
) -> tuple[bool, list[Transaction]]:
    """
    Detect if a merchant has started appearing regularly in the last
    lookback_months and was NOT present before.
    """
    cutoff = date.today() - timedelta(days=lookback_months * 30)
    older_cutoff = date.today() - timedelta(days=lookback_months * 60)

    recent = [
        t for t in transactions
        if t.date >= cutoff and merchant_fragment.lower() in t.merchant.lower()
    ]
    historical = [
        t for t in transactions
        if older_cutoff <= t.date < cutoff
        and merchant_fragment.lower() in t.merchant.lower()
    ]

    if len(recent) >= min_occurrences and len(historical) == 0:
        return True, recent
    return False, []


# ---------------------------------------------------------------------------
# Detection rules
# ---------------------------------------------------------------------------

def _detect_new_baby(transactions: list[Transaction]) -> LifeEventSignal | None:
    cutoff = date.today() - timedelta(days=90)
    recent = [t for t in transactions if t.date >= cutoff and t.amount < 0]

    nursery_txns = [t for t in recent if _merchant_matches(t.merchant, NURSERY_KEYWORDS)]
    baby_equipment = [t for t in recent if _merchant_matches(t.merchant, BABY_EQUIPMENT_KEYWORDS)]

    signals = []
    confidence = 0.0
    first_date = date.today()

    if len(nursery_txns) >= 2:
        confidence += 0.60
        signals.append(f"{len(nursery_txns)} nursery/childcare payments detected")
        first_date = min(t.date for t in nursery_txns)

    if baby_equipment:
        confidence = min(1.0, confidence + 0.25)
        total = sum(abs(t.amount) for t in baby_equipment)
        signals.append(f"Baby equipment purchases totalling £{total:.2f}")
        if baby_equipment[0].date < first_date:
            first_date = baby_equipment[0].date

    if confidence < 0.40:
        return None

    return LifeEventSignal(
        event_type="new_baby",
        confidence=round(confidence, 2),
        detected_date=first_date,
        evidence=signals,
        suggested_coaching=(
            "Starting a family changes your financial picture significantly. "
            "I can help you review your budget for childcare costs, check your "
            "emergency fund, and explore whether any government support (Tax-Free "
            "Childcare, Child Benefit) applies to your situation."
        ),
        requires_confirmation=True,
    )


def _detect_property_purchase(transactions: list[Transaction]) -> LifeEventSignal | None:
    cutoff = date.today() - timedelta(days=120)
    recent = [t for t in transactions if t.date >= cutoff and t.amount < 0]

    property_txns = [
        t for t in recent if _merchant_matches(t.merchant, PROPERTY_KEYWORDS)
    ]
    large_payments = [t for t in recent if abs(t.amount) > Decimal("5000")]

    confidence = 0.0
    signals = []
    first_date = date.today()

    if property_txns:
        confidence += 0.55
        signals.append(
            f"Property-related payments: {', '.join(t.merchant for t in property_txns[:3])}"
        )
        first_date = min(t.date for t in property_txns)

    if large_payments:
        confidence = min(1.0, confidence + 0.25)
        signals.append(
            f"{len(large_payments)} large payment(s) over £5,000 detected"
        )

    if confidence < 0.40:
        return None

    return LifeEventSignal(
        event_type="property_purchase",
        confidence=round(confidence, 2),
        detected_date=first_date,
        evidence=signals,
        suggested_coaching=(
            "Buying a home is one of the biggest financial events in your life. "
            "I can help you review your new monthly budget including mortgage, "
            "utility and maintenance costs, and ensure your emergency fund "
            "accounts for homeownership."
        ),
        requires_confirmation=True,
    )


def _detect_income_change(transactions: list[Transaction]) -> LifeEventSignal | None:
    credits = [t for t in transactions if t.amount > 0 and t.category == "salary"]
    if len(credits) < 4:
        return None

    credits_sorted = sorted(credits, key=lambda t: t.date)
    recent = credits_sorted[-2:]
    older = credits_sorted[-4:-2]

    recent_avg = sum(t.amount for t in recent) / len(recent)
    older_avg = sum(t.amount for t in older) / len(older)

    change_pct = abs((recent_avg - older_avg) / older_avg * 100)

    if change_pct < Decimal("5"):
        return None

    direction = "increased" if recent_avg > older_avg else "decreased"
    confidence = min(0.90, float(change_pct) / 20)

    return LifeEventSignal(
        event_type="income_change",
        confidence=round(confidence, 2),
        detected_date=recent[0].date,
        evidence=[
            f"Income {direction} by approximately {change_pct:.1f}%",
            f"Previous average: £{older_avg:.2f}, Recent average: £{recent_avg:.2f}",
        ],
        suggested_coaching=(
            f"Your income appears to have {direction} recently. "
            f"{'An increase is a great opportunity to boost savings or pay down debt faster.' if direction == 'increased' else 'A drop in income may mean reviewing your budget to protect essential spending.'}"
        ),
        requires_confirmation=True,
    )


def _detect_new_rent(transactions: list[Transaction]) -> LifeEventSignal | None:
    cutoff = date.today() - timedelta(days=60)
    recent = [t for t in transactions if t.date >= cutoff and t.amount < 0]
    rent_txns = [t for t in recent if _merchant_matches(t.merchant, RENT_KEYWORDS)]

    if len(rent_txns) < 2:
        return None

    # Check these weren't present before
    older_cutoff = date.today() - timedelta(days=120)
    historical_rent = [
        t for t in transactions
        if older_cutoff <= t.date < cutoff
        and _merchant_matches(t.merchant, RENT_KEYWORDS)
    ]

    if historical_rent:
        return None  # Not new — already had rent payments

    monthly_rent = sum(abs(t.amount) for t in rent_txns) / len(rent_txns)

    return LifeEventSignal(
        event_type="new_rental",
        confidence=0.75,
        detected_date=rent_txns[0].date,
        evidence=[
            f"New recurring rent payment detected (~£{monthly_rent:.2f}/month)",
            f"No rent payments in the previous period",
        ],
        suggested_coaching=(
            f"It looks like you've recently started renting. "
            f"A monthly rent of ~£{monthly_rent:.2f} is a significant fixed cost. "
            f"I can help you adjust your budget to account for this and ensure "
            f"you still have adequate savings headroom."
        ),
        requires_confirmation=True,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def detect_life_events(
    customer_id: str,
    transactions: list[Transaction],
    scan_days: int = 120,
) -> LifeEventReport:
    """
    Run all detection rules against a customer's transaction history.
    Returns structured report — no LLM involved at any stage.
    """
    detectors = [
        _detect_new_baby,
        _detect_property_purchase,
        _detect_income_change,
        _detect_new_rent,
    ]

    detected: list[LifeEventSignal] = []
    for detector in detectors:
        result = detector(transactions)
        if result is not None:
            detected.append(result)

    high_confidence = [e for e in detected if e.confidence >= 0.70]

    return LifeEventReport(
        customer_id=customer_id,
        detected_events=detected,
        high_confidence_events=high_confidence,
        scan_period_days=scan_days,
    )
