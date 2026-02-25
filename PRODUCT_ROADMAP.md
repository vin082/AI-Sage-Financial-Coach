# LBG Customer AI Super Agent — Product Roadmap

> **Product:** AI Financial Wellbeing Platform
> **Owner:** LBG Digital & AI
> **Horizon:** 24 months
> **Last updated:** February 2026
> **Version:** 2.0 — Updated with Phase 1 delivery status, RICE-scored backlog, and Emotional Connect / Business Activation epics

---

## Vision

> *Every LBG customer has access to a trusted, always-on AI financial companion that understands their life, coaches their money habits, and acts on their behalf — deepening the relationship that 26 million customers already have with Lloyds, Halifax and Bank of Scotland.*

---

## Build Status — February 2026

### Phase 1 MVP: Delivered ✅

| Epic | Feature | Status |
|------|---------|--------|
| 1.1 Spending Intelligence | Monthly spend breakdown by category | ✅ Done |
| 1.1 Spending Intelligence | Top merchant analysis | ✅ Done |
| 1.1 Spending Intelligence | Income vs spend summary with surplus/deficit | ✅ Done |
| 1.1 Spending Intelligence | Savings opportunity identifier | ✅ Done |
| 1.1 Spending Intelligence | Inline Chart.js visualisations (donut, radar, line) | ✅ Done |
| 1.2 Health Score | 5-pillar financial health score (0–100) | ✅ Done |
| 1.2 Health Score | Score history tracking | ✅ Done |
| 1.2 Health Score | Support signpost for score < 40 (Consumer Duty) | ✅ Done |
| 1.3 Conversational Q&A | Natural language spend queries | ✅ Done |
| 1.3 Conversational Q&A | Financial literacy RAG Q&A | ✅ Done |
| 1.3 Conversational Q&A | FCA input guardrails (regulated advice, OOS, distress) | ✅ Done |
| 1.3 Conversational Q&A | Output guard — anti-hallucination (£ grounding) | ✅ Done |
| 1.3 Conversational Q&A | FCA disclaimer auto-injection | ✅ Done |
| 1.3 Conversational Q&A | AI identity disclosure (Consumer Duty) | ✅ Done |
| 1.3 Conversational Q&A | GDPR consent gate | ✅ Done |
| 1.4 Platform | Deterministic tools + narrating-LLM architecture | ✅ Done |
| 1.4 Platform | Session memory (10-turn window) | ✅ Done |
| 1.4 Platform | Cross-session customer memory (JSON persistence) | ✅ Done |
| 2.1 Decision Support | Mortgage affordability modeller (PRA 4.5× LTI + stress test) | ✅ Done |
| 2.1 Decision Support | Debt vs savings optimiser | ✅ Done |
| 2.1 Decision Support | Budget planner (50/30/20) | ✅ Done |
| 2.1 Decision Support | Life event detection (basic) | ✅ Done |
| 2.1 Decision Support | Warm adviser handoff | ✅ Done |
| 2.4 Memory | Goal tracking with deduplication | ✅ Done |
| 2.4 Memory | Preference learning (tone, topics) | ✅ Done |
| 2.4 Memory | Context continuity across sessions | ✅ Done |
| Quality | 291-test pytest suite (guardrails, tools, memory, API, charts) | ✅ Done |
| Quality | 6 custom Claude Code agents (Security, FCA, Guardrails, Tests, Hallucination, Reporter) | ✅ Done |
| Compliance | Distress signposting (MoneyHelper, StepChange, National Debtline) | ✅ Done |
| Compliance | Regulated advice redirect (10 patterns including which/pick/best) | ✅ Done |
| Compliance | Complaints FOS signposting | ✅ Done |

### Phase 1 Exit Gates — Status

| Gate | Status |
|------|--------|
| Zero hallucination incidents in UAT | ✅ Output guard live + tested |
| FCA guidance vs advice boundary enforced | ✅ 10 regulated advice patterns + output guard |
| Anti-hallucination framework | ✅ Deterministic tools → grounded amounts → output guard |
| Security pen test | 🟡 Security Review agent created; awaiting formal pen test |
| GDPR consent mechanism | ✅ Consent modal + localStorage gate live |
| Consumer Duty — vulnerable customer support | ✅ Distress patterns + signposting live |
| AI identity disclosure | ✅ AI disclosure in welcome message |
| Self-service containment lift | 🟡 Measuring post-launch |

---

## Strategic Bets

| # | Bet | Why Now |
|---|---|---|
| 1 | **Trust as moat** | LBG brand + 20 years of transaction data cannot be replicated by fintechs |
| 2 | **Agentic over chatbot** | 1-in-3 UK adults already use AI weekly for money — expectation bar is rising fast |
| 3 | **Cross-brand scale** | Halifax, BoS and MBNA share infrastructure — one platform, 26M customers |
| 4 | **Proactive over reactive** | Customers who are reached before a financial event are 3× more likely to act |

---

## KPI Targets by Phase

| KPI | Baseline | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|---|
| Digital CSAT | 68 | 72 | 76 | 80 | 85 |
| Self-service containment | 41% | 55% | 65% | 72% | 78% |
| Depth of relationship (products/customer) | 2.1 | 2.2 | 2.4 | 2.7 | 3.1 |
| Monthly active users (agent) | 0 | 500K | 2M | 5M | 12M |
| Proactive engagement open rate | — | — | 35% | 42% | 50% |

---

## Immediate Priority Backlog — RICE Scored

> **RICE = (Reach × Impact × Confidence) / Effort**
> Reach: % of customers affected (1–10). Impact: value per customer (1–10). Confidence: certainty of estimate (%). Effort: person-weeks.

