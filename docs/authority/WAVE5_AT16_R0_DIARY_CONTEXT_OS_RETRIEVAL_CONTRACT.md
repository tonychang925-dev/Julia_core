# Wave5 AT-16 R0 Contract — Diary Retrieval Through Context OS Only

Status: READY FOR FREEZE ✅  
Date: 2026-08-23  
Repository: `/Users/admin/julia_core`  
Branch: `cm-r0-fix`  
Audit commit: `d7c37a4`  
Acceptance item: AT-16 — Diary retrieval through Context OS only

## 1. Contract Position

```text
AT-15 Diary ≠ Memory: FROZEN ✅
AT-16 Audit: COMPLETE ✅
AT-16 R0 Contract: READY FOR FREEZE ✅
AT-16 Minimal Remediation: NEXT ▶
AT-16 R1 Permanent Evidence: HOLD ⚠️
AT-16 Integration Acceptance: HOLD ⚠️
AT-16 Freeze: NOT READY
```

This R0 freezes the AT-16 model-visible Diary retrieval authority boundary only. It does not implement AT-17 Claude migration, Diary UI redesign, Context OS ranking/search optimization, MemoryExperience creation, provider response generation changes, or large Memory OS redesign.

## 2. Frozen Problem Statement

AT-12 froze:

```text
Reflection ≠ Diary
```

AT-13 froze:

```text
Meaning ≠ Memory
```

AT-14 froze:

```text
Reference ≠ Provenance Truth
```

AT-15 froze:

```text
Diary ≠ Memory
```

AT-16 freezes the next boundary:

```text
Diary retrieval
  ≠
Diary authority
```

and:

```text
Context OS ContextBlock
  ≠
Diary authority
  ≠
Memory authority
  ≠
Identity authority
```

A Diary entry may be selected for model-visible context, but selection is short-lived projection. Selection does not mutate Diary, create Memory, rewrite identity/persona, or become canonical history.

## 3. Canonical Retrieval Path

The only valid AT-16 Diary model-visible path is:

```text
AcceptedDiaryEntry
  ↓
Diary provenance validation
  ↓
Diary Context OS admission
  ↓
DiaryContextCandidate
  ↓
Context OS provider/resolver
  ↓
ContextBlock selection + budget
  ↓
CognitiveContextPackage provenance trace
  ↓
model-visible context
```

Forbidden shortcut:

```text
AcceptedDiaryEntry / diary file / session summary diary / density diary-like text
  ↓
direct prompt text / wake-state text / provider message
```

## 4. Frozen Invariants

### AT16-I01 — Context OS is the only Diary retrieval admission path

```text
Diary content
  → Context OS admission
  → ContextBlock
  → model-visible context
```

No runtime, provider, session recorder, density restorer, cache, projection, or legacy helper may inject Diary content directly into model input while claiming AT-16 compliance.

### AT16-I02 — AcceptedDiaryEntry is not model-visible by default

```text
AcceptedDiaryEntry
  ≠
model-visible context
```

Durability, acceptance, body text, themes, title, or source refs do not by themselves authorize model-visible use.

### AT16-I03 — Provenance validation is required but not sufficient

```text
DiaryProvenanceReport RESOLVED
  ≠
automatic context injection
```

Provenance validation is an admission prerequisite. Context OS still owns selection, budget, ordering, and final assembly.

### AT16-I04 — DiaryContextCandidate is temporary projection input

```text
DiaryContextCandidate
  ≠
AcceptedDiaryEntry
  ≠
MemoryCandidate
  ≠
MemoryExperience
```

A Diary context candidate is a short-lived retrieval/admission object only. It cannot write Diary, Memory, identity, persona, continuity checkpoints, or session history.

### AT16-I05 — Diary ContextBlock is model-visible projection only

```text
Diary ContextBlock
  ≠
Diary mutation authority
  ≠
Memory persistence authority
  ≠
identity/persona authority
```

A ContextBlock may expose selected Diary meaning to the model for the current turn. It must not be used as source truth, durable Diary, Memory, or identity state.

### AT16-I06 — Legacy wake-state diary text is not governed Diary retrieval evidence

Legacy path:

```text
Session summary diary text
  ↓
wake-state string
  ↓
experience_frame
```

is not AT-16-compliant Diary retrieval unless it passes the governed Diary Context OS admission path.

### AT16-I07 — Density-restored experience text is not Diary retrieval authority

```text
density restored experience text
  ≠
Diary retrieval authority
  ≠
MemoryExperience authority
```

Density/experience reconstruction may remain a separate context surface, but it cannot satisfy AT-16 Diary retrieval evidence or bypass Diary provenance/admission.

