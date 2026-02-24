"""
Tests for CoachingAgent._extract_chart_data() static method.

This method converts raw tool JSON results into Chart.js-compatible
structured data without involving the LLM.

Chart types:
  - donut    → get_spending_insights
  - radar    → get_financial_health_score
  - line     → get_long_term_trends_tool
"""
import json
import pytest


def _extract(tool_name: str, result_str: str):
    """Thin wrapper to call the static method under test."""
    from coaching_agent.agent import CoachingAgent
    return CoachingAgent._extract_chart_data(tool_name, result_str)


# ---------------------------------------------------------------------------
# Spending Insights → Donut chart
# ---------------------------------------------------------------------------

class TestSpendingInsightsDonut:

    SPENDING_DATA = {
        "top_categories": [
            {"category": "groceries",   "monthly_average": "£350.00"},
            {"category": "eating_out",  "monthly_average": "£120.00"},
            {"category": "transport",   "monthly_average": "£80.00"},
            {"category": "utilities",   "monthly_average": "£60.00"},
            {"category": "subscriptions","monthly_average": "£25.00"},
        ]
    }

    def test_returns_dict_not_none(self):
        result = _extract("get_spending_insights", json.dumps(self.SPENDING_DATA))
        assert result is not None

    def test_chart_type_is_donut(self):
        result = _extract("get_spending_insights", json.dumps(self.SPENDING_DATA))
        assert result["type"] == "donut"

    def test_title_present(self):
        result = _extract("get_spending_insights", json.dumps(self.SPENDING_DATA))
        assert "title" in result
        assert len(result["title"]) > 0

    def test_labels_match_categories(self):
        result = _extract("get_spending_insights", json.dumps(self.SPENDING_DATA))
        assert "groceries" in result["labels"]
        assert "eating_out" in result["labels"]

    def test_values_are_floats(self):
        result = _extract("get_spending_insights", json.dumps(self.SPENDING_DATA))
        for v in result["values"]:
            assert isinstance(v, float)

    def test_labels_and_values_same_length(self):
        result = _extract("get_spending_insights", json.dumps(self.SPENDING_DATA))
        assert len(result["labels"]) == len(result["values"])

    def test_values_parsed_from_gbp_strings(self):
        result = _extract("get_spending_insights", json.dumps(self.SPENDING_DATA))
        # Groceries = 350.00
        idx = result["labels"].index("groceries")
        assert result["values"][idx] == pytest.approx(350.0)

    def test_capped_at_six_categories(self):
        data = {
            "top_categories": [
                {"category": f"cat{i}", "monthly_average": f"£{(i+1)*100:.2f}"}
                for i in range(10)
            ]
        }
        result = _extract("get_spending_insights", json.dumps(data))
        assert len(result["labels"]) <= 6

    def test_returns_none_for_empty_categories(self):
        data = {"top_categories": []}
        result = _extract("get_spending_insights", json.dumps(data))
        assert result is None

    def test_handles_missing_top_categories_key(self):
        data = {"other_key": "value"}
        result = _extract("get_spending_insights", json.dumps(data))
        assert result is None


# ---------------------------------------------------------------------------
# Financial Health Score → Radar chart
# ---------------------------------------------------------------------------

class TestHealthScoreRadar:

    HEALTH_DATA = {
        "overall_score": 72,
        "overall_grade": "B",
        "pillars": [
            {"name": "Savings Rate",       "score": 20, "max_score": 30},
            {"name": "Spend Stability",    "score": 15, "max_score": 20},
            {"name": "Essentials Balance", "score": 13, "max_score": 20},
            {"name": "Subscription Load",  "score": 10, "max_score": 15},
            {"name": "Emergency Buffer",   "score": 14, "max_score": 15},
        ]
    }

    def test_returns_dict_not_none(self):
        result = _extract("get_financial_health_score", json.dumps(self.HEALTH_DATA))
        assert result is not None

    def test_chart_type_is_radar(self):
        result = _extract("get_financial_health_score", json.dumps(self.HEALTH_DATA))
        assert result["type"] == "radar"

    def test_title_contains_score(self):
        result = _extract("get_financial_health_score", json.dumps(self.HEALTH_DATA))
        assert "72" in result["title"]

    def test_title_contains_grade(self):
        result = _extract("get_financial_health_score", json.dumps(self.HEALTH_DATA))
        assert "B" in result["title"]

    def test_labels_match_pillar_names(self):
        result = _extract("get_financial_health_score", json.dumps(self.HEALTH_DATA))
        assert "Savings Rate" in result["labels"]
        assert "Emergency Buffer" in result["labels"]

    def test_values_are_floats(self):
        result = _extract("get_financial_health_score", json.dumps(self.HEALTH_DATA))
        for v in result["values"]:
            assert isinstance(v, float)

    def test_max_values_are_correct(self):
        result = _extract("get_financial_health_score", json.dumps(self.HEALTH_DATA))
        assert result["max_values"] == [30, 20, 20, 15, 15]

    def test_labels_values_and_maxes_same_length(self):
        result = _extract("get_financial_health_score", json.dumps(self.HEALTH_DATA))
        assert len(result["labels"]) == len(result["values"]) == len(result["max_values"])

    def test_returns_none_for_empty_pillars(self):
        data = {"overall_score": 50, "overall_grade": "C", "pillars": []}
        result = _extract("get_financial_health_score", json.dumps(data))
        assert result is None

    def test_handles_integer_score_in_pillar(self):
        """Pillar scores may be ints — must convert to float."""
        data = {
            "overall_score": 40,
            "overall_grade": "C",
            "pillars": [{"name": "Savings Rate", "score": 10, "max_score": 30}],
        }
        result = _extract("get_financial_health_score", json.dumps(data))
        assert isinstance(result["values"][0], float)


