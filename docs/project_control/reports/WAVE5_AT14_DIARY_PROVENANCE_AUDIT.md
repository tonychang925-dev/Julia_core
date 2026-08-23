# Wave5 AT-14 — Diary Provenance Audit

Status: AUDIT COMPLETE / R0 REQUIRED  
Date: 2026-08-23  
Repository: `/Users/admin/julia_core`  
Branch: `cm-r0-fix`  
Audit base commit: `8224dfc`  
Acceptance item: AT-14 — Diary provenance / broken source reference detection

## 1. Gate Position

```text
AT-13 Diary Significant Event: FROZEN ✅
AT-14 Audit: COMPLETE ✅
AT-14 R0 Contract: NEXT ▶
AT-14 Minimal Remediation: HOLD ⚠️
AT-14 R1 Permanent Evidence: HOLD ⚠️
AT-14 Integration Acceptance: HOLD ⚠️
AT-14 Freeze: NOT READY
```

This audit does not implement AT-14. It identifies the provenance/source-reference authority boundary and records the gaps that must be frozen in R0 before remediation.

## 2. Numbering Decision

Some older Core architecture work-breakdown documents use `AT-14` for Effective Context Density. The current Wave5 Acceptance Program and QA gate define:

```text
AT-14 — Diary provenance
Break/remove a referenced source in a test fixture.
Reference validator detects it.
```

This audit follows the current Wave5 acceptance matrix and treats AT-14 as Diary provenance.

## 3. Audit Question

AT-14 asks whether Diary provenance can detect broken/missing source references without allowing missing evidence, copied transcript bodies, projection refs, or source deletion to rewrite canonical Diary history.

Core question:

```text
Can accepted Diary retain source_refs while a source resolver reports RESOLVED / ARCHIVED / TOMBSTONED / PURGED / MISSING explicitly, never silently dangling?
```

## 4. Source Evidence Reviewed

Architecture / QA:

```text
docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md
docs/project_control/QA_GATE.md
```

Governance contracts:

```text
docs/authority/STO_D0_DECISION_REGISTER_v1.0.md
docs/authority/WAVE5_AT13_R0_DIARY_SIGNIFICANT_EVENT_CONTRACT.md
```

Active implementation:

```text
julia_core/diary/models.py
julia_core/diary/significant_event.py
julia_core/diary/repository_protocol.py
julia_core/conversation_state/repository_protocol.py
julia_core/memory/memory_store.py
julia_core/narrative/source_awareness.py
```

Existing evidence:

```text
tests/diary/test_at13_minimal_remediation.py
tests/diary/test_at13_r1_sabotage.py
tests/diary/test_at13_ia.py
```

## 5. AT-14 Authority Boundary

AT-13 froze:

```text
source_refs must use canonical namespaces
```

AT-14 must freeze the stronger rule:

```text
source_refs namespace-valid
  ≠
source provenance verified
```

Correct provenance path:

```text
AcceptedDiaryEntry.source_refs
  ↓
Diary source resolver / provenance validator
  ↓
per-ref source state
  ↓
RESOLVED | ARCHIVED | TOMBSTONED | PURGED | MISSING / INVALID
  ↓
explicit provenance report
```

Forbidden state:

```text
source_ref → FileNotFoundError / None / silent omission / copied transcript fallback
```

## 6. Positive Findings

| Area | Status | Evidence |
| --- | --- | --- |
| AT-13 canonical namespace guard | GREEN ✅ | `validate_canonical_source_refs()` rejects projection/cache refs. |
| Diary keeps refs instead of transcript copy | GREEN ✅ | D0 §7.11 requires `Diary = reflection + provenance refs ≠ source-history duplication`. |
| Source deletion semantics exist in contract | GREEN ✅ | D0 §7.12 requires source resolver states `RESOLVED / ARCHIVED / TOMBSTONED / PURGED`. |
| Accepted Diary survives source purge | GREEN ✅ | D0 says Diary remains valid historical artifact when source is purged. |
| Active Diary entry has source_refs shape | GREEN ✅ | `AcceptedDiaryEntry.source_refs` is non-empty and typed. |

