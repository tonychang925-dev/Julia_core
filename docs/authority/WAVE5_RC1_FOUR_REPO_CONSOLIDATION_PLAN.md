# WAVE5 RC1 Four Repo Consolidation Plan

**Status:** DRAFT FOR REVIEW
**Date:** 2026-08-25
**Author:** Julia (work-assistant, with Tony)
**Purpose:** Define how the four Wave5 repos consolidate into a governed
main-lineage, with an explicit boundary for Brain (which requires runtime
authority reconciliation, not a Git merge).

**Note:** This is a plan, not a merge. No code, branch, or runtime state is
modified by this document. All figures below are read-only audit results
captured 2026-08-25.

---

## 1. Current Authority Matrix (audit snapshot)

**Snapshot timestamp:** 2026-08-25 16:17 +0800

This matrix records the repo state *at the time of the read-only audit*, not a
final conclusion. D1/D5 may change how `main↔RC1` is interpreted; the snapshot
observation itself remains valid regardless.

| Repo | Remote | RC1 branch | HEAD | main HEAD | main↔RC1 | ahead/behind | dirty |
|---|---|---|---|---|---|---|---|
| Julia_core | `Julia_core` | `wave5/authority-consolidation` | `989b5a9` | `5bc33ba` | non-ancestor divergence observed at audit snapshot | 154 / 4 | exclusion-registered only |
| Voice-S2S | `Julia-Voice-S2S` | `phase5/rmd-3g-observability` | `cbbb10a` | `ad21dad` (origin/main) | **correction:** origin/main advanced by `ad21dad`; non-ancestor divergence observed | 0/0 (vs origin/phase5); 1/77 (vs origin/main) | clean |
| Electron | `Julia_client` (julia_electron_v2) | `fix/voice-ws-lifecycle-001` | `7a9506d` | `c44bb7e` | main is ancestor (observed) | 0 / 0 | clean |
| Brain (source) | `Julia-AI-Assistant` | `phase5/rmd-3g-observability` | `47a3e4a` | `accc977` | — | 8 / 2 | **runtime code modified** |
| Brain (runtime) | worktree `julia_ai_assistant_rmd3g_prod` | (detached HEAD) | `bbd90af` | — | not ancestor of local source HEAD (observed) | — | runtime artifacts |

**Corrections vs prior records (must propagate):**

1. Julia_core `main` HEAD is `5bc33ba`, **not** `ffc7c38` (as previously
   recorded). Needs confirmation whether main was updated post-RC1.
2. Brain source is **ahead 8 / behind 2**, not "behind 8" as previously
   recorded. The old description is stale and must be updated everywhere.
3. Brain source has **uncommitted runtime code changes**
   (`M runtime/assistant_runtime.py`, `M memory/claude_diary/julia_character.md`,
   `?? providers/llm/claude_provider.py`). These cannot enter reconciliation
   without first being classified.
4. **Voice-S2S ff eligibility was superseded.** The original Phase A assessment
   was based on the local `main` snapshot (`4b4154e`); the remote `origin/main`
   has since advanced to `ad21dad` (`ADR-VOICE-C1B-R`). This is not a
   contradiction in the audit — the authority state changed after the initial
   snapshot. Current assessment supersedes the previous one.

---

## 2. Authority Precedence Rule (Global Consolidation Principle)

This rule applies to **all four repos**, not just Brain. Whenever source
lineage and a runtime deployment diverge, the following order holds:

1. **Preserve verified runtime behavior** — AT-20/AT-21 continuity is the
   validated truth; it is not to be regressed by source reconciliation.
2. **Preserve rollback point** — the running deployment's current commit is the
   rollback anchor. Do not move it without a recorded replacement.
3. **Reconcile source lineage before merge** — source must be mapped back onto
   runtime authority first; merge follows reconciliation, never precedes it.
4. **Never overwrite runtime authority by source guess** — a newer Git commit
   does not, by itself, outrank a verified running deployment.

This principle exists to prevent the default intuition that "source moved, so
runtime should follow source." The reverse is true: verified runtime defines
authority; source lineage is reconciled to match it.

---

## 3. Merge Candidates

### Phase A — Safe fast-forward merges

A repo is *eligible* for `git merge --ff-only` only when `main` is a direct
ancestor of the RC1 branch. Eligibility is **not** approval — no merge is
authorized by this document.

| Repo | Action | Command (illustrative, NOT executed) |
|---|---|---|
| Electron (Julia_client) | ff `fix/voice-ws-lifecycle-001` → `main` | `git checkout main && git merge --ff-only fix/voice-ws-lifecycle-001` |

**Precondition (D4):** Electron `main` is confirmed clean and equal to
`origin/main` (`c44bb7e`), `0 / 0`. This is the only remaining ff-eligible
candidate.

**No merge operation is authorized by this document.**

### Phase B — Reconciliation merges

