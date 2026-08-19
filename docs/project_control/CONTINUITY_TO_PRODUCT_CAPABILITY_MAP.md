# CONTINUITY → PRODUCT CAPABILITY MAP

**Status:** CANONICAL
**Date:** 2026-08-19
**Purpose:** Pin, for every capability, whether it is owned by the frozen CONT-DIA Core semantics or by a product layer (Assistant/Electron). Wave4 must **consume** Core semantics and implement **only adapters** for product-specific binding — never redefine a frozen capability under a new Wave name.

**Primary invariant:**

> CONT-DIA Core semantics are consumed by product runtime, never redefined by it.

---

## 1. Capability Ownership Matrix

**Classification tags (exactly one per row):**

| Tag | Meaning |
|---|---|
| `REUSE` | Frozen Core capability; product consumes it directly |
| `ADAPTER` | Product implements only the binding/adapter onto a frozen Core contract |
| `PRODUCT-ONLY` | Pure product concern; Core has no semantic ownership |
| `MISSING` | Not yet implemented anywhere |
| `DUPLICATE-CANDIDATE` | Suspected reimplementation of frozen Core semantics — must be audited (CLN-03) |

| Capability | Existing implementation | Authority | Wave4 behavior | Tag |
|---|---|---|---|---|
| `ReflectionOpportunity` | `CONT-DIA-3` | Core | reuse canonical objects | `REUSE` |
| `PendingOpportunity` | `CONT-DIA-3` | Core | reuse | `REUSE` |
| Reflection Context | `CONT-DIA-4` | Core | reuse | `REUSE` |
| Handoff | `CONT-DIA-5` | Core | reuse | `REUSE` |
| Evolution / Lineage | `CONT-DIA-6` | Core | reuse | `REUSE` |
| `ContinuityState` | `CONT-DIA-7` | Core | consume only | `REUSE` |
| Decision Invariance | `CONT-DIA-8` | Core | consume only | `REUSE` |
| Conversation Storage | Wave1 (`wave1/*`) | Assistant | keep as-is | `PRODUCT-ONLY` |
| Conversation CRUD | Wave2 (`wave2/*`) | Assistant | keep as-is | `PRODUCT-ONLY` |
| `DiaryEntry` | `DIARY-IMPL-DIA-1` | Core contract | reuse | `REUSE` |
| `DiaryRepository` Port | `DIARY-IMPL-DIA-2A` | Core contract | reuse | `REUSE` |
| Diary Persistence | `DIARY-IMPL-DIA-2B` | Assistant adapter | keep | `ADAPTER` |
| Trigger Runtime | `STORAGE-DIA-3` | Assistant | implement adapter only | `ADAPTER` |
| Reflection Context Assembly | `STORAGE-DIA-4` | Core (`CONT-DIA-4`) | adapter / orchestration only | `ADAPTER` |
| Reflection Generation | `STORAGE-DIA-5` | product (LLM-authored) | product-only | `PRODUCT-ONLY` |
| Reflection Governance | `STORAGE-DIA-6` | product orchestration | product-only (consumes CONT-DIA) | `PRODUCT-ONLY` |
| Diary Retrieval | `STORAGE-DIA-7` | product (Context OS source) | adapter onto Context OS | `ADAPTER` |
| Diary UI | `STORAGE-DIA-8` | Electron | later | `PRODUCT-ONLY` |

---

## 2. Hard Ownership Boundaries

### 2.1 Reflection Trigger (CONT-DIA-3 vs STORAGE-DIA-3)

- **CONT-DIA-3 owns (frozen):** `ReflectionOpportunity` identity, `PendingOpportunity` semantics, canonical trigger admission state, causal identity, trigger truth.
- **STORAGE-DIA-3 may only do:** timer / event / manual signal → **adapter** → CONT-DIA-3 canonical objects.
- **Must NOT reimplement:** opportunity identity, admission semantics, causal identity, trigger truth.

### 2.2 Reflection Context (CONT-DIA-4 vs STORAGE-DIA-4)

- **CONT-DIA-4 owns (frozen):** `ReflectionContext` identity/schema, canonical assembly semantics, serialization/invariants.
- **STORAGE-DIA-4 may:** gather product inputs, call Core assembly, bind runtime dependencies.
- **STORAGE-DIA-4 must NOT:** redefine `ReflectionContext`, create alternate context identity, duplicate assembly semantics.

### 2.3 Diary Persistence (DIARY-IMPL-DIA-2A vs 2B)

- **Julia_core owns:** `DiaryRepository` Port — interface + semantic contract only.
- **Julia-AI-Assistant owns:** concrete persistence adapter (JSON/Markdown/SQLite, `PRIVATE_DATA_ROOT`, product paths).
- **Forbidden in Core:** writing JSON/Markdown/SQLite, resolving `PRIVATE_DATA_ROOT`, holding product-specific paths.

### 2.4 Conversation (Wave1/Wave2)

- **Wave1** owns canonical conversation storage (durable append, idempotency, segment rotation).
- **Wave2** owns product conversation management (CRUD, pagination, rename, search).
- Both are `PRODUCT-ONLY`; Core `ConversationRuntime` remains the semantic authority they bind to.

---

## 3. Wave4 Direction

```
Wave4 = integrate existing capabilities, never reinvent existing semantics.

CONT-DIA-3..8   → consumed via import/adapter (REUSE)
Wave1/Wave2     → kept (PRODUCT-ONLY)
DIARY-IMPL      → Core contract reused, Assistant adapter kept (REUSE + ADAPTER)
STORAGE-DIA-3   → adapter only (ADAPTER)
STORAGE-DIA-4   → adapter / orchestration only (ADAPTER)
STORAGE-DIA-5/6 → product orchestration only (PRODUCT-ONLY)
STORAGE-DIA-8   → Electron, later (PRODUCT-ONLY)
```

No row may carry `DUPLICATE-CANDIDATE` after CLN-03 completes — any such row must be resolved to `REUSE` (retire the duplicate) or `ADAPTER` (rewrite as adapter).

---

## 4. Acceptance

- [x] Every capability mapped to exactly one authority (Core vs product)
- [x] Every capability tagged with exactly one classification
- [x] No vague "similar/overlapping" wording — each row is a concrete decision
- [x] Primary invariant stated: product consumes Core, never redefines it
