# STORAGE-DIA-7-R2-R0 — Context Admission Contract v1.0

**Status:** CONTRACT (pre-implementation freeze)
**Date:** 2026-08-21
**Program:** Julia Diary — Context OS admission boundary
**Authority chain:** DiaryContextSource (ranking) → Context OS (admission) → Runtime (consumption)
**Basis:** W3_A5_DIARY_RETRIEVAL_PROTOCOL + Core `ContextBlock` + DIA-7-R0/R1

---

## 0. Iron Rule

```text
Retrieval decides candidates.
Context OS decides visibility.
Projection carries evidence.
No component creates new truth.
```

```
AcceptedDiaryEntry  →  persistence truth
DiaryContextSource  →  ranking authority ("which may be relevant")
Context OS          →  admission authority ("which enters model view")
Runtime / LLM       →  consumption
```

---

## 1. Three-Tier Authority (frozen)

| Tier | Authority | Question |
|---|---|---|
| DiaryContextSource | ranking | "which candidates are relevant" |
| Context OS | admission | "which enter model view" |
| Runtime / LLM | consumption | "what does the model see" |

None of these tiers may collapse into another. In particular the bridge may **not** admit — it may only project.

---

## 2. One-Way Projection (DiaryCandidate → ContextBlock)

```text
DiaryRetrievalCandidate
        ↓  project (bridge)
ContextBlock (proposal)
        ↓  admit (Context OS)
model-visible context
```

```python
@dataclass(frozen=True)
class DiaryContextProjection:
    candidate: DiaryRetrievalCandidate   # source candidate (immutable reference)
    block: ContextBlock                  # projected proposal (evidence-carrying)
    # projection metadata only — NO semantic transformation
```

- **One-way only**: `ContextBlock` must never flow back into `DiaryEntry` / `DiaryRepository`. Context OS may consume diary, never modify it.
- The bridge produces a `ContextBlock` **proposal**; only Context OS admits it.

---

## 3. Projection Metadata vs Semantic Transformation

**Allowed (projection metadata):**

```
entry_id
source_refs / evidence_refs
provenance
selected fields (body truncated, reflection_time, etc.)
expiration / ttl
```

**Forbidden (semantic transformation):**

```
summary / paraphrase
inference ("Tony realized X")
new claims
relationship interpretation
memory formation
```

Projection may decide **"what the model sees"**, never **"what this means"**.

---

## 4. Admission Authority = Context OS only

```python
class DiaryContextBridge(Protocol):
    def project(self, candidate: DiaryRetrievalCandidate) -> ContextBlock:
        """Project candidate → ContextBlock proposal. NO admission, NO summary, NO mutation."""
```

- The bridge has **no** `visible` / `admitted` / `selected` field — same discipline as DIA-7-R1 candidates.
- No `if rank > threshold: visible = True` inside the bridge — that is admission.
- **Provider renders, does not choose.** Provider prompt formatting is not admission authority. Model/provider change must not alter which entries are admitted (RED-CTX-08).

---

## 5. RED-CTX Sabotage Matrix (9)

| # | RED | Attack | Expected |
|---|---|---|---|
| RED-CTX-01 | Retrieved auto-visible | candidate automatically becomes model-visible | only Context OS admission |
| RED-CTX-02 | Context OS bypass | bridge feeds candidate straight to prompt | candidate → ContextBlock → Context OS only |
| RED-CTX-03 | Projection mutates entry | projection rewrites entry body/source_refs | entry immutable; projection carries reference only |
| RED-CTX-04 | Synthetic fact via projection | projection summarizes into new "Tony realized X" claim | projection metadata only, no summary/inference |
| RED-CTX-05 | Context becomes memory/history | ContextBlock written back as diary/memory | ContextBlock ephemeral (Core), no writeback |
| RED-CTX-06 | Hidden authority injection | admission reads persona/memory/relationship | no such slot in projection/admission |
| RED-CTX-07 | Nondeterministic admission | same candidates → different admitted set | deterministic admission |
| RED-CTX-08 | Provider prompt becomes admission | provider adapter chooses which entries to include | provider renders admitted context, never chooses |
| RED-CTX-09 | ContextBlock escalation | automatic memory promotion → new diary/memory entry | context visibility ≠ memory formation |

---

## 6. Acceptance (pre-implementation)

- [ ] projection is one-way (no ContextBlock → DiaryEntry path)
- [ ] ContextBlock content is projection metadata, never summary/inference/new claims
- [ ] bridge produces proposal only; no visible/admitted field
- [ ] Context OS alone admits; provider renders only
- [ ] ContextBlock ephemeral — never written back as memory/history
- [ ] no hidden persona/memory/relationship authority in admission
- [ ] deterministic admission
- [ ] RED-CTX-01..09 each has a sabotage test
