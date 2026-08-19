# CLN-09 — Persistence / Authority Matrix

**Status:** CANONICAL (verification + authority freeze)
**Date:** 2026-08-19
**Scope:** conversation / diary / continuity persistence authority

---

## 0. Governing Principle

```text
Core defines meaning.
Persistence stores artifact.
Runtime consumes truth.
```

Persistence is **never** a semantic owner. It stores bytes and validates integrity — it does not decide `accepted/rejected`, does not reconstruct meaning, does not decide cognitive admissibility.

---

## 1. Conversation Persistence Authority

Frozen boundary (already enforced in code by W4-BASE-R2/R3):

```text
Canonical Conversation Store   ≠   Context OS History Projection
```

| Concern | Owner | Surface |
|---|---|---|
| Message truth (transcript) | Core `ConversationRuntime` + `ConversationMessage` | `conversation_state` repository |
| Raw transcript read (all statuses) | Core | `ConversationRuntime.get_messages()` |
| Cognitive admissibility (completed-only) | Core Context OS | `ConversationRuntime.get_canonical_history()` |

- The store persists `completed / interrupted / failed / pending` — it does **not** decide what is admissible.
- The projection selects `completed` only — it does **not** rewrite the transcript.

---

## 2. Diary Authority

Frozen boundary:

```text
Governance decides.  Persistence stores.
```

| Concern | Owner | Surface |
|---|---|---|
| Diary semantics (shape) | Core | `julia_core/diary/models.py` (`DiaryCandidate`, `AcceptedDiaryEntry`) |
| Repository contract | Core | `julia_core/diary/repository_protocol.py` (`DiaryRepository` Port) |
| accepted / rejected decision | Governance (DIA-6) | (separate governance gate) |
| Physical durability | Assistant adapter (DIA-2) | concrete JSON/Markdown/SQLite (not yet implemented) |

- `AcceptedDiaryEntry.governance_status` is frozen to `"accepted"` — a persistence layer **cannot** manufacture accepted truth by writing a record.
- `diary/models.py` explicitly forbids "filesystem I/O, persistence, governance execution, Memory".

---

## 3. Continuity Artifact Persistence

Frozen boundary:

```text
Core defines ContinuityState / DecisionInvariant meaning.
Persistence stores a snapshot and validates integrity.
Persistence does NOT reconstruct meaning.
```

| Concern | Owner | Surface |
|---|---|---|
| `ContinuityState` semantics | Core CONT-DIA-7 | `julia_core/continuity_projection/models.py` |
| `DecisionInvariant` semantics | Core CONT-DIA-8 | `julia_core/decision_invariance/models.py` |
| Snapshot persistence | Core persistence module | `julia_core/continuity_persistence/models.py` |
| Integrity validation | Core persistence module | `_validate_reconstructed_state_header()` — digest cross-check, not meaning |

- `continuity_persistence` treats stored bytes as "untrusted until deserialized, reconstructed, and cross-validated" — validation is digest integrity, never semantic re-derivation.

---

## 4. RED-DP1 check

| Signal | Result |
|---|---|
| `repository.save()` / append decides `approve` / `reject` | ✅ clean — no persistence layer performs governance |
| Storage layer reconstructs meaning | ✅ clean — persistence validates digests, never re-derives semantics |
| Storage layer becomes semantic owner | ✅ clean — all three lanes keep `Core defines / persistence stores` separation |

---

## 5. Authority Summary Table

| Artifact | Semantic owner | Persistence owner | Admissibility owner |
|---|---|---|---|
| ConversationMessage | Core `ConversationRuntime` | `conversation_state` repository | Context OS (completed projection) |
| `DiaryCandidate` / `AcceptedDiaryEntry` | Core `diary/models.py` | Assistant adapter | Governance (DIA-6) |
| `ContinuityState` | Core CONT-DIA-7 | `continuity_persistence` (snapshot) | Core continuity projection |
| `DecisionInvariant` | Core CONT-DIA-8 | `continuity_persistence` (snapshot) | Core decision evaluator |

No lane lets persistence silently own meaning.

---

## 6. Conclusion

Persistence/Authority matrix verified **GREEN** — zero RED-DP. The three frozen boundaries (`Store ≠ Projection`, `Governance decides / Persistence stores`, `persistence validates not reconstructs`) hold in the current merged codebase.