Two repos now require reconciliation (not fast-forward):

**Voice-S2S** — `origin/main` advanced to `ad21dad` (ADR-VOICE-C1B-R) after the
initial snapshot, so `origin/main` is no longer an ancestor of
`phase5/rmd-3g-observability`. Divergence:

```
4b4154e  (common ancestor)
 ├─ ad21dad  → origin/main   (ADR doc, 1 commit)
 └─ cbbb10a  → phase5/rmd-3g-observability  (77 commits)
```

Required: decide whether `ad21dad` is preserved/merged/superseded, then
reconcile `phase5` onto `origin/main`. See D4.

**Julia_core** — `wave5/authority-consolidation` and `main` are true divergent
branches (154 vs 4 commits, no ancestor relationship). This is **not** a
fast-forward.

Required:
- Review of 154 wave5 commits (authority lineage is 6 commits on top of a long
  wave5 history; the RC1 governance slice is `935b231..989b5a9`).
- Review of 4 main-only commits — what are they? Do they overlap or conflict?
- A merge PR (or release branch) that preserves review, not a silent merge.

**Open question:** what are the 4 `main`-only commits? Must be enumerated
before merge strategy is finalized.

### Phase C — Brain Runtime Authority Reconciliation (NOT a merge)

Brain must not be merged as a normal Git operation. The core fact:

```
runtime authority  bbd90af
  ├─ is ancestor of main                    ✅
  ├─ is ancestor of origin/phase5           ✅
  └─ is NOT ancestor of local source HEAD   ❌  (47a3e4a)
```

The production runtime runs a commit that is already reconciled into
`main` and `origin/phase5`, but the **local source checkout `47a3e4a` has
diverged onto a parallel development line** that lacks the authority commits
(`44cea89` closeout, `197ada9` reconcile, `78f267c` CURRENT_AUTHORITY).

This is a **runtime truth vs source truth** problem, not a merge problem.
The authoritative reconciliation procedure is defined in §4 (Brain
Reconciliation Boundary); this section is a summary only.

---

## 4. Brain Reconciliation Boundary

**Hard constraint:** runtime truth is authoritative over source truth.
AT-20/AT-21 continuity verification protects the running system; the goal of
this phase is to map source lineage back onto runtime authority without
disturbing the running deployment.

Steps (illustrative, NOT executed):

1. **Preserve runtime state** — `bbd90af` is the authority. Do not checkout,
   reset, or delete anything under `julia_ai_assistant_rmd3g_prod`.
2. **Classify source dirty files** — before any branch movement:
   - `M runtime/assistant_runtime.py` — is this part of runtime authority, or
     experimental residue? Diff first, decide later.
   - `M memory/claude_diary/julia_character.md` — identity content; must not be
     silently dropped or silently committed.
   - `?? providers/llm/claude_provider.py` — new provider file; separate wave?
3. **Rebase/reconcile source onto origin/phase5 tip `44cea89`** — the line that
   has already absorbed `bbd90af`. Only after dirty files are classified.
4. **Confirm `bbd90af` becomes a source ancestor** before any main promotion.

**Do NOT:**
- `git merge` Brain into main while source HEAD diverges from runtime.
- Move the runtime worktree off `bbd90af`.
- Commit the dirty `assistant_runtime.py` as-is.

---

## 5. Open Decisions (must be resolved by Tony)

| # | Decision | Blocking |
|---|---|---|
| D1 | Julia_core `main` = `5bc33ba` — confirm whether main moved post-RC1 and what it contains | Phase B |
| D2 | Brain source ahead/behind correction (8/2, not behind-8) — propagate to all prior docs | Phase C |
| D3 | Brain dirty `assistant_runtime.py` — runtime-authority or experiment residue? | Phase C |
| D4 | Voice-S2S main divergence — `ad21dad` (ADR-VOICE-C1B-R) detected after previous snapshot. Should it be preserved, merged, or superseded during reconciliation? | Voice-S2S consolidation |
| D5 | Julia_core 4 main-only commits — enumerate and review | Phase B |
| D6 | Consolidation Authority Acceptance — has the four-repo authority matrix been accepted as the basis for merge execution? | All merge phases |

D6 is the gate that converts this plan from a draft into an execution basis.
Committing this document does **not** imply D6 is resolved; D6 is OPEN until
Tony explicitly accepts the matrix.

---

## 6. Execution Order

```
0. Resolve D6 → authority matrix accepted            [gate: no merge before this]
1. Resolve D4 → Phase A (Electron ff) + Voice-S2S reconciliation decision
2. Resolve D1 + D5 → Phase B (Julia_core merge PR)    [requires review]
3. Resolve D2 + D3 → Phase C (Brain reconciliation)   [runtime truth first]
```

No merge begins until D6 (authority acceptance) and its phase-specific blocking
decisions are resolved. This plan is the artifact; the next step is decision,
not action.
