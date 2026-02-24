---
name: Test Case Generator
description: Reads the AI Sage codebase — tools, guardrails, API endpoints, data models and memory — and generates a comprehensive pytest test suite covering happy paths, boundary values, edge cases and regression scenarios. Writes directly to the tests/ directory.
tools: Bash, Grep, Glob, Read, Write, Edit
model: sonnet
---
---

## Your Mission

Read the AI Sage Financial Coach codebase and generate production-quality pytest tests.
Your goal: every tool, guardrail pattern, API endpoint and data model must have meaningful tests.

**Test philosophy for this app:**
- Financial figures must be tested with `Decimal` not `float`
- Every guardrail pattern needs both a should-trigger and should-NOT-trigger test
- Anti-hallucination tests verify `grounded_amounts` is populated before the LLM runs
- Session isolation tests ensure one customer's data never leaks to another

---

## Step 0: Audit Existing Tests

First, read what tests already exist:
```bash
find tests/ -name "*.py" | sort
```

For each existing test file, note:
- Which component it covers
- What is missing (no edge cases, no error paths, no Decimal tests)

Then check test config:
```bash
cat pyproject.toml  # or pytest.ini / setup.cfg
```

---

## Step 1: Generate Guardrails Tests — `tests/test_guardrails.py`

Read `coaching_agent/guardrails.py` fully before writing.

Generate tests for every pattern category:

```python
"""Tests for coaching_agent/guardrails.py"""
import pytest
from coaching_agent.guardrails import (
    check_input, check_output, apply_disclaimer,
    GuardResult, IntentType, extract_grounded_amounts,
)

# ---- Input guard: regulated advice ----
class TestRegulatedAdviceBlocking:
    @pytest.mark.parametrize("msg", [
        "Which stocks should I buy?",
        "Tell me which ISA to put my money in",
        "What pension should I take out?",
        "I want to invest £10,000 — what should I invest in?",
        "Give me tax advice",
    ])
    def test_blocks_regulated_advice(self, msg):
        result = check_input(msg)
        assert result.result == GuardResult.BLOCK
        assert result.safe_response is not None

    @pytest.mark.parametrize("msg", [
        "What is an ISA?",
        "Explain the 50/30/20 rule",
        "How much am I spending on groceries?",
        "What is my financial health score?",
        "Help me set a savings goal",
    ])
    def test_allows_guidance_queries(self, msg):
        result = check_input(msg)
        assert result.result == GuardResult.PASS

# ---- Input guard: out-of-scope ----
class TestOutOfScopeBlocking:
    @pytest.mark.parametrize("msg", [
        "What is the capital of France?",
        "Write me a poem",
        "Who won the World Cup?",
    ])
    def test_blocks_out_of_scope(self, msg):
        result = check_input(msg)
        assert result.result in (GuardResult.BLOCK, GuardResult.REDIRECT)

# ---- Input guard: financial distress ----
class TestDistressSignposting:
    @pytest.mark.parametrize("msg", [
        "I cant pay bill this month",      # apostrophe-free
        "I can't pay my bills",
        "cant afford rent",
        "bailiff came to my door",
        "I might go bankrupt",
        "overwhelmed by debt",
        "struggling to pay my mortgage",
        "I cannot afford my loan payments",
        "debt collectors keep calling",
        "facing repossession",
    ])
    def test_triggers_distress_signpost(self, msg):
        result = check_input(msg)
        assert result.result == GuardResult.REDIRECT
        assert "MoneyHelper" in result.safe_response
        assert "StepChange" in result.safe_response
        assert "0800" in result.safe_response  # free phone number present

    @pytest.mark.parametrize("msg", [
        "I want to save more money",
        "Help me reduce my bills",
        "I'd like to pay off my credit card",
        "Can I afford a holiday?",
    ])
    def test_does_not_trigger_distress_for_normal_queries(self, msg):
        result = check_input(msg)
        assert result.result != GuardResult.REDIRECT or "MoneyHelper" not in (result.safe_response or "")

# ---- Output guard ----
class TestOutputGuard:
    def test_blocks_ungrounded_amount(self):
        result = check_output("Your monthly spend is £1,234.56", grounded_amounts=set())
        assert result.result == GuardResult.FAIL

    def test_passes_grounded_amount(self):
        result = check_output("Your monthly spend is £1,234.56", grounded_amounts={"£1,234.56"})
        assert result.result == GuardResult.PASS

    def test_passes_response_with_no_amounts(self):
        result = check_output("That is a great goal to work towards.", grounded_amounts=set())
        assert result.result == GuardResult.PASS

    def test_blocks_multiple_with_one_ungrounded(self):
        # £100.00 grounded but £999.99 is not
        result = check_output(
            "Your spend is £100.00 and your savings target is £999.99",
            grounded_amounts={"£100.00"}
        )
        assert result.result == GuardResult.FAIL

# ---- FCA disclaimer ----
class TestFCADisclaimer:
    @pytest.mark.parametrize("keyword", [
        "mortgage", "ISA", "pension", "investment", "loan", "bond", "annuity"
    ])
    def test_disclaimer_added_for_regulated_keywords(self, keyword):
        response = apply_disclaimer(f"Consider a {keyword} for your goals.")
        assert "guidance" in response.lower() or "not regulated" in response.lower() or \
               "financial adviser" in response.lower()

    def test_no_disclaimer_for_general_guidance(self):
        response = apply_disclaimer("Your spending looks healthy this month.")
        # Disclaimer should not be appended to non-regulated content
        # (it may still be there if always appended — verify the design intent)
        assert len(response) >= len("Your spending looks healthy this month.")

# ---- Extract grounded amounts ----
class TestExtractGroundedAmounts:
    def test_extracts_gbp_strings(self):
        result_dict = {"income": "£3,200.00", "spend": "£2,100.50"}
        amounts = extract_grounded_amounts(result_dict)
        assert "£3,200.00" in amounts
        assert "£2,100.50" in amounts

    def test_ignores_non_monetary_strings(self):
        result_dict = {"grade": "A", "trend": "increasing", "months": "3"}
        amounts = extract_grounded_amounts(result_dict)
        assert len(amounts) == 0  # or just the sentinel £0.00

    def test_nested_dict_extraction(self):
        result_dict = {"category": {"amount": "£150.00", "name": "Groceries"}}
        amounts = extract_grounded_amounts(result_dict)
        assert "£150.00" in amounts
```

