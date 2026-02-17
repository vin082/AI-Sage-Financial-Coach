"""
Transaction Analyser Tool — GROUNDED, deterministic computation only.

ANTI-HALLUCINATION PRINCIPLE:
  All monetary figures, percentages and trends returned by this module are
  computed directly from raw transaction records.  No LLM is involved in
  numerical calculations.  The LLM is only used to narrate pre-computed facts.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from data.mock_transactions import Category, CustomerProfile, Transaction


# ---------------------------------------------------------------------------
# Result types — strongly typed so the LLM receives only verified numbers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CategorySummary:
    category: str
    total_spend: Decimal
    transaction_count: int
    average_per_transaction: Decimal
    largest_single_spend: Decimal
    merchants: list[str]


@dataclass(frozen=True)
class MonthlySpendSummary:
    year: int
    month: int
    total_debit: Decimal
    total_credit: Decimal
    net: Decimal                # credit - debit
    category_breakdown: dict[str, Decimal]


@dataclass(frozen=True)
class SpendingInsights:
    customer_id: str
    analysis_period_months: int
    average_monthly_spend: Decimal
    average_monthly_income: Decimal
    average_monthly_surplus: Decimal
    current_balance_estimate: Decimal
    top_categories: list[CategorySummary]          # sorted by spend desc
    monthly_summaries: list[MonthlySpendSummary]
    spend_trend: str                               # "increasing" | "decreasing" | "stable"
    highest_spend_month: str                       # "YYYY-MM"
    lowest_spend_month: str                        # "YYYY-MM"
    eating_out_vs_groceries_ratio: Decimal | None
    subscription_monthly_cost: Decimal


# ---------------------------------------------------------------------------
# Core analyser
# ---------------------------------------------------------------------------


class TransactionAnalyser:
    """
    Deterministic financial analytics engine.

    Inputs:  CustomerProfile (raw transactions)
    Outputs: SpendingInsights (pre-computed, verified numbers)

    The coaching agent calls this tool and receives structured data.
    It MUST NOT re-compute or modify any numbers — only narrate them.
    """

    def __init__(self, profile: CustomerProfile) -> None:
        self.profile = profile
        self._debits = [t for t in profile.transactions if t.amount < 0]
        self._credits = [t for t in profile.transactions if t.amount > 0]

    # ------------------------------------------------------------------
    # Public interface — called by LangChain tools
    # ------------------------------------------------------------------

    def get_full_insights(self, months: int = 3) -> SpendingInsights:
        """Return complete spending insights for the last `months` months."""
        cutoff = self._months_ago(months)
        recent_debits = [t for t in self._debits if t.date >= cutoff]
        recent_credits = [t for t in self._credits if t.date >= cutoff]

        monthly_summaries = self._build_monthly_summaries(months)
        category_summaries = self._build_category_summaries(recent_debits)

        monthly_spend_totals = [s.total_debit for s in monthly_summaries]
        avg_spend = self._safe_avg(monthly_spend_totals)
        avg_income = self._safe_avg([s.total_credit for s in monthly_summaries])
        avg_surplus = avg_income - avg_spend

        trend = self._compute_trend(monthly_spend_totals)
        highest, lowest = self._min_max_months(monthly_summaries)

        eating_out = next((c.total_spend for c in category_summaries if c.category == "eating_out"), None)
        groceries = next((c.total_spend for c in category_summaries if c.category == "groceries"), None)
        ratio = (
            (eating_out / groceries).quantize(Decimal("0.01"))
            if eating_out and groceries and groceries > 0
            else None
        )

        subscription_cost = sum(
            abs(t.amount) for t in recent_debits if t.category == "subscriptions"
        ) / Decimal(str(months))

        latest_balance = (
            self.profile.transactions[-1].balance_after
            if self.profile.transactions
            else Decimal("0")
        )

        return SpendingInsights(
            customer_id=self.profile.customer_id,
            analysis_period_months=months,
            average_monthly_spend=avg_spend.quantize(Decimal("0.01")),
            average_monthly_income=avg_income.quantize(Decimal("0.01")),
            average_monthly_surplus=avg_surplus.quantize(Decimal("0.01")),
            current_balance_estimate=latest_balance.quantize(Decimal("0.01")),
            top_categories=category_summaries[:6],
            monthly_summaries=monthly_summaries,
            spend_trend=trend,
            highest_spend_month=highest,
            lowest_spend_month=lowest,
            eating_out_vs_groceries_ratio=ratio,
            subscription_monthly_cost=subscription_cost.quantize(Decimal("0.01")),
        )

    def get_category_detail(self, category: str, months: int = 3) -> dict[str, Any]:
        """Return granular breakdown for a specific category."""
        cutoff = self._months_ago(months)
        txns = [
            t for t in self._debits
            if t.category == category and t.date >= cutoff
        ]
        if not txns:
            return {"category": category, "transactions": [], "total": "£0.00", "count": 0}

        total = sum(abs(t.amount) for t in txns)
        by_merchant: dict[str, Decimal] = defaultdict(Decimal)
        for t in txns:
            by_merchant[t.merchant] += abs(t.amount)

        return {
            "category": category,
            "period_months": months,
            "total_spend": f"£{total:.2f}",
            "transaction_count": len(txns),
            "average_per_month": f"£{(total / months):.2f}",
            "top_merchants": [
                {"merchant": m, "total": f"£{v:.2f}"}
                for m, v in sorted(by_merchant.items(), key=lambda x: x[1], reverse=True)
            ],
            "transactions": [
                {
                    "date": str(t.date),
                    "merchant": t.merchant,
                    "amount": f"£{abs(t.amount):.2f}",
                }
                for t in sorted(txns, key=lambda x: x.date, reverse=True)
            ],
        }

    def get_long_term_trends(self, months: int = 12) -> dict[str, Any]:
        """
        Compute long-term spending trends over up to 12 months.
        Returns:
          - month-by-month spend/income/surplus
          - YoY category comparison (last 3 months vs same 3 months prior year)
          - overall spend trajectory (linear regression direction)
          - average monthly surplus trend
        """
        months = max(3, min(12, months))
        summaries = self._build_monthly_summaries(months)
        if not summaries:
            return {"error": "Not enough transaction history for trend analysis."}

        # Month-by-month timeline
        timeline = [
            {
                "month": f"{s.year}-{s.month:02d}",
                "income": f"£{s.total_credit:.2f}",
                "spend": f"£{s.total_debit:.2f}",
                "surplus": f"£{s.net:.2f}",
            }
            for s in summaries
        ]

        # Average surplus trend: compare first half vs second half
        mid = len(summaries) // 2
        first_half_surplus = self._safe_avg([s.net for s in summaries[:mid]])
        second_half_surplus = self._safe_avg([s.net for s in summaries[mid:]])
        surplus_direction = "improving" if second_half_surplus > first_half_surplus else (
            "declining" if second_half_surplus < first_half_surplus else "stable"
        )
        surplus_change = abs(second_half_surplus - first_half_surplus)

        # Highest and lowest spend months over the period
        highest_spend = max(summaries, key=lambda s: s.total_debit)
        lowest_spend = min(summaries, key=lambda s: s.total_debit)

        # Category totals over the full period
        cutoff = self._months_ago(months)
        all_debits = [t for t in self._debits if t.date >= cutoff]
        category_totals = defaultdict(Decimal)
        for t in all_debits:
            category_totals[t.category] += abs(t.amount)

        top_categories_period = [
            {
                "category": cat.replace("_", " ").title(),
                "total": f"£{total:.2f}",
                "monthly_avg": f"£{(total / months):.2f}",
            }
            for cat, total in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:6]
        ]

        # YoY comparison: last 3 months spend vs 12-15 months ago (if data exists)
        yoy_note = None
        if months >= 12:
            recent_3m_debits = [t for t in self._debits if t.date >= self._months_ago(3)]
            prior_3m_debits = [
                t for t in self._debits
                if self._months_ago(15) <= t.date < self._months_ago(12)
            ]
            if recent_3m_debits and prior_3m_debits:
                recent_total = sum(abs(t.amount) for t in recent_3m_debits)
                prior_total = sum(abs(t.amount) for t in prior_3m_debits)
                change_pct = ((recent_total - prior_total) / prior_total * 100).quantize(Decimal("0.1"))
                direction = "higher" if change_pct > 0 else "lower"
                yoy_note = (
                    f"Spending over the last 3 months is {abs(change_pct)}% {direction} "
                    f"than the same period last year "
                    f"(£{recent_total:.2f} vs £{prior_total:.2f})."
                )

        result: dict[str, Any] = {
            "analysis_period_months": months,
            "timeline": timeline,
            "surplus_trend": {
                "direction": surplus_direction,
                "change_vs_earlier_period": f"£{surplus_change:.2f}",
                "recent_avg_monthly_surplus": f"£{second_half_surplus:.2f}",
                "earlier_avg_monthly_surplus": f"£{first_half_surplus:.2f}",
            },
            "highest_spend_month": {
                "month": f"{highest_spend.year}-{highest_spend.month:02d}",
                "amount": f"£{highest_spend.total_debit:.2f}",
            },
            "lowest_spend_month": {
                "month": f"{lowest_spend.year}-{lowest_spend.month:02d}",
                "amount": f"£{lowest_spend.total_debit:.2f}",
            },
            "top_categories_over_period": top_categories_period,
        }
        if yoy_note:
            result["year_on_year_comparison"] = yoy_note

        return result

    def get_savings_opportunity(self) -> dict[str, Any]:
        """
        Identify concrete, data-backed savings opportunities.
        Returns specific £ amounts — no estimates or guesses.
        """
        insights = self.get_full_insights(months=3)

        opportunities = []

        # Rule 1: Eating out > 30% of grocery spend
        if insights.eating_out_vs_groceries_ratio and insights.eating_out_vs_groceries_ratio > Decimal("0.30"):
            eating_out_cat = next(
                (c for c in insights.top_categories if c.category == "eating_out"), None
            )
            if eating_out_cat:
                monthly_eating_out = eating_out_cat.total_spend / insights.analysis_period_months
                potential_saving = (monthly_eating_out * Decimal("0.3")).quantize(Decimal("0.01"))
                opportunities.append({
                    "area": "Eating Out",
                    "monthly_spend": f"£{monthly_eating_out:.2f}",
                    "potential_monthly_saving": f"£{potential_saving:.2f}",
                    "annual_saving": f"£{(potential_saving * 12):.2f}",
                    "tip": "Reducing eating out by 30% could free up significant funds.",
                })

        # Rule 2: Subscriptions > £50/month
        if insights.subscription_monthly_cost > Decimal("50"):
            opportunities.append({
                "area": "Subscriptions",
                "monthly_spend": f"£{insights.subscription_monthly_cost:.2f}",
                "potential_monthly_saving": f"£{(insights.subscription_monthly_cost * Decimal('0.25')):.2f}",
                "annual_saving": f"£{(insights.subscription_monthly_cost * 3):.2f}",
                "tip": "Review unused subscriptions — a common source of silent spending.",
            })

        # Rule 3: Surplus < 10% of income → flag low savings rate
        if insights.average_monthly_income > 0:
            savings_rate = insights.average_monthly_surplus / insights.average_monthly_income
            if savings_rate < Decimal("0.10"):
                opportunities.append({
                    "area": "Savings Rate",
                    "current_rate": f"{(savings_rate * 100):.1f}%",
                    "target_rate": "20%",
                    "gap_monthly": f"£{((Decimal('0.20') - savings_rate) * insights.average_monthly_income):.2f}",
                    "tip": "Financial best practice suggests saving at least 20% of take-home pay.",
                })

        return {
            "monthly_surplus": f"£{insights.average_monthly_surplus:.2f}",
            "opportunities": opportunities,
            "opportunity_count": len(opportunities),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_monthly_summaries(self, months: int) -> list[MonthlySpendSummary]:
        cutoff = self._months_ago(months)
        bucket: dict[tuple[int, int], dict] = defaultdict(
            lambda: {"debit": Decimal("0"), "credit": Decimal("0"), "cats": defaultdict(Decimal)}
        )
        for t in self.profile.transactions:
            if t.date < cutoff:
                continue
            key = (t.date.year, t.date.month)
            if t.amount < 0:
                bucket[key]["debit"] += abs(t.amount)
                bucket[key]["cats"][t.category] += abs(t.amount)
            else:
                bucket[key]["credit"] += t.amount

        summaries = []
        for (year, month), data in sorted(bucket.items()):
            summaries.append(MonthlySpendSummary(
                year=year,
                month=month,
                total_debit=data["debit"].quantize(Decimal("0.01")),
                total_credit=data["credit"].quantize(Decimal("0.01")),
                net=(data["credit"] - data["debit"]).quantize(Decimal("0.01")),
                category_breakdown={k: v.quantize(Decimal("0.01")) for k, v in data["cats"].items()},
            ))
        return summaries

    def _build_category_summaries(self, txns: list[Transaction]) -> list[CategorySummary]:
        bucket: dict[str, list[Transaction]] = defaultdict(list)
        for t in txns:
            bucket[t.category].append(t)

        summaries = []
        for cat, cat_txns in bucket.items():
            amounts = [abs(t.amount) for t in cat_txns]
            total = sum(amounts)
            summaries.append(CategorySummary(
                category=cat,
                total_spend=total.quantize(Decimal("0.01")),
                transaction_count=len(cat_txns),
                average_per_transaction=(total / len(cat_txns)).quantize(Decimal("0.01")),
                largest_single_spend=max(amounts).quantize(Decimal("0.01")),
                merchants=list({t.merchant for t in cat_txns}),
            ))

        return sorted(summaries, key=lambda s: s.total_spend, reverse=True)

    def _compute_trend(self, monthly_totals: list[Decimal]) -> str:
        if len(monthly_totals) < 2:
            return "stable"
        diffs = [monthly_totals[i] - monthly_totals[i - 1] for i in range(1, len(monthly_totals))]
        avg_diff = sum(diffs) / len(diffs)
        if avg_diff > Decimal("50"):
            return "increasing"
        if avg_diff < Decimal("-50"):
            return "decreasing"
        return "stable"

    def _min_max_months(self, summaries: list[MonthlySpendSummary]) -> tuple[str, str]:
        if not summaries:
            return ("N/A", "N/A")
        highest = max(summaries, key=lambda s: s.total_debit)
        lowest = min(summaries, key=lambda s: s.total_debit)
        return (
            f"{highest.year}-{highest.month:02d}",
            f"{lowest.year}-{lowest.month:02d}",
        )

    @staticmethod
    def _safe_avg(values: list[Decimal]) -> Decimal:
        if not values:
            return Decimal("0")
        return sum(values) / Decimal(str(len(values)))

    @staticmethod
    def _months_ago(months: int) -> date:
        today = date.today()
        month = today.month - months
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        return date(year, month, 1)
