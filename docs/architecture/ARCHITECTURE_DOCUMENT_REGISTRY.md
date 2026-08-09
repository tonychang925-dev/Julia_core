# Architecture Document Registry

**Status**: GOVERNED
**Date**: 2026-08-09
**Purpose**: Single registry of all architecture documents with current disposition.

## CANONICAL

| Document | Status |
|----------|--------|
| `JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md` | CANONICAL |
| `ARCHITECTURE_INDEX.md` | GOVERNED |

## HISTORICAL / SUPERSEDED — Master Architecture Docs

| Document | Original Status | Current Status | Replacement |
|----------|----------------|----------------|-------------|
| `JULIA_CORE_PRINCIPLES.md` | FROZEN | SUPERSEDED | Unified Arch §3-4 |
| `ARCH-R0_AUTHORITY_MAP.md` | FROZEN | SUPERSEDED | Unified Arch §5 |
| `ARCHITECTURE_OVERVIEW.md` | FROZEN | SUPERSEDED | Unified Arch §5-6 |
| `ARCHITECTURE_STATUS.md` | FROZEN | SUPERSEDED | ARCHITECTURE_INDEX.md |
| `Julia_Agent_Design_v1.0.md` | DESIGN | SUPERSEDED | Unified Arch |
| `Julia_Agent_Frontier_Assessment_v0.1.md` | ASSESSMENT | SUPERSEDED | — |
| `CXT-C0_REALITY_MATRIX.md` | FROZEN | HISTORICAL | — |
| `CXT-C1_TRANSCRIPT_AUTHORITY_CONTRACT.md` | FROZEN | HISTORICAL (invariants adopted in UA §9) | C-02 |

## HISTORICAL / SUPERSEDED — Subsystem Design Docs

| Document | Original Status | Current Status | Replacement |
|----------|----------------|----------------|-------------|
| `CONTEXT_OS_DESIGN.md` | FROZEN | SUPERSEDED | Unified Arch §8, C-03 |
| `MEMORY_OS_DESIGN.md` | FROZEN | SUPERSEDED | Unified Arch §11, C-05 |
| `PERSONA_ENGINE_DESIGN.md` | FROZEN | SUPERSEDED | Unified Arch §10, C-04 |
| `CONTINUITY_OS_DESIGN.md` | FROZEN | SUPERSEDED | Unified Arch §12, C-06 |
| `ALIGNMENT_OS_DESIGN.md` | FROZEN | SUPERSEDED | Unified Arch §16, C-09 |
| `VOICE_OS_DESIGN.md` | DESIGN | SUPERSEDED AS CORE ONTOLOGY | Unified Arch §17, C-11 |
| `CONTEXT_RECONSTRUCTION_DESIGN.md` | FROZEN | SUPERSEDED | Unified Arch §8, C-06 |
| `MEMORY_CONTINUITY_BINDING_DESIGN.md` | FROZEN | SUPERSEDED | Unified Arch §21, C-06 |
| `CONTINUITY_API_DESIGN.md` | FROZEN | SUPERSEDED | C-06 |
| `CORE_RUNTIME_STATUS.md` | FROZEN | SUPERSEDED | — |

## HISTORICAL — Public Contract Docs

| Document | Original Status | Current Status |
|----------|----------------|----------------|
| `Public_Contract_Model_v1.md` | FROZEN | SUPERSEDED |
| `Context_OS_API_v1.md` | FROZEN | LEGACY CONTRACT — REVALIDATION REQUIRED |
| `Runtime_API_v1.md` | FROZEN | LEGACY CONTRACT — REVALIDATION REQUIRED |
| `Memory_API_v1.md` | FROZEN | LEGACY CONTRACT — REVALIDATION REQUIRED |
| `Persona_API_v1.md` | FROZEN | LEGACY CONTRACT — REVALIDATION REQUIRED |
| `Provider_API_v1.md` | FROZEN | LEGACY CONTRACT — REVALIDATION REQUIRED |
| `ContextRequest_Schema_v1.0_FROZEN.md` | FROZEN | LEGACY CONTRACT — REVALIDATION REQUIRED |

