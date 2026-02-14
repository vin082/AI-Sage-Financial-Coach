"""
AI Sage Financial Coach — FastAPI REST layer.

Endpoints:
  POST /chat              — Send a message to the coaching agent
  GET  /health-score      — Get customer financial health score
  GET  /spending-insights — Get spending breakdown
  GET  /savings-opps      — Get savings opportunities
  POST /session/new       — Create a new session

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
from data.mock_transactions import get_demo_customer

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
    allow_origins=["http://localhost:8501"],  # Streamlit dev origin
    allow_credentials=True,
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
def new_session(customer_id: str = Depends(verify_token)):
    """Create a new coaching session for the authenticated customer."""
    profile = get_demo_customer()   # Production: load from Customer 360 API
    session_id = str(uuid.uuid4())
    agent = CoachingAgent(profile)
    _agents[session_id] = agent
    return NewSessionResponse(
        session_id=session_id,
        customer_name=profile.name,
        message=f"Welcome back, {profile.name}! I'm AI Sage, your financial coach. How can I help you today?",
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


@app.get("/health")
def api_health():
    """API liveness check."""
    return {"status": "ok", "service": "AI Sage Financial Coach", "version": "0.1.0"}
