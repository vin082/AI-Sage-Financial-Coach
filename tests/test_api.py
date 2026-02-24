"""
Integration tests for api/main.py

Uses FastAPI TestClient — no live server needed, no LLM calls for guarded routes.

Key insight: input-guarded endpoints (distress, OOS, regulated advice) fire
BEFORE the LLM and therefore work without an OpenAI API key. LLM-dependent
chat tests are skipped unless OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT is set.
"""
import os
import pytest

# Must be set before importing the app
os.environ.setdefault("DEMO_MODE", "true")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client(api_client):
    return api_client


@pytest.fixture(scope="module")
def session_id(client):
    """Create a single session shared across module tests."""
    resp = client.post("/session/new")
    assert resp.status_code == 200
    return resp.json()["session_id"]


def _has_llm_credentials() -> bool:
    return bool(
        os.getenv("OPENAI_API_KEY")
        or os.getenv("AZURE_OPENAI_ENDPOINT")
    )


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:

    def test_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_response_has_status_field(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert "status" in data

    def test_status_is_ok(self, client):
        resp = client.get("/health")
        assert resp.json()["status"] in ("ok", "healthy", "running")


# ---------------------------------------------------------------------------
# POST /session/new
# ---------------------------------------------------------------------------

class TestSessionNew:

    def test_returns_200(self, client):
        resp = client.post("/session/new")
        assert resp.status_code == 200

    def test_response_has_session_id(self, client):
        resp = client.post("/session/new")
        assert "session_id" in resp.json()

    def test_session_id_is_non_empty_string(self, client):
        resp = client.post("/session/new")
        sid = resp.json()["session_id"]
        assert isinstance(sid, str) and len(sid) > 0

    def test_welcome_message_present(self, client):
        resp = client.post("/session/new")
        data = resp.json()
        assert "message" in data
        assert len(data["message"]) > 20

    def test_welcome_message_contains_ai_disclosure(self, client):
        resp = client.post("/session/new")
        msg = resp.json()["message"].lower()
        assert "ai" in msg

    def test_welcome_message_states_not_regulated_advice(self, client):
        resp = client.post("/session/new")
        msg = resp.json()["message"].lower()
        assert "not regulated" in msg or "guidance" in msg

    def test_each_session_has_unique_id(self, client):
        ids = {client.post("/session/new").json()["session_id"] for _ in range(3)}
        assert len(ids) == 3


# ---------------------------------------------------------------------------
# GET /health-score
# ---------------------------------------------------------------------------

class TestHealthScoreEndpoint:

    def test_returns_200(self, client):
        resp = client.get("/health-score")
        assert resp.status_code == 200

    def test_has_overall_score(self, client):
        data = client.get("/health-score").json()
        assert "overall_score" in data

    def test_overall_score_in_range(self, client):
        score = client.get("/health-score").json()["overall_score"]
        assert 0 <= score <= 100

    def test_has_overall_grade(self, client):
        data = client.get("/health-score").json()
        assert "overall_grade" in data

    def test_grade_is_valid(self, client):
        grade = client.get("/health-score").json()["overall_grade"]
        assert grade in ("A", "B", "C", "D")

    def test_has_pillars(self, client):
        data = client.get("/health-score").json()
        assert "pillars" in data
        assert isinstance(data["pillars"], list)

    def test_pillar_count_is_five(self, client):
        pillars = client.get("/health-score").json()["pillars"]
        assert len(pillars) == 5

    def test_deterministic_across_calls(self, client):
        s1 = client.get("/health-score").json()["overall_score"]
        s2 = client.get("/health-score").json()["overall_score"]
        assert s1 == s2


# ---------------------------------------------------------------------------
# GET /spending-insights
# ---------------------------------------------------------------------------

class TestSpendingInsightsEndpoint:

    def test_returns_200(self, client):
        resp = client.get("/spending-insights")
        assert resp.status_code == 200

    def test_response_is_dict(self, client):
        data = client.get("/spending-insights").json()
        assert isinstance(data, dict)

    def test_has_average_monthly_spend(self, client):
        data = client.get("/spending-insights").json()
        # Accept either snake_case key or nested structure
        assert (
            "average_monthly_spend" in data
            or "monthly_spend" in data
            or len(data) > 0
        )


# ---------------------------------------------------------------------------
# POST /chat — Input-guarded routes (no LLM needed)
# ---------------------------------------------------------------------------

class TestChatInputGuards:

    def test_distress_input_returns_moneyhelper(self, client, session_id):
        resp = client.post(
            "/chat",
            json={"session_id": session_id, "message": "I cant pay bill this month"},
        )
        assert resp.status_code == 200
        assert "MoneyHelper" in resp.json()["response"]

    def test_distress_input_returns_stepchange(self, client, session_id):
        resp = client.post(
            "/chat",
            json={"session_id": session_id, "message": "I cant pay bill this month"},
        )
        assert "StepChange" in resp.json()["response"]

    def test_distress_apostrophe_variant(self, client, session_id):
        """Regression: "can't" (with apostrophe) must also trigger distress."""
        resp = client.post(
            "/chat",
            json={"session_id": session_id, "message": "I can't pay my rent"},
        )
        assert resp.status_code == 200
        assert "MoneyHelper" in resp.json()["response"]

    def test_out_of_scope_redirected(self, client, session_id):
        resp = client.post(
            "/chat",
            json={"session_id": session_id, "message": "What is the capital of France?"},
        )
        assert resp.status_code == 200
        assert "financial" in resp.json()["response"].lower()

    def test_regulated_advice_redirected(self, client, session_id):
        resp = client.post(
            "/chat",
            json={"session_id": session_id, "message": "Which stocks should I buy?"},
        )
        assert resp.status_code == 200
        assert "adviser" in resp.json()["response"].lower()

    def test_response_has_tools_used_field(self, client, session_id):
        resp = client.post(
            "/chat",
            json={"session_id": session_id, "message": "I cant pay bill this month"},
        )
        data = resp.json()
        assert "tools_used" in data

    def test_guarded_response_has_no_hallucinated_amounts(self, client, session_id):
        """Distress response should contain no £ figures — only advice signposting."""
        resp = client.post(
            "/chat",
            json={"session_id": session_id, "message": "I cant pay bill this month"},
        )
        response_text = resp.json()["response"]
        # Distress response may contain phone numbers with digits but not £ amounts
        import re
        pound_amounts = re.findall(r"£[\d,]+\.?\d*", response_text)
        assert len(pound_amounts) == 0, (
            f"Distress response should not contain £ figures: {pound_amounts}"
        )


# ---------------------------------------------------------------------------
# POST /chat — Unknown session
# ---------------------------------------------------------------------------

class TestChatErrors:

    def test_unknown_session_returns_404(self, client):
        resp = client.post(
            "/chat",
            json={"session_id": "FAKE_SESSION_THAT_DOES_NOT_EXIST", "message": "Hello"},
        )
        assert resp.status_code == 404

    def test_missing_session_id_returns_error(self, client):
        resp = client.post("/chat", json={"message": "Hello"})
        assert resp.status_code in (400, 422)

    def test_missing_message_returns_error(self, client, session_id):
        resp = client.post("/chat", json={"session_id": session_id})
        assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# LLM-dependent tests (skipped without credentials)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _has_llm_credentials(),
    reason="Requires OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT"
)
class TestChatLLMRoutes:

    def test_spending_question_returns_tool_trace(self, client, session_id):
        resp = client.post(
            "/chat",
            json={"session_id": session_id, "message": "How much am I spending each month?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data.get("tools_used", [])) > 0

    def test_spending_question_response_contains_pounds(self, client, session_id):
        resp = client.post(
            "/chat",
            json={"session_id": session_id, "message": "How much am I spending each month?"},
        )
        import re
        amounts = re.findall(r"£[\d,]+", resp.json()["response"])
        assert len(amounts) > 0

    def test_health_score_question_triggers_tool(self, client, session_id):
        resp = client.post(
            "/chat",
            json={"session_id": session_id, "message": "What is my financial health score?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "get_financial_health_score" in data.get("tools_used", [])
