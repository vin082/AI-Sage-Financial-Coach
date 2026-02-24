"""
Tests for deterministic financial tools:
  - coaching_agent/tools/transaction_analyser.py
  - coaching_agent/tools/financial_health.py

Anti-hallucination principle: all computations must be reproducible
with the same input — no LLM, no randomness in these modules.
"""
import pytest
from decimal import Decimal

from coaching_agent.tools.financial_health import (
    FinancialHealthReport,
    HealthPillar,
    _grade,
    compute_health_score,
)
from coaching_agent.tools.transaction_analyser import (
    SpendingInsights,
    TransactionAnalyser,
)


# ---------------------------------------------------------------------------
# TransactionAnalyser — spending insights
# ---------------------------------------------------------------------------

class TestTransactionAnalyserInsights:

    def test_returns_spending_insights_type(self, demo_analyser):
        result = demo_analyser.get_full_insights(months=3)
        assert isinstance(result, SpendingInsights)

    def test_customer_id_preserved(self, demo_analyser, demo_profile):
        result = demo_analyser.get_full_insights(months=3)
        assert result.customer_id == demo_profile.customer_id

    def test_monetary_fields_are_decimal_not_float(self, demo_analyser):
        result = demo_analyser.get_full_insights(months=3)
        assert isinstance(result.average_monthly_spend, Decimal)
        assert isinstance(result.average_monthly_income, Decimal)
        assert isinstance(result.average_monthly_surplus, Decimal)
        assert isinstance(result.subscription_monthly_cost, Decimal)
        assert isinstance(result.current_balance_estimate, Decimal)

    def test_income_is_positive(self, demo_analyser):
        result = demo_analyser.get_full_insights(months=3)
        assert result.average_monthly_income > 0

    def test_spend_is_positive(self, demo_analyser):
        result = demo_analyser.get_full_insights(months=3)
        assert result.average_monthly_spend > 0

    def test_surplus_equals_income_minus_spend(self, demo_analyser):
        result = demo_analyser.get_full_insights(months=3)
        expected = result.average_monthly_income - result.average_monthly_spend
        diff = abs(result.average_monthly_surplus - expected)
        assert diff < Decimal("0.02"), (
            f"Surplus {result.average_monthly_surplus} != income - spend {expected}"
        )

    def test_top_categories_not_empty(self, demo_analyser):
        result = demo_analyser.get_full_insights(months=3)
        assert len(result.top_categories) > 0

    def test_top_categories_sorted_descending_by_spend(self, demo_analyser):
        result = demo_analyser.get_full_insights(months=3)
        totals = [c.total_spend for c in result.top_categories]
        assert totals == sorted(totals, reverse=True)

    def test_top_categories_capped_at_six(self, demo_analyser):
        result = demo_analyser.get_full_insights(months=3)
        assert len(result.top_categories) <= 6

    def test_spend_trend_is_valid_value(self, demo_analyser):
        result = demo_analyser.get_full_insights(months=3)
        assert result.spend_trend in ("increasing", "decreasing", "stable")

    def test_monthly_summaries_count_within_bounds(self, demo_analyser):
        result = demo_analyser.get_full_insights(months=3)
        assert 1 <= len(result.monthly_summaries) <= 3

    def test_monthly_summaries_debit_not_negative(self, demo_analyser):
        result = demo_analyser.get_full_insights(months=3)
        for summary in result.monthly_summaries:
            assert summary.total_debit >= 0

    def test_deterministic_same_result_on_repeat_call(self, demo_analyser):
        r1 = demo_analyser.get_full_insights(months=3)
        r2 = demo_analyser.get_full_insights(months=3)
        assert r1.average_monthly_spend == r2.average_monthly_spend
        assert r1.average_monthly_income == r2.average_monthly_income

    def test_analysis_period_stored_correctly(self, demo_analyser):
        result = demo_analyser.get_full_insights(months=3)
        assert result.analysis_period_months == 3

    def test_subscription_cost_non_negative(self, demo_analyser):
        result = demo_analyser.get_full_insights(months=3)
        assert result.subscription_monthly_cost >= 0


class TestTransactionAnalyserCategoryDetail:

    def test_returns_dict(self, demo_analyser):
        result = demo_analyser.get_category_detail("groceries", months=3)
        assert isinstance(result, dict)

    def test_has_category_field(self, demo_analyser):
        result = demo_analyser.get_category_detail("groceries", months=3)
        assert result.get("category") == "groceries"

    def test_total_spend_is_currency_string(self, demo_analyser):
        result = demo_analyser.get_category_detail("groceries", months=3)
        total = result.get("total_spend", "")
        assert total.startswith("£"), f"Expected £-prefixed string, got: {total!r}"

    def test_unknown_category_returns_zero_count(self, demo_analyser):
        result = demo_analyser.get_category_detail("nonexistent_xyz", months=3)
        assert result.get("count", 0) == 0 or result.get("transaction_count", 0) == 0

    def test_transactions_list_present(self, demo_analyser):
        result = demo_analyser.get_category_detail("groceries", months=3)
        assert "transactions" in result