| # | Feature | Epic | Reach | Impact | Conf% | Effort (wks) | RICE | Phase |
|---|---------|------|-------|--------|-------|-------------|------|-------|
| 1 | **Money Personality Types** (6 types + shift narrative) | FE-7 | 10 | 9 | 75% | 2 | **338** | Now |
| 2 | **Savings Win Celebrations** (gamified milestones) | FE-7 | 8 | 9 | 85% | 1 | **306** | Now |
| 3 | **Context-Aware Product Recommendations** | FE-8 | 9 | 10 | 80% | 4 | **180** | Phase 2 |
| 4 | **Emotional Financial Timeline** (6-month story) | FE-7 | 10 | 8 | 70% | 3 | **187** | Now |
| 5 | **Multi-Persona Demo Environment** (6 personas) | FE-9 | 2 | 10 | 95% | 1 | **190** | Now |
| 6 | **Payday Optimiser** (salary-day sweep nudge) | Epic 2.2 | 9 | 8 | 85% | 2 | **306** | Phase 2 |
| 7 | **Subscription Audit** (identify unused subs) | Epic 2.2 | 8 | 7 | 85% | 1 | **238** | Phase 2 |
| 8 | **Bill Spike Alert** (DD increased notification) | Epic 2.2 | 9 | 7 | 80% | 1 | **252** | Phase 2 |
| 9 | **Goal Savings Planner + ISA bridge** | FE-8 | 8 | 9 | 75% | 3 | **180** | Phase 2 |
| 10 | **Mortgage Readiness Score** | FE-8 | 6 | 10 | 70% | 3 | **140** | Phase 2 |
| 11 | **Runway Alert** (pre-payday shortfall warning) | Epic 2.2 | 8 | 8 | 80% | 1 | **256** | Phase 2 |
| 12 | **In-app push notifications** (iOS/Android) | Epic 2.3 | 10 | 7 | 75% | 4 | **131** | Phase 2 |
| 13 | **FE-5 create_agent migration** | FE-5 | 1 | 6 | 90% | 4 | **14** | Phase 2 |
| 14 | **Weekly email digest** | Epic 2.3 | 7 | 6 | 80% | 2 | **168** | Phase 2 |
| 15 | **WhatsApp channel pilot** | Epic 2.3 | 6 | 8 | 60% | 6 | **48** | Phase 3 |

### Sprint 0 (Now — Pre-Demo) — Top 5 by RICE

```
Priority 1  Money Personality Types         RICE 338  — Identity hook, demo wow factor
Priority 2  Savings Win Celebrations        RICE 306  — Easy ship, peak-emotion conversion
Priority 3  Multi-Persona Demo Environment  RICE 190  — Unlocks client demo differentiation
Priority 4  Emotional Financial Timeline    RICE 187  — Demo centrepiece, shareable moment
Priority 5  Context-Aware Product Recs      RICE 180  — First direct revenue conversion
```

---

## Roadmap Overview

```
2026                        2027
Q1   Q2   Q3   Q4   Q1   Q2   Q3   Q4
│────│────│────│────│────│────│────│────│
│                                       │
│  PHASE 1          │                   │
│  Coaching Agent   │                   │
│  MVP (0–6 mo)     │                   │
│                   │  PHASE 2          │
│                   │  Decision Support │
│                   │  + Proactive      │
│                   │  (6–12 mo)        │
│                   │         │         │
│                   │         │ PHASE 3 │
│                   │         │ Exec.   │
│                   │         │ Agent   │
│                   │         │(12-18m) │
│                   │         │         │
│                   │         │    PHASE 4
│                   │         │    Predictive +
│                   │         │    Cross-brand
│                   │         │    (18mo+)
```

---

## Phase 1 — Coaching Agent MVP (0–6 months)

### Theme: *"Know Your Money"*

**Objective:** Prove the agent can deliver accurate, trusted, personalised financial coaching within the existing Lloyds app. Establish the data pipeline, guardrail framework and LLM integration as a reusable platform.

---

### Epics & Features

#### Epic 1.1 — Spending Intelligence
| Feature | Description | Priority |
|---|---|---|
| Monthly spend breakdown | Category-level spend with month-on-month trend | P0 |
| Top merchant analysis | Where money actually goes (Deliveroo vs Tesco split) | P0 |
| Income vs spend summary | Surplus/deficit with plain-English narrative | P0 |
| Savings opportunity identifier | Rule-based: subscriptions, eating out, idle balance | P1 |
| Spend anomaly detection | "You've spent 40% more than usual on shopping this month" | P1 |

#### Epic 1.2 — Financial Health Score
| Feature | Description | Priority |
|---|---|---|
| Health score (0–100) | 5-pillar deterministic score | P0 |
| Score history tracking | Week-on-week trend line | P1 |
| Pillar drill-down | "Your savings rate dropped — here's why" | P1 |
| Peer benchmarking | Anonymous comparison to similar income cohort | P2 |

#### Epic 1.3 — Conversational Q&A
| Feature | Description | Priority |
|---|---|---|
| Natural language spend queries | "How much did I spend on coffee last month?" | P0 |
| Financial literacy Q&A | RAG over LBG knowledge base | P0 |
| Scope guardrails | Block off-topic, regulated-advice, OOS queries | P0 |
| FCA compliance layer | Guidance vs advice boundary enforcement | P0 |
| Session memory | Coherent multi-turn conversation | P1 |

#### Epic 1.4 — Platform Foundation
| Feature | Description | Priority |
|---|---|---|
| Transaction ingestion pipeline | Pub/Sub → Dataflow → Firestore | P0 |
| Merchant enrichment service | MCC mapping + ML categorisation | P0 |
| Customer 360 serving layer | Redis cache + warm store for <100ms reads | P0 |
| Anti-hallucination framework | Deterministic tools + output guard | P0 |
| Observability & audit logging | Every LLM call logged, guardrail triggers alerted | P0 |

---

### Phase 1 Success Criteria (Exit Gates)
- [ ] Agent answers spending questions with verified figures (zero hallucination incidents in UAT)
- [ ] Response latency p95 < 3 seconds
- [ ] Digital CSAT ≥ 72 on agent-assisted journeys
- [ ] FCA sign-off on guidance vs advice boundary
- [ ] 500K MAU within 6 weeks of GA launch
- [ ] Self-service containment lift of +14 percentage points vs baseline

