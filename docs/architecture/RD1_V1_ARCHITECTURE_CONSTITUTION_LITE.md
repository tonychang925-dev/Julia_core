# RD1-V1 Architecture Constitution Lite

**Date:** 2026-09-17  
**Owner:** Tony  
**Status:** ACTIVE / OWNER APPROVED  
**Scope:** Julia Core / Julia-AI-Assistant / Market Brain / Research

## 1. Product goal

```text
Tony question
→ Assistant transport
→ Julia cognition
→ Julia chooses tool(s)
→ Market and/or Claude/Web Research
→ structured evidence returns
→ Julia cognition continues
→ Julia final judgment
→ Assistant transport
→ Tony
```

Tool calls are product functions, not governance events.

## 2. Component responsibilities

### Julia-AI-Assistant

```text
transport
session edge
serialization
presentation
voice/text I/O
```

Assistant does not own Julia cognition, investment judgment, Market semantics, or final judgment.

### Julia Core

```text
Julia cognition runtime
personality / memory activation
tool selection
tool orchestration
evidence re-entry
final response generation
```

### Market Brain / ai_theme_app

```text
Market-domain data
Market-domain operations
Market strategy knowledge
Market public functions
Market public result semantics
Market private composition
```

### Claude / Research

```text
external source acquisition
web/news/document research
source-bearing summaries
bounded analytical assistance
```

Claude / Research provides evidence; Julia keeps final judgment responsibility.

## 3. Dependency direction

```text
Assistant → Julia Core → Market public functions
Julia Core → Claude / Research functions
```

No component may depend on another component's private implementation.

## 4. Core ↔ Market ABI

Market owns the semantics of its public results, including:

```text
MarketResultEnvelope
Market operation status
Market data state
Market failure kind
Market provenance
Market payload
```

Core may own execution metadata such as provider/function identity, execution id, duration, timeout, binding failure, protocol failure, and exceptions before a valid Market result exists.

Canonical rule:

```text
ADAPTER MAY ADAPT SHAPE
ADAPTER MAY NOT REINTERPRET DOMAIN RESULT SEMANTICS
```

Allowed adapter work:

```text
request-shape adaptation
sync/async adaptation
lifecycle adaptation
serialization/wrapping
```

Core must not create a second domain-equivalent taxonomy that redefines Market public result semantics.

## 5. Two failure planes

```text
Core execution failure
= failure before a valid domain result exists

Market domain outcome
= valid MarketResultEnvelope, including domain failure/empty/stale/etc.
```

These planes must not swallow each other.

## 6. Market public boundary

Julia/Core accesses Market through Market public functions/contracts only.

Private Market implementation must not cross the boundary:

```text
private repository
DB session
ORM object
private adapter
private filesystem layout
private MCP implementation
```

## 7. C08 and C03

For ordinary internal READ_ONLY capabilities:

```text
C08 = capability allowed / available check
```

C08 is a runtime function guard, not a project-governance ceremony.

```text
C03 = tool result / evidence → model-visible Julia context
```

C03 preserves evidence for Julia and does not reinterpret Market public result semantics.

## 8. Architectural invariants

```text
1. Julia remains the cognition and final-judgment responsibility holder.
2. Assistant remains transport/session/presentation only.
3. Market owns Market-domain implementation and public result semantics.
4. Cross-repo Market access uses Market public functions/contracts only.
5. Core executes tool calls but does not re-author Market public result semantics.
6. Claude / Research provides evidence, not final Julia judgment.
7. No hidden fallback or synthetic success on the canonical product path.
8. Tool evidence returns to Julia before the final answer.
9. Private implementation does not leak across repository boundaries.
```

## 9. Non-requirements for current READ_ONLY path

```text
enterprise IAM
JWT/OAuth between Julia and Market
PKI/Sigstore
mandatory HTTP/RPC/MCP transport
cross-repo semantic normalization taxonomy
task-level permission matrices for normal function work
Owner approval for each normal READ function call
```

These may be added later only for a concrete product/security need.

## 10. Architecture review test

An implementation is an architecture change only when it changes or breaks one of:

```text
component ownership
dependency direction
public/private boundary
public contract semantics
tool evidence re-entry
fallback policy
Julia final-judgment responsibility
```

Wording preference, helper choice, ordinary implementation style, test organization, and non-semantic adapter mechanics are not architecture violations.