---

## Step 2: Generate Tool Tests — `tests/test_tools.py`

Read each tool in `coaching_agent/tools/` before generating.

Key patterns:
```python
"""Tests for coaching_agent tools"""
import pytest
from decimal import Decimal
from data.mock_transactions import get_demo_customer
from coaching_agent.tools.transaction_analyser import TransactionAnalyser
from coaching_agent.tools.financial_health import compute_health_score
from coaching_agent.tools.mortgage_affordability import assess_affordability
from coaching_agent.tools.debt_savings_tradeoff import analyse_tradeoff
from coaching_agent.tools.budget_planner import build_budget_plan

class TestTransactionAnalyser:
    def setup_method(self):
        self.profile = get_demo_customer()
        self.analyser = TransactionAnalyser(self.profile)

    def test_returns_decimal_not_float(self):
        insights = self.analyser.get_full_insights(months=3)
        assert isinstance(insights.average_monthly_income, Decimal)
        assert isinstance(insights.average_monthly_spend, Decimal)
        assert isinstance(insights.average_monthly_surplus, Decimal)

    def test_surplus_equals_income_minus_spend(self):
        insights = self.analyser.get_full_insights(months=3)
        expected = insights.average_monthly_income - insights.average_monthly_spend
        assert abs(insights.average_monthly_surplus - expected) < Decimal("0.01")

    def test_months_boundary_clamped(self):
        # months should be clamped to 1-6
        insights_low = self.analyser.get_full_insights(months=0)
        insights_high = self.analyser.get_full_insights(months=99)
        assert insights_low is not None
        assert insights_high is not None

    def test_top_categories_non_empty(self):
        insights = self.analyser.get_full_insights(months=3)
        assert len(insights.top_categories) > 0

    def test_top_categories_sorted_by_spend(self):
        insights = self.analyser.get_full_insights(months=3)
        spends = [c.total_spend for c in insights.top_categories]
        assert spends == sorted(spends, reverse=True)

class TestFinancialHealth:
    def setup_method(self):
        self.profile = get_demo_customer()
        self.analyser = TransactionAnalyser(self.profile)

    def test_score_in_valid_range(self):
        insights = self.analyser.get_full_insights(months=3)
        report = compute_health_score(insights)
        assert 0 <= report.overall_score <= 100

    def test_pillar_scores_sum_to_overall(self):
        insights = self.analyser.get_full_insights(months=3)
        report = compute_health_score(insights)
        pillar_sum = sum(p.score for p in report.pillars)
        assert pillar_sum == report.overall_score

    def test_grade_matches_score(self):
        insights = self.analyser.get_full_insights(months=3)
        report = compute_health_score(insights)
        if report.overall_score >= 80:
            assert report.overall_grade == "A"
        elif report.overall_score >= 60:
            assert report.overall_grade == "B"

    def test_five_pillars_returned(self):
        insights = self.analyser.get_full_insights(months=3)
        report = compute_health_score(insights)
        assert len(report.pillars) == 5

class TestMortgageAffordability:
    def test_stress_test_adds_three_percent(self):
        result = assess_affordability(
            net_monthly_income=Decimal("3000"),
            average_monthly_spend=Decimal("1500"),
            requested_loan=Decimal("200000"),
            mortgage_term_years=25,
            interest_rate=Decimal("4.5"),
        )
        # Stress rate should be interest_rate + 3.0
        assert result.stress_test_rate == Decimal("7.5")

    def test_lti_multiple_capped_at_4_5(self):
        result = assess_affordability(
            net_monthly_income=Decimal("5000"),
            average_monthly_spend=Decimal("2000"),
            requested_loan=Decimal("500000"),
            mortgage_term_years=25,
            interest_rate=Decimal("4.5"),
        )
        annual_income = Decimal("5000") * 12
        assert result.max_loan_by_income_multiple <= annual_income * Decimal("4.5")

    def test_uses_decimal_not_float(self):
        result = assess_affordability(
            net_monthly_income=Decimal("3000"),
            average_monthly_spend=Decimal("1500"),
            requested_loan=Decimal("200000"),
            mortgage_term_years=25,
            interest_rate=Decimal("4.5"),
        )
        assert isinstance(result.monthly_payment, Decimal)
        assert isinstance(result.max_loan_by_income_multiple, Decimal)
```

