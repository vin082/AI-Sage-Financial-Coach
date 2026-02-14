"""
Customer Memory — session context + persistent preferences.

Two tiers:
  - SessionMemory:    in-memory, single conversation (cleared on session end)
  - CustomerMemory:   persistent goals, preferences, past summaries
                      (in production: stored in Cosmos DB / Redis)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class FinancialGoal:
    goal_id: str
    description: str
    target_amount: float | None
    target_date: date | None
    created_at: datetime = field(default_factory=datetime.utcnow)
    progress_notes: list[str] = field(default_factory=list)


@dataclass
class CustomerMemory:
    """
    Persistent customer context — survives between sessions.
    In production: loaded from / saved to a secure customer data store.
    """
    customer_id: str
    name: str
    goals: list[FinancialGoal] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    last_health_score: int | None = None
    last_health_score_date: date | None = None
    previous_insights_summary: str | None = None
    conversation_count: int = 0

    def add_goal(self, description: str, target_amount: float | None = None,
                 target_date: date | None = None) -> FinancialGoal:
        goal = FinancialGoal(
            goal_id=f"GOAL_{len(self.goals) + 1:03d}",
            description=description,
            target_amount=target_amount,
            target_date=target_date,
        )
        self.goals.append(goal)
        return goal

    def update_health_score(self, score: int) -> None:
        self.last_health_score = score
        self.last_health_score_date = date.today()


@dataclass
class SessionMemory:
    """
    Per-conversation context — cleared at session end.
    Holds the current conversation history and loaded data.
    """
    session_id: str
    customer_id: str
    messages: list[dict[str, str]] = field(default_factory=list)
    loaded_insights: dict[str, Any] | None = None
    grounded_amounts: set[str] = field(default_factory=set)
    tool_calls_made: list[str] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

    def get_history(self) -> list[dict[str, str]]:
        """Return conversation history for LLM context window."""
        return self.messages[-10:]  # Last 10 turns to control token usage

    def register_tool_call(self, tool_name: str) -> None:
        self.tool_calls_made.append(tool_name)


# ---------------------------------------------------------------------------
# In-memory store (production: replace with Redis / Cosmos DB)
# ---------------------------------------------------------------------------

_customer_store: dict[str, CustomerMemory] = {}
_session_store: dict[str, SessionMemory] = {}


def get_or_create_customer(customer_id: str, name: str) -> CustomerMemory:
    if customer_id not in _customer_store:
        _customer_store[customer_id] = CustomerMemory(
            customer_id=customer_id,
            name=name,
        )
    return _customer_store[customer_id]


def create_session(session_id: str, customer_id: str) -> SessionMemory:
    session = SessionMemory(session_id=session_id, customer_id=customer_id)
    _session_store[session_id] = session
    return session


def get_session(session_id: str) -> SessionMemory | None:
    return _session_store.get(session_id)
