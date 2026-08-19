# DIA-5 R1 — Reflection Context Handoff Core Contract

> **Namespace:** CONT-DIA
> **Canonical phase:** CONT-DIA-5 — Reflection Context Handoff
> **Not to be confused with:** STORAGE-DIA-5 — Julia Reflection Generation

## 0. Status

Phase: DIA-5 — Reflection Context Handoff Surface  
Artifact: R1 Core implementation  
Implementation provenance: Codex A  
Branch: `codex/dia-5/reflection-handoff-r1`  
Base: `017ba4e2d77f3a8e3cddbcb0f71822ea0edf9e48`  
Frozen design input: DIA-5 R0 @ `c2e6a8060fb2d363f06b198808f4b2c6b16d0494`

DIA-4 R0/R1/R2.1 are treated as FINAL / CLOSED / FROZEN. This implementation does not modify DIA-4 context identity, canonical bytes, digest algorithms, assembly semantics, Assistant integration, Diary, Memory, Context OS, or generation behavior.

## 1. Implemented module

```text
julia_core/reflection_handoff/
  __init__.py
  models.py

tests/reflection_handoff/test_dia5_core_contract.py
```

Public Core nouns:

- `HandoffEndpoint`
- `HandoffIntegrity`
- `ReflectionContextHandoff`
- `HandoffReceiptStatus`
- `HandoffReceipt`
- `ReflectionHandoffValidator`
- `StrictReflectionHandoffValidator`

## 2. Boundary semantics

DIA-5 R1 is a transport / validation contract over DIA-4 semantic context bytes.

```text
DIA-4 ReflectionContext
        ↓ exact semantic bytes + existing context_digest
DIA-5 ReflectionContextHandoff
        ↓ strict consumer validation
HandoffReceipt
```

Frozen R1 rule:

```text
DIA-5 may carry and validate context identity.
DIA-5 does not own, recompute, repair, or reinterpret context identity.
```

## 3. Identity separation

`ReflectionContextHandoff` carries two distinct identity surfaces:

1. DIA-4 context identity
   - `context_version`
   - `context_digest`
   - `context_semantic_bytes`

2. DIA-5 envelope identity
   - `handoff_version`
   - `handoff_id`
   - `producer`
   - `consumer`
   - `created_at`
   - `integrity`

Implication verified by tests:

```text
same ReflectionContext
+ different handoff_id / producer / created_at
⇒ same context_digest and semantic bytes
⇒ different handoff_envelope_digest
```

## 4. Integrity contract

`HandoffIntegrity` freezes:

```text
semantic_bytes_sha256 = SHA-256(context_semantic_bytes)
context_digest        = carried DIA-4 ReflectionContext.context_digest
context_version       = dia4-reflection-context-v1
digest_algorithm      = sha256:handoff-semantic-bytes:v1
```

It validates:

- `context_digest` equality
- byte-exact semantic payload hash
- 64-character lowercase SHA-256 hex format
- frozen context version
- frozen handoff integrity algorithm

Malformed or mismatched handoffs fail closed; no repair path exists in Core.

## 5. Semantic / transport separation

`context_semantic_bytes` is byte-native and model-visible / consumer-visible context payload.

Transport metadata is excluded from DIA-4 semantic bytes:

- producer
- consumer
- handoff id
- created_at
- receipts
- retries
- validation timestamps

Changing transport metadata does not alter `context_semantic_bytes` or `context_digest`.

## 6. Consumer validation

`StrictReflectionHandoffValidator` enforces:

- exact `ReflectionContextHandoff` boundary type
- intended consumer equality
- integrity verification

It emits `HandoffReceipt(status=ACCEPTED)` only after validation. Rejected receipts require a reason; accepted receipts cannot carry a rejection reason.

## 7. Authority exclusions

The Core module has no authority over:

- Diary
- Memory
- Context OS
- client-native histories
- filesystem persistence
- model / LLM generation
- transport persistence

R2 / Assistant transport remains responsible for physical delivery, receipt persistence, and any durable handoff-id conflict detection.

## 8. Golden vectors

Canonical DIA-5 R1 vectors from the fixed test fixture:

```text
context_digest:
0b6a3f9b1c7b195c9f00ab40833130bf2452e74cd73c3bcf2a8298cabd9cac9c

handoff semantic bytes SHA-256:
f0e72dda9e1e7e518eff781f6cb33600e123528632cce0100795a79ce93b7e7b

handoff envelope digest:
e70dbc86bee5013c8dbf1cbceb744004c42dcfabf0f8daf6c40718329ef0ee02
```

## 9. Owner validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/reflection_handoff/test_dia5_core_contract.py -q
16 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/reflection_context/test_dia4_core_contract.py -q
24 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/reflection_trigger/test_dia3_core_contract.py -q
44 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/reflection_handoff tests/reflection_handoff/test_dia5_core_contract.py
PASS
```

## 10. R1 Gate summary

```text
DIA-5 R1 Core Handoff Contract

Codex A implementation     ✅ COMPLETE
DIA-5 focused tests        ✅ 16 passed
DIA-4 regression           ✅ 24 passed
DIA-3 regression           ✅ 44 passed
compileall                 ✅ PASS

Ready for Mira review      ▶
Codex B sabotage           ⏸ HOLD
DIA-5 R2 transport         ⏸ HOLD
```
