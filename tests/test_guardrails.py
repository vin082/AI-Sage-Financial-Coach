"""
Tests for coaching_agent/guardrails.py

Critical compliance layer — all tests must pass before any push.
Covers:
  - Financial distress signposting (Consumer Duty FG21/1)
  - Regulated advice blocking (FSMA 2000 s.19)
  - Out-of-scope filtering
  - Output anti-hallucination guard
  - FCA disclaimer injection
  - extract_grounded_amounts
"""
import pytest

from coaching_agent.guardrails import (
    GuardResult,
    IntentType,
    apply_disclaimer,
    check_input,
    check_output,
    extract_grounded_amounts,
    should_append_disclaimer,
)


# ---------------------------------------------------------------------------
# Financial Distress Signposting — Consumer Duty FG21/1
# ---------------------------------------------------------------------------

class TestDistressSignposting:

    TRIGGERS = [
        "I cant pay bill this month",          # apostrophe-free (key regression)
        "I can't pay my bills this month",     # apostrophe variant
        "cant afford rent",
        "i cant pay",
        "can't make ends meet",
        "I cannot afford my mortgage payments",
        "struggling to pay my loan",
        "I'm struggling to afford my bills",
        "bailiff came to my door",
        "I'm facing repossession",
        "I received an eviction notice",
        "overwhelmed by debt",
        "I might go bankrupt",
        "I am bankrupt",
        "debt collectors keep calling me",    # plural (regression test)
        "debt collector knocked on my door",   # singular
        "I'm in a financial crisis",
        "I'm desperate — I have no financial options",
        "I cant afford anything this month",
        "I cannot pay my rent",
        "I am unable to pay my loan",
        "I cant pay my mortgage",
    ]

    NON_TRIGGERS = [
        "I want to save more money",
        "How can I reduce my bills?",
        "I'd like to pay off my credit card",
        "Can I afford a holiday this year?",
        "Help me budget better",
        "What is my spending this month?",
    ]

    @pytest.mark.parametrize("message", TRIGGERS)
    def test_triggers_distress_signpost(self, message):
        result = check_input(message)
        assert result.result == GuardResult.REDIRECT, (
            f"Expected REDIRECT for distress input: {message!r}, got {result.result}"
        )

    @pytest.mark.parametrize("message", TRIGGERS)
    def test_distress_response_includes_moneyhelper(self, message):
        result = check_input(message)
        assert "MoneyHelper" in (result.safe_response or ""), (
            f"MoneyHelper missing from distress response for: {message!r}"
        )

    @pytest.mark.parametrize("message", TRIGGERS)
    def test_distress_response_includes_stepchange(self, message):
        result = check_input(message)
        assert "StepChange" in (result.safe_response or ""), (
            f"StepChange missing from distress response for: {message!r}"
        )

    def test_distress_response_includes_national_debtline(self):
        result = check_input("I cant pay bill this month")
        assert "National Debtline" in (result.safe_response or "")

    @pytest.mark.parametrize("message", NON_TRIGGERS)
    def test_does_not_trigger_distress_for_normal_queries(self, message):
        result = check_input(message)
        # Either not REDIRECT at all, or REDIRECT for regulated advice (not distress)
        if result.result == GuardResult.REDIRECT:
            assert result.intent == IntentType.REGULATED_ADVICE, (
                f"Unexpectedly triggered distress REDIRECT for: {message!r}"
            )

    def test_distress_check_fires_before_regulated_advice(self):
        """Consumer Duty requires distress check to run first."""
        msg = "I cant afford my mortgage payments, should I remortgage?"
        result = check_input(msg)
        assert result.result == GuardResult.REDIRECT
        assert "MoneyHelper" in (result.safe_response or "")

    def test_distress_result_has_safe_response(self):
        result = check_input("I cant pay bill this month")
        assert result.safe_response is not None
        assert len(result.safe_response) > 50


# ---------------------------------------------------------------------------
# Regulated Advice Blocking — FSMA 2000 s.19
# ---------------------------------------------------------------------------

