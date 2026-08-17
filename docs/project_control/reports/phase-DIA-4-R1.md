# DIA-4 R1.2 — Core Reflection Context Contract

## Status

Implementation Owner: Codex A  
Gate: DIA-4 R1.2 Core Context Contract ready for Mira review  
Core base: `659594fd1d3d290d6587e45ab5d3c51c3534a2be`  
Frozen DIA-4 R0 design: `9356a736ce16dc7a16f3db6c5221eab4b8613d84`

## Scope

Added Core-only semantic contract:

- `julia_core/reflection_context/__init__.py`
- `julia_core/reflection_context/models.py`
- `tests/reflection_context/test_dia4_core_contract.py`
- `docs/project_control/reports/phase-DIA-4-R1.md`

No Assistant physical integration. No Diary, Memory, Context OS, client/voice history, or model generation authority.

## R1.2 fixes

- Byte-opaque canonical payload support: `ReflectionContext.semantic_canonical_bytes()` now frames ordered `ContextFact.canonical_bytes()` as bytes via byte-native length framing. It no longer decodes fact bytes through UTF-8.
- Added opaque binary payload regressions and verified existing ASCII context golden vector remains unchanged.

## R1.1 fixes

- Algorithm revision truthfulness: unknown `selection_algorithm_revision` and `context_digest_algorithm_revision` fail closed.
- Structural interpretation firewall: `fact_type` is now closed `CanonicalFactType`, not a blacklist string.
- Frozen context digest domain: removed the non-R0 `context.fact_count` field; ordered length-framed facts are sufficient.

## Implemented Core nouns

- `CanonicalFact`
- `CanonicalFactType`
- `ContextFact`
- `FactSemanticProvenance`
- `FactAuditMetadata`
- `ReflectionContext`
- `ReflectionContextAudit`
- `ContextBounds`
- `ContextAssemblyPolicy`
- `ReflectionOpportunityHandoff`
- `ReflectionOpportunityInputPort`
- `CanonicalFactReader`
- `ReflectionContextAssembler`
- `DeterministicReflectionContextAssembler`

## Frozen semantics implemented

- Production assembly requires `ReflectionOpportunityHandoff`; arbitrary type-valid `ReflectionOpportunity` is not accepted by the assembler.
- Selected refs are exactly `ReflectionOpportunity.source_refs` in existing canonical order.
- Missing facts, source mismatches, digest mismatches, duplicate refs, projection mismatches, and bounds violations fail closed.
- `ContextFact` is an exact byte-level copy of the selected `CanonicalFact` semantic fields.
- DIA-4 does not truncate, summarize, redact, reinterpret, reproject, or expand context.
- `ReflectionContext` contains semantic DIA-5 input only.
- `ReflectionContextAudit` is a separate sidecar; audit metadata is excluded from `context_digest` and `semantic_canonical_bytes()`.
- `ContextAssemblyPolicy.policy_fingerprint()` binds bounds, selection algorithm revision, fact projection revision, and context digest algorithm revision.
- `context_digest` binds opportunity id, opportunity key digest, policy revision/fingerprint, exact bounds, ordered fact bytes, payload bytes, and semantic provenance.

## Golden vectors

- policy fingerprint: `1e2ad176a764ef0447422a60e1a469aeb2a7fb8d305664dffabf102c2c4e4f86`
- canonical fact payload digest: `7c487cbcd022b34aa379dc38eeb21c5e082528b8b1981bcb8de53723a007a81c`
- reflection context digest: `f3622e40f42fc4cc01ce7dd1e7a65d75fc2c3ba0dfbbbc1deb1d6703da6594cf`

## Validation evidence

```bash
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/reflection_context/test_dia4_core_contract.py -q
# 24 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/reflection_trigger/test_dia3_core_contract.py -q
# 44 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/reflection_context tests/reflection_context/test_dia4_core_contract.py
# passed
```

## Non-goals / deferred to DIA-4 R2

- Physical durable policy binding
- Real ConversationRepository / ConversationRuntime canonical reader adapter
- DIA-3 handoff physical composition
- Assistant integration wiring

## Gate summary

DIA-4 R1.2 implements the frozen Core semantic contract: Julia may receive bounded canonical facts, but DIA-4 has no authority to interpret, rewrite, expand, persist, or generate from them.