---

### Phase 1 Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| FCA approval delay | Medium | High | Engage FCA sandbox early (Month 1); pre-brief on guidance vs advice approach |
| LLM accuracy issues in UAT | Medium | High | Anti-hallucination architecture already built; red-team testing in Month 3 |
| Core banking data pipeline latency | High | Medium | Start pipeline build in Month 1; mock data fallback for agent dev in parallel |
| Customer trust / data anxiety | Medium | High | Transparent data usage banner; easy opt-out; explainability UI |
| Transaction categorisation accuracy | Medium | Medium | Human review queue for <80% confidence; iterative model improvement |

---

## Phase 2 — Decision Support + Proactive Engagement (6–12 months)

### Theme: *"Guide My Decisions"*

**Objective:** Move from reactive Q&A to proactive coaching. Introduce multi-channel delivery and support customers at key financial decision moments.

---

### Epics & Features

#### Epic 2.1 — Decision Support Agent
| Feature | Description | Priority |
|---|---|---|
| Mortgage affordability modeller | "Can I afford a £300K mortgage?" with real balance data | P0 |
| Savings vs debt trade-off | "Should I overpay my mortgage or save?" — contextual | P0 |
| Budget planner | Goal-based budgeting with automated suggestions | P0 |
| Life event detection | Detect nursery payments, rent changes, new income | P1 |
| Warm adviser handoff | Full context pre-loaded when escalating to human | P1 |
| Product eligibility guidance | "Based on your profile, you may qualify for X" (not advice) | P2 |

#### Epic 2.2 — Proactive Engagement Engine
| Feature | Description | Priority |
|---|---|---|
| Salary-day trigger | "Your £X,XXX is in — move £200 to savings?" | P0 |
| Overspend alert | 20% above category average → push notification | P0 |
| Direct debit warning | Low balance detected 3–5 days before DD | P0 |
| Subscription price increase | "Netflix has gone up by £2/month" | P1 |
| Monthly money summary | Auto-generated on pay+3 days | P1 |
| Goal progress nudge | "You're 60% to your holiday fund — on track!" | P1 |
| Bill switching opportunity | "Your energy tariff has a cheaper alternative" | P2 |

#### Epic 2.3 — Multi-Channel Delivery
| Feature | Description | Priority |
|---|---|---|
| In-app push notifications | Native iOS/Android | P0 |
| In-app inbox | Persistent message history | P0 |
| Email digest | Weekly money summary opt-in | P1 |
| WhatsApp channel (pilot) | Conversational banking via WhatsApp Business API | P2 |

#### Epic 2.4 — Persistent Memory & Personalisation
| Feature | Description | Priority |
|---|---|---|
| Goal tracking | Customer-set goals persisted across sessions | P0 |
| Preference learning | Coaching style, notification frequency, topics | P1 |
| Context continuity | "Last time we spoke, you were saving for a car…" | P1 |
| Long-term trend analysis | 12-month rolling view, not just 90 days | P1 |

#### Epic 2.5 — Configuration-Driven Agent (Reusability)
| Feature | Description | Priority |
|---|---|---|
| `AgentConfig` abstraction | Externalise all brand/rules/tools config | P0 |
| Halifax config | Branded config for Halifax deployment | P1 |
| BoS config | Branded config for Bank of Scotland | P2 |

---

### Phase 2 Success Criteria (Exit Gates)
- [ ] Proactive notification open rate ≥ 35%
- [ ] Decision support journeys reduce adviser call volume by 15%
- [ ] MAU reaches 2M
- [ ] Multi-channel delivery live (app + email)
- [ ] Agent config framework deployed (enables Phase 4 cross-brand)
- [ ] Depth of relationship metric at 2.4 products/customer

---

### Phase 2 Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Notification fatigue | High | Medium | Strict frequency capping; customer preference controls |
| Life event detection false positives | Medium | Medium | Confidence threshold gating; "is this right?" confirmation step |
| Adviser handoff friction | Medium | High | CRM integration work-stream started in Month 7 |
| Halifax data model differences | Medium | Medium | AgentConfig abstraction built in Phase 2 Sprint 1 |

---

## Phase 3 — Execution Agent + Open Banking (12–18 months)

### Theme: *"Act on My Behalf"*

**Objective:** Move from guidance to action. The agent executes financial tasks autonomously on the customer's behalf, with human-in-the-loop confirmation for high-value actions.

---

### Epics & Features

#### Epic 3.1 — Agentic Task Execution
| Feature | Description | Priority |
|---|---|---|
| Savings pot automation | "Round up every purchase into my holiday fund" | P0 |
| Scheduled payment setup | Create/modify standing orders via natural language | P0 |
| Budget envelope creation | Auto-create spending pots based on category analysis | P0 |
| Money sweep rules | "Move anything over £500 in current account to savings" | P1 |
| Subscription cancellation | Identify and cancel unwanted subscriptions | P1 |
| Bill renegotiation trigger | Flag and prepare switching journey for better tariff | P2 |

#### Epic 3.2 — Human-in-the-Loop Confirmations
| Feature | Description | Priority |
|---|---|---|
| Action confirmation UI | Clear "approve / reject" for every agent action | P0 |
| Action explanation | "Here's exactly what I'll do and why" before execution | P0 |
| Undo / rollback | Reverse any agent action within 24 hours | P0 |
| High-value action threshold | Extra confirmation step for actions > £500 | P0 |
| Action audit trail | Full history of every action taken by the agent | P0 |

#### Epic 3.3 — Open Banking Integrations
| Feature | Description | Priority |
|---|---|---|
| FDX / CDR API connections | Read-only access to non-LBG accounts | P0 |
| Unified balance view | See all accounts (LBG + external) in one view | P0 |
| Cross-bank spending analysis | Full picture including Barclays, Monzo, etc. | P1 |
| External savings rate comparison | "You could earn 1.2% more at competitor X" | P1 |
| Debt consolidation analysis | Full debt picture across all providers | P2 |