class TestRegulatedAdviceBlock:

    REGULATED = [
        # Matched by r"\b(should I|shall I|tell me to)\b.*(invest|buy|sell|stocks|shares|ISA|pension|fund)"
        "Should I put my pension into a SIPP?",
        "Should I buy shares in Lloyds?",
        "Should I sell my investments?",
        "Should I invest in stocks?",
        # Matched by r"\bbest (rate|deal|product|provider)\b"
        "What is the best deal for my mortgage?",
        "Which is the best product for savings?",
        # Matched by r"\b(tax advice|tax planning|inheritance tax|capital gains)\b"
        "Give me tax advice for my situation",
        "I need help with inheritance tax",
        # Matched by r"\b(should I|can I afford to)\b.*(borrow|take out a loan|remortgage)\b"
        "Can I afford to take out a loan?",
        "Should I remortgage my house?",
        # Matched by r"\bwhich (mortgage|loan|credit card|insurance)\b.*(should I|best for me|recommend)"
        "Which mortgage should I take?",
    ]

    @pytest.mark.parametrize("message", REGULATED)
    def test_blocks_regulated_advice(self, message):
        result = check_input(message)
        assert result.result == GuardResult.REDIRECT, (
            f"Expected REDIRECT for regulated advice: {message!r}, got {result.result}"
        )
        assert result.intent == IntentType.REGULATED_ADVICE

    def test_regulated_response_mentions_adviser(self):
        result = check_input("Which stocks should I buy right now?")
        assert "adviser" in (result.safe_response or "").lower()

    def test_general_isa_question_is_not_blocked(self):
        """General financial education about ISAs is NOT regulated advice."""
        result = check_input("Can you explain what an ISA is in general?")
        # Should pass or at most be general info — not regulated advice block
        assert result.intent != IntentType.REGULATED_ADVICE or result.result == GuardResult.PASS


# ---------------------------------------------------------------------------
# Out-of-Scope Filtering
# ---------------------------------------------------------------------------

class TestOutOfScopeFilter:

    OOS = [
        # Matched by geography/general knowledge patterns
        "What is the capital of France?",
        "Who invented the telephone?",
        "Who wrote Pride and Prejudice?",
        # Matched by food/lifestyle patterns
        "Give me a recipe for pasta",
        # Matched by sport patterns
        "Who won the World Cup?",
    ]

    IN_SCOPE = [
        "What is a savings rate?",
        "Explain compound interest to me",
        "Tell me about 50/30/20 budgeting",
        "What is a good emergency fund size?",   # "emergency fund" = savings concept, not distress
        "How much am I spending on groceries?",
        "What is my financial health score?",
        "Can you help me make a budget?",
    ]

    @pytest.mark.parametrize("message", OOS)
    def test_blocks_out_of_scope(self, message):
        result = check_input(message)
        assert result.result == GuardResult.BLOCK, (
            f"Expected BLOCK for OOS: {message!r}, got {result.result}"
        )
        assert result.intent == IntentType.OUT_OF_SCOPE

    @pytest.mark.parametrize("message", IN_SCOPE)
    def test_passes_in_scope_financial(self, message):
        result = check_input(message)
        assert result.result == GuardResult.PASS, (
            f"Expected PASS for in-scope: {message!r}, got {result.result}"
        )

    def test_oos_response_redirects_to_finance(self):
        result = check_input("What is the capital of France?")
        assert "financial" in (result.safe_response or "").lower()


# ---------------------------------------------------------------------------
# Output Anti-Hallucination Guard
# ---------------------------------------------------------------------------

