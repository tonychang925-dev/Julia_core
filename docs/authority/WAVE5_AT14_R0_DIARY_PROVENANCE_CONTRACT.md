# Wave5 AT-14 R0 Contract — Diary Provenance / Broken Source Reference Detection

Status: READY FOR FREEZE ✅  
Date: 2026-08-23  
Repository: `/Users/admin/julia_core`  
Branch: `cm-r0-fix`  
Audit commit: `f8a7eb2`  
Acceptance item: AT-14 — Diary provenance / broken source reference detection

## 1. Contract Position

```text
AT-13 Diary Significant Event: FROZEN ✅
AT-14 Audit: COMPLETE ✅
AT-14 R0 Contract: READY FOR FREEZE ✅
AT-14 Minimal Remediation: NEXT ▶
AT-14 R1 Permanent Evidence: HOLD ⚠️
AT-14 Integration Acceptance: HOLD ⚠️
AT-14 Freeze: NOT READY
```

This R0 freezes the provenance authority boundary for AT-14 only. It does not implement AT-15 Diary ≠ Memory, AT-16 Context OS retrieval, AT-17 Claude migration, Diary UI redesign, Conversation deletion implementation, or MemoryExperience creation.

## 2. Frozen Problem Statement

AT-13 froze:

```text
source_refs must use canonical namespaces
```

AT-14 freezes the stronger rule:

```text
source_refs present / namespace-valid
  ≠
provenance validated
```

A Diary entry may be accepted and durable, but each `source_ref` still requires explicit provenance resolution. A canonical-looking URI must not become provenance truth merely because it has the right prefix.

## 3. Canonical Provenance Resolution Path

The only R0-allowed AT-14 path is:

```text
AcceptedDiaryEntry.source_refs
  ↓
Diary source resolver
  ↓
per-ref lifecycle state
  ↓
DiaryProvenanceReport
  ↓
explicit validation outcome
```

Allowed lifecycle states:

```text
RESOLVED     source exists and is available as evidence
ARCHIVED     source exists and is available through archived access
TOMBSTONED   source exists physically but is not available to cognition/access
PURGED       source content is gone; provenance/deletion state remains explicit
MISSING      canonical-looking source ref target is not found
INVALID      source ref is malformed or not an accepted authority namespace
```

No source ref may resolve to silent `None`, unhandled `FileNotFoundError`, omitted result, transcript-copy fallback, or generic truthy/falsey state.

## 4. Frozen Invariants

### AT14-I01 — source_refs field is not provenance validation

```text
source_refs exists
  ≠
provenance validated
```

The field being non-empty and syntactically valid only establishes a reference claim. It does not establish that the source currently resolves.

### AT14-I02 — namespace validity is not source existence

```text
conversation://conv_A/msg_1
  ≠
source exists
```

Canonical namespace validation from AT-13 remains necessary, but AT-14 requires per-ref source lifecycle resolution.

### AT14-I03 — every accepted Diary source_ref must resolve explicitly

Each `AcceptedDiaryEntry.source_refs` item must appear in the provenance report exactly once with a lifecycle state.

Forbidden:

```text
skip missing ref
collapse multiple refs into one generic status
return success without per-ref state
```

### AT14-I04 — broken/missing refs must be detected

```text
canonical-looking missing source
  →
MISSING / BROKEN provenance result
```

Broken references must not be silently accepted, silently dropped, or treated as verified.

### AT14-I05 — PURGED/TOMBSTONED/ARCHIVED are lifecycle states, not generic errors

A purged, tombstoned, or archived source is not the same as an invalid source.

```text
PURGED source
  ≠
MISSING source
  ≠
INVALID source
```

This distinction preserves historical truth:

```text
Julia did write this Diary entry.
The original source may no longer be re-verifiable.
```

### AT14-I06 — source purge does not delete or rewrite Diary

```text
source_ref resolves PURGED
  ≠
Diary deletion
  ≠
Diary body rewrite
  ≠
Diary regeneration
```

Accepted Diary remains canonical historical reflection. Only its source resolution state changes.

### AT14-I07 — provenance validation must not copy transcript/source history

```text
broken source ref
  ≠
copy transcript into Diary for self-containment
```

Diary provenance is refs + lifecycle state, not shadow transcript authority.

### AT14-I08 — UI/cache/projection refs cannot satisfy provenance authority

```text
projection://...
cache://...
ui://...
runtime://...
  ≠
Diary source authority
```

Projection and runtime state may display provenance but cannot validate it.

### AT14-I09 — provenance report is derived, not Diary authority

