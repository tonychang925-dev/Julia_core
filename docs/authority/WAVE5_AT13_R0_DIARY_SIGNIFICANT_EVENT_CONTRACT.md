# Wave5 AT-13 R0 Contract — Diary Significant Event / Narrative Causal Integrity

Status: READY FOR FREEZE ✅  
Date: 2026-08-23  
Repository: `/Users/admin/julia_core`  
Branch: `cm-r0-fix`  
Audit commit: `15f121b`  
Acceptance item: AT-13 — Diary significant event / Narrative causal integrity

## 1. Contract Position

```text
AT-12 Diary NO_ENTRY: FROZEN ✅
AT-13 Audit: COMPLETE ✅
AT-13 R0 Contract: READY FOR FREEZE ✅
AT-13 Minimal Remediation: NEXT ▶
AT-13 R1 Permanent Evidence: HOLD ⚠️
AT-13 Integration Acceptance: HOLD ⚠️
AT-13 Freeze: NOT READY
```

This R0 freezes the authority boundary for AT-13 only. It does not implement Diary significant-event generation, Diary UI, Context OS retrieval, MemoryExperience creation, Claude migration, or AT-14 provenance validation.

## 2. Frozen Problem Statement

AT-13 is the positive counterpart to AT-12.

AT-12 froze:

```text
NO_ENTRY
  ≠
canonical Diary history
```

AT-13 freezes:

```text
Meaningful grounded event
  ≠
automatic canonical Diary
```

A meaningful event may justify a Diary candidate, but meaning does not itself create canonical Diary history.

## 3. Canonical Authority Path

The only R0-allowed AT-13 path is:

```text
Grounded significant event / reflection opportunity
  ↓
DiaryCandidate
  ↓
Diary governance decision
  ↓
GOVERNANCE_ACCEPTED
  ↓
AcceptedDiaryEntry
  ↓
DIARY_DURABLE
  ↓
canonical Diary history
```

Every state before `DIARY_DURABLE` is non-canonical for Diary history.

## 4. Frozen Invariants

### AT13-I01 — Significance is not Diary authority

```text
significance detection
  ≠
Diary acceptance
```

A router, trigger, LLM judgment, heuristic, importance score, workflow event, or user-visible marker can identify a candidate opportunity, but none of these may create canonical Diary history.

### AT13-I02 — Meaningful event is not automatic Diary

```text
meaningful grounded event
  ≠
automatic canonical Diary
```

Even if an event is meaningful, grounded, emotionally important, project-important, or relationship-important, it remains outside canonical Diary until the governed path completes.

### AT13-I03 — DiaryCandidate is not canonical history

```text
DiaryCandidate
  ≠
AcceptedDiaryEntry
  ≠
canonical Diary history
```

`DiaryCandidate` is a review object. It may be accepted, rejected, or discarded. It must not be written as canonical Diary and must not become observable as accepted Diary history.

### AT13-I04 — AcceptedDiaryEntry shape is not governance proof

```text
AcceptedDiaryEntry dataclass/object
  ≠
GOVERNANCE_ACCEPTED proof
```

Constructing an object with accepted-entry fields is not sufficient. AT-13 requires an explicit governance acceptance boundary before repository append.

### AT13-I05 — First-person reflection is required

Accepted AT-13 Diary entries must be Julia first-person reflections.

Forbidden as accepted Diary body:

```text
raw transcript summary
third-person system summary
provider/tool execution summary
copied conversation excerpt as self-contained history
observability log rendered as diary
```

Allowed minimum property:

```text
Julia first-person reflective body
  +
source_refs
  +
governance acceptance
```

This R0 does not require LLM quality scoring. It requires a deterministic boundary that prevents transcript summaries or copied source history from being accepted as Diary merely because they are non-empty text.

### AT13-I06 — source_refs must anchor source authority

```text
source_refs present
  ≠
source authority established
```

For AT-13, accepted significant Diary must carry non-empty source refs anchored to canonical source namespaces such as:

```text
conversation://...
memory://experience/...
migration://...
```

Full broken/missing source validation is AT-14. AT-13 only freezes that arbitrary strings or projection-only references cannot satisfy the source authority boundary.

### AT13-I07 — DIARY_DURABLE is the canonical boundary

```text
AcceptedDiaryEntry object
  ≠
canonical Diary history until DIARY_DURABLE
```

Canonical Diary history begins only after durable repository success. A normal repository return must mean `DIARY_DURABLE`; failure must fail closed.

### AT13-I08 — Diary significant event does not create MemoryExperience

```text
AcceptedDiaryEntry
  ≠
MemoryExperience
```

AT-13 Diary acceptance must not write Memory OS canonical experience objects. Any later MemoryCandidate or MemoryExperience path belongs to Memory governance and future gates.

