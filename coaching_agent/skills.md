---
name: life-event-coaching
description: >
  Detects probable life events (new baby, property purchase, income change, new rental,
  marriage) from transaction patterns and coaches the customer through the financial
  implications. Always runs detect_life_events_tool first — deterministically — before
  any budgeting or planning tool. Acknowledges confirmed transaction evidence before
  offering advice. Use this skill when the customer mentions baby, nursery, childcare,
  moving home, buying a house, new job, pay rise, promotion, marriage, or new rent.
---

---
name: spending-analysis
description: >
  Analyses the customer's recent spending patterns, income, surplus and top categories
  from verified transaction data. Always calls get_spending_insights before responding
  with any monetary figures. Use this skill when the customer asks how much they are
  spending, where their money is going, wants a monthly breakdown, or asks about a
  specific spending category.
---

---
name: financial-health-check
description: >
  Calculates and explains the customer's financial health score (0–100) across five
  pillars: savings rate, spend stability, essentials balance, subscription load, and
  emergency buffer. All scores are deterministic — no LLM estimation. Use this skill
  when the customer asks about their financial health score, savings rate, emergency
  fund, or wants an overall assessment of their finances.
---

---
name: mortgage-affordability
description: >
  Models mortgage affordability from verified income and spending data. Applies the
  PRA 4.5× LTI cap and FCA +3% stress test. Returns max loan, monthly payment
  scenarios and deposit requirements. This is guidance only — not a mortgage offer
  or Decision in Principle. Use this skill when the customer asks about buying a
  house, how much they can borrow, mortgage affordability, LTV, or deposit requirements.
  Never quote specific rates as guaranteed. Escalate to adviser for product recommendations.
---

---
name: debt-vs-savings
description: >
  Compares overpaying a debt versus saving the surplus each month, producing a
  clear data-backed recommendation based on the interest rate differential.
  Always calls get_spending_insights first to obtain the verified monthly surplus,
  then analyse_debt_vs_savings. Use this skill when the customer asks whether to
  overpay their mortgage, pay off debt, or whether they should save or pay down debt.
---

---
name: budget-planning
description: >
  Creates a personalised 50/30/20 budget plan with goal tracking using verified
  spending data. Must always call get_spending_insights before build_budget_plan_tool —
  never build a plan without verified figures. Use this skill when the customer
  asks for a budget plan, mentions the 50/30/20 rule, wants to set savings goals,
  or asks how to allocate their income.
---

---
name: adviser-escalation
description: >
  Builds a warm handoff package and directs the customer to a qualified Lloyds
  financial adviser for regulated advice topics. Always calls escalate_to_adviser.
  Use this skill when the customer asks for regulated financial advice, wants to
  speak to an adviser, asks about pensions, investments, specific mortgage product
  recommendations, or when any topic exceeds the guidance boundary under FSMA 2000.
---

---
name: product-eligibility
description: >
  Checks indicative eligibility for LBG products based on verified income and
  surplus. Always calls get_spending_insights then check_product_eligibility_tool.
  This is guidance only — not a credit decision or product recommendation.
  Use this skill when the customer asks which products they may qualify for,
  whether they are eligible for a credit card or savings account, or which
  account might suit their profile.
---

---
name: guidance-search
description: >
  Retrieves LBG-reviewed financial guidance on general money management topics
  such as budgeting methods, savings strategies, and debt principles. Always calls
  search_guidance. Use this skill when the customer asks a general financial
  literacy question, wants to understand a concept like the 50/30/20 rule or
  emergency funds, or requests tips on saving or managing debt.
---