#### Epic 3.4 — Regulatory & Safety Framework
| Feature | Description | Priority |
|---|---|---|
| Execution guardrails | Hard limits on amount, frequency, reversibility | P0 |
| FCA CASS compliance | Client asset rules for money movement | P0 |
| Fraud detection integration | Agent actions checked against fraud models | P0 |
| Power of attorney support | Authorised third-party agent access | P2 |

---

### Phase 3 Success Criteria (Exit Gates)
- [ ] Execution agent live with 5 task types
- [ ] Zero unauthorised actions in first 90 days (execution guardrail SLA)
- [ ] Open banking connections to top 5 UK banks
- [ ] Self-service containment reaches 72%
- [ ] MAU 5M, with 40% using at least one agentic action per month

---

## Phase 4 — Predictive Life-Event Engine + Cross-Brand (18 months+)

### Theme: *"Anticipate My Life"*

**Objective:** Use LBG's unique data depth to predict life events before they happen and offer proactive guidance across all LBG brands from a single unified agent platform.

---

### Epics & Features

#### Epic 4.1 — Predictive Life-Event Engine
| Feature | Description | Priority |
|---|---|---|
| Life event ML models | Predict: baby, house purchase, job change, retirement | P0 |
| Pre-emptive guidance | Triggered 30–90 days before predicted event | P0 |
| Event confidence scoring | Only surface prediction when confidence > 75% | P0 |
| "Did we get it right?" feedback | Customer confirms/rejects prediction → retraining loop | P1 |
| Bereavement support | Sensitive detection + specialist signposting | P1 |

#### Epic 4.2 — Cross-Brand Unified Agent
| Feature | Description | Priority |
|---|---|---|
| Halifax agent | Full feature parity under Halifax brand/config | P0 |
| Bank of Scotland agent | Full feature parity under BoS brand/config | P0 |
| MBNA credit agent | Credit-focused coaching (spend, utilisation, paydown) | P1 |
| Unified customer graph | Single view of customer across all LBG brands | P1 |
| Cross-brand product journey | "Your Halifax mortgage + Lloyds savings — here's your full picture" | P2 |

#### Epic 4.3 — Advanced Personalisation
| Feature | Description | Priority |
|---|---|---|
| Financial personality profiling | Risk appetite, money mindset, goal orientation | P1 |
| Adaptive coaching style | Tone and depth adjusted to customer engagement pattern | P1 |
| Longitudinal goal tracking | Multi-year goal progress (retirement, school fees) | P1 |
| Household view | Joint account holders see shared financial picture | P2 |

#### Epic 4.4 — Platform Maturity
| Feature | Description | Priority |
|---|---|---|
| Agent marketplace | Internal teams can add new tools to the agent framework | P1 |
| A/B testing framework | Test coaching approaches, tone, nudge timing | P1 |
| Regulatory reporting | Automated FCA outcome monitoring | P0 |
| Carbon footprint tracking | Spending linked to estimated carbon impact | P3 |

---

### Phase 4 Success Criteria (Exit Gates)
- [ ] Cross-brand agent live across Lloyds, Halifax, BoS
- [ ] Life-event prediction accuracy > 70% precision
- [ ] Digital CSAT ≥ 85
- [ ] 12M MAU across all brands
- [ ] Depth of relationship at 3.1 products/customer

---

## Phase 1 → Phase 2 Transition Plan

This is the most critical transition — moving from a working MVP to a production-scale, proactive, multi-channel product. Here is the detailed progression:

### Pre-conditions to Exit Phase 1

Before Phase 2 work begins, the following must be true:

```
✅ Agent is live in production (not just UAT)
✅ FCA guidance vs advice boundary formally signed off
✅ Transaction data pipeline stable (<5 min latency, 99.9% uptime for 4 weeks)
✅ Hallucination rate = 0% in production monitoring (30-day window)
✅ p95 response latency < 3s sustained
✅ CSAT ≥ 72 on agent-assisted journeys
✅ Security pen test passed
✅ Customer opt-out mechanism live and working
```

---

### Month 6 — Parallel Track Kickoff

Phase 2 engineering begins in Month 5 (one month overlap), in two parallel tracks:

```
TRACK A — Proactive Engine           TRACK B — Reusability Refactor
(new capability)                     (platform investment)

Month 5:                             Month 5:
  Define event trigger rules           Design AgentConfig schema
  Build Stream Analytics rules         Audit hardcoded LBG-specifics
  Design notification schema           Define config vs code boundary

Month 6:                             Month 6:
  Implement Pub/Sub event triggers     Implement AgentConfig dataclass
  Build notification service           Refactor guardrails to config-driven
  A/B test: push vs in-app inbox       Refactor scoring weights to config
                                       Create LloydsConfig, HalifaxConfig stubs
```

Track B is essential to do **now** — if the AgentConfig abstraction is not in place before Phase 2 feature work begins, each new feature gets built with LBG hardcoding and the cross-brand goal of Phase 4 becomes a rewrite, not a config swap.

---

### Month 7–9 — Decision Support Build

```
Sprint 13–14:  Mortgage affordability modeller
               Data: LBG rate API + customer balance/income from Phase 1 pipeline
               Guard: Output must include FCA disclaimer on all mortgage content
               Escalation: Warm handoff CRM integration with Salesforce

Sprint 15–16:  Life event detection (v1)
               Signal: nursery payments, school fees, rent deposits, salary change
               Action: Coaching nudge only (no automated action until Phase 3)
               Threshold: Confidence > 70% before surfacing to customer

Sprint 17–18:  Goal-based budgeting
               Customer sets goal (e.g. "Save £5,000 for a holiday by December")
               Agent tracks weekly progress, adjusts coaching based on trajectory
               Persistent across sessions via CustomerMemory → Firestore
```

---

### Month 10–12 — Multi-Channel + Phase 2 Hardening

