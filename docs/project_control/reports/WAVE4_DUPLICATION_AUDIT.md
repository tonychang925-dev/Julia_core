# WAVE4 DUPLICATION AUDIT

**Status:** REPORT
**Date:** 2026-08-19
**Scope:** Wave1~3 branches vs frozen CONT-DIA semantics (`codex/dia-7/continuity-projection-r0` @ `abe3d56`)
**Method:** cross-branch `git grep` of the ten frozen object names + six RED reimplementation signals.

---

## 0. Conclusion (TL;DR)

**No duplicate implementation of frozen CONT-DIA semantics was found in Wave1~3.** The ten frozen objects are each defined exactly once (in the CONT-DIA cumulative branch or in `wave3/diary-implementation` as the authoritative DIARY-IMPL Core contract). Six RED reimplementation signals are all clean.

The only real finding is **two naming collisions** (`continuity` vs `continuity_projection`, `evolution` vs `context_evolution`) plus a **branch divergence** (CONT-DIA code not yet merged into Wave1~3). These are namespace/merge problems, not semantic duplicates — and are already addressed by CLN-01 / CLN-04.

---

## 1. Object Scan

| # | Object | Canonical definition (authority) | Redefined in Wave1~3? | Verdict |
|---|---|---|---|---|
| 1 | `ReflectionOpportunity` | `julia_core/reflection_trigger/models.py:310` (CONT-DIA-3) | NO | `KEEP` |
| 2 | `PendingOpportunity` | `julia_core/reflection_trigger/models.py:399` (CONT-DIA-3) | NO | `KEEP` |
| 3 | `ReflectionContext` | `julia_core/reflection_context/models.py:288` (CONT-DIA-4) | NO | `KEEP` |
| 4 | `ReflectionContextHandoff` | `julia_core/reflection_handoff/models.py:123` (CONT-DIA-5) | NO | `KEEP` |
| 5 | `ContinuityState` | `julia_core/continuity_projection/models.py:445` (CONT-DIA-7) | NO | `KEEP` |
| 6 | `DecisionSituation` | `julia_core/decision_invariance/models.py:83` (CONT-DIA-8) | NO | `KEEP` |
| 7 | `CandidateDecision` | `julia_core/decision_invariance/models.py:138` (CONT-DIA-8) | NO | `KEEP` |
| 8 | `AcceptedDiaryEntry` | `julia_core/diary/models.py:112` (DIARY-IMPL-DIA-1, wave3) | NO (authoritative) | `KEEP` |
| 9 | `DiaryRepository` | `julia_core/diary/repository_protocol.py:19` (DIARY-IMPL-DIA-2A, wave3) | NO (authoritative) | `KEEP` |
| 10 | `ContextLineageEdge` (Lineage) | `julia_core/context_evolution/` (CONT-DIA-6) | NO | `KEEP` |

> Note: `DiaryEntry` as a bare name does not exist — the DIARY-IMPL contract uses `DiaryCandidate` + `AcceptedDiaryEntry`. This is itself a naming point recorded for CLN-08-adjacent hardening, not a duplicate.

---

## 2. Naming Collisions (NOT semantic duplicates)

Two module-name pairs collide across the two development lines. They are **different semantics with similar names** — resolved by the PHASE_NAMESPACE_MAP, not by code deletion.

| Wave1~3 module | Semantics | CONT-DIA module | Semantics |
|---|---|---|---|
| `julia_core/continuity` | Memory continuity / recovery: `ContinuityRequest`, `ContinuityCheckpoint`, `RecoveryPlan`, `TTLPolicy`, `MemoryContinuityBinder` | `julia_core/continuity_projection` | `ContinuityState` projection (identity continuity) |
| `julia_core/evolution` | Evolution proposals: `EvolutionProposal`, `RealityFeedbackAnalyzer`, `PatternClassification` | `julia_core/context_evolution` | lineage binding to verified provenance |

Verdict for both: `KEEP` both sides. They are distinct domains (Memory recovery vs Identity continuity; proposal evolution vs context lineage). Do **not** delete either. The collision is solved by always writing `CONT-DIA-7` / `CONT-DIA-6` for the Core projection/lineage semantics, and reserving the bare `continuity`/`evolution` names for the Wave-line Memory/Evolution modules.

---

## 3. RED Reimplementation Signals

| # | RED signal | Result |
|---|---|---|
| 1 | Assistant generates its own `opportunity_id` | ✅ clean (no match in Wave1~3) |
| 2 | Assistant computes its own context identity | ✅ clean |
| 3 | Assistant defines its own lineage truth | ✅ clean |
| 4 | Diary runtime judges `ContinuityState` | ✅ clean (no `ContinuityState` ref in `julia_core/diary/`) |
| 5 | Product layer redefines `DiaryEntry` invariant | ✅ clean (single canonical definition) |
| 6 | Product layer bypasses Core `DiaryRepository` Port | ✅ clean (no `open(`/`write_text`/`PRIVATE_DATA_ROOT` in `julia_core/diary/`) |

---

## 4. Branch Divergence (handed to CLN-04)

The CONT-DIA modules (`reflection_trigger`, `reflection_context`, `reflection_handoff`, `context_evolution`, `continuity_projection`, `decision_invariance`, `assistant_continuity`) exist **only** on `codex/dia-7/continuity-projection-r0`, and are **not present** in `wave1/*`, `wave2/*`, or `wave3/diary-implementation`. This is a merge gap, not a duplicate. It means the Storage/Diary product line has not yet consumed the CONT-DIA Core semantics — which is exactly what Wave4 must do (via REUSE/ADAPTER, per CLN-02).

---

## 5. Classification Summary

| Classification | Objects |
|---|---|
| `KEEP` | all 10 scanned objects + both Wave-line `continuity`/`evolution` modules |
| `DELETE` | (none found) |
| `REPLACE_WITH_CORE` | (none found) |
| `ADAPTER_ONLY` | (none required yet — product trigger runtime is not yet implemented) |
| `LEGACY` | (none found) |

No `DUPLICATE-CANDIDATE` remains open.
