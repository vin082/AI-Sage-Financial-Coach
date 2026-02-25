"""
AI Sage Financial Coach — FastAPI REST layer.

Endpoints:
  POST /chat              — Send a message to the coaching agent
  GET  /health-score      — Get customer financial health score
  GET  /spending-insights — Get spending breakdown
  GET  /savings-opps      — Get savings opportunities
  POST /session/new       — Create a new session
  POST /session/end       — End a session (generates + persists summary)

All endpoints are authenticated (Bearer token stub — replace with
Azure AD B2C / SSO in production).
"""

from __future__ import annotations

import os
import uuid
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

from coaching_agent.agent import CoachingAgent
from coaching_agent.tools.financial_health import compute_health_score
from coaching_agent.tools.transaction_analyser import TransactionAnalyser
from data.mock_transactions import (
    get_demo_customer,
    get_demo_customer_with_life_events,
    get_persona_spontaneous_spender,
    get_persona_cautious_planner,
    get_persona_reactive_manager,
    get_persona_balanced_achiever,
)

# Map customer IDs to their persona loader functions
_PERSONA_LOADERS = {
    "CUST_DEMO_002": get_demo_customer_with_life_events,
    "CUST_DEMO_003": get_persona_spontaneous_spender,
    "CUST_DEMO_004": get_persona_cautious_planner,
    "CUST_DEMO_005": get_persona_reactive_manager,
    "CUST_DEMO_006": get_persona_balanced_achiever,
}

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Sage Financial Coach API",
    version="0.1.0",
    description="Phase 1 MVP — Coaching Agent",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Allow file:// and any localhost origin for demo
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory agent store (production: Redis-backed session pool)
# ---------------------------------------------------------------------------

_agents: dict[str, CoachingAgent] = {}


def _get_agent(session_id: str) -> CoachingAgent:
    if session_id not in _agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found. Call POST /session/new first.",
        )
    return _agents[session_id]


# ---------------------------------------------------------------------------
# Auth stub
# ---------------------------------------------------------------------------

def verify_token(authorization: Annotated[str | None, Header()] = None) -> str:
    """
    Stub token verification.
    In production: validate Azure AD B2C JWT, extract customer_id from claims.
    """
    if not authorization:
        # Allow unauthenticated in demo mode
        if os.getenv("DEMO_MODE", "true").lower() == "true":
            return "CUST_DEMO_001"
        raise HTTPException(status_code=401, detail="Authorization header required.")
    return "CUST_DEMO_001"


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class NewSessionResponse(BaseModel):
    session_id: str
    customer_name: str
    message: str


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    session_id: str
    response: str
    tools_used: list[str]
    tool_trace: list[dict]   # [{tool, args, result_summary}] for explainability panel
    chart_data: dict | None = None   # Structured data for inline Chart.js rendering


class HealthScoreResponse(BaseModel):
    customer_id: str
    overall_score: int
    overall_grade: str
    summary: str
    pillars: list[dict]
    savings_rate: str
    months_buffer: str


class SpendingInsightsResponse(BaseModel):
    customer_id: str
    average_monthly_income: str
    average_monthly_spend: str
    average_monthly_surplus: str
    current_balance: str
    spend_trend: str
    top_categories: list[dict]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/session/new", response_model=NewSessionResponse)
def new_session(
    customer_id: str | None = None,          # optional query param from HTML demo
    auth_customer_id: str = Depends(verify_token),
):
    """Create a new coaching session for the authenticated customer."""
    # Resolve profile: query param takes precedence for demo, else use auth identity
    resolved_id = customer_id or auth_customer_id
    loader = _PERSONA_LOADERS.get(resolved_id, get_demo_customer)
    profile = loader()
    session_id = str(uuid.uuid4())
    agent = CoachingAgent(profile)
    _agents[session_id] = agent
    return NewSessionResponse(
        session_id=session_id,
        customer_name=profile.name,
        message=(
            f"Hi {profile.name}! I'm **AI Sage** — an AI assistant, not a human financial adviser.\n\n"
            "I provide personalised **financial guidance** based on your verified transaction data. "
            "This is **not regulated financial advice** under FSMA 2000. "
            "For regulated advice on investments, pensions or mortgages, I can connect you with a qualified adviser at any time.\n\n"
            "How can I help you today?"
        ),
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, customer_id: str = Depends(verify_token)):
    """Send a message to the coaching agent and receive a grounded response."""
    agent = _get_agent(request.session_id)
    response = agent.chat(request.message)
    return ChatResponse(
        session_id=request.session_id,
        response=response,
        tools_used=agent.session.tool_calls_made[-5:],  # Last 5 tool calls
        tool_trace=agent.session.tool_trace,             # Full trace for explainability
        chart_data=agent.session.chart_data,             # Inline chart for spending/health/trends
    )