These are necessary but not sufficient for AT-14.

## 7. P0 Gaps

### P0-GAP-1 — No active Diary source resolver

Current active line has namespace validation only:

```text
conversation://...
memory://experience/...
migration://...
```

But there is no active Diary provenance resolver that reports whether each source ref is actually:

```text
RESOLVED
ARCHIVED
TOMBSTONED
PURGED
MISSING
INVALID
```

Impact:

```text
namespace-valid source_ref
  ≠
validated provenance
```

### P0-GAP-2 — Broken/missing source fixture is not detected

The AT-14 acceptance requires:

```text
Break/remove a referenced source in a test fixture.
Reference validator detects it.
```

Current tests cover fake namespace rejection, but not a canonical-looking reference whose target is missing/broken.

Impact:

```text
conversation://conv_missing/msg_404
  could pass AT-13 namespace guard
  but remain silently dangling
```

### P0-GAP-3 — Source lifecycle state is not represented in Diary provenance

D0 requires explicit lifecycle states:

```text
RESOLVED
ARCHIVED
TOMBSTONED
PURGED
```

The active Diary line does not expose a source-state value object or report that can distinguish:

```text
source available
source archived
source tombstoned
source purged
source missing
```

Impact:

```text
source deletion/purge could be confused with nonexistent evidence or system error
```

### P0-GAP-4 — Purged source semantics are not protected

D0 says a Diary does not auto-vanish when a source is purged; the source ref becomes `PURGED` and the Diary remains historical.

Active line has no test or resolver behavior proving:

```text
source_ref resolves PURGED
  ↓
Diary remains valid
  ↓
source is not copied or rewritten
```

Impact:

```text
purged source could trigger either silent Diary deletion or fake source reconstruction
```

### P0-GAP-5 — Provenance fallback could copy transcript history

D0 forbids copying dozens/hundreds of ConversationMessages into Diary for self-containment. AT-14 must ensure missing/broken refs do not cause:

```text
broken ref
  ↓
copy transcript into Diary body/provenance
  ↓
shadow transcript authority
```

Impact:

```text
Diary provenance validation could accidentally recreate Conversation authority inside Diary
```

## 8. R0 Contract Required

R0 is required before remediation.

AT-14 R0 should freeze at minimum:

```text
AT14-I01 source_refs present/namespace-valid is not provenance validation.
AT14-I02 every accepted Diary source_ref must resolve to an explicit source state.
AT14-I03 broken/missing refs must be detected, not silently omitted.
AT14-I04 PURGED/TOMBSTONED/ARCHIVED are valid lifecycle states, not generic missing errors.
AT14-I05 source purge does not delete, rewrite, or regenerate Diary.
AT14-I06 provenance validation must not copy transcript/source content into Diary.
AT14-I07 UI/cache/projection refs cannot satisfy provenance authority.
AT14-I08 AT-14 validates refs only; it does not implement AT-15/16/17.
```

## 9. Suggested Minimal Remediation Direction After R0

Do not implement during Audit. If R0 freezes the above, remediation should remain narrow:

```text
1. Add minimal SourceRefState enum/value object.
2. Add minimal DiaryProvenanceReport with per-ref results.
3. Add fixture-backed resolver protocol or function for accepted Diary entries.
4. Detect canonical-looking but missing refs as MISSING/BROKEN.
5. Preserve PURGED as explicit provenance state without deleting Diary.
6. Prove no transcript-copy fallback occurs.
```

Do not include:

```text
AT-15 Diary ≠ Memory implementation
AT-16 Context OS retrieval
AT-17 Claude migration
Diary UI redesign
Conversation deletion implementation
MemoryExperience creation
large provenance graph redesign
```

## 10. Audit Decision

```text
Audit: COMPLETE ✅
P0 gaps found: YES ⚠️
R0 required: YES ▶
Implementation: HOLD ⚠️
R1: HOLD ⚠️
IA: HOLD ⚠️
Freeze: NOT READY
```

AT-14 may proceed to R0 Contract. It must not proceed directly to implementation.