---

## Step 3: Generate API Tests — `tests/test_api.py`

Read `api/main.py` before generating:

```python
"""Tests for FastAPI endpoints"""
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)
HEADERS = {"Authorization": "Bearer demo-token-alex"}

class TestSessionNew:
    def test_returns_session_id(self):
        response = client.post("/session/new", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 36  # UUID format

    def test_welcome_message_contains_ai_disclosure(self):
        response = client.post("/session/new", headers=HEADERS)
        msg = response.json()["message"].lower()
        assert "ai" in msg or "artificial intelligence" in msg
        assert "not a human" in msg or "ai assistant" in msg

    def test_welcome_message_contains_guidance_disclaimer(self):
        response = client.post("/session/new", headers=HEADERS)
        msg = response.json()["message"].lower()
        assert "guidance" in msg
        assert "not regulated" in msg or "not financial advice" in msg

    def test_rejects_missing_auth(self):
        response = client.post("/session/new")
        assert response.status_code in (401, 403)

class TestChatEndpoint:
    def setup_method(self):
        resp = client.post("/session/new", headers=HEADERS)
        self.session_id = resp.json()["session_id"]

    def test_response_schema(self):
        response = client.post("/chat", headers=HEADERS, json={
            "session_id": self.session_id,
            "message": "What is a savings rate?"
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "response" in data
        assert "tools_used" in data
        assert "tool_trace" in data
        assert "chart_data" in data  # may be null but field must exist

    def test_distress_message_returns_signpost(self):
        response = client.post("/chat", headers=HEADERS, json={
            "session_id": self.session_id,
            "message": "I cant pay bill this month"
        })
        text = response.json()["response"]
        assert "MoneyHelper" in text
        assert "0800" in text

    def test_regulated_advice_blocked(self):
        response = client.post("/chat", headers=HEADERS, json={
            "session_id": self.session_id,
            "message": "Which stocks should I buy?"
        })
        text = response.json()["response"].lower()
        assert "can't help" in text or "unable to" in text or "adviser" in text

    def test_invalid_session_returns_error(self):
        response = client.post("/chat", headers=HEADERS, json={
            "session_id": "invalid-session-id",
            "message": "Hello"
        })
        assert response.status_code in (400, 404, 422)

class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
```

---