## HISTORICAL — Voice Architecture Docs

| Document | Original Status | Current Status |
|----------|----------------|----------------|
| `JULIA_REALTIME_VOICE_ARCHITECTURE_FREEZE_V2.md` | FROZEN | SUPERSEDED AS CORE ONTOLOGY |
| `Julia_Voice_Engine_Architecture_Review_v1.0.md` | REVIEW | SUPERSEDED |
| `Julia_Voice_Engine_Architecture_Review_v2.0.md` | REVIEW | SUPERSEDED |

## AUDIT EVIDENCE — Not Superseded (empirical observations)

| Document |
|----------|
| `docs/audit/IDENTITY_RUNTIME_AUDIT_v1.md` |
| `docs/audit/CROSS_SESSION_RETRIEVAL_AUDIT_v1.md` |
| `docs/audit/MEMORY_QUALITY_AUDIT_v1.md` |
| `docs/audit/JULIA_TOOL_RUNTIME_AUDIT_v1.md` |

## OPERATIONS — Not architecture

| Document | Status |
|----------|--------|
| `AUTODL_RESTART_CHECKLIST.md` | ACTIVE |
| `JULIA_VOICE_SERVER_RUNBOOK.md` | ACTIVE |


## ADR Disposition Matrix

| ADR | Title | Disposition |
|-----|-------|-------------|
| ADR-001 | Context OS Authority | RE-ADOPTABLE — UA §8, C-03 |
| ADR-002 | Domain Facts, Not Cognition | RE-ADOPTABLE — UA §14-15 |
| ADR-003 | Workbench Action Context | APPLICATION-SPECIFIC |
| ADR-004 | Voice Provider Boundary | VOICE-SPECIFIC |
| ADR-005 | Persona/Identity Separation | PARTIAL — IdentityContract adopted; refined in UA §10 |
| ADR-006 | Provider Alignment Boundary | PARTIAL — adaptation kept; continuity claim removed |
| ADR-007 | Model Behavior Adaptation | PARTIAL — superseded by C-09 |
| ADR-008 | Alignment OS Authority | PARTIAL — adaptation scope kept; "same agent" removed (UA §16) |
| ADR-009 | Continuity OS Authority | RE-ADOPTABLE — UA §12, C-06 |
| ADR-010 | Continuity Checkpoint Model | RE-ADOPTABLE — UA §12.6 |
| ADR-011 | Compact Recovery Protocol | RE-ADOPTABLE — UA §8, C-06 |
| ADR-012 | Memory Continuity Governance | RE-ADOPTABLE — UA §21 |
| ADR-013 | Context Reconstruction Boundary | RE-ADOPTABLE — UA §8.7, C-06 |
| ADR-020 | Production Context Reconciliation | PARTIAL — CXT-C1 adopted; superseded by UA |
| ADR-022 | Runtime Gateway Architecture | INFRASTRUCTURE |
| ADR-025 series | Voice Architecture | VOICE-SPECIFIC — not Core ontology |
| ADR-026 | Capability MCP Adapter | INFRASTRUCTURE |
| ADR-027 | Runtime Execution Model | PARTIAL — lifecycle kept; superseded by C-01 |
| ADR-028 series | Awareness / Domain Intelligence | APPLICATION/DOMAIN-SPECIFIC |
| ADR-029 | Observation Policy | APPLICATION-SPECIFIC |
| ADR-030 | Market Intelligence Integration | DOMAIN-SPECIFIC |
| ADR-031 | Experience Feedback | PARTIAL — Memory governance |
| ADR-032 | Strategy Knowledge Model | DOMAIN-SPECIFIC |

Rejected claims: LLM=interpreter, Runtime owns identity/memory/context, Voice OS owns CognitiveEmotion, Alignment owns continuity, IntentRouter decides semantic action.


## Normative Precedence

```
1. JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md   CANONICAL
2. Frozen C-series Contracts                   DERIVED
3. Compatible Accepted ADRs                    SUPPORTING
4. API / Schemas                               IMPLEMENTATION
5. Production Implementation                   CODE
6. Historical Architecture Documents           EVIDENCE ONLY
```

No other document has normative architecture authority.