@app.get("/health-score", response_model=HealthScoreResponse)
def health_score(customer_id: str = Depends(verify_token)):
    """Return the customer's financial health score."""
    profile = get_demo_customer()
    analyser = TransactionAnalyser(profile)
    insights = analyser.get_full_insights(months=3)
    report = compute_health_score(insights)

    return HealthScoreResponse(
        customer_id=profile.customer_id,
        overall_score=report.overall_score,
        overall_grade=report.overall_grade,
        summary=report.summary,
        pillars=[
            {
                "name": p.name,
                "score": p.score,
                "max_score": p.max_score,
                "grade": p.grade,
                "explanation": p.explanation,
            }
            for p in report.pillars
        ],
        savings_rate=f"{report.savings_rate_pct}%",
        months_buffer=f"{report.months_buffer} months",
    )


@app.get("/spending-insights", response_model=SpendingInsightsResponse)
def spending_insights(months: int = 3, customer_id: str = Depends(verify_token)):
    """Return verified spending insights for the customer."""
    months = max(1, min(6, months))
    profile = get_demo_customer()
    analyser = TransactionAnalyser(profile)
    insights = analyser.get_full_insights(months=months)

    return SpendingInsightsResponse(
        customer_id=profile.customer_id,
        average_monthly_income=f"£{insights.average_monthly_income:.2f}",
        average_monthly_spend=f"£{insights.average_monthly_spend:.2f}",
        average_monthly_surplus=f"£{insights.average_monthly_surplus:.2f}",
        current_balance=f"£{insights.current_balance_estimate:.2f}",
        spend_trend=insights.spend_trend,
        top_categories=[
            {
                "category": c.category.replace("_", " ").title(),
                "monthly_average": f"£{(c.total_spend / insights.analysis_period_months):.2f}",
            }
            for c in insights.top_categories
        ],
    )


@app.get("/session/profile")
def session_profile(session_id: str, customer_id: str = Depends(verify_token)):
    """
    Return lightweight customer profile for the onboarding flow.
    Tells the UI whether this is a first visit and what goals/prefs already exist.
    """
    agent = _get_agent(session_id)
    mem = agent.customer_memory
    return {
        "customer_name": agent.profile.name,
        "conversation_count": mem.conversation_count,
        "is_first_visit": mem.conversation_count == 0,
        "active_goals": [
            {
                "goal_id": g.goal_id,
                "description": g.description,
                "target_amount": g.target_amount,
                "target_date": g.target_date,
            }
            for g in mem.active_goals
        ],
        "preferences": {
            "preferred_tone": mem.preferences.preferred_tone,
            "preferred_topics": mem.preferences.preferred_topics,
        },
    }


@app.post("/session/end")
def end_session(session_id: str, customer_id: str = Depends(verify_token)):
    """
    End a coaching session — generates a session summary and persists it
    to the customer store for context continuity in future sessions.
    Removes the agent from the in-memory pool.
    """
    agent = _get_agent(session_id)
    agent.end_session()      # generates summary + saves to JSON store
    _agents.pop(session_id, None)
    return {"status": "ok", "session_id": session_id, "message": "Session ended and summary saved."}


@app.get("/health")
def api_health():
    """API liveness check."""
    return {"status": "ok", "service": "AI Sage Financial Coach", "version": "0.1.0"}