class TestTransactionAnalyserSavingsOpportunity:

    def test_returns_dict_with_opportunities(self, demo_analyser):
        result = demo_analyser.get_savings_opportunity()
        assert isinstance(result, dict)
        assert "opportunities" in result
        assert isinstance(result["opportunities"], list)

    def test_monthly_surplus_is_currency_string(self, demo_analyser):
        result = demo_analyser.get_savings_opportunity()
        assert result["monthly_surplus"].startswith("£")

    def test_opportunity_count_matches_list(self, demo_analyser):
        result = demo_analyser.get_savings_opportunity()
        assert result["opportunity_count"] == len(result["opportunities"])

    def test_each_opportunity_has_area_and_tip(self, demo_analyser):
        result = demo_analyser.get_savings_opportunity()
        for opp in result["opportunities"]:
            assert "area" in opp
            assert "tip" in opp


class TestTransactionAnalyserLongTermTrends:

    def test_returns_dict_with_timeline(self, demo_analyser):
        result = demo_analyser.get_long_term_trends(months=6)
        assert isinstance(result, dict)
        assert "timeline" in result

    def test_timeline_entries_have_month_key(self, demo_analyser):
        result = demo_analyser.get_long_term_trends(months=6)
        for entry in result["timeline"]:
            assert "month" in entry

    def test_surplus_trend_present(self, demo_analyser):
        result = demo_analyser.get_long_term_trends(months=6)
        assert "surplus_trend" in result

    def test_months_capped_at_12(self, demo_analyser):
        result = demo_analyser.get_long_term_trends(months=99)
        # Internally capped at 12
        assert result.get("analysis_period_months", 99) <= 12


# ---------------------------------------------------------------------------
# Financial Health Score — deterministic scoring engine
# ---------------------------------------------------------------------------

class TestFinancialHealthScore:

    def test_returns_health_report_type(self, demo_health_report):
        assert isinstance(demo_health_report, FinancialHealthReport)

    def test_overall_score_in_range_0_to_100(self, demo_health_report):
        assert 0 <= demo_health_report.overall_score <= 100

    def test_overall_grade_is_valid(self, demo_health_report):
        assert demo_health_report.overall_grade in ("A", "B", "C", "D")

    def test_exactly_five_pillars_returned(self, demo_health_report):
        assert len(demo_health_report.pillars) == 5

    def test_pillar_scores_sum_to_overall(self, demo_health_report):
        total = sum(p.score for p in demo_health_report.pillars)
        assert total == demo_health_report.overall_score

    def test_each_pillar_score_within_its_max(self, demo_health_report):
        for pillar in demo_health_report.pillars:
            assert 0 <= pillar.score <= pillar.max_score, (
                f"Pillar {pillar.name}: score {pillar.score} exceeds max {pillar.max_score}"
            )

    def test_each_pillar_grade_is_valid(self, demo_health_report):
        for pillar in demo_health_report.pillars:
            assert pillar.grade in ("A", "B", "C", "D"), (
                f"Pillar {pillar.name} has invalid grade: {pillar.grade!r}"
            )

    def test_pillar_max_scores_sum_to_100(self, demo_health_report):
        total_max = sum(p.max_score for p in demo_health_report.pillars)
        assert total_max == 100

    def test_pillar_explanations_non_empty(self, demo_health_report):
        for pillar in demo_health_report.pillars:
            assert len(pillar.explanation) > 0

    def test_customer_id_preserved(self, demo_health_report, demo_profile):
        assert demo_health_report.customer_id == demo_profile.customer_id

    def test_deterministic_on_same_insights(self, demo_insights):
        r1 = compute_health_score(demo_insights)
        r2 = compute_health_score(demo_insights)
        assert r1.overall_score == r2.overall_score
        assert r1.overall_grade == r2.overall_grade

    def test_raw_metrics_are_decimal(self, demo_health_report):
        assert isinstance(demo_health_report.savings_rate_pct, Decimal)
        assert isinstance(demo_health_report.essentials_pct, Decimal)
        assert isinstance(demo_health_report.subscription_pct, Decimal)
        assert isinstance(demo_health_report.months_buffer, Decimal)


class TestGradeFunction:
    """Unit tests for the _grade helper — covers all boundary conditions."""

    def test_a_grade_at_85_percent(self):
        assert _grade(85, 100) == "A"

    def test_a_grade_at_100_percent(self):
        assert _grade(100, 100) == "A"

    def test_b_grade_at_70_percent(self):
        assert _grade(70, 100) == "B"

    def test_b_grade_at_84_percent(self):
        assert _grade(84, 100) == "B"

    def test_c_grade_at_50_percent(self):
        assert _grade(50, 100) == "C"

    def test_c_grade_at_69_percent(self):
        assert _grade(69, 100) == "C"

    def test_d_grade_at_49_percent(self):
        assert _grade(49, 100) == "D"

    def test_d_grade_at_zero(self):
        assert _grade(0, 100) == "D"

    def test_works_with_pillar_max(self):
        # Savings Rate max = 30
        assert _grade(30, 30) == "A"    # 100% → A
        assert _grade(26, 30) == "A"    # 86.7% → A (>= 85%)
        assert _grade(21, 30) == "B"    # 70.0% → B (>= 70%, < 85%)
        assert _grade(15, 30) == "C"    # 50.0% → C (>= 50%, < 70%)
        assert _grade(0, 30) == "D"     # 0% → D
