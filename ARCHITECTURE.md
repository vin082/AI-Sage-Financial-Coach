# LBG Financial Coaching Agent — System Architecture

> **Phase 1 MVP | Coaching Agent**
> Lloyds Banking Group · AI Financial Wellbeing Platform

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Step-by-Step Workflow](#3-step-by-step-workflow)
4. [Component Deep-Dives](#4-component-deep-dives)
5. [Tech Stack](#5-tech-stack)
6. [Data Flow Diagram](#6-data-flow-diagram)
7. [Security & Compliance](#7-security--compliance)

---

## 1. System Overview

The LBG Coaching Agent is a **grounded, guardrailed AI assistant** that answers financial questions using a customer's actual transaction data — never inventing or estimating figures. It is built around a strict separation of concerns:

| Layer | Responsibility | LLM Involved? |
|---|---|---|
| Input Guard | Block off-topic / regulated-advice queries | No |
| Transaction Analyser | Compute all monetary figures | No |
| Financial Health Engine | Score calculation (rule-based) | No |
| RAG Knowledge Base | Retrieve LBG-reviewed guidance | No |
| LLM Narration | Translate verified data into natural language | Yes (narrate only) |
| Output Guard | Verify no figures cited without tool call | No |
| FCA Disclaimer Engine | Append regulatory notice where needed | No |

**The LLM is never trusted to compute, recall or estimate financial figures. It is only trusted to narrate pre-verified facts.**

---

## 2. Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════╗
║                        CUSTOMER TOUCHPOINTS                          ║
║                                                                      ║
║    ┌─────────────┐   ┌─────────────┐   ┌──────────────────────┐     ║
║    │  Streamlit  │   │  FastAPI    │   │  Future: Mobile App  │     ║
║    │  Demo UI    │   │  REST API   │   │  / WhatsApp / Voice  │     ║
║    └──────┬──────┘   └──────┬──────┘   └──────────┬───────────┘     ║
╚═══════════╪═════════════════╪════════════════════╪══════════════════╝
            └─────────────────┼────────────────────┘
                              │  User Message
                              ▼
╔══════════════════════════════════════════════════════════════════════╗
║                         GUARDRAILS LAYER                             ║
║                                                                      ║
║   ┌────────────────────────────────────────────────────────────┐     ║
║   │                     INPUT GUARD                            │     ║
║   │                                                            │     ║
║   │  ┌─────────────────────┐   ┌───────────────────────────┐  │     ║
║   │  │  Out-of-Scope Check │   │  Regulated Advice Check   │  │     ║
║   │  │  (general knowledge,│   │  (investments, pensions,  │  │     ║
║   │  │   geography, etc.)  │   │   specific product recs)  │  │     ║
║   │  └──────────┬──────────┘   └─────────────┬─────────────┘  │     ║
║   │             │ BLOCK / REDIRECT            │                │     ║
║   └─────────────┼─────────────────────────────┘                │     ║
║                 │ PASS                                          ║
╚═════════════════╪════════════════════════════════════════════════════╝
                  │
                  ▼
╔══════════════════════════════════════════════════════════════════════╗
║                      ORCHESTRATION LAYER                             ║
║                                                                      ║
║   ┌──────────────────────────────────────────────────────────┐       ║
║   │              CoachingAgent  (LangGraph ReAct)            │       ║
║   │                                                          │       ║
║   │   Session Memory ◄──► Customer Memory                   │       ║
║   │   (conversation)        (goals, prefs, score history)   │       ║
║   │                                                          │       ║
║   │   LLM (GPT-4o / Azure OpenAI)                           │       ║
║   │   temp=0.1  ·  max_tokens=1024                          │       ║
║   └────────────────────────┬─────────────────────────────────┘       ║
║                            │  Tool Call                               ║
╚════════════════════════════╪═════════════════════════════════════════╝
                             │
            ┌────────────────┼───────────────────┐
            │                │                   │
            ▼                ▼                   ▼
╔═══════════════╗  ╔══════════════════╗  ╔═══════════════════╗
║  TRANSACTION  ║  ║    FINANCIAL     ║  ║   RAG KNOWLEDGE   ║
║   ANALYSER    ║  ║  HEALTH ENGINE   ║  ║      BASE         ║
║               ║  ║                 ║  ║                   ║
║ Pure Python   ║  ║  Rule-based     ║  ║ FAISS + LBG docs  ║
║ Decimal maths ║  ║  scoring 0-100  ║  ║ (FCA-reviewed)    ║
║ No LLM        ║  ║  No LLM         ║  ║ Embeddings only   ║
╚═══════┬───────╝  ╚════════┬════════╝  ╚════════┬══════════╝
        │                   │                    │
        └───────────────────┼────────────────────┘
                            │  Verified structured data
                            ▼
╔══════════════════════════════════════════════════════════════════════╗
║                        LLM NARRATION                                  ║
║                                                                      ║
║   LLM receives: pre-computed facts + grounded £ amounts              ║
║   LLM task:     translate data into warm, clear natural language      ║
║   LLM must NOT: compute, estimate or recall any financial figure      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
                            │
                            ▼
╔══════════════════════════════════════════════════════════════════════╗
║                        OUTPUT GUARD                                   ║
║                                                                      ║
║   ┌──────────────────────────────────────────────────────────┐       ║
║   │  If £ amounts in response AND no tool was called → BLOCK │       ║
║   │  FCA disclaimer injected for regulated-adjacent topics   │       ║
║   └──────────────────────────────────────────────────────────┘       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
                            │
                            ▼
                   ✅ Response to Customer
```

---

## 3. Step-by-Step Workflow

### Step 1 — Customer Sends a Message

The customer types a question in the UI (Streamlit demo, mobile app, or via the API). Example: *"How much am I spending on eating out?"*

---

### Step 2 — Input Guard (Pre-LLM screening)

Before the message reaches the LLM, two checks run in sequence:

**Check A — Financial Allowlist**
If the message contains financial terms (`spend`, `budget`, `savings`, `bank`, `income`, etc.), it is immediately marked as in-scope and the OOS check is skipped.

**Check B — Out-of-Scope Pattern Match**
If no financial terms are found, the message is tested against out-of-scope patterns:
- General knowledge (geography, history, science, culture)
- Non-financial technology questions
- Food, travel, sport, politics, religion

→ **If matched:** Return a fixed refusal message. No LLM call made. No tokens consumed.

**Check C — Regulated Advice Pattern Match**
Regardless of financial terms, the message is checked for regulated-advice intent:
- Investment or product recommendations
- Specific interest rate queries
- Tax planning or legal advice
- Borrowing recommendations without full context

→ **If matched:** Return a redirect to a qualified Lloyds adviser.

→ **If all checks pass:** Proceed to orchestration.

---

### Step 3 — Session & Memory Loading

The `CoachingAgent` loads two memory contexts:

- **SessionMemory** — current conversation history (last 10 turns), list of tools called this session, set of grounded £ amounts retrieved so far.
- **CustomerMemory** — persistent goals, preferences, last health score date, conversation count.

Both are combined with the system prompt to form the full LLM context window.

---

### Step 4 — ReAct Tool-Calling Loop

The LLM enters a **Reason → Act** loop (max 5 iterations):

```
LLM reasons about what data it needs
    ↓
LLM emits a tool call (e.g. get_spending_insights)
    ↓
Tool executes deterministically (pure Python, no LLM)
    ↓
Tool result appended to message history
    ↓
LLM reasons again with new data
    ↓
LLM emits final natural-language response (no more tool calls)
```

**Available tools and what they do:**

| Tool | What it computes | LLM role |
|---|---|---|
| `get_spending_insights` | Avg monthly spend/income/surplus, category breakdown, trend | Narrate |
| `get_financial_health_score` | 0–100 score across 5 pillars (rule-based) | Narrate |
| `get_category_detail` | Per-merchant breakdown for one category | Narrate |
| `get_savings_opportunities` | Concrete £ savings opportunities (rule-based) | Narrate |
| `search_guidance` | Retrieves relevant chunks from LBG knowledge base via RAG | Narrate |

---

### Step 5 — Deterministic Computation (Tools)

Each tool performs pure, deterministic computation:

**Transaction Analyser**
- Reads raw `Transaction` records (date, amount, merchant, category)
- Computes totals using Python `Decimal` arithmetic (no floating-point errors)
- Returns structured `SpendingInsights` dataclass with all figures pre-formatted as `£X.XX` strings

**Financial Health Engine**
- Receives `SpendingInsights` as input
- Applies five deterministic scoring rules (savings rate, spend stability, essentials ratio, subscription load, emergency buffer)
- Returns `FinancialHealthReport` with scores, grades and plain-English explanations — all generated without LLM involvement

**RAG Knowledge Base**
- User query embedded via `text-embedding-3-small`
- Top-3 most relevant chunks retrieved from FAISS vector index
- Chunks are from LBG-reviewed guidance documents only
- LLM is instructed to base its response on retrieved chunks, not training data

---

### Step 6 — LLM Narration

The LLM receives the tool output (structured JSON with verified figures) and its only job is to translate it into warm, clear, jargon-free English. The system prompt explicitly instructs it:

- Use only the numbers provided in tool outputs
- Do not supplement with figures from training knowledge
- Keep responses to 3–5 sentences unless detail is requested
- Refuse off-topic questions with the prescribed message

---

### Step 7 — Output Guard (Post-LLM screening)

Before the response reaches the customer:

**Rule:** If the response contains `£` amounts **and** no tool was called this turn → **BLOCK** and retry with an explicit instruction to call the tool first.

This catches the edge case where the LLM answers a financial question from its training memory without calling the tool.

If the retry also contains ungrounded amounts, a safe fallback message is returned.

---

### Step 8 — FCA Disclaimer Injection

If the response contains any regulated-adjacent terms (`savings account`, `mortgage`, `loan`, `ISA`, `interest rate`, etc.), a standardised FCA disclaimer is appended:

> *This is financial guidance based on your transaction data, not regulated financial advice. For personalised investment or borrowing advice, please speak to a Lloyds financial adviser.*

---

### Step 9 — Response Delivery & Memory Update

- Final response is returned to the customer via the UI or API
- Response is stored in `SessionMemory` for conversation continuity
- If health score was computed, `CustomerMemory` is updated with the new score and date

---

## 4. Component Deep-Dives

### Transaction Analyser (`coaching_agent/tools/transaction_analyser.py`)

```
Input:  CustomerProfile (raw Transaction list)
Output: SpendingInsights (all figures as verified Decimal values)

Key design:
- All arithmetic uses Python Decimal (not float) — no rounding errors
- Category totals, averages, trends computed from raw records only
- Savings opportunity rules are deterministic (e.g. eating_out > 30% of groceries)
- No LLM involvement at any stage
```

### Financial Health Engine (`coaching_agent/tools/financial_health.py`)

```
5 scoring pillars (max points):

  Savings Rate        (30pts) — % of income saved each month
  Spend Stability     (20pts) — coefficient of variation month-on-month
  Essentials Balance  (20pts) — essential vs discretionary spend ratio
  Subscription Load   (15pts) — subscriptions as % of income
  Emergency Buffer    (15pts) — months of expenses covered by current balance

Grade scale:  A (≥85%)  B (≥70%)  C (≥50%)  D (<50%)
```

### Guardrails (`coaching_agent/guardrails.py`)

```
Input Guard:
  1. Financial allowlist check  → skip OOS if financial terms present
  2. Out-of-scope pattern match → 25+ patterns across 7 topic areas
  3. Regulated advice match     → 8 patterns covering FCA regulated topics

Output Guard:
  - Detects £ amounts in response with no prior tool call
  - Triggers one automatic retry with explicit tool-call instruction
```

### Memory (`coaching_agent/memory.py`)

```
SessionMemory (per conversation):
  - messages[]          last 10 turns for LLM context window
  - grounded_amounts    set of £ strings returned by tools this session
  - tool_calls_made     audit trail of tools invoked

CustomerMemory (persistent):
  - goals[]             customer-defined financial goals
  - last_health_score   score + date for trend tracking
  - conversation_count  engagement depth metric
```

---

## 5. Tech Stack

### Core AI / LLM

| Component | Technology | Reason |
|---|---|---|
| LLM | GPT-4o (OpenAI) / Azure OpenAI | Best instruction-following; Azure for UK data residency |
| LLM Temperature | 0.1 | Low randomness for factual accuracy |
| Embeddings | `text-embedding-3-small` | Efficient, accurate semantic search |
| Agent Framework | LangChain + LangGraph | ReAct loop, tool binding, message history |
| Vector Store | FAISS (dev) → Azure AI Search (prod) | Fast similarity search; Azure for compliance |

### Application

| Component | Technology | Reason |
|---|---|---|
| API Layer | FastAPI | High-performance async REST; auto OpenAPI docs |
| Demo UI | Streamlit | Rapid prototyping; data visualisation built-in |
| Data Validation | Pydantic v2 | Type-safe request/response models |
| Configuration | python-dotenv | 12-factor app config |

### Data & Computation

| Component | Technology | Reason |
|---|---|---|
| Financial Arithmetic | Python `Decimal` | No floating-point rounding errors on monetary values |
| Data Structures | Python `dataclasses` | Typed, immutable results from all deterministic tools |
| Data Analysis | Pandas + NumPy | Category aggregation, monthly summaries |
| Mock Data | Custom generator (seeded `random`) | Reproducible demo data for presentations |

### Infrastructure (Production Target)

| Component | Technology | Reason |
|---|---|---|
| Cloud | Microsoft Azure (UK South) | Data residency; LBG existing agreements |
| LLM Hosting | Azure OpenAI Service | UK data residency; enterprise SLA |
| Session Store | Azure Redis Cache | Low-latency session memory |
| Vector DB | Azure AI Search | Managed, scalable, compliant |
| Auth | Azure AD B2C | LBG SSO integration |
| API Gateway | Azure API Management | Rate limiting, audit logging, throttling |
| Observability | Azure Monitor + App Insights | LLM call tracing, guardrail trigger alerts |
| Secrets | Azure Key Vault | No secrets in code or environment files |

### Development

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Package Manager | `uv` (fast) / `pip` |
| Testing | pytest + pytest-asyncio |
| Build | Hatchling |

---

## 6. Data Flow Diagram

```
Customer Transaction Data
        │
        │  (Production: Customer 360 API / Core Banking)
        │  (Demo: deterministic mock generator, seed=42)
        ▼
┌─────────────────────┐
│  CustomerProfile    │  customer_id, name, salary_day
│  Transaction[]      │  date, amount (Decimal), merchant,
│                     │  category, channel, balance_after
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ TransactionAnalyser │  Pure Python · Decimal arithmetic
│                     │
│  get_full_insights()│──► SpendingInsights (all Decimal)
│  get_category_detail│──► CategorySummary
│  get_savings_opps() │──► dict (rule-based opportunities)
└──────────┬──────────┘
           │  Structured data (no £ strings yet)
           ▼
┌─────────────────────┐
│   Tool Serialiser   │  Formats Decimal → "£X.XX" strings
│                     │  Registers all amounts in
│                     │  session.grounded_amounts set
└──────────┬──────────┘
           │  JSON string → LLM context
           ▼
┌─────────────────────┐
│    LLM (GPT-4o)     │  Receives: JSON facts
│    Narration only   │  Produces: natural language
│    temp = 0.1       │  Constraint: use only provided figures
└──────────┬──────────┘
           │  Text response
           ▼
┌─────────────────────┐
│   Output Guard      │  Check: £ in response + no tools called?
│   + FCA Disclaimer  │  Append: regulatory notice if needed
└──────────┬──────────┘
           │
           ▼
      Customer UI
```

---

## 7. Security & Compliance

### FCA Compliance

| Control | Implementation |
|---|---|
| Guidance vs Advice boundary | Regulated advice patterns blocked at input guard |
| Disclaimer injection | Automatic on regulated-adjacent responses |
| No product recommendations | System prompt + regulated advice input guard |
| Adviser escalation path | Redirect message with offer to connect |

### Data Protection

| Control | Implementation |
|---|---|
| UK data residency | Azure OpenAI UK South deployment |
| No PII to LLM training | Azure OpenAI does not use API data for training |
| Session isolation | UUID-keyed session store; no cross-customer data |
| Secrets management | Azure Key Vault (production); `.env` never committed |

### AI Safety

| Control | Implementation |
|---|---|
| Anti-hallucination | All numbers computed by deterministic tools; LLM narrates only |
| Output verification | Output guard blocks responses with ungrounded £ figures |
| Prompt injection defence | Input guard runs before LLM sees any user input |
| Audit trail | All tool calls logged per session; guardrail triggers monitored |
| Temperature control | `temp=0.1` minimises creative deviation from facts |

---

*Document version: 1.0 · Phase 1 MVP · LBG AI Financial Wellbeing Platform*
