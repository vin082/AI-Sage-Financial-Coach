# SECURITY REVIEW — AI Sage Financial Coach

Date: 2026-02-23
Files Reviewed: 8
Scope: Prompt injection, API auth bypass, PII leakage, path traversal

VERDICT: CLEARED WITH CRITICAL WARNINGS - Demo-only approval

---

## CRITICAL FINDINGS

### CRITICAL-1: DEMO_MODE Authentication Bypass
File: api/main.py lines 77-82
Severity: CRITICAL (CWE-306, CWE-287)

Issue: Default DEMO_MODE=true completely bypasses authentication.

Code:
```python
if os.getenv("DEMO_MODE", "true").lower() == "true":  # DEFAULT IS TRUE
    return "CUST_DEMO_001"
```

Risk: Any unauthenticated client can access /health-score, /chat, /spending-insights

Exploit: curl http://localhost:8000/health-score (no header)

Fix: Change default to DEMO_MODE=false; implement Azure AD B2C JWT validation

---

### CRITICAL-2: Overly Permissive CORS
File: api/main.py lines 44-50
Severity: CRITICAL (CWE-346)

Issue: allow_origins=["*"] accepts requests from ANY domain

Risk: Malicious JavaScript from attacker.com can fetch customer data

Fix: Restrict to ["http://localhost:3000", "http://localhost:8501"]

---

### CRITICAL-3: Path Traversal in Customer Store
File: coaching_agent/memory.py lines 233-234
Severity: HIGH (CWE-22)

Issue: customer_id not validated before file path construction

```python
def _store_path(customer_id: str) -> str:
    return os.path.join(_STORE_DIR, f"{customer_id}.json")
```

Risk: Attacker can inject "../../../.env" to read/write arbitrary files

Fix: Validate customer_id format; canonicalize and verify path stays in _STORE_DIR

---

## HIGH-PRIORITY FINDINGS

### HIGH-1: Debug Logging Exposes Customer Context
File: coaching_agent/memory.py lines 291, 305
Severity: HIGH (CWE-532)

Issue: Uses print() to log customer_id and exceptions

Risk: Customer IDs visible in production logs

Fix: Use Python logging module; never log customer_id in production

---

### HIGH-2: Session Ownership Not Validated
File: api/main.py lines 161-172
Severity: HIGH (CWE-20)

Issue: /chat endpoint doesn't verify session_id belongs to authenticated customer

Risk: Attacker can guess another customer's session UUID

Fix: Validate session ownership on all endpoints; return 403 if not owner

---

## ADVISORY FINDINGS

### MEDIUM-1: No Rate Limiting
Severity: MEDIUM (CWE-770)

Fix: Add slowapi rate limiter; 10 requests/minute per customer

---

## CHECKS PASSED

PASS: Prompt Injection - Input passes through check_input() guardrail before LLM

PASS: Hallucination Prevention - Output guard blocks ungrounded currency figures

PASS: Unsafe Deserialization - No pickle/eval/exec; JSON only with explicit schema

PASS: Dependency Security - All recent versions; no known CVEs

PASS: FCA Compliance - Input guard blocks regulated advice patterns

---

## REMEDIATION CHECKLIST (BLOCKING)

- [ ] Change DEMO_MODE default to false
- [ ] Restrict CORS to explicit whitelist
- [ ] Add path traversal validation in _store_path()
- [ ] Remove print() debugging; use logging module
- [ ] Add session ownership validation on /chat, /health-score, /spending-insights, /session/profile

---

## REMEDIATION CHECKLIST (NON-BLOCKING)

- [ ] Implement rate limiting (10/minute per customer)
- [ ] Implement Azure AD B2C JWT validation
- [ ] Add token counting for messages
- [ ] Set up automated dependency scanning (pip-audit)
- [ ] Add security headers (CSP, X-Frame-Options)

---

## SUMMARY

Strengths:
+ Deterministic tool architecture prevents hallucination
+ Robust guardrails and FCA compliance enforcement
+ No hardcoded secrets or unsafe deserialization

Weaknesses:
- DEMO_MODE auth bypass is production-blocking
- CORS misconfiguration exposes API to any domain
- Path traversal risk in customer store
- Missing session ownership validation
- Debug logging leaks customer context

Verdict: CONDITIONAL APPROVAL FOR DEMO ONLY. BLOCK PRODUCTION UNTIL CRITICAL ISSUES FIXED.

Reviewer: Claude Code (claude-haiku-4-5)
Review Date: 2026-02-23
