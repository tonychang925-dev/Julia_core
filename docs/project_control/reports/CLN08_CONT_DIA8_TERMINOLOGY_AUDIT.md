# CLN-08 — CONT-DIA-8 Terminology Hardening (Audit)

**Status:** AUDIT (no code change)
**Date:** 2026-08-19
**Scope:** terminology / namespace audit of `DIA-8` references across docs

---

## Verdict: ✅ GREEN — no RED-TM violation (no cross-namespace mis-citation)

No document mis-attributes `STORAGE-DIA-8` as decision invariance, nor `CONT-DIA-8` as the Electron Diary UI. Decision invariance is never described as personality generation or emotion simulation.

---

## 1. RED-TM signals — all clean

| Signal | Result |
|---|---|
| RED-TM1 — `STORAGE-DIA-8` cited as Continuity-to-Decision Invariance (or reverse) | ✅ clean — `STORAGE-DIA-8` consistently = Electron Diary UI; `CONT-DIA-8` consistently = decision invariance |
| RED-TM2 — a doc writes "DIA-8 = Julia Diary UI" but actually refers to decision invariance | ✅ clean — the only "DIA-8 = Electron Diary UI" occurrences are inside the Storage Plan (STORAGE-DIA namespace), which is correct |
| RED-TM3 — decision invariance described as personality generation / emotion simulation | ✅ clean — zero matches |

---

## 2. Attendant finding (namespace, not mis-citation)

`docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md` body contains **59 bare `DIA-N` tokens** (e.g. `DIA-0 … DIA-8`, `# 22. DIA-8 — Electron Diary UI`, `## DIA-3-T01 …`). These are all STORAGE-DIA, but are written without the `STORAGE-` prefix, violating the CLN-01 rule "bare `DIA-N` is forbidden".

This is the same ambiguity the namespace map was built to kill — a bare `DIA-8` inside the Storage Plan reads identically to `CONT-DIA-8` unless the reader already knows the file's namespace (the header added in CLN-05).

**Recommendation:** mechanical `DIA-N` → `STORAGE-DIA-N` prefix pass over the Storage Plan body (doc-only, no semantic change). Flagging here rather than silently rewriting, per P1 "verification by default" discipline.

---

## 3. Conclusion

CONT-DIA-8 terminology is clean: no cross-namespace mis-citation, no semantic mis-description. One namespace-hardening follow-up is identified (59 bare `DIA-N` in the Storage Plan body), recommended as a doc-only prefix pass.