class TestOutputGuard:

    def test_blocks_ungrounded_monetary_amount(self):
        """LLM mentions £ figure but no tools were called — must block."""
        result = check_output("Your spend is £999.99", grounded_numbers=set())
        assert result.result == GuardResult.BLOCK

    def test_passes_when_no_amounts_in_response(self):
        """Response with no £ figures — always passes even without tool data."""
        result = check_output("That's great budgeting!", grounded_numbers=set())
        assert result.result == GuardResult.PASS

    def test_passes_when_tools_were_called(self):
        """When grounded_numbers is populated (tools called), monetary response is fine."""
        result = check_output(
            "Your monthly spend is £1,234.56",
            grounded_numbers={"£1,234.56"},
        )
        assert result.result == GuardResult.PASS

    def test_passes_when_tools_called_any_amount_grounded(self):
        """If tools ran (non-empty grounded_numbers), trust the grounding contract."""
        result = check_output(
            "You spent about £500 this month",
            grounded_numbers={"£499.99"},   # different format — trust tools
        )
        assert result.result == GuardResult.PASS

    def test_passes_for_empty_response(self):
        result = check_output("", grounded_numbers=set())
        assert result.result == GuardResult.PASS

    def test_multiple_ungrounded_amounts_blocked(self):
        result = check_output(
            "You earn £3,000 and spend £2,500 monthly.",
            grounded_numbers=set(),
        )
        assert result.result == GuardResult.BLOCK

    def test_returns_guard_decision_with_reason(self):
        result = check_output("Your spend is £999.99", grounded_numbers=set())
        assert result.reason is not None
        assert len(result.reason) > 0


# ---------------------------------------------------------------------------
# FCA Disclaimer Injection
# ---------------------------------------------------------------------------

class TestFCADisclaimer:

    TRIGGER_TERMS = [
        "mortgage",
        "ISA",
        "pension",
        "investment",
        "loan",
        "interest rate",
        "savings account",
        "remortgage",
        "credit card",
        "borrow",
    ]

    NON_TRIGGER_TERMS = [
        "groceries",
        "budget",
        "spending",
        "emergency fund",
        "monthly surplus",
    ]

    @pytest.mark.parametrize("term", TRIGGER_TERMS)
    def test_disclaimer_added_for_regulated_adjacent_terms(self, term):
        response = f"You should consider a {term} for your situation."
        result = apply_disclaimer(response)
        assert "not regulated" in result.lower() or "guidance" in result.lower(), (
            f"FCA disclaimer not injected for term: {term!r}"
        )

    @pytest.mark.parametrize("term", NON_TRIGGER_TERMS)
    def test_no_disclaimer_for_non_regulated_terms(self, term):
        original = f"Your {term} this month looks good."
        result = apply_disclaimer(original)
        # Disclaimer should not have been added
        assert "not regulated financial advice" not in result

    def test_disclaimer_appended_at_end(self):
        response = "You might want to look into a pension."
        result = apply_disclaimer(response)
        assert result.startswith(response)

    def test_should_append_disclaimer_returns_bool(self):
        assert should_append_disclaimer("Here is some pension info.") is True
        assert should_append_disclaimer("You saved money this month.") is False

    def test_disclaimer_applied_once_per_response(self):
        """Normal code path only calls apply_disclaimer once."""
        response = "Consider an ISA for your savings."
        result = apply_disclaimer(response)
        assert result.count("not regulated financial advice") == 1


# ---------------------------------------------------------------------------
# extract_grounded_amounts
# ---------------------------------------------------------------------------

class TestExtractGroundedAmounts:

    def test_extracts_top_level_currency_string(self):
        data = {"total": "£1,234.56"}
        result = extract_grounded_amounts(data)
        assert "£1,234.56" in result

    def test_extracts_nested_amounts(self):
        data = {
            "insights": {
                "monthly_spend": "£500.00",
                "categories": [
                    {"amount": "£100.00"},
                    {"amount": "£50.00"},
                ],
            }
        }
        result = extract_grounded_amounts(data)
        assert "£500.00" in result
        assert "£100.00" in result
        assert "£50.00" in result

    def test_ignores_non_currency_strings(self):
        data = {"label": "groceries", "trend": "stable", "grade": "B"}
        result = extract_grounded_amounts(data)
        assert len(result) == 0

    def test_extracts_from_list_of_dicts(self):
        data = [{"spend": "£200.00"}, {"spend": "£300.00"}]
        result = extract_grounded_amounts({"items": data})
        assert "£200.00" in result
        assert "£300.00" in result

    def test_handles_empty_dict(self):
        result = extract_grounded_amounts({})
        assert result == set()

    def test_returns_set_type(self):
        result = extract_grounded_amounts({"amount": "£100.00"})
        assert isinstance(result, set)

    def test_deduplicates_same_amount(self):
        data = {"a": "£100.00", "b": "£100.00"}
        result = extract_grounded_amounts(data)
        assert result == {"£100.00"}
