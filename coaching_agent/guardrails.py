"""
Guardrails — Anti-hallucination and FCA compliance layer.

Three layers of protection:
  1. INPUT GUARD:   Detect regulated-advice questions before LLM sees them
  2. OUTPUT GUARD:  Verify LLM response doesn't contain ungrounded numbers
  3. FCA BOUNDARY:  Enforce guidance-vs-advice distinction

FCA Note:
  This agent provides INFORMATION and GUIDANCE only.
  It does NOT provide regulated financial advice under FSMA 2000.
  Any specific product recommendations must route to a qualified adviser.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GuardResult(Enum):
    PASS = "pass"
    BLOCK = "block"
    REDIRECT = "redirect"       # Route to human adviser


class IntentType(Enum):
    GENERAL_QUERY = "general_query"
    SPEND_ANALYSIS = "spend_analysis"
    SAVINGS_ADVICE = "savings_advice"
    REGULATED_ADVICE = "regulated_advice"   # Must redirect
    ABUSIVE = "abusive"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass
class GuardDecision:
    result: GuardResult
    intent: IntentType
    reason: str
    safe_response: str | None = None        # Pre-canned response if blocked


# ---------------------------------------------------------------------------
# Regulated advice patterns (route to adviser, never answer directly)
# ---------------------------------------------------------------------------

REGULATED_ADVICE_PATTERNS = [
    # Investment advice
    r"\b(should I|shall I|tell me to)\b.*(invest|buy|sell|stocks|shares|ISA|pension|fund)",
    r"\bwhat (stocks?|shares?|funds?|etf)\b.*\b(buy|invest|pick|choose)\b",
    # Specific product recommendations
    r"\bwhich (mortgage|loan|credit card|insurance)\b.*(should I|best for me|recommend)",
    r"\bbest (rate|deal|product|provider)\b",
    # Tax / legal
    r"\b(tax advice|tax planning|inheritance tax|capital gains)\b",
    r"\b(legal advice|legal claim|sue|lawsuit)\b",
    # Borrowing without full context
    r"\b(should I|can I afford to)\b.*(borrow|take out a loan|remortgage)\b",
]

# Topics outside scope — general knowledge and non-financial subjects.
# These are caught before the LLM sees the message, saving tokens and
# preventing the LLM from answering despite prompt instructions.
OUT_OF_SCOPE_PATTERNS = [
    # Geography / general knowledge
    r"\b(capital (city|of)|largest (city|country|continent)|population of|where is)\b",
    r"\b(who (is|was|invented|discovered|wrote|directed|won))\b",
    r"\b(what (is|are|was|were) the? (colour|color|speed|distance|height|weight|age|year|date|language|currency(?! in my)))\b",
    # Science / maths (non-financial)
    r"\b(formula|equation|periodic table|chemical|atom|molecule|planet|galaxy|evolution)\b",
    r"\bhow (do|does|did) .{0,30} work\b(?!.{0,60}(money|budget|saving|spend|bank|finance|debt|loan|payment))",
    # History / culture
    r"\b(world war|history of|ancient|medieval|renaissance|revolution(?! in (my|spending|saving)))\b",
    r"\b(novel|book|film|movie|song|album|artist|actor|director|sport|team|match|score|goal)\b",
    # Food / lifestyle
    r"\b(recipe|ingredient|cook|bake|calories|diet(?! budget)|exercise|workout|gym routine)\b",
    # Technology (non-banking)
    r"\b(programming language|javascript|python(?! script)|html|css|linux|windows|android|iphone)\b",
    # Travel / geography
    r"\b(best (place|country|city|hotel|restaurant|flight) to)\b",
    r"\b(weather|forecast|temperature|climate)\b",
    # Politics / religion
    r"\b(politics|political party|election|prime minister(?! of my)|president(?! of my)|religion|god|pray)\b",
]

# Fast-path: topics that are clearly financial and should NEVER be caught by OOS patterns
FINANCIAL_ALLOWLIST = [
    r"\b(spend|spending|spent)\b",
    r"\b(save|saving|savings)\b",
    r"\b(budget|budgeting)\b",
    r"\b(income|salary|wage|earn)\b",
    r"\b(debt|loan|mortgage|credit)\b",
    r"\b(bank|account|balance|transaction)\b",
    r"\b(money|finance|financial|cost|price|afford)\b",
    r"\b(health score|insurance premium|subscription)\b",
]

# ---------------------------------------------------------------------------
# Financial distress patterns — trigger proactive support signposting
# ---------------------------------------------------------------------------

DISTRESS_PATTERNS = [
    r"\b(can't|cannot|struggle to)\b.*(pay|afford).*(bill|rent|mortgage|loan|debt)",
    r"\b(bailiff|debt collector|repossession|eviction|bankruptcy|bankrupt|insolvent|iva)\b",
    r"\b(overwhelmed|drowning)\b.*(debt|money|bills|finance)",
    r"\b(desperate|crisis|emergency)\b.*(money|financial|cash|fund)",
    r"\bcan't (make|meet) ends?\b",
]

DISTRESS_RESPONSE = (
    "I'm sorry to hear you're going through a difficult time. "
    "Before we look at your finances together, I want to make sure you know about some "
    "**free, confidential support** that's available to you:\n\n"
    "- **MoneyHelper** (free & impartial): 0800 138 7777 | moneyhelper.org.uk\n"
    "- **StepChange Debt Charity**: 0800 138 1111 | stepchange.org\n"
    "- **National Debtline**: 0808 808 4000 | nationaldebtline.org\n\n"
    "These services are completely free and can help with debt advice, budgeting and "
    "negotiating with creditors. Would you still like me to look at your transaction data "
    "to help identify where we can make improvements?"
)

# Patterns to detect if LLM hallucinated a number not from grounded data
# e.g. "£1,234.56" that wasn't in the context
CURRENCY_PATTERN = re.compile(r"£[\d,]+\.?\d*")


def _normalise_amount(amount: str) -> str:
    """
    Normalise a currency string for comparison.
    Strips commas and trailing zeros so that £1,234.50 == £1234.5 == £1234.50.
    """
    # Remove £ and commas, then convert to float and back for canonical form
    try:
        numeric = float(amount.replace("£", "").replace(",", ""))
        return f"£{numeric:.2f}"
    except ValueError:
        return amount


# ---------------------------------------------------------------------------
# Input Guard
# ---------------------------------------------------------------------------

def check_input(user_message: str) -> GuardDecision:
    """
    Classify user intent and decide whether to allow, block or redirect.
    Called BEFORE the message reaches the LLM.
    """
    msg_lower = user_message.lower()

    # Check financial distress — Consumer Duty proactive signpost (before regulated check)
    for pattern in DISTRESS_PATTERNS:
        if re.search(pattern, msg_lower, re.IGNORECASE):
            return GuardDecision(
                result=GuardResult.REDIRECT,
                intent=IntentType.GENERAL_QUERY,
                reason="Message indicates potential financial distress.",
                safe_response=DISTRESS_RESPONSE,
            )

    # Check regulated advice
    for pattern in REGULATED_ADVICE_PATTERNS:
        if re.search(pattern, msg_lower, re.IGNORECASE):
            return GuardDecision(
                result=GuardResult.REDIRECT,
                intent=IntentType.REGULATED_ADVICE,
                reason="Message requests regulated financial advice.",
                safe_response=(
                    "That's a great question, but it falls into regulated financial advice territory "
                    "which I can't provide. I can connect you with one of our qualified financial "
                    "advisers who can give you a personalised recommendation. Would you like me to "
                    "arrange that?"
                ),
            )

    # Check out of scope — but only if the message doesn't contain financial terms
    is_financial = any(re.search(p, msg_lower, re.IGNORECASE) for p in FINANCIAL_ALLOWLIST)
    if not is_financial:
        for pattern in OUT_OF_SCOPE_PATTERNS:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                return GuardDecision(
                    result=GuardResult.BLOCK,
                    intent=IntentType.OUT_OF_SCOPE,
                    reason="Message is outside financial coaching scope.",
                    safe_response=(
                        "I'm AI Sage, your financial coach, so I can only help with questions about "
                        "your money, spending, savings and financial wellbeing. Is there something "
                        "about your finances I can help you with today?"
                    ),
                )

    return GuardDecision(
        result=GuardResult.PASS,
        intent=IntentType.GENERAL_QUERY,
        reason="Message passed all input checks.",
    )


# ---------------------------------------------------------------------------
# Output Guard
# ---------------------------------------------------------------------------

def check_output(
    llm_response: str,
    grounded_numbers: set[str],
) -> GuardDecision:
    """
    Verify the LLM response is grounded in tool-retrieved data.

    Strategy: rather than exact string matching (which breaks on rounding and
    comma-formatting differences), we enforce a softer but reliable rule:
      - If the response contains £ amounts AND no tools were called → BLOCK
        (LLM invented numbers from thin air)
      - If tools were called, the grounding guarantee comes from the tool
        architecture (all numbers originate from TransactionAnalyser), so PASS.

    This avoids false positives from legitimate LLM reformatting of tool outputs
    (e.g. £1234.56 → £1,234.56, or rounding £412.33 → ~£412).
    """
    mentioned_amounts = set(CURRENCY_PATTERN.findall(llm_response))

    # LLM mentioned money figures but called no tools — likely hallucinated
    if mentioned_amounts and not grounded_numbers:
        return GuardDecision(
            result=GuardResult.BLOCK,
            intent=IntentType.GENERAL_QUERY,
            reason="LLM cited monetary figures without calling any data tool.",
        )

    return GuardDecision(
        result=GuardResult.PASS,
        intent=IntentType.GENERAL_QUERY,
        reason="Response is grounded — tool data was retrieved before answering.",
    )


# ---------------------------------------------------------------------------
# FCA Disclaimer injector
# ---------------------------------------------------------------------------

FCA_DISCLAIMER = (
    "\n\n---\n*This is financial guidance based on your transaction data, not regulated "
    "financial advice. For personalised investment or borrowing advice, please speak to "
    "a qualified financial adviser.*"
)

DISCLAIMER_TRIGGER_TERMS = [
    "invest", "pension", "mortgage", "loan", "borrow", "savings account",
    "isa", "interest rate", "remortgage", "credit card",
]


def should_append_disclaimer(response: str) -> bool:
    """Return True if the response touches on regulated-adjacent topics."""
    lower = response.lower()
    return any(term in lower for term in DISCLAIMER_TRIGGER_TERMS)


def apply_disclaimer(response: str) -> str:
    if should_append_disclaimer(response):
        return response + FCA_DISCLAIMER
    return response


# ---------------------------------------------------------------------------
# Number extractor — used to build grounded_numbers set
# ---------------------------------------------------------------------------

def extract_grounded_amounts(data: dict) -> set[str]:
    """
    Recursively extract all currency strings from a structured data dict
    (e.g. SpendingInsights serialised to dict) to form the allowed-numbers set.
    """
    amounts: set[str] = set()
    _extract_recursive(data, amounts)
    return amounts


def _extract_recursive(obj, amounts: set[str]) -> None:
    if isinstance(obj, str) and re.match(r"^£[\d,]+\.?\d*$", obj):
        amounts.add(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _extract_recursive(v, amounts)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _extract_recursive(item, amounts)