```
Sprint 19–20:  Push notifications (iOS + Android)
               Event triggers: salary, overspend, DD warning, goal milestone
               Frequency cap: max 3 per week per customer
               Preference centre: customer controls what they receive and when

Sprint 21–22:  Email digest
               Weekly summary: top 3 insights + 1 action
               Unsubscribe / frequency controls
               Rendered from same agent output — no duplicate content pipeline

Sprint 23–24:  Phase 2 hardening
               Load testing to 2M MAU
               Proactive notification open rate analysis + tuning
               Phase 2 exit gate review
               Phase 3 planning and architecture spike
```

---

### Engineering Investment Required: Phase 1 → Phase 2

| Work stream | Effort | Team |
|---|---|---|
| AgentConfig refactor | 2 weeks | 1 senior engineer |
| Proactive event trigger pipeline | 4 weeks | 1 data engineer + 1 backend engineer |
| Notification service (push + email) | 3 weeks | 1 backend + 1 mobile engineer |
| Decision support tools (mortgage, goals) | 6 weeks | 2 engineers |
| CRM warm handoff integration | 3 weeks | 1 integration engineer |
| Life event detection model (v1) | 4 weeks | 1 ML engineer |
| Multi-channel UI (preference centre) | 2 weeks | 1 frontend engineer |
| Load testing + hardening | 2 weeks | 1 engineer + QA |
| **Total** | **~26 weeks of engineering effort** | **~4–5 person team** |

---

## Dependencies & Sequencing

```
Phase 1 ──────────────────────────────────────────────────────────────►
  Transaction pipeline              ← must be stable before Phase 2
  FCA sign-off                      ← must be complete before Phase 2 launch
  AgentConfig refactor              ← must be done before Phase 2 features built

Phase 2 ──────────────────────────────────────────────────────────────►
  Open Banking API access (FDX)     ← 6-month procurement, start in Phase 2
  CRM integration (Salesforce)      ← needed for adviser handoff in Phase 2
  Halifax data model mapping        ← needed for Phase 4 cross-brand

Phase 3 ──────────────────────────────────────────────────────────────►
  Execution guardrail FCA review    ← start regulatory engagement in Phase 2
  CASS compliance sign-off          ← 3-month process, start Month 10
  Open banking connections          ← procurement starts Phase 2

Phase 4 ──────────────────────────────────────────────────────────────►
  Life-event ML model training data ← 12+ months of labelled data needed
  Halifax / BoS brand approval      ← brand and legal review, 3 months
  Unified customer graph            ← major data engineering, 6 months
```

---

## Principles

1. **Ship early, learn fast** — Phase 1 in production by Month 4, not Month 6. Real customer data is irreplaceable for tuning.
2. **Platform before features** — AgentConfig and pipeline stability are not optional. Skipping them creates Phase 4 rewrite risk.
3. **Compliance is a feature** — FCA engagement is a workstream, not a sign-off at the end. Regulators respond better to transparency than to finished products.
4. **Data quality gates everything** — a miscategorised transaction corrupts health scores, triggers wrong nudges and breaks customer trust. The categorisation pipeline is the most critical non-AI component.
5. **Customer control at every phase** — opt-out, preference centre and action undo are not backlog items. They ship with every new capability.

---

## Future Enhancements

The following improvements have been identified during MVP development and stakeholder demos. They are candidates for inclusion in Phase 2 and Phase 3 sprints.

---

### FE-1 — Token & Cost Optimisation

> *Identified during: MVP load testing and cost modelling*

Every customer message triggers 1–3 OpenAI API calls. At production scale (e.g. 100k customers × 5 messages/month) unoptimised token usage becomes a significant operating cost. The following improvements should be implemented before Phase 2 GA launch.

| Enhancement | Description | Est. Token Saving | Priority |
|---|---|---|---|
| **Conversation history trimming** | Cap `session.get_history()` to last 6 messages instead of full history. Older turns are rarely needed and inflate input token count significantly. | ~40% on long sessions | P0 |
| **Health score caching** | Financial health score does not change turn-to-turn. Cache the result in `SessionMemory` and only recompute when new transactions arrive. Avoids a full tool call + LLM narration on repeated questions. | ~800 tokens/repeat query | P1 |
| **Tiered LLM routing** | Route simple queries (spending summary, health score, savings tips) to **GPT-4o-mini** which is 10× cheaper with equivalent narration quality. Reserve GPT-4o for complex multi-tool chains (mortgage + life event + budget in one turn). | ~60% cost reduction on simple queries | P1 |
| **Tool output summarisation** | Pre-summarise structured JSON tool outputs before sending to LLM. The full `get_spending_insights` JSON is ~600 tokens; a pre-formatted summary is ~150 tokens with no loss of response quality. | ~450 tokens per tool call | P2 |
| **Prompt compression** | The system prompt is currently ~800 tokens. Use a compressed variant (~400 tokens) for single-turn factual queries where the full instruction set is not needed. | ~400 tokens per simple query | P2 |

**Target:** Reduce average cost per message from ~$0.007 to ~$0.002 before Phase 2 GA (3.5× cost reduction).

---

### FE-2 — RM Copilot Agent

> *Identified during: stakeholder solution design session*

A relationship manager (RM) facing co-pilot that surfaces customer intelligence and personalised product talking points before client meetings. Proposed as a standalone Phase 3 internal agent reusing the existing coaching agent infrastructure.

| Enhancement | Description | Priority |
|---|---|---|
| **Pre-meeting brief generator** | Auto-generate a structured customer brief before every RM-client meeting: detected life events, financial snapshot, recommended talking points, risk flags | P0 |
| **Product propensity scorer** | Deterministic rules engine mapping transaction signals to product triggers (e.g. nursery payments → life cover, income increase → ISA review) | P0 |
| **Next Best Action (NBA) engine** | One prioritised product action per customer with a suggested conversation opener, confidence score, and FCA compliance label | P1 |
| **CRM auto-updater** | Write meeting notes and detected signals back to Salesforce after each RM interaction | P1 |
| **AI Sage signal sharing** | With customer consent, surface life event signals detected by AI Sage (customer-facing) to the RM — creating a joined-up experience where RM arrives knowing what the customer has already discussed with the agent | P2 |