### AT16-I08 — Trace is mandatory and trace is not authority

AT-16 requires a trace proving:

```text
source → provenance/admission → Context OS assembly → model handoff
```

However:

```text
trace/provenance metadata
  ≠
source authority
  ≠
Diary authority
```

Trace proves routing; it does not create or repair source truth.

### AT16-I09 — Context assembly must not mutate canonical state

```text
Context OS selection
  ≠
Diary write
  ≠
Memory write
  ≠
identity/persona update
  ≠
conversation history rewrite
```

Reading or projecting Diary into model context must be side-effect free with respect to canonical Diary, Memory, Identity, and Conversation authority.

### AT16-I10 — Cross-context isolation applies to Diary retrieval

```text
context A Diary candidate/block
  ≠
context B model-visible Diary authority
```

Diary retrieval must preserve source/context isolation. A selected Diary block for one context cannot authorize another context, conversation, session, or user boundary.

## 5. Required R0 Remediation Boundaries

Minimal remediation may only close P0 authority gaps found by Audit:

1. Add or expose a governed Diary Context OS retrieval/admission surface.
2. Require accepted Diary + provenance validation before Diary can become a Diary context candidate.
3. Convert admitted Diary entries into ContextBlocks only via Context OS provider/resolver/source assembly.
4. Emit a trace proving Diary content reached the model only through Context OS source assembly.
5. Guard legacy wake-state/session diary text so it cannot be counted as governed Diary retrieval.
6. Guard density-restored experience text so it cannot be counted as Diary retrieval authority.
7. Prove ContextBlock projection cannot mutate Diary, Memory, identity, persona, or conversation history.

## 6. Forbidden Remediation Expansion

AT-16 remediation must not add or redesign:

```text
AT-17 Claude migration
Diary UI redesign
Context OS ranking/search optimization
MemoryExperience creation
Memory schema migration
provider generation behavior
large Memory OS redesign
new long-term identity/persona write path
```

## 7. R1 Permanent Evidence Requirements

After minimal remediation, R1 must sabotage the AT-16 boundary without expanding feature scope:

```text
AT16-R1-001 direct AcceptedDiaryEntry injection → rejected / not model-visible
AT16-R1-002 provenance report alone → cannot inject context
AT16-R1-003 legacy wake-state diary text → not counted as governed Diary retrieval
AT16-R1-004 density diary-like text → not counted as Diary retrieval authority
AT16-R1-005 fake DiaryContextCandidate / fake ContextBlock → cannot mutate Diary/Memory/Identity
AT16-R1-006 missing/broken source ref → no transcript-copy fallback into context
AT16-R1-007 cross-context Diary block → no context contamination
AT16-R1-008 trace tampering → cannot become source authority
```

## 8. Integration Acceptance Requirements

IA must prove product-shaped path, not fixture-only sabotage:

```text
TC-AT16-IA-001 AcceptedDiaryEntry → provenance validation → Context OS admission → ContextBlock → model package trace
TC-AT16-IA-002 product runtime does not inject legacy diary text outside Context OS admission
TC-AT16-IA-003 density/experience context remains separated from Diary retrieval authority
TC-AT16-IA-004 missing/broken provenance prevents governed Diary model visibility or marks degraded state without source fabrication
TC-AT16-IA-005 restart/fresh runtime preserves Diary retrieval routing; no direct auto-injection
TC-AT16-IA-006 cross-context Diary retrieval isolation
```

## 9. Acceptance Matrix Impact

Current state after this R0:

```text
AT-01  FROZEN ✅
AT-02  FROZEN READY ✅
AT-03  FROZEN READY / evidence committed ✅
AT-04  FROZEN ✅
AT-05  FROZEN ✅
AT-06  FROZEN ✅
AT-07  FROZEN ✅
AT-08  FROZEN ✅
AT-09  FROZEN ✅
AT-10  FROZEN ✅
AT-11  DEFERRED ⏸️
AT-12  FROZEN ✅
AT-13  FROZEN ✅
AT-14  FROZEN ✅
AT-15  FROZEN ✅
AT-16  R0 READY FOR FREEZE ✅
AT-17  NOT STARTED ❌
```

## 10. Final R0 Decision

```text
AT-16 Diary retrieval through Context OS only

Audit: COMPLETE ✅
R0 Contract: READY FOR FREEZE ✅
Minimal Remediation: NEXT ▶
R1: HOLD ⚠️
IA: HOLD ⚠️
Freeze: NOT READY
```

R0 freeze statement:

```text
Diary may become model-visible only through governed Context OS source assembly. Retrieval and ContextBlock projection do not create, mutate, own, or elevate Diary, Memory, Identity, Persona, Conversation, or provenance authority.
```
