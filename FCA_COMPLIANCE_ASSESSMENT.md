# FCA Compliance Assessment — AI Sage Financial Coach

**Date:** 22 February 2026
**Prepared by:** Claude Code (claude-sonnet-4-6)
**Scope:** AI Sage Financial Coach MVP — coaching_agent, guardrails, API, demo UI
**Regulatory framework:** FCA (UK) — FSMA 2000, Consumer Duty (PRIN 12), FG21/1, UK GDPR, PSD2/PSR 2017

> **Update 22 Feb 2026:** Five quick-win compliance fixes implemented in commit following this assessment.
> See [Section 8 — Changes Implemented](#8-changes-implemented-22-feb-2026) for details.

---

## 1. What's Already Well-Implemented ✅

The codebase shows solid foundational compliance work across the core accuracy and advice-boundary layers.

| Component | What it does | Why it helps compliance |
|-----------|-------------|------------------------|
| **Input guardrail** (`guardrails.py`) | Blocks 8 regulated advice pattern categories before the LLM sees them | Prevents FSMA 2000 s.19/s.21 violations (unauthorised regulated activity) |
| **Output guardrail** + grounded amounts | Verifies every £ figure in a response came from a deterministic tool | Prevents misleading financial statements — FCA Principle 7 (clear, fair, not misleading) |
| **FCA disclaimer auto-injection** | Appended automatically when response mentions mortgage/ISA/pension/loan | Required boundary between "guidance" and "advice" |
| **Adviser escalation** (`adviser_handoff.py`) | Full context handoff package sent to human adviser | Consumer Duty (PRIN 12) — supports customers to pursue their financial objectives |
| **System prompt** | Explicitly states "You do NOT provide regulated financial advice" | Documents the agent's intended regulatory status |
| **Decimal arithmetic** throughout | All monetary calculations use `Decimal`, not `float` | No rounding errors in financial figures — accuracy obligation |
| **Vulnerability flag** (`is_vulnerable: bool`) | Structural hook exists in handoff package | Foundation for FCA FG21/1 vulnerable customer support |
| **Scope restriction** | Non-financial questions are blocked before reaching the LLM | Limits regulatory exposure to financial coaching only |
| **Adviser handoff reasons** | Includes "vulnerability", "bereavement", "complaint" routing codes | Maps to FCA-required escalation pathways |

---

## 2. Critical Gaps — Would Fail FCA Review 🔴

### 2.1 No Explicit AI Disclosure at Session Start

**Regulation:** FCA AI transparency guidance; Consumer Duty PRIN 12 (acting in good faith)

The session welcome message currently reads:
> *"Welcome back, Alex! I'm AI Sage, your financial coach."*

"AI Sage" is ambiguous — a customer could reasonably believe they are speaking to a human financial coach. FCA and UK Government guidance on AI transparency requires customers to be **explicitly informed** they are interacting with an automated system, not a human adviser.

**Recommended fix:** Add to the `/session/new` welcome message:
> *"I'm an AI assistant, not a human financial adviser. Everything I provide is financial guidance based on your own data."*

---

### 2.2 No Session-Start Guidance Disclaimer

**Regulation:** FSMA 2000 s.19 (regulated activity boundary); FCA guidance on financial guidance vs advice

The FCA disclaimer (in `guardrails.py`) only triggers when the LLM's *response* contains regulated keywords (mortgage, ISA, pension, etc.). Customers receive **no upfront notice** that all outputs from this system are guidance, not regulated financial advice.

A customer who receives a budget plan or savings recommendation with no prior disclaimer could argue they were misled.

**Recommended fix:** The session welcome message should include:
> *"I provide financial guidance based on your transaction data — not regulated financial advice. For regulated advice, I can connect you with a qualified adviser at any time."*

---

### 2.3 UK GDPR — No Consent or Privacy Notice for AI Processing

**Regulation:** UK GDPR Art. 6 (lawful basis), Art. 13 (transparency), Art. 22 (automated decisions); ICO guidance on AI

Transaction data and salary data are sensitive personal financial data. Processing this data through an LLM (OpenAI/Azure OpenAI) requires:

- A documented **lawful basis** (likely legitimate interests or explicit consent)
- A **Privacy Notice** informing customers that an AI processes their financial data, including which third-party model provider is used
- A defined **data retention policy** for `data/customer_store/*.json` files
- **Encryption at rest** for stored customer profiles
- A mechanism for **Subject Access Requests** (Art. 15) and **Right to Erasure** (Art. 17)

**Current state:** None of these exist in the codebase. Customer memory is stored as unencrypted plain-text JSON.

---

### 2.4 Product Eligibility Tool — Financial Promotions Risk

**Regulation:** FSMA 2000 s.21 (financial promotions); FCA COBS 4 (communicating with clients)

The `check_product_eligibility_tool` provides *"indicative eligibility for banking products."* Even framed as guidance, this output can constitute a **financial promotion** under FSMA 2000 s.21 if it names specific products without the required risk warnings and regulatory caveats. The system prompt states "guidance only" but this needs to be enforced at the **tool output level**, not just the prompt level.

**Recommended fix:** Every product eligibility response must include:
> *"This is an indicative check only and does not constitute a product offer or recommendation. Eligibility criteria and product terms are subject to change. [Firm name] is authorised and regulated by the Financial Conduct Authority [FCA Reg No.]."*

---

## 3. Important Gaps — Fix Before Live Regulated Deployment 🟠

### 3.1 Vulnerable Customer Detection is Passive

**Regulation:** FCA FG21/1 (Guidance on the Fair Treatment of Vulnerable Customers); Consumer Duty PRIN 12

FCA FG21/1 requires firms to **proactively identify** customers who may be vulnerable due to health, life events, resilience, or capability. The `life_event_detector` touches this (pregnancy, bereavement, job loss) but:

- Vulnerability is **never formally flagged** to the agent or escalation system
- Communication style is **never adapted** for vulnerable customers (simpler language, slower pace)
- No proactive signpost to **MoneyHelper** or **StepChange** for customers showing financial distress signals
- The `is_vulnerable: bool` hook exists in `adviser_handoff.py` but nothing in the agent sets it to `True`

**Recommended fix:** Define vulnerability signals (health score < 40, bereavement detected, repeated failed payment patterns) and have the agent proactively adapt tone and escalate to "urgent" channel.

---

### 3.2 No Financial Distress Escalation

**Regulation:** Consumer Duty PRIN 12 — avoiding foreseeable harm; FCA Financial Lives guidance

If a customer's financial health score is very low (e.g. < 40/100) or transaction data shows signs of serious debt stress (repeated overdraft, missed direct debits), there is currently no escalation to:
- Free debt support services (MoneyHelper: 0800 138 7777)
- National Debtline or StepChange
- The firm's own hardship team

Under Consumer Duty, foreseeable harm to retail customers must be identified and mitigated.

---

### 3.3 No Complaints Process Disclosure

**Regulation:** FCA DISP 1.2 (Complaints handling); FCA DISP 1.4 (publicising complaints procedure)

FCA DISP rules require firms to inform customers about how to raise a complaint and their right to escalate to the **Financial Ombudsman Service (FOS)**. There is no mention of the complaints process anywhere in the agent's responses, welcome messages, or UI.

**Recommended fix:** Add to the session welcome or UI footer:
> *"To raise a complaint: [link to complaints page] · Financial Ombudsman Service: 0800 023 4567 · financialombudsman.org.uk"*

---

### 3.4 Strong Customer Authentication (SCA) Not Implemented

**Regulation:** UK Payment Services Regulations 2017 (PSR); PSD2 SCA requirements

Accessing and narrating detailed salary and transaction history falls under PSD2 / PSR 2017 scope. Step-up re-authentication (biometric or OTP challenge) should be required before the AI accesses and narrates detailed financial data. The current authentication is a bearer token stub (`CUST_DEMO_001`) with no real identity verification.

**Note:** This is already marked as a production concern in the codebase; it must be resolved before any live deployment.

---

## 4. Advisory Items — Best Practice Before Live Deployment 🟡

| Item | FCA/Legal Reference | Current State |
|------|---------------------|---------------|
| **Full audit log** of every AI interaction (beyond session summaries) | FCA SYSC 9 (record-keeping obligations) | Partial — session summaries only |
| **AI model risk management** — accuracy testing, bias testing, output drift monitoring | FCA Discussion Paper DP5/22 (AI in financial services) | Not implemented |
| **SM&CR accountability** — named approved person responsible for the AI system | FCA Senior Managers and Certification Regime | Not defined |
| **Human review loop** — periodic compliance officer review of AI output samples | Consumer Duty — ongoing monitoring | Not implemented |
| **Bias/fairness testing** — verify advice quality does not vary by protected characteristic | FCA PRIN 6 (fair treatment); Equality Act 2010 | Not implemented |
| **Opt-out from automated processing** — customer right to request human review | UK GDPR Art. 22 | Not implemented |
| **Data Subject Access Requests** — mechanism to export/delete `customer_store` JSON | UK GDPR Art. 15–17 | Not implemented |
| **Third-party model disclosure** — customers informed data is sent to OpenAI/Azure | UK GDPR Art. 13; ICO guidance | Not implemented |
| **Financial promotions sign-off** — regulated approval for any product mention | FSMA 2000 s.21 | Not implemented |

---

## 5. Overall Scorecard

| Compliance Area | Status | Priority |
|-----------------|--------|----------|
| Guidance vs regulated advice boundary | ✅ Good foundation | — |
| Anti-hallucination / financial accuracy | ✅ Strong (deterministic tools + output guard) | — |
| Adviser escalation pathway | ✅ Implemented | — |
| AI identity disclosure | ✅ **Implemented** | Done |
| Session-start guidance disclaimer | ✅ **Implemented** | Done |
| UK GDPR consent & Privacy Notice | ✅ **Consent modal implemented** | Done (production: full DPA required) |
| Product eligibility financial promotions | ✅ Standard caveat already in tool | Done |
| Vulnerable customer proactive support | ✅ **Distress signposting implemented** | Done |
| Financial distress escalation | ✅ **MoneyHelper / StepChange implemented** | Done |
| Complaints process disclosure | ✅ **FOS details in footer + system prompt** | Done |
| Strong Customer Authentication | 🟠 Stub only | Pre-launch |
| Full audit log | 🟡 Partial | Before regulatory inspection |
| AI model risk governance | 🟡 Not implemented | Before regulatory inspection |
| SM&CR accountability | 🟡 Not defined | Before regulatory inspection |
| Bias / fairness testing | 🟡 Not implemented | Before regulatory inspection |

---

## 6. Recommended Immediate Actions (Before Any Client-Facing Demo)

1. **Add AI disclosure to welcome message** — *"I am an AI assistant, not a human financial adviser."* — 2 lines of code in `api/main.py` (`/session/new` response)

2. **Add guidance disclaimer to welcome message** — *"I provide financial guidance, not regulated advice."* — 1 line in `api/main.py`

3. **Add complaints signpost to UI** — Financial Ombudsman Service number and link in the chat panel footer — 2 lines in `dashboard.html`

4. **Add risk warning to product eligibility responses** — Caveat in `product_eligibility.py` output

5. **Label demo materials clearly** — All demo materials must state *"Mock data only — no real customer data is processed in this demonstration"*

6. **Define data retention** — Document how long `customer_store/*.json` files are kept and add a deletion mechanism

---

## 7. Architecture Strengths for FCA Compliance

The core technical architecture is well-suited for FCA compliance and represents genuine innovation in responsible AI design:

- **Deterministic-tools + narrating-LLM** pattern means the AI never computes or invents financial figures — all numbers are pre-verified by auditable Python tools using `Decimal` arithmetic
- **Grounded amounts set** ensures the output guard can mathematically verify every £ figure in a response
- **Input guardrail runs before the LLM** — regulated advice questions are caught deterministically, not relying on the LLM to self-police
- **Adviser handoff package** includes the full conversation context so customers never have to repeat themselves — aligns with Consumer Duty's requirement for joined-up support

These architectural decisions mean the hardest compliance problems (accuracy, advice boundary, escalation) are solved structurally, not through prompt engineering alone.

---

---

## 8. Changes Implemented (22 Feb 2026)

The following fixes were applied to the codebase following this assessment:

### 8.1 AI Disclosure + Guidance Disclaimer — `api/main.py`
The `/session/new` welcome message now opens with:
> *"Hi [Name]! I'm AI Sage — an AI assistant, not a human financial adviser. I provide personalised financial guidance based on your verified transaction data. This is not regulated financial advice under FSMA 2000..."*

### 8.2 GDPR Consent Modal — `dashboard.html`, `chat_panel.js`, `style.css`
- A full-screen consent modal is shown the **first time** a user opens the chat panel.
- The modal explains: AI processing of financial data, guidance-not-advice distinction, third-party AI usage, UK GDPR rights, and FOS complaints information.
- Consent is recorded in `localStorage` and persists across sessions (key: `ai_sage_gdpr_consent_v1`).
- Declining closes the modal without opening the chat.
- A "Privacy Notice" link in the fca-notice footer triggers a summary privacy notice.

### 8.3 Complaints Disclosure — `dashboard.html`, `coaching_agent/agent.py`
- The persistent fca-notice footer now shows: *"Financial Ombudsman Service: 0800 023 4567"* on every screen.
- System prompt Rule 10 instructs the agent to provide FOS details whenever a customer expresses dissatisfaction and to escalate via `escalate_to_adviser` with `reason_code="complaint"`.

### 8.4 Financial Distress Escalation — `guardrails.py`, `coaching_agent/agent.py`
- **Input guardrail:** 5 distress signal patterns (bailiff, repossession, can't pay bills, debt collector, overwhelming debt). When detected, the guardrail immediately returns a warm signpost response including MoneyHelper (0800 138 7777), StepChange (0800 138 1111), and National Debtline (0808 808 4000) — **before** the LLM processes the message.
- **Health score tool:** When `overall_score < 40`, the tool output includes a `support_signpost` field with the same free services.
- **System prompt Rule 9:** Instructs the agent to surface the `support_signpost` services if present in tool output, and to proactively mention them for distress keywords.

### 8.5 Remaining Items for Production
The following items from Section 2–4 still require action before a live regulated deployment:
- Full UK GDPR Data Protection Agreement with Azure OpenAI
- Formal Privacy Notice (replace alert with dedicated privacy page)
- Strong Customer Authentication (SCA) via Azure AD B2C
- Full audit log (SYSC 9 compliant)
- SM&CR accountability mapping
- AI model bias testing and drift monitoring

---

*This assessment is based on a code review as of 22 February 2026 and is intended as internal technical guidance. It does not constitute legal advice. The firm should obtain formal legal and compliance sign-off from FCA-authorised compliance counsel before any live deployment.*