---

### FE-3 — Online Banking Portal Integration

> *Identified during: stakeholder demo feedback — "the agent should live inside the banking app, not as a standalone tool"*

The AI Sage chat experience should be embedded within the existing online and mobile banking journey rather than accessed as a separate product. The HTML demo (`login.html`, `dashboard.html`) built during MVP development is the prototype for this integration.

| Enhancement | Description | Priority |
|---|---|---|
| **Embedded chat panel** | Sliding chat panel within the authenticated banking dashboard — no separate login or product discovery needed | P0 |
| **Proactive nudge banners** | Contextual banners on the dashboard (e.g. "Your income increased — want to review your savings?") that pre-fill the chat with a relevant question | P0 |
| **Transaction-linked coaching** | Customer taps a transaction in their feed → agent opens pre-loaded with context about that merchant or category | P1 |
| **Mobile app native integration** | Native iOS/Android chat component replacing the web panel for mobile banking customers | P1 |
| **Session continuity** | Customer switches from mobile to desktop mid-conversation — session and context preserved seamlessly | P2 |

---

### FE-4 — Agent Reusability & Skills Framework

> *Identified during: architecture review — "is this agent reusable across brands?"*

The current agent has LBG-specific logic hardcoded throughout. An `AgentConfig` abstraction and formal skills manifest are required before Phase 4 cross-brand deployment.

| Enhancement | Description | Priority |
|---|---|---|
| **`AgentConfig` dataclass** | Externalise brand name, colour scheme, product catalogue, adviser contact details, FCA firm reference, and guardrail thresholds into a config object. One codebase, multiple brand deployments. | P0 |
| **Skills manifest (Anthropic format)** | Formalise each agent capability as a declarative skill with `name`, `description`, trigger keywords, required tool sequence, and FCA boundary label. Enables orchestrator-driven tool sequencing without prompt engineering. | P1 |
| **Skill hot-reload** | Add or update skills without redeploying the agent — read skills manifest at runtime from a config store | P2 |
| **Multi-brand config store** | Versioned config store (GCS / Firestore) for Lloyds, Halifax, BoS and MBNA configs — brand teams manage their own config without engineering intervention | P2 |

---

### FE-5 — Agent Runtime Modernisation: Migrate to `create_agent` (LangChain v1)

> *Identified during: architecture review — "why not use the latest LangChain agent creation API?"*

The current agent uses a manually implemented ReAct loop (`_run_react_loop` in `agent.py`). LangChain v1 introduces `create_agent` with a composable middleware system that maps directly to every custom component already built. This refactor eliminates ~150 lines of bespoke orchestration code and unlocks streaming, human-in-the-loop confirmations, and framework-native checkpointing with no feature regression.

| Enhancement | Description | Current Approach | `create_agent` Equivalent | Priority |
|---|---|---|---|---|
| **FE-5.1 Replace ReAct loop** | Remove manual `_run_react_loop` — use `create_agent` with `tools=` parameter | `while True` loop in `agent.py` parsing LLM tool calls | `create_agent(model, tools)` | P0 |
| **FE-5.2 Guardrails as middleware** | Replace wrapper functions with composable middleware hooks | `_input_guard()`, `_output_guard()` called manually in loop | `@before_agent` (input guard), `@after_model` (output guard + FCA disclaimer) | P0 |
| **FE-5.3 Life event bypass** | Replace `if life_event: return early` branch with framework-native early exit | Manual `if` branch in `_run_react_loop` | `@before_agent` middleware returning `jump_to: "end"` | P1 |
| **FE-5.4 Memory via `state_schema`** | Replace `CustomerMemory` JSON persistence with framework-managed checkpointing | Manual JSON read/write to `data/customer_store/` | `state_schema=CustomAgentState` + LangGraph `checkpointer` | P1 |
| **FE-5.5 Grounding tracking** | Replace manual `session.tool_calls_made.append()` with middleware | List appended inside loop on each tool execution | `@wrap_tool_call` middleware — zero boilerplate | P1 |
| **FE-5.6 Streaming + Human-in-the-Loop** | Enable token-by-token streaming and mid-conversation confirmation steps | Not supported in current synchronous loop | Native in `create_agent` — streaming via `agent.stream()`, HITL via `interrupt_before=` | P2 |

**Effort estimate:** 3–4 engineering days. No feature regression — all existing tools, guardrails, memory, and FCA compliance logic are preserved; the orchestration layer is replaced, not the business logic.

**Prerequisites:** None — can begin any time after Phase 1 exit gates are met.

**Key migration steps:**
1. Replace `_run_react_loop` with `create_agent(model, tools)` call
2. Extract `_input_guard` → `InputGuardMiddleware` decorated with `@before_agent`
3. Extract `_output_guard` + FCA disclaimer → `OutputGuardMiddleware` decorated with `@after_model`
4. Extract life event bypass → `LifeEventBypassMiddleware` decorated with `@before_agent`, returning `jump_to: "end"` when triggered
5. Define `CustomAgentState(AgentState)` with `goals`, `preferences`, `session_summaries` fields
6. Pass `checkpointer=JsonFileSaver("data/customer_store/")` to `create_agent`
7. Replace manual `tool_calls_made.append()` with `@wrap_tool_call` middleware

---

### FE-6 — Multi-Agent Architecture

> *Identified during: architecture review — "would a multi-agent approach help at scale?"*

The current single ReAct agent handles all capabilities in one context window. As the platform scales to Phase 3 (execution) and Phase 4 (cross-brand), a multi-agent architecture decouples specialist concerns, enables parallel execution, and isolates compliance boundaries per agent.

**Recommended target architecture (Phase 3+):**

