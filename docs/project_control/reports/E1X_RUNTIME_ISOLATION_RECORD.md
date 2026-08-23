# E1X_RUNTIME_ISOLATION_RECORD

Status: EXPERIMENTAL / LEGACY ISOLATED
Date: 2026-08-23
Repository scope: julia_ai_assistant (+rmd3g_prod) `runtime/assistant_runtime.py` / `JuliaAssistantRuntime`
Mode: READ-ONLY audit (no patch)

---

## 1. Classification

```text
JuliaAssistantRuntime = E1.x Experimental Runtime
                         No Production Consumer
                         No Authority
                         Deprecated Isolation
```

## 2. Why (isolated)

- Provides independent context assembly capability (recall policy / self
  archive / relationship / experience reconstruction → system prompt → provider).
- NOT connected to production topology:
  - `voice_api/*.py` (production Brain) — ZERO references
  - Electron — ZERO references
  - launchd — NO startup entry
  - ConversationRuntime / ContextExecutionRuntime — NOT integrated
- Used only by the top-level E1.x `server.py` and the E1.x test suite.

## 3. Capability vs Authority (audit verdict)

```text
Current production authority leakage:   NONE
Second transcript authority:            NONE
Second identity authority:              NONE
Second memory authority:                NONE
Second Context Assembly capability:     EXISTS (isolated)
Current production risk:                LOW
Architecture debt:                      YES
```

## 4. Frozen Admission Condition

Future integration REQUIRES the Context OS admission path:

```text
FORBIDDEN:
    Product Runtime → JuliaAssistantRuntime → Provider

REQUIRED:
    Product Runtime → ConversationRuntime.process_turn()
                    → ContextExecutionRuntime (Context OS)
                    → Provider
```

JuliaAssistantRuntime MUST NOT become a product runtime entry.

## 5. Governance Note — authority_chain vs execution_path

`authority_chain` (a governance concept: who has definition right) and
`execution_path` (who executes the call) are DIFFERENT dimensions and must
NOT be merged. Recommendation: ADD `execution_path` trace field; do NOT
replace `authority_chain` (preserves Phase8 boundary proof semantics).

## 6. Expiry / Review

- Re-review when any future Product Runtime integration is proposed.
- No active removal required (isolated, non-production).

## 7. Relationship to :8100

```text
:8100 Gateway                → legacy gateway, compatibility, no production topology
JuliaAssistantRuntime (E1.x) → experimental runtime, no production consumer, isolated

Unified classification: capability exists, authority absent, production isolated.
```