## Step 4: Generate Memory Tests — `tests/test_memory.py`

```python
"""Tests for session and customer memory"""
import pytest
from coaching_agent.memory import (
    create_session, SessionMemory, get_or_create_customer,
)

class TestSessionMemory:
    def test_tool_trace_resets_between_turns(self):
        session = create_session("test-session", "CUST_001")
        session.tool_trace.append({"tool": "get_spending_insights"})
        session.tool_trace = []  # simulates reset at chat() start
        assert session.tool_trace == []

    def test_chart_data_defaults_to_none(self):
        session = create_session("test-session-2", "CUST_001")
        assert session.chart_data is None

    def test_grounded_amounts_is_set(self):
        session = create_session("test-session-3", "CUST_001")
        assert isinstance(session.grounded_amounts, set)

    def test_session_isolation(self):
        session1 = create_session("s1", "CUST_001")
        session2 = create_session("s2", "CUST_002")
        session1.grounded_amounts.add("£999.99")
        assert "£999.99" not in session2.grounded_amounts
```

---

## Step 5: Generate Chart Extraction Tests — `tests/test_chart_extraction.py`

```python
"""Tests for _extract_chart_data in CoachingAgent"""
import json, pytest
from coaching_agent.agent import CoachingAgent

class TestExtractChartData:
    def test_spending_donut_chart(self):
        payload = json.dumps({"top_categories": [
            {"category": "Groceries", "monthly_average": "£854.67"},
            {"category": "Transport", "monthly_average": "£536.17"},
        ]})
        result = CoachingAgent._extract_chart_data("get_spending_insights", payload)
        assert result is not None
        assert result["type"] == "donut"
        assert "Groceries" in result["labels"]
        assert 854.67 in result["values"]

    def test_health_radar_chart(self):
        payload = json.dumps({
            "overall_score": 85,
            "overall_grade": "A",
            "pillars": [
                {"name": "Savings Rate", "score": "28/30"},
                {"name": "Spend Stability", "score": "18/20"},
            ]
        })
        result = CoachingAgent._extract_chart_data("get_financial_health_score", payload)
        assert result is not None
        assert result["type"] == "radar"
        assert "85/100" in result["title"] or "85" in result["title"]

    def test_trends_line_chart(self):
        payload = json.dumps({"timeline": [
            {"month": "2025-11", "income": "£3200.00", "spend": "£2100.00"},
            {"month": "2025-12", "income": "£3200.00", "spend": "£2300.00"},
        ]})
        result = CoachingAgent._extract_chart_data("get_long_term_trends_tool", payload)
        assert result is not None
        assert result["type"] == "line"
        assert len(result["income"]) == 2

    def test_unknown_tool_returns_none(self):
        result = CoachingAgent._extract_chart_data("search_guidance", '{"results": []}')
        assert result is None

    def test_invalid_json_returns_none(self):
        result = CoachingAgent._extract_chart_data("get_spending_insights", "not json")
        assert result is None

    def test_empty_categories_returns_none(self):
        result = CoachingAgent._extract_chart_data(
            "get_spending_insights", '{"top_categories": []}'
        )
        assert result is None
```

---

## Step 6: Write All Files and Run

After generating all test files, run:
```bash
cd "e:/LBG Customer AI Super Agent" && .venv/Scripts/pytest tests/ -v --tb=short 2>&1 | head -80
```

Fix any import errors or API mismatches before finalising.

---

## Output

1. Write test files directly to `tests/test_guardrails.py`, `tests/test_tools.py`,
   `tests/test_api.py`, `tests/test_memory.py`, `tests/test_chart_extraction.py`
2. **MANDATORY: Use the Write tool to save the summary to disk.**

First get today's date:
```bash
python3 -c "from datetime import date; print(date.today())"
```

Then call the Write tool with:
- **file_path**: `e:/LBG Customer AI Super Agent/docs/test-reports/YYYY-MM-DD-test-generation-summary.md` (replace YYYY-MM-DD with today's date)
- **content**: the completed summary markdown below

The file MUST exist on disk after the Write tool call completes.

Content:

```markdown
# Test Generation Report — [Date]

## Files Generated
| File | Tests Generated | Components Covered |
|------|----------------|-------------------|

## Coverage Estimate
| Module | Before | After (estimated) |
|--------|--------|------------------|

## Known Gaps (deferred to next sprint)
```
