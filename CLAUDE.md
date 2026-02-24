# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LBG Customer AI Super Agent — an AI financial coaching agent built for Lloyds Banking Group. It uses a **deterministic-tools + narrating-LLM** architecture to prevent hallucinated financial figures while remaining conversational.

## Commands

```bash
# Install dependencies
pip install -e .
# or with uv:
uv sync

# Run FastAPI server (development)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
# Docs at http://localhost:8000/docs

# Run Streamlit demo UI
streamlit run demo/streamlit_app.py

# Run tests
pytest -v
pytest -v --asyncio-mode=auto   # for async tests
```

## Architecture

### Core Design Principle: Anti-Hallucination

The LLM **never computes financial figures** — it only narrates pre-verified facts. Every £ amount flows through deterministic Python tools first, is registered in `session.grounded_amounts`, then passed as JSON facts for the LLM to narrate. The output guard (`guardrails.py`) blocks any response containing ungrounded amounts.

### Request Flow

```
User Input
  → Input Guard (regulated advice / out-of-scope check — no LLM)
  → Life Event Bypass (deterministic pre-check before LLM routing)
  → CoachingAgent / LangGraph ReAct loop (max 5 iterations)
  → Tool Execution (pure Python, Decimal arithmetic, no LLM)
  → LLM Narration (GPT-4o, temp=0.1, given JSON facts)
  → Output Guard (verify £ amounts are grounded; retry if not)
  → FCA Disclaimer (auto-injected for regulated-adjacent terms)
  → Session Memory + Customer Store
```

### Key Components

| File | Role |
|------|------|
| `coaching_agent/agent.py` | Main `CoachingAgent` class; LangGraph orchestration; 16 tool definitions |
| `coaching_agent/guardrails.py` | Input guard (8 regulated + 25 OOS patterns), output guard, FCA disclaimer injection |
| `coaching_agent/memory.py` | `SessionMemory` (per-conversation, last 10 turns) + `CustomerMemory` (cross-session, JSON-persisted) |
| `coaching_agent/tools/transaction_analyser.py` | Spending insights using `Decimal` — no float arithmetic |
| `coaching_agent/tools/financial_health.py` | 5-pillar scoring engine (Savings Rate 30pts, Spend Stability 20pts, Essentials 20pts, Subscriptions 15pts, Emergency Buffer 15pts) |
| `coaching_agent/tools/knowledge_base.py` | RAG retrieval via FAISS (dev) / Azure AI Search (prod); top-3 chunks |
| `api/main.py` | FastAPI endpoints: `/chat`, `/session/new`, `/health-score`, `/spending-insights`, `/session/end` |
| `demo/streamlit_app.py` | Interactive demo UI |
| `data/customer_store/*.json` | Persistent customer memory (production: Cosmos DB / Redis) |

### Tool Inventory

The agent has 16 tools across phases:
- **Phase 1**: transaction analyser, financial health, life event detector, knowledge base RAG, session end
- **Phase 2**: mortgage affordability (PRA 4.5× LTI + FCA +3% stress test), debt vs savings optimiser, budget planner (50/30/20), adviser handoff, product eligibility
- **Epic 2.4**: goal management, preference updates, session summary

### Money Handling

Always use `Decimal` (not `float`) for monetary calculations. Tools return `dataclasses` with `Decimal` fields. The tool serialiser converts `Decimal → "£X.XX"` strings before passing to the LLM.

## Configuration

`.env` variables:
```
OPENAI_API_KEY              # Dev (OpenAI direct)
AZURE_OPENAI_ENDPOINT       # Prod (Azure, UK South)
AZURE_OPENAI_API_KEY
AZURE_CHAT_DEPLOYMENT       # e.g. "gpt-4o"
AZURE_EMBEDDING_DEPLOYMENT  # e.g. "text-embedding-ada-002"
DEMO_MODE                   # true = skip auth for demos
LOG_LEVEL                   # INFO / DEBUG
```

## FCA Compliance Boundaries

- **Input guard** blocks regulated advice (specific investment recommendations, specific product advice). These patterns are in `guardrails.py`.
- **Output guard** auto-injects FCA disclaimer when response contains regulated-adjacent terms (mortgages, ISAs, pensions, loans).
- The agent provides **guidance** only, not regulated financial advice.

## Memory & Persistence

- `SessionMemory`: In-memory per conversation (last 10 turns, tool calls, grounded amounts dict)
- `CustomerMemory`: JSON file at `data/customer_store/<customer_id>.json` — persists goals, preferences, health scores, session summaries across sessions
- Goal updates deduplicate against existing goals (update in-place, don't create duplicates)

## Stack

- **Python 3.11+**, LangChain + LangGraph (ReAct), GPT-4o via OpenAI/Azure OpenAI
- **Embeddings**: `text-embedding-3-small` → FAISS (dev), Azure AI Search (prod)
- **API**: FastAPI + Uvicorn, **Demo**: Streamlit, **Validation**: Pydantic v2
- **Tests**: pytest + pytest-asyncio
- **Mock data**: seeded `random` (seed=42) for reproducible demos
