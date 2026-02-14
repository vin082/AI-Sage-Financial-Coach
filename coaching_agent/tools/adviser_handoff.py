"""
Warm Adviser Handoff — Phase 2, Epic 2.1 (P1)

When a customer needs regulated advice, the agent assembles a full context
package and creates a handoff record so the human adviser receives:
  - Customer financial snapshot (verified figures)
  - The conversation that led to the escalation
  - The specific question or need that triggered the handoff
  - Detected life events (if any)
  - Customer goals

This eliminates the "start over" experience — the adviser picks up
exactly where the agent left off.

In production: this writes to the CRM (Salesforce / internal CRM)
via API. Here we return a structured handoff package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Handoff types
# ---------------------------------------------------------------------------

HANDOFF_REASONS = {
    "regulated_advice":     "Customer requires regulated financial advice",
    "mortgage_enquiry":     "Mortgage application or detailed mortgage advice",
    "investment_advice":    "Investment portfolio or ISA advice",
    "pension_advice":       "Pension planning or retirement advice",
    "complex_debt":         "Complex debt restructuring or IVA enquiry",
    "bereavement":          "Bereavement support and estate matters",
    "vulnerability":        "Customer vulnerability flag raised",
    "customer_requested":   "Customer explicitly requested to speak to an adviser",
    "complaint":            "Customer expressing dissatisfaction",
}

ADVISER_CHANNELS = {
    "phone":    "0800 072 7000",      # Financial planning line (stub)
    "branch":   "Find your nearest branch via the app",
    "callback": "Arrange a callback via the app or website",
    "video":    "Book a video appointment via the app or website",
}


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class HandoffPackage:
    """
    Complete context bundle passed to the human adviser.
    In production: POSTed to CRM API as a case/task record.
    """
    handoff_id: str
    created_at: datetime
    reason_code: str
    reason_description: str

    # Customer snapshot
    customer_id: str
    customer_name: str
    net_monthly_income: str
    average_monthly_spend: str
    average_monthly_surplus: str
    current_balance: str
    financial_health_score: int | None
    financial_health_grade: str | None

    # What brought them here
    triggering_question: str
    conversation_summary: list[dict[str, str]]   # last N turns

    # Enrichment
    active_goals: list[dict[str, Any]]
    detected_life_events: list[str]
    savings_opportunities_identified: int

    # Routing
    recommended_channel: str
    contact_details: str
    priority: str                    # "standard" | "urgent" | "vulnerable"

    # Agent notes (pre-computed, not LLM-generated)
    adviser_notes: list[str]


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_handoff_package(
    reason_code: str,
    triggering_question: str,
    customer_id: str,
    customer_name: str,
    conversation_history: list[dict[str, str]],
    spending_snapshot: dict[str, str],
    health_score: int | None = None,
    health_grade: str | None = None,
    goals: list[dict[str, Any]] | None = None,
    life_events: list[str] | None = None,
    savings_opps_count: int = 0,
    is_vulnerable: bool = False,
) -> HandoffPackage:
    """
    Assemble a complete adviser handoff package from session context.
    All content is structured data — the LLM does not generate the handoff.
    """
    import uuid

    reason_desc = HANDOFF_REASONS.get(reason_code, "Adviser assistance required")

    # Priority escalation
    if is_vulnerable or reason_code in ("bereavement", "vulnerability", "complaint"):
        priority = "urgent"
        channel = "phone"
    elif reason_code in ("mortgage_enquiry", "pension_advice", "investment_advice"):
        priority = "standard"
        channel = "callback"
    else:
        priority = "standard"
        channel = "callback"

    # Pre-compute adviser notes from structured data
    adviser_notes: list[str] = []
    surplus_str = spending_snapshot.get("average_monthly_surplus", "unknown")
    adviser_notes.append(
        f"Customer has a monthly surplus of {surplus_str} — financially active profile."
    )
    if goals:
        goal_summaries = [g.get("description", "") for g in goals if g.get("description")]
        if goal_summaries:
            adviser_notes.append(f"Active goals: {'; '.join(goal_summaries[:3])}")
    if life_events:
        adviser_notes.append(f"Recent life events detected: {', '.join(life_events)}")
    if health_score and health_score < 50:
        adviser_notes.append(
            f"Financial health score is {health_score}/100 (Grade {health_grade}) — "
            f"customer may benefit from broader financial review."
        )
    if savings_opps_count > 0:
        adviser_notes.append(
            f"{savings_opps_count} savings opportunity/ies identified by AI coach — "
            f"customer is engaged and open to optimisation."
        )

    return HandoffPackage(
        handoff_id=str(uuid.uuid4()),
        created_at=datetime.utcnow(),
        reason_code=reason_code,
        reason_description=reason_desc,
        customer_id=customer_id,
        customer_name=customer_name,
        net_monthly_income=spending_snapshot.get("average_monthly_income", "N/A"),
        average_monthly_spend=spending_snapshot.get("average_monthly_spend", "N/A"),
        average_monthly_surplus=spending_snapshot.get("average_monthly_surplus", "N/A"),
        current_balance=spending_snapshot.get("current_balance", "N/A"),
        financial_health_score=health_score,
        financial_health_grade=health_grade,
        triggering_question=triggering_question,
        conversation_summary=conversation_history[-6:],   # last 6 turns
        active_goals=goals or [],
        detected_life_events=life_events or [],
        savings_opportunities_identified=savings_opps_count,
        recommended_channel=channel,
        contact_details=ADVISER_CHANNELS[channel],
        priority=priority,
        adviser_notes=adviser_notes,
    )


def format_handoff_for_customer(package: HandoffPackage) -> dict[str, Any]:
    """
    Customer-facing summary of the handoff — what they see in the chat.
    """
    return {
        "handoff_reference": package.handoff_id[:8].upper(),
        "reason": package.reason_description,
        "next_step": f"Speak to a financial adviser via {package.recommended_channel}",
        "contact": package.contact_details,
        "context_shared": (
            "Your adviser will already have your financial summary, "
            "so you won't need to repeat yourself."
        ),
        "priority": package.priority,
        "adviser_has": [
            "Your spending and income summary",
            "Your financial health score",
            "Your active financial goals",
            "The question that brought you here",
        ],
    }