# ---------------------------------------------------------------------------
# Long-Term Trends → Line chart
# ---------------------------------------------------------------------------

class TestLongTermTrendsLine:

    TRENDS_DATA = {
        "timeline": [
            {"month": "2025-01", "income": "£2500.00", "spend": "£1200.00", "surplus": "£1300.00"},
            {"month": "2025-02", "income": "£2500.00", "spend": "£1100.00", "surplus": "£1400.00"},
            {"month": "2025-03", "income": "£2500.00", "spend": "£1300.00", "surplus": "£1200.00"},
        ]
    }

    def test_returns_dict_not_none(self):
        result = _extract("get_long_term_trends_tool", json.dumps(self.TRENDS_DATA))
        assert result is not None

    def test_chart_type_is_line(self):
        result = _extract("get_long_term_trends_tool", json.dumps(self.TRENDS_DATA))
        assert result["type"] == "line"

    def test_title_present(self):
        result = _extract("get_long_term_trends_tool", json.dumps(self.TRENDS_DATA))
        assert "title" in result

    def test_labels_are_month_strings(self):
        result = _extract("get_long_term_trends_tool", json.dumps(self.TRENDS_DATA))
        assert len(result["labels"]) == 3

    def test_income_and_spend_arrays_present(self):
        result = _extract("get_long_term_trends_tool", json.dumps(self.TRENDS_DATA))
        assert "income" in result
        assert "spend" in result

    def test_income_values_are_floats(self):
        result = _extract("get_long_term_trends_tool", json.dumps(self.TRENDS_DATA))
        for v in result["income"]:
            assert isinstance(v, float)

    def test_returns_none_for_single_month(self):
        """Line chart requires at least 2 data points."""
        data = {
            "timeline": [
                {"month": "2025-01", "income": "£2500.00", "spend": "£1200.00"},
            ]
        }
        result = _extract("get_long_term_trends_tool", json.dumps(data))
        assert result is None

    def test_returns_none_for_empty_timeline(self):
        data = {"timeline": []}
        result = _extract("get_long_term_trends_tool", json.dumps(data))
        assert result is None


# ---------------------------------------------------------------------------
# Edge cases and error handling
# ---------------------------------------------------------------------------

class TestChartExtractionEdgeCases:

    def test_returns_none_for_unknown_tool(self):
        result = _extract("completely_unknown_tool", json.dumps({"foo": "bar"}))
        assert result is None

    def test_returns_none_for_invalid_json(self):
        result = _extract("get_spending_insights", "not valid json {{{")
        assert result is None

    def test_handles_malformed_amount_gracefully(self):
        """Bad £ strings should produce 0.0, not raise."""
        data = {
            "top_categories": [
                {"category": "groceries", "monthly_average": "not_a_number"},
            ]
        }
        result = _extract("get_spending_insights", json.dumps(data))
        assert result is not None
        assert result["values"][0] == pytest.approx(0.0)

    def test_handles_none_amount_gracefully(self):
        data = {
            "top_categories": [
                {"category": "groceries", "monthly_average": None},
            ]
        }
        result = _extract("get_spending_insights", json.dumps(data))
        # Should not raise — returns 0.0 for None
        assert result is not None

    def test_handles_empty_string_input(self):
        result = _extract("get_spending_insights", "")
        assert result is None

    def test_handles_null_json(self):
        result = _extract("get_spending_insights", "null")
        assert result is None
