# WAVE5 RC1 Baseline Freeze Record

**Status:** RC1 BASELINE FROZEN
**Date:** 2026-08-25

This record pins the Wave5 RC1 authority baseline before any `main` pointer
mutation. It is the recovery anchor.

---

## Wave5 FINAL

**NO.** This is the RC1 authority baseline freeze, **not** the Wave5 final
freeze. Later waves may add verified evidence on top of this baseline.

## Pinned SHAs

| Object | SHA |
|---|---|
| Julia_core candidate before freeze | `6e598143e24ce20697c9e49de0f626ce679912ca` |
| Main pre-transition | `ffc7c3818de291048c07424ee3223fb583ea24c4` |

## Topology

`main` (`ffc7c381`) is a **strict ancestor** of
`wave5/authority-consolidation`. Fast-forward is technically valid:
ahead 150 / behind 0, no branch protection, no CI, no submodule, no hardcoded
`main` dependency.

## Known Exclusions

Preserved per `WAVE5_RC1_EXCLUSION_REGISTER.md` — identity fallback, runtime
state, AT17 archive, draft/superseded docs, review candidates, implementation
plan, duplicate files, density experiment.

## D1 Execution

`main` pointer mutation (fast-forward to the frozen baseline) is **not part of
baseline identity**. The baseline is this commit itself; `main` may advance
afterward without changing what RC1 froze.

## Recovery Anchor

The immutable annotated tag `wave5-rc1-authority-baseline-20260825` points to
this commit. Rollback to this tag restores the full RC1 authority lineage
independent of any subsequent `main` movement.
