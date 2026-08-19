# PHASE NAMESPACE MAP

**Status:** CANONICAL
**Date:** 2026-08-19
**Purpose:** Resolve the three-way `DIA-N` numbering collision that has caused duplicate-implementation risk across Wave1~3 and the Continuity-DIA line. From this document onward, **no report, commit message, or code comment may use a bare `DIA-N` token.**

---

## 1. The Three Namespaces

There are exactly three independent `DIA` numbering spaces in this program. They are **not** the same phase sequence and must never be merged or cross-referenced by bare number.

### Namespace A — `CONT-DIA` (Core continuity / identity semantics)

- **Owner:** `julia_core` — frozen semantic contracts.
- **Meaning:** the canonical Continuity/Identity/Decision semantics that product runtimes **consume**, never redefine.
- **Branches:** `codex/dia-3/*` … `codex/dia-7/*`.

| Canonical phase | Branch (latest) | Head | Content |
|---|---|---|---|
| `CONT-DIA-3` | `codex/dia-3/reflection-trigger-r1` | `659594f` | `ReflectionOpportunity` identity, `PendingOpportunity` semantics, trigger admission state |
| `CONT-DIA-3-R2` | `codex/dia-3/trigger-state-runtime-r2` | `bfc76ac` | trigger-state persistence adapter |
| `CONT-DIA-4` | `codex/dia-4/reflection-context-r1` | `017ba4e` | `ReflectionContext` assembly / serialization |
| `CONT-DIA-5` | `codex/dia-5/reflection-handoff-r1` | `f829208` | reflection context handoff |
| `CONT-DIA-6` | `codex/dia-6/context-evolution-r1` | `393491a` | evolution / lineage binding to provenance |
| `CONT-DIA-7` | `codex/dia-7/continuity-projection-r0` | `abe3d56` | `ContinuityState` projection |
| `CONT-DIA-8` | `codex/dia-7/continuity-projection-r0` | `abe3d56` | decision invariance (`DecisionSituation` / `CandidateDecision` / evaluator) |

> `codex/dia-7/continuity-projection-r0` is the **cumulative authority branch** for CONT-DIA-3..8. The earlier `codex/dia-3/4/5/6` branches are per-phase snapshots; the cumulative branch is the production truth.

### Namespace B — `STORAGE-DIA` (Diary product roadmap)

- **Owner:** the Storage & Diary Development Plan (`docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md`).
- **Meaning:** high-level **work breakdown** for the Diary product lifecycle. This is a **roadmap**, not an implementation namespace.
- **Branches:** none directly — it decomposes into Wave1~3 (conversation/diary storage) plus product diary work.

| Canonical phase | Content |
|---|---|
| `STORAGE-DIA-0` | Claude Julia diary audit & reclassification |
| `STORAGE-DIA-1` | diary domain contract |
| `STORAGE-DIA-2` | diary persistence |
| `STORAGE-DIA-3` | reflection trigger runtime (product adapter) |
| `STORAGE-DIA-4` | reflection context assembly |
| `STORAGE-DIA-5` | Julia reflection generation |
| `STORAGE-DIA-6` | reflection governance |
| `STORAGE-DIA-7` | diary retrieval / context integration |
| `STORAGE-DIA-8` | **Electron diary UI** (NOT decision invariance) |

### Namespace C — `DIARY-IMPL` (Diary product implementation)

- **Owner:** `julia_core` Core ports + `Julia-AI-Assistant` persistence adapters.
- **Meaning:** the actual Diary implementation artifacts (Core `DiaryRepository` port + Assistant persistence).
- **Branches:** `wave3/diary-*`.

| Canonical phase | Branch | Head | Content |
|---|---|---|---|
| `DIARY-IMPL-DIA-1` | `wave3/diary-implementation` | `33d4903` | `DiaryEntry` / `AcceptedDiaryEntry` primitive (exact, reject subclass spoof) |
| `DIARY-IMPL-DIA-2A` | `wave3/diary-implementation` | `33d4903` | Core `DiaryRepository` Port (application-agnostic) |
| `DIARY-IMPL-DIA-2B` | `wave3/diary-implementation` | `33d4903` | Assistant persistence reality audit / adapter |
| `DIARY-IMPL-CG-01` | `wave3/diary-implementation` | `33d4903` | adjudication seal (reinterprets semantics) |

---

## 2. Branch → Namespace Mapping (complete)

| Branch | Namespace | Role |
|---|---|---|
| `codex/dia-3/reflection-trigger-r1` | `CONT-DIA-3` | Core semantics (snapshot) |
| `codex/dia-3/trigger-state-runtime-r2` | `CONT-DIA-3-R2` | Core semantics (snapshot) |
| `codex/dia-4/reflection-context-r1` | `CONT-DIA-4` | Core semantics (snapshot) |
| `codex/dia-5/reflection-handoff-r1` | `CONT-DIA-5` | Core semantics (snapshot) |
| `codex/dia-6/context-evolution-r1` | `CONT-DIA-6` | Core semantics (snapshot) |
| `codex/dia-7/continuity-projection-r0` | `CONT-DIA-3..8` | **Core semantics (cumulative authority)** |
| `wave0-closeout` | STORAGE Wave0 | Authority & contracts (frozen) |
| `wave1/sto-f2a-core`, `wave1/sto-f2a-r3`, `wave1/cm-s1-protocol-freeze` | STORAGE Wave1 | Conversation storage |
| `wave2/conversation-management-*` | STORAGE Wave2 | Conversation management |
| `wave3/diary-reflection-protocol-freeze` | `DIARY-IMPL` | Diary/reflection protocol |
| `wave3/diary-implementation` | `DIARY-IMPL` | Diary product implementation |
| `cm-r0-fix` | repository authority | Julia_core canonical branch |
| `main` | legacy/default | not production authority for CONT-DIA |

---

## 3. Report Naming Rule

From this document onward, **bare `DIA-N` is forbidden** in any report, commit message, code comment, or architecture note.

| If you mean… | You MUST write… |
|---|---|
| Core decision invariance | `CONT-DIA-8` |
| Storage plan "Electron Diary UI" | `STORAGE-DIA-8` |
| Diary repository port | `DIARY-IMPL-DIA-2A` |
| Core reflection trigger | `CONT-DIA-3` |
| Storage plan "Reflection Trigger Runtime" | `STORAGE-DIA-3` |

A bare token like `DIA-8` is ambiguous between `CONT-DIA-8` (decision invariance) and `STORAGE-DIA-8` (Electron diary UI) — the two are unrelated. This ambiguity is exactly what caused prior confusion and duplicate-implementation risk.

---

## 4. Acceptance

- [x] Three namespaces defined (`CONT-DIA`, `STORAGE-DIA`, `DIARY-IMPL`)
- [x] Branch → namespace mapping complete
- [x] Report naming rule defined (full-name tokens only)
- [x] Bare `DIA-N` banned in future documents
