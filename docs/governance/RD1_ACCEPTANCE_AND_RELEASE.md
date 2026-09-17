# RD1-V1 Acceptance and Release

**Date:** 2026-09-17  
**Owner:** Tony  
**Status:** ACTIVE / OWNER APPROVED

## 1. Separation of concerns

```text
Architecture = what the system is
Acceptance = whether the implementation works
Release = which exact build ships
```

Do not mix these layers.

## 2. Minimum functional flows

### Market-only

```text
Tony asks for current market/stock data
→ Julia selects Market function
→ Market returns real structured data
→ Julia interprets and answers
```

### Research-only

```text
Tony asks for current/external research
→ Julia selects Claude/Web Research
→ research returns source-bearing findings
→ Julia interprets and answers
```

### Composite

```text
Tony asks a market reasoning question
→ Julia calls Market and Research as needed
→ evidence returns
→ Julia compares/synthesizes
→ Julia gives fresh judgment
```

## 3. Failure acceptance

```text
Market unavailable
→ visible typed/tool failure
→ no fake data

Research unavailable
→ visible limitation/failure
→ no fabricated sources

one tool fails
→ Julia may use remaining real evidence
→ missing evidence must remain visible in the answer/reasoning state

no alternate hidden fallback
```

## 4. Boundary acceptance

Verify:

```text
Assistant does not perform final cognition
Core does not inspect Market private implementation
Core does not reinterpret Market public result semantics
Market private objects do not cross the public boundary
Claude/Research does not replace Julia final judgment
```

## 5. Release identity

For a release candidate, record as needed:

```text
Julia_core SHA
Julia-AI-Assistant SHA
ai_theme_app SHA
configuration identity
runtime/deployment identity
```

## 6. Release gates

Before production release:

```text
functional E2E PASS
failure/no-fallback PASS
boundary checks PASS
regression PASS
exact repo SHAs recorded
Owner release approval
```

Implementation approval does not imply release approval.

## 7. Cutover

If the accepted release cannot run:

```text
STOP
DIAGNOSE
FIX
RETEST
```

Do not hide failure behind a legacy path.
