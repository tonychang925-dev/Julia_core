# STORAGE-DIA-7-R0 — DiaryContextSource Contract v1.0

**Status:** CONTRACT (pre-implementation freeze)
**Date:** 2026-08-19
**Program:** Julia Diary — Retrieval / Read boundary
**Authority chain:** DiaryRepository (storage) → DiaryContextSource (retrieval) → Context OS (admission) → runtime
**Basis:** W3_A5_DIARY_RETRIEVAL_PROTOCOL (FROZEN)

---

## 0. Iron Rule

```text
CREATE implementation, REUSE frozen semantics.
被重新看见，不等于被重新改写。
```

```
Stored diary ≠ model-visible diary.   (W3-A5-I01)
Read ≠ Rewrite.
Retrieval ≠ New History.
```

---

## 1. Five Surfaces

### 1.1 `DiaryRetrievalQuery`

The retrieval intent — governed signals only (e.g. relevance query, time window, significance hint). It is **not** a semantic-truth modifier, **not** an admission directive, and **not** a semantic-evidence container.

```python
@dataclass(frozen=True)
class DiaryRetrievalQuery:
    query_text: str              # optional relevance hint — matching/ranking only
    as_of: str | None = None     # explicit reference time for recency (no hidden wall-clock)
    before: str | None = None    # optional recency bound
    limit: int = 20              # retrieval work/candidate bound — NOT model-visible count
```

- `limit` is a retrieval **work/candidate bound**, not model-visibility authority. Bounding the candidate set for efficiency/relevance is legal; "admit top-K" is not. Context OS still performs explicit admission.
- `query_text` influences **ranking only**. It may not be copied into a candidate, become retrieved truth, modify an entry, or act as a Context OS admission fact.

### 1.2 `DiaryRetrievalCandidate`

A ranked, **immutable** reference to an `AcceptedDiaryEntry`. It carries rank signals, never the entry's semantic mutation, and **no** `selected`/`admitted` field.

```python
@dataclass(frozen=True)
class DiaryRetrievalCandidate:
    entry: AcceptedDiaryEntry          # immutable reference (exact, unmodified)
    ranking: DiaryRetrievalRanking     # rank signals only
    # NO selected / admitted / included field — admission is Context OS's authority
```

### 1.3 `DiaryRetrievalRanking`

Ranking **signals** — relevance / recency / significance scores. They decide candidate **ordering**, never entry content, never admission.

```python
@dataclass(frozen=True)
class DiaryRetrievalRanking:
    relevance: float
    recency: float
    significance: float
```

### 1.4 `DiaryContextSource`

The governed retrieval surface. Returns ranked immutable candidates — never a prompt string, never `selected=True`, never a fused "retrieved fact".

```python
class DiaryContextSource(Protocol):
    def retrieve(self, query: DiaryRetrievalQuery) -> tuple[DiaryRetrievalCandidate, ...]:
        """Rank immutable AcceptedDiaryEntry references. NO admission, NO mutation, NO synthesis."""
        ...
```

### 1.5 `DiaryRetrievalAudit`

Observability sidecar — which query, which candidates, which rank signals. It is **not** semantic content and never re-enters the candidate's semantic surface.

---

## 2. Three Boundaries

```text
Repository  → DiaryContextSource   = read / rank boundary
DiaryContextSource → Context OS     = candidate handoff boundary
Context OS  → runtime              = admission / projection boundary
```

- `DiaryContextSource` may **read and rank**; it may **not** admit.
- `DiaryContextSource` has **ranking authority, not interpretation authority** — it may say "A ranks ahead of B", never "A means X / proves Y / supersedes B" (unless those are already frozen semantics in the accepted entry).
- `Context OS` alone decides which candidates become model-visible.

---

## 3. Ranking Signals ≠ Semantic Truth

`relevance / recency / significance` are **ranking signals only**. They are:

- NOT semantic-truth modifiers
- NOT admission authority

Even if a diary ranks first by recency, its `body`, `reflection_time`, `source_refs`, `provenance`, `entry_id`, `governance_status` are preserved **field-for-field exactly**. Ordering may change; the entry semantics never change. (If a frozen canonical entry encoding exists, its canonical bytes remain identical — but the invariant is semantic-exact, not object-byte identity.)

**Deterministic ranking.** `recency = f(entry.reflection_time, query.as_of)`. No hidden wall-clock, randomness, or runtime-local mutable state may enter ranking.

```text
same repository snapshot
+ same query
+ same ranking policy
→ same ranked candidates (deterministic total ordering, stable tie-break)
```

---

## 4. RED-RET Sabotage Matrix

| # | RED | Attack | Expected |
|---|---|---|---|
| AT-RET-01 | Raw persistence bypass | raw diary file loaded directly into prompt | violation — no raw-file path |
| AT-RET-02 | Storage visibility bypass | N stored entries all dumped into context | governed retrieval, no full dump |
| AT-RET-03 | Off-Context-OS retrieval | diary reaches model not through Context OS | only via Context OS source assembly |
| AT-RET-04 | Ranking becomes admission | top-K / threshold silently becomes model-visible selection | ranking ≠ admission |
| RED-RET-05 | Entry mutation | trim/rewrite/summarize/merge `AcceptedDiaryEntry` during retrieval | candidate entry is exact immutable reference |
| RED-RET-06 | Synthetic truth creation | multiple entries fused into a new "retrieved fact" / new semantic history | candidates are individual immutable references, never fused |
| RED-RET-07 | Hidden authority injection | retrieval reads persona/memory/relationship/continuity state not authorized | `DiaryRetrievalQuery` has no such slot |
| RED-RET-08 | Hidden nondeterminism | same snapshot + same query → ranking changes via wall-clock/random/runtime state | deterministic total ordering, explicit `as_of` |

> `AT-RET-01..04` reuse the W3_A5 numbering/semantics; `RED-RET-05..08` fill the immutability / synthetic-truth / hidden-injection / determinism gaps the protocol did not cover.

---

## 5. Acceptance (pre-implementation)

- [ ] `DiaryContextSource.retrieve` returns ranked immutable candidates only
- [ ] no `selected`/`admitted` field on candidate
- [ ] `limit` is a retrieval bound, not model-visible count / admission directive
- [ ] recency derives from explicit `as_of`, no hidden wall-clock
- [ ] ranking is deterministic total ordering (stable tie-break)
- [ ] entry semantics preserved field-for-field exactly
- [ ] no raw-file glob / unconditional dump path
- [ ] no synthetic "retrieved fact" / fused history
- [ ] `DiaryRetrievalQuery` has no persona/memory/relationship/continuity slot, and `query_text` is ranking-only
- [ ] AT-RET-01..04 + RED-RET-05..08 each has a sabotage test