### AT13-I09 — Projection/runtime/cache cannot create Diary authority

```text
UI state
cache state
workflow runtime state
awareness significance result
Context OS projection
Memory projection
  ≠
canonical Diary authority
```

Projection can display or route candidate information, but cannot create, accept, persist, or mutate canonical Diary history.

### AT13-I10 — Conversation authority is not blocked by Diary authority

Diary significant-event processing must remain outside the conversation acceptance critical path.

```text
Conversation CORE_ACCEPTED
  ≠ blocked by
DiaryCandidate / Diary governance / DIARY_DURABLE
```

Diary failure must not roll back accepted conversation history.

## 5. Explicitly Forbidden Shortcuts

The following shortcuts are R0 violations:

```text
significance marker → direct Diary file
LLM summary → canonical Diary
transcript excerpt → Diary body
DiaryCandidate → repository append
AcceptedDiaryEntry constructor alone → repository append
source_refs arbitrary string → source authority
legacy DiaryWriter.save_diary() → canonical Diary
MemoryExperience/event → Diary authority
UI/cache/projection/runtime state → accepted Diary
accepted entry object in memory → canonical history without DIARY_DURABLE
```

## 6. Minimal Remediation Scope

After this R0, Minimal Remediation is allowed only to close P0 gaps required by the contract.

Allowed:

```text
1. Minimal grounded significant-event input/value object.
2. Minimal DiaryCandidate creation path for grounded meaningful events.
3. Explicit governance acceptance/promotion boundary.
4. Deterministic guard against transcript-summary-as-diary.
5. Canonical source namespace guard for source_refs.
6. Repository append proof that only governed AcceptedDiaryEntry reaches durable boundary.
7. Fixture or minimal repository evidence for DIARY_DURABLE semantics, if needed to prove the boundary.
```

Not allowed:

```text
Diary UI redesign
Context OS retrieval/ranking/search implementation
MemoryExperience creation
Claude diary migration
provider/LLM reflection generation redesign
AT-14 broken source resolver
AT-15 Diary ≠ Memory implementation
AT-16 Diary retrieval through Context OS
AT-17 migration implementation
large Diary pipeline redesign
```

## 7. R1 Permanent Evidence Requirements

R1 must attack the contract, not add features.

Required sabotage surfaces:

```text
AT13-R1-001 significance marker attempts direct Diary promotion → blocked
AT13-R1-002 DiaryCandidate attempts repository append → blocked
AT13-R1-003 transcript summary body attempts accepted Diary → blocked
AT13-R1-004 fake/projection source_ref attempts accepted Diary → blocked
AT13-R1-005 accepted-entry object without governance proof attempts canonical append → blocked
AT13-R1-006 durable failure leaves no canonical Diary history → fail closed
AT13-R1-007 accepted Diary does not create MemoryExperience → zero Memory mutation
```

R1 must not depend on UI redesign, LLM generation quality, or full AT-14 source-resolution behavior.

## 8. Integration Acceptance Requirements

IA must prove the product-shaped governed path:

```text
grounded meaningful event
  ↓
DiaryCandidate
  ↓
Governance acceptance
  ↓
AcceptedDiaryEntry
  ↓
DiaryRepository durable success
  ↓
canonical Diary observable
```

Minimum IA cases:

```text
TC-AT13-IA-001 grounded event creates candidate, not entry
TC-AT13-IA-002 governed acceptance creates AcceptedDiaryEntry
TC-AT13-IA-003 durable repository success makes entry observable
TC-AT13-IA-004 transcript summary path cannot become accepted Diary
TC-AT13-IA-005 source_refs remain refs and do not copy transcript history
TC-AT13-IA-006 Diary acceptance does not create MemoryExperience
```

## 9. Relationship to Adjacent Gates

```text
AT-12 NO_ENTRY
  Frozen: no meaningless Diary artifact

AT-13 Significant Event
  This contract: meaningful event still requires governance and durability

AT-14 Provenance
  Future: broken/missing source refs are detected

AT-15 Diary ≠ Memory
  Future: Diary acceptance and MemoryExperience creation remain separate

AT-16 Context OS retrieval
  Future: Diary enters model context only through governed Context OS assembly

AT-17 Claude migration
  Future: legacy diary-like text requires semantic reclassification
```

## 10. Freeze Decision

```text
AT-13 R0 Contract: READY FOR FREEZE ✅
Minimal Remediation: NEXT ▶ after commit
R1: HOLD ⚠️
IA: HOLD ⚠️
Final Freeze: NOT READY
```

R0 freezes the AT-13 authority law:

```text
Meaning
  ≠
Memory

Candidate
  ≠
History

Accepted shape
  ≠
Governance proof

AcceptedDiaryEntry
  ≠
canonical Diary until DIARY_DURABLE
```
