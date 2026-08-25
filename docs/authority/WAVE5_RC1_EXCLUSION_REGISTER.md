# WAVE5 RC1 Exclusion Register

**Status:** RC1 Governance Record
**Date:** 2026-08-25
**Purpose:** Record artifacts intentionally excluded from the Wave5 RC1 baseline.

This register documents *what did not enter RC1* and *why*. It is the boundary
that separates RC1 authority from workspace residue. Every excluded item maps to
a reason; none are "discarded" — they are deferred to a later governance wave.

---

## 1. Identity pending

| Artifact | Reason | Decision |
|---|---|---|
| `julia_agent_server.py` (fallback prompt diff) | Hardcoded relationship anchor ("Tony对你说：…") is ungoverned identity content; duplicates Context OS identity_source | Pending `IDENTITY-SOURCE-CONSOLIDATION-001` |

The fallback prompt contains a relation-affirmative anchor that is neither
identity policy nor governed continuity. It is excluded from RC1 authority
until identity source-of-truth is consolidated onto Context OS frames.

## 2. Runtime state

| Artifact | Reason |
|---|---|
| `data/conversations.json` | Runtime-generated conversation state |
| `data/events/*.jsonl` | Runtime-generated event stream |
| `evidence/BASELINE_E2E_CONVERSATION.json` | Runtime E2E baseline (timestamp noise) |

**Reason:** Runtime generated state, not source lineage. These are not
authoritative documents; they are the *output* of the runtime RC1 protects.

## 3. AT17 archive

| Artifact | Reason |
|---|---|
| `at17_test_harness/evidence/*` (15 DRYRUN + report) | Historical validation artifact |

**Reason:** Historical validation asset. Outside the RC1 runtime baseline.
Retain as archive evidence; do not promote to baseline.

## 4. Draft / superseded documents

| Artifact | Reason |
|---|---|
| `docs/architecture/JULIA_CONVERSATION_MANAGEMENT_UNIFIED_ARCHITECTURE_v1.1_DRAFT.md` | DRAFT / CODE HOLD |
| `docs/architecture/JULIA_CONVERSATION_MANAGEMENT_UNIFIED_ARCHITECTURE_v1.1_FREEZE_CANDIDATE.md` | Filename says freeze; content Status still DRAFT |
| `docs/architecture/JULIA_PHASE5_FOUR_REPO_DEVELOPMENT_PLAN_v1.0_DRAFT.md` | DRAFT / CODE HOLD |
| `docs/audit/FRA_DRAFT1_ADDENDUM.md` | DRAFT addendum |
| `docs/audit/FRA_DRAFT1_2_ADDENDUM.md` | DRAFT addendum |
| `docs/audit/FRA_D2L_MATRIX.md` (v1) | Superseded — v2 declares "Replaces D2-L v1" |

**Reason:** Not approved authority documents. RC1 contains only current,
frozen authority; drafts and superseded versions are excluded to avoid
dual-version ambiguity.

## 5. Review candidates

| Artifact | Reason |
|---|---|
| `docs/architecture/JULIA_PHASE5_AUTHORITY_RECONCILIATION_REGISTER_v1.0_FINAL_REVIEW.md` | FINAL REVIEW CANDIDATE |
| `docs/architecture/JULIA_PHASE5_FOUR_REPO_DEVELOPMENT_PLAN_v1.2_FINAL_FREEZE_CANDIDATE.md` | FINAL FREEZE CANDIDATE / READY FOR TONY |
| `docs/architecture/JULIA_WAVE_B_EXACT_PATCH_MAP_v1.0_FINAL_REVIEW.md` | FINAL REVIEW / READY FOR TONY GO |

**Reason:** `READY FOR TONY` ≠ `APPROVED`. The state chain is DRAFT →
FINAL_REVIEW → READY FOR APPROVAL → APPROVED/FROZEN. RC1 contains only the
final state. These remain excluded pending explicit Tony approval.

## 6. Implementation plan (not frozen authority)

| Artifact | Reason |
|---|---|
| `docs/architecture/Julia_Continuity_MVP_Implementation_Plan_v1.0.md` | Implementation plan; not frozen authority |

**Reason:** A development plan, not an authority/freeze/audit record. Excluded
from RC1 authority scope.

## 7. Duplicate files

| Artifact | Reason |
|---|---|
| `docs/architecture/JULIA_CONVERSATION_MANAGEMENT_UNIFIED_ARCHITECTURE_v1.1 (1).md` | Content differs from tracked FINAL_FREEZE_CANDIDATE (RMD-3A released, no CC-2) — historical node, not duplicate |
| `docs/architecture/JULIA_CONVERSATION_MANAGEMENT_UNIFIED_ARCHITECTURE_v1.1_DRAFT (1).md` | Byte-identical to `_DRAFT.md` |
| `docs/architecture/JULIA_PERSONALITY_MIGRATION_ABLATION_REPORT_v1 (1).md` | Byte-identical to tracked `docs/verification/...v1.md` |

**Reason:** `(1)`-suffixed files are byte-identical duplicates with no authority
value. Exception: `..._v1.1 (1).md` is *not* a byte-duplicate — it represents a
distinct historical node (RMD-3A released) and is retained as archive, not RC1
authority.

## 8. Density experiment

| Artifact | Reason |
|---|---|
| `julia_core/context_assembly/density_restorer.py` | Experimental capability |
| `scripts/extract_density_from_session.py` | Experimental capability |
| `artifacts/density/*` (profile + 1.1MB jsonl + context md) | Experimental artifact |

**Reason:** Experimental capability with **no RC1 validation coverage**.
AT-20 / AT-21 / AT-21V do not verify density recovery. It is an optional
extension point (runtime wraps it in try/except with silent fallback), not an
RC1 runtime dependency. Deferred to a separate wave (`DENSITY-RECOVERY-001`).

**Note:** "excluded from RC1 scope" ≠ "discarded". This is not a value judgment
on the density mechanism; it is a scope boundary.
