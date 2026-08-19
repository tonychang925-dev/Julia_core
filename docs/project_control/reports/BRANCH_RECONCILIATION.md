# BRANCH REALITY RECONCILIATION

**Status:** REPORT (CLN-04)
**Date:** 2026-08-19
**Purpose:** One authoritative table of every active branch — so Wave4 never starts with "this capability might be on some old branch". Each production truth is pinned to exactly one SHA.

> **Retire = YES below is a recommendation only.** Actual branch deletion is a destructive op and requires explicit Tony approval. Nothing here was deleted.

---

## 1. Branch Reconciliation Table

| Branch | HEAD | Purpose | frozen? | superseded? | unique production code? | merge target | retire? |
|---|---|---|---|---|---|---|---|
| `cm-r0-fix` | `ea32072` | Julia_core repository authority | NO | NO | YES (authority manifests/docs) | — | NO |
| `main` | `5bc33ba` | legacy default | NO | YES (by `cm-r0-fix`) | NO | `cm-r0-fix` | YES |
| `wave0-closeout` | `c5f0fbd` | Wave0 authority & contracts closure | YES | NO | YES (W0-1..W0-6 PASS record) | — | NO |
| `sto-d0` / `sto-d0-integrate` / `sto-f1` / `sto-f1-integrate` / `sto-f2` / `sto-f2-integrate` | (various) | Wave0 subtasks | YES | YES (folded into `wave0-closeout`) | NO | `wave0-closeout` | YES |
| `wave1/sto-f2a-core` | `d62aabf` | Wave1 F2a ConversationRuntime DI | NO | NO | YES | Wave1 integration | NO |
| `wave1/sto-f2a-r3` | `782865d` | Wave1 F2a R3 recovery hold | NO | NO | YES | Wave1 integration | NO |
| `wave1/cm-s1-protocol-freeze` | `f1d5734` | Wave1 CM-S1 protocol freeze | NO | NO | YES | Wave1 integration | NO |
| `wave2/conversation-management-protocol-freeze` | `6d4cfe7` | Wave2 management protocol | NO | NO | YES | Wave2 integration | NO |
| `wave2/conversation-management-implementation` | `ef4657e` | Wave2 management impl | NO | NO | YES | Wave2 integration | NO |
| `wave3/diary-reflection-protocol-freeze` | `7221bbb` | Wave3 diary/reflection protocol | NO | NO | YES | Wave3 integration | NO |
| `wave3/diary-implementation` | `33d4903` | Wave3 diary impl (`DIARY-IMPL-DIA-1/2`) | NO | NO | YES | Wave3 integration | NO |
| `codex/dia-3/reflection-trigger-r1` | `659594f` | CONT-DIA-3 snapshot | YES | YES (in dia-7) | NO | `codex/dia-7/continuity-projection-r0` | YES |
| `codex/dia-3/trigger-state-runtime-r2` | `bfc76ac` | CONT-DIA-3-R2 snapshot | YES | YES | NO | `codex/dia-7/continuity-projection-r0` | YES |
| `codex/dia-4/reflection-context-r1` | `017ba4e` | CONT-DIA-4 snapshot | YES | YES | NO | `codex/dia-7/continuity-projection-r0` | YES |
| `codex/dia-5/reflection-handoff-r1` | `f829208` | CONT-DIA-5 snapshot | YES | YES | NO | `codex/dia-7/continuity-projection-r0` | YES |
| `codex/dia-6/context-evolution-r1` | `393491a` | CONT-DIA-6 snapshot | YES | YES | NO | `codex/dia-7/continuity-projection-r0` | YES |
| `codex/dia-7/continuity-projection-r0` | `abe3d56` | **CONT-DIA-3..8 cumulative authority** | YES (frozen semantics) | NO | YES | — | NO |
| `phase5/cc-1-conversation-convergence` | `eedbaca` | phase5 conversation convergence | NO | NO | YES | (outside Wave4 scope) | NO |
| `phase5/rmd-1-cancel-durability` | `b463a3f` | phase5 cancel durability | NO | NO | YES | (outside Wave4 scope) | NO |
| `codex/bugfix/m3-3-0c-runtime-integrity` | `2541935` | M3.3.0c runtime integrity | NO | NO | YES | (outside Wave4 scope) | NO |
| `codex/bugfix/provider-fallback-chat-copy` | `a12ced4` | provider fallback | NO | NO | YES | (outside Wave4 scope) | NO |

---

## 2. Pinned Production Truth (authoritative SHAs)

| Capability | Authoritative SHA | Branch |
|---|---|---|
| CONT-DIA-3..8 (all Core continuity/identity/decision semantics) | `abe3d563f20fb8bf71f76176b8616222c28f2362` | `codex/dia-7/continuity-projection-r0` |
| Wave0 authority & contracts | `c5f0fbd` | `wave0-closeout` |
| Wave1 conversation storage | `d62aabf` (F2a-core), `782865d` (F2a-r3), `f1d5734` (protocol) | `wave1/*` |
| Wave2 conversation management | `6d4cfe7` (protocol), `ef4657e` (impl) | `wave2/*` |
| Wave3 diary | `7221bbb` (protocol), `33d4903` (impl) | `wave3/*` |
| DIARY-IMPL-DIA-1/2 (DiaryEntry + DiaryRepository) | `33d4903` | `wave3/diary-implementation` |

---

## 3. Ancestry Confirmation

Verified: each of `codex/dia-3/4/5/6` HEAD commits is an ancestor of `codex/dia-7/continuity-projection-r0`. Therefore `codex/dia-7` is a true cumulative authority and the per-phase `dia-3..6` branches carry **no unique production code** — they are safe to retire (with approval).

---

## 4. Open Questions for Tony (before Wave4)

1. **Wave1/2/3 integration ordering** — the three wave branches are parallel and not yet merged into any single integration branch. Which branch is the Wave4 base? (Recommend: a new `wave4` integration branch off `cm-r0-fix`, consuming CONT-DIA via merge of `codex/dia-7` + Wave1/2/3 heads.)
2. **`main` retirement** — `main` (`5bc33ba`) is superseded by `cm-r0-fix` and should be retired or repointed, but this needs explicit approval.
3. **CONT-DIA merge into Wave line** — confirmed NOT yet merged (see CLN-03 §4). Wave4 must merge `abe3d56` before product runtime can consume CONT-DIA.