```text
DiaryProvenanceReport
  ≠
canonical Diary entry
```

The report describes source resolution state at validation time. It must not mutate the accepted Diary entry, rewrite `source_refs`, or become the source of Diary body truth.

### AT14-I10 — AT-14 does not create Memory or Context visibility

```text
provenance validation
  ≠
MemoryExperience creation
  ≠
Context OS retrieval
  ≠
model-visible injection
```

AT-14 validates Diary source references only.

## 5. Explicitly Forbidden Shortcuts

The following are R0 violations:

```text
source_refs non-empty → provenance valid
namespace-valid URI → source exists
missing ref → silently omitted
missing ref → treated as RESOLVED
purged ref → Diary deletion
purged ref → Diary rewrite/regeneration
broken ref → transcript copied into Diary
projection/cache ref → source authority
provenance report → Diary body authority
provenance validation → MemoryExperience creation
provenance validation → Context OS/model injection
```

## 6. Minimal Remediation Scope

After this R0, Minimal Remediation is allowed only to close P0 gaps required by the contract.

Allowed:

```text
1. Minimal SourceRefState enum/value object.
2. Minimal per-ref DiarySourceResolution value object.
3. Minimal DiaryProvenanceReport value object.
4. Fixture-backed resolver protocol/function for accepted Diary entries.
5. Detection of canonical-looking but missing refs.
6. Explicit PURGED/TOMBSTONED/ARCHIVED state support.
7. Tests proving no transcript-copy fallback and no Diary mutation.
```

Not allowed:

```text
AT-15 Diary ≠ Memory implementation
AT-16 Context OS retrieval/ranking/search
AT-17 Claude migration
Diary UI redesign
Conversation deletion implementation
MemoryExperience creation
provider/LLM reflection generation
large reference graph redesign
large Diary persistence redesign
```

## 7. R1 Permanent Evidence Requirements

R1 must attack the provenance boundary, not add features.

Required sabotage surfaces:

```text
AT14-R1-001 namespace-valid but missing conversation ref → MISSING detected
AT14-R1-002 projection/cache ref attempts provenance authority → INVALID / blocked
AT14-R1-003 PURGED source ref resolves PURGED and Diary remains unchanged
AT14-R1-004 tombstoned/archived refs resolve distinct lifecycle states
AT14-R1-005 broken ref cannot trigger transcript-copy fallback
AT14-R1-006 provenance report cannot rewrite Diary source_refs/body
AT14-R1-007 all source_refs must be reported exactly once
```

R1 must not depend on UI redesign, real Conversation hard-delete implementation, Context OS retrieval, or MemoryExperience creation.

## 8. Integration Acceptance Requirements

IA must prove the product-shaped provenance path:

```text
AcceptedDiaryEntry
  ↓
source_refs
  ↓
Diary provenance resolver
  ↓
per-ref lifecycle report
  ↓
explicit detection of broken/purged sources
  ↓
Diary entry remains canonical and unrewritten
```

Minimum IA cases:

```text
TC-AT14-IA-001 accepted Diary with resolved conversation source → RESOLVED
TC-AT14-IA-002 accepted Diary with missing source fixture → MISSING detected
TC-AT14-IA-003 accepted Diary with PURGED source fixture → PURGED detected; Diary preserved
TC-AT14-IA-004 mixed refs produce per-ref states with no omission
TC-AT14-IA-005 provenance validation does not copy transcript/source content
```

## 9. Relationship to Adjacent Gates

```text
AT-13 Significant Event
  Frozen: source refs must be canonical namespace and Diary becomes canonical only after governance + durability

AT-14 Provenance
  This contract: refs must resolve to explicit lifecycle states; broken refs detected

AT-15 Diary ≠ Memory
  Future: accepted Diary and MemoryExperience creation remain separate

AT-16 Context OS retrieval
  Future: Diary content enters model only through governed Context OS assembly

AT-17 Claude migration
  Future: legacy diary-like text requires semantic reclassification
```

## 10. Freeze Decision

```text
AT-14 R0 Contract: READY FOR FREEZE ✅
Minimal Remediation: NEXT ▶ after commit
R1: HOLD ⚠️
IA: HOLD ⚠️
Final Freeze: NOT READY
```

R0 freezes the AT-14 authority law:

```text
Origin
  ≠
Provenance truth

source_refs present
  ≠
provenance validated

broken source
  ≠
silent dangling ref

PURGED source
  ≠
Diary deletion / Diary rewrite

provenance validation
  ≠
transcript reconstruction
```