```
OrchestratorAgent (thin router — classifies intent, dispatches, synthesises)
    │
    ├── CoachingAgent       ← current agent (Epic 1 + 2); spending, health, goals
    ├── DecisionAgent       ← mortgage, debt/savings trade-off, pension modelling
    ├── ExecutionAgent      ← Epic 3.1 task execution (payments, pot automation)
    ├── MonitorAgent        ← Epic 2.2 proactive triggers; runs continuously in background
    └── RMCopilotAgent      ← FE-2 internal RM-facing tool; separate compliance boundary
             │
        ─────────────────────────────────────
        Shared Platform Layer
        CustomerMemory · CustomerGraph · Transaction Pipeline · Guardrail Middleware
```

| Enhancement | Description | Phase | Priority |
|---|---|---|---|
| **FE-6.1 OrchestratorAgent** | Thin router that classifies incoming intent and dispatches to the correct specialist agent. Synthesises multi-agent responses into a single coherent reply. | Phase 3 | P0 |
| **FE-6.2 DecisionAgent** | Specialist agent for complex financial modelling: mortgage affordability, debt vs savings trade-off, pension contribution analysis. Runs tools in parallel sub-chains. | Phase 3 | P0 |
| **FE-6.3 MonitorAgent** | Background agent that continuously monitors account events (salary in, DD risk, overspend threshold) and hands off to CoachingAgent with pre-loaded context when a trigger fires. | Phase 3 | P1 |
| **FE-6.4 ExecutionAgent** | Isolated agent for task execution (Epic 3.1) with its own stricter guardrail middleware — amount limits, reversibility checks, CASS compliance — separate from the coaching compliance boundary. | Phase 3 | P1 |
| **FE-6.5 Shared platform layer** | `CustomerMemory`, transaction pipeline and guardrail middleware extracted into a shared library consumed by all agents. No agent owns state — all agents read/write through the shared layer. | Phase 3 | P0 |
| **FE-6.6 Cross-brand routing** | OrchestratorAgent reads `brand` from JWT claim and routes to brand-isolated agent instance (`LloydsCoachingAgent`, `HalifaxCoachingAgent`). Enables Phase 4 cross-brand with zero code duplication. | Phase 4 | P1 |

**Prerequisites:** FE-5 (`create_agent` refactor) — each specialist agent should be a clean `create_agent` instance with middleware before composition under an orchestrator.

**When to adopt:** Multi-agent adds routing overhead and state-handoff complexity that is not justified for Phase 1/2 single-turn Q&A. Introduce `OrchestratorAgent` + `DecisionAgent` at the start of Phase 3 when execution and parallel tool chains become requirements.

---

---

### FE-7 — Emotional Connect & Financial Personality Engine

> *Identified during: product strategy session — "customers connect with stories, not numbers"*

The single highest-impact demo and retention differentiator. Customers form an emotional identity around their financial type and track their progression — making AI Sage feel personal rather than transactional. Personality profiling also serves as the personalisation engine for coaching tone and product recommendations.

#### FE-7.1 — Money Personality Types

| Feature | Description | RICE | Priority |
|---------|-------------|------|----------|
| **6 personality types** | Derived deterministically from transaction patterns: Steady Saver, Spontaneous Spender, Goal Crusher, Cautious Planner, Reactive Manager, Balanced Achiever | 338 | P0 |
| **Personality shift narrative** | "3 months ago you were a Spontaneous Spender. You're becoming a Balanced Achiever." — progress framing, not just labelling | 338 | P0 |
| **Type-to-product bridge** | Each type maps to a natural next product: Steady Saver → ISA, Goal Crusher → Mortgage readiness, Cautious Planner → investment nudge | 180 | P1 |
| **Adaptive coaching tone** | AI Sage adjusts language depth and framing based on personality type — Cautious Planner gets data-heavy responses; Spontaneous Spender gets empathetic and action-focused | 150 | P1 |
| **Monthly personality pulse** | "This month you showed up as a Goal Crusher — your best month yet" — repeat engagement trigger | 120 | P2 |

**Personality type logic (deterministic, not LLM):**

| Type | Savings Rate | Spend Stability | Goal Progress | Primary Signal |
|------|-------------|----------------|---------------|----------------|
| Steady Saver | > 20% | High | Moderate | Consistent saving, few goals set |
| Spontaneous Spender | < 5% | Low | Low | High discretionary variance |
| Goal Crusher | > 15% | Medium | High | Active goals, high completion rate |
| Cautious Planner | > 30% | Very High | Low | Over-saves, no investment signals |
| Reactive Manager | Variable | Very Low | Low | Crisis spending patterns, irregular income |
| Balanced Achiever | 15–25% | High | High | Healthy across all 5 health pillars |

**FCA note:** Language must be aspirational, never judgmental. "Spontaneous Spender" framed as "you live in the moment." Suppress personality feature if distress patterns detected in session.

#### FE-7.2 — Emotional Financial Timeline

| Feature | Description | RICE | Priority |
|---------|-------------|------|----------|
| **6-month financial story** | Interactive timeline showing key financial moments — pay rise, new rent, first savings goal hit, best spending month | 187 | P0 |
| **AI-generated chapter titles** | "The month you got your pay rise", "The tough November" — narrative framing for each month | 187 | P0 |
| **Life event auto-detection** | Nursery payments, rent changes, salary change, large one-off purchases — auto-marked on timeline with opt-in confirmation ("It looks like your rent changed — want me to mark that?") | 160 | P1 |
| **Before/after comparison** | "6 months ago vs today" — side-by-side health score, savings rate, spending split | 150 | P1 |
| **Milestone markers** | "First month you saved over £500", "Your best spending month" — gamified annotation | 140 | P1 |
| **Zoomable chart with AI annotations** | Chart.js timeline with clickable annotations that open an AI Sage explanation of what happened | 120 | P2 |

**Why the timeline matters for the bank:** Shareable "financial glow-up" moments drive organic acquisition. It also reinforces switching cost — a 6-month financial story is locked to LBG; customers won't start again elsewhere.

#### FE-7.3 — Savings Win Celebrations

| Feature | Description | RICE | Priority |
|---------|-------------|------|----------|
| **Full-screen celebration moment** | Confetti + large number + shareable card when savings milestone hit — not a toast notification, a moment | 306 | P0 |
| **Milestone thresholds** | First £100 saved, first £500, first £1,000, goal completion, 3-month emergency fund reached | 306 | P0 |
| **Peak-emotion product prompt** | Celebration → immediate "Put it to work in a Lloyds Cash ISA earning X%" — conversion at highest trust moment | 240 | P0 |
| **Shareable achievement card** | "I hit my savings goal with AI Sage" — branded card for social sharing | 120 | P2 |

---

### FE-8 — Context-Aware Business Activation

> *Identified during: product strategy session — "features that improve user financial health automatically create bank revenue opportunities"*

The principle: **never recommend a product unless a signal has appeared first.** Context-aware means the recommendation feels like help, not sales. Every feature here is triggered by a real customer event, not a scheduled push.

#### FE-8.1 — Proactive Financial Intelligence

| Feature | Description | RICE | Priority |
|---------|-------------|------|----------|
| **Payday Optimiser** | "Your salary landed — move £300 to savings, pay £150 off your card?" — automated sweep suggestion on salary day | 306 | P0 |
| **Runway Alert** | "Based on your spending you'll run short 4 days before payday" — proactive, not reactive | 256 | P0 |
| **Bill Spike Alert** | "Your energy DD increased £40 this month — here's the cashflow impact" | 252 | P0 |
| **Subscription Audit** | "You have 7 subscriptions costing £94/mo — 3 appear unused" | 238 | P0 |

#### FE-8.2 — Goal-to-Product Bridge (Revenue Engine)

| Trigger Signal | AI Sage Action | Bank Product | RICE |
|---------------|---------------|-------------|------|
| Savings goal set | "To reach £10k by December, save £556/mo — want to open a dedicated savings pot?" | Linked savings account / Cash ISA | 180 |
| End-of-month surplus ≥ 3 months running | "You've had a surplus 3 months in a row — your money could be working harder" | ISA, Fixed Rate Saver | 165 |
| Mortgage readiness score ≥ 80% | "You're mortgage-ready — want to speak to an adviser?" | Mortgage appointment | 140 |
| Life event: baby/nursery payments detected | "Your outgoings changed — shall I recalculate your budget and look at life cover?" | Life insurance, children's savings | 130 |
| Life event: salary increase detected | "Your income increased £600/mo — here's how to put that to work" | ISA, pension top-up, overpay mortgage | 125 |
| Debt freedom date set | "You'll be debt-free by March 2027 — want to plan what comes next?" | Investment / ISA conversation | 110 |

**Rule:** Every recommendation must include the FCA caveat. No specific product names or rates unless pulled from a live, auditable product API. Phrase as "you appear to meet the indicative criteria for" not "you qualify for."

#### FE-8.3 — Mortgage Readiness Score

| Feature | Description | RICE | Priority |
|---------|-------------|------|----------|
| **Readiness score (0–100%)** | Composite of deposit progress, income stability, debt-to-income, credit behaviour | 140 | P1 |
| **Gap analysis** | "Fix these 2 things to improve your score" — actionable, not just informational | 140 | P1 |
| **6-month trajectory** | "At your current savings rate you'll be mortgage-ready in 8 months" | 120 | P1 |
| **Warm adviser handoff** | Score ≥ 80% → one-tap adviser appointment with full context pre-loaded | 140 | P0 |

---

### FE-9 — Multi-Persona Demo Environment

> *Identified during: client demo preparation — "a demo locked to one customer profile limits stakeholder engagement"*

Six distinct demo personas mapped to the six money personality types. The presenter can select a persona from a login dropdown, demonstrating AI Sage's personalisation depth to different audience segments in real time. Each persona has its own transaction history, financial health score, goals, and personality type — creating genuinely different AI Sage conversations.

#### Personas

| ID | Name | Type | Story | Demo use case |
|----|------|------|-------|---------------|
| CUST_DEMO_001 | Alex Johnson | Steady Saver | Existing profile — baseline, simple | Onboarding, first-time user journey |
| CUST_DEMO_002 | Alex Johnson | Goal Crusher | Life events: baby, pay rise, house | Life event detection, goal tracking |
| CUST_DEMO_003 | Jordan Lee | Spontaneous Spender | £3,800 salary, high discretionary, no savings | Subscription audit, budget coaching |
| CUST_DEMO_004 | Sam Carter | Cautious Planner | £5,200 salary, over-saves, never invested | ISA/investment nudge, health score |
| CUST_DEMO_005 | Morgan Davies | Reactive Manager | £2,800 salary, some debt, irregular | Debt optimiser, distress guardrail |
| CUST_DEMO_006 | Jamie Williams | Balanced Achiever | £4,500 salary, all pillars healthy | Aspirational "after" state, product bridge |

#### Features

| Feature | Description | Priority |
|---------|-------------|----------|
| **Persona login page** | `login.html` with styled dropdown showing name + personality type + brief description | P0 |
| **Universal demo password** | Single password (`LBG@2026`) for all personas — prevents fumbling in live demos | P0 |
| **Dynamic dashboard header** | Name, avatar initials, personality type badge update based on selected persona | P0 |
| **Per-persona transaction data** | Different salary, spending patterns, life events, health scores — genuinely different AI conversations | P0 |
| **Pre-seeded customer store** | Each persona has pre-built goals, session history, preferences — returning-user experience from first run | P0 |
| **Personality type badge in UI** | Visible in nav bar and financial overview — reinforces FE-7 personality concept | P1 |

**Presenter note:** CUST_DEMO_005 (Morgan Davies, Reactive Manager) demonstrates Consumer Duty / distress guardrail features. Use selectively — powerful for a compliance/FCA audience, may feel heavy for a commercial audience. Know your room.

**Effort:** ~3–4 days total (backend routing + 4 transaction generators + 4 JSON stores + login.html + chat_panel.js update)

---

*Document version: 2.0 · AI Sage Financial Wellbeing Platform · Confidential*
