"""STORAGE-DIA-7-R1 — DiaryContextSource sabotage tests."""
from __future__ import annotations

import dataclasses

from julia_core.diary import AcceptedDiaryEntry, DiaryProvenance, DiarySourceRef
from julia_core.diary.context_source import (
    DiaryRetrievalCandidate,
    DiaryRetrievalQuery,
    DeterministicDiaryContextSource,
)


class _RecordingRepository:
    def __init__(self, entries=()):
        self._entries = list(entries)

    def list_entries(self, before=None, after=None, limit=None, **kwargs):
        result = list(self._entries)
        if before is not None:
            result = [e for e in result if e.created_at < before]
        if after is not None:
            result = [e for e in result if e.created_at > after]
        if limit is not None:
            result = result[:limit]
        return result


def _entry(entry_id="e1", body="entry body", reflection_time="2026-08-17T00:00:00+08:00", created_at="2026-08-17T00:00:00+08:00"):
    return AcceptedDiaryEntry(
        entry_id=entry_id,
        created_at=created_at,
        reflection_time=reflection_time,
        source_refs=(DiarySourceRef("handoff://handoff-1"),),
        body=body,
        body_hash="0" * 64,
        provenance=DiaryProvenance("deepseek", "deepseek-chat", "julia-assistant-wave4"),
    )


# AT-RET-01: no raw persistence bypass surface (source reads repository, not files).
def test_at_ret_01_no_raw_file_surface():
    src = DeterministicDiaryContextSource(_RecordingRepository())
    assert not hasattr(src, "glob")
    assert not hasattr(src, "read_file")
    assert not hasattr(src, "load_all")


# AT-RET-02: limit bounds candidates, does not dump all stored entries.
def test_at_ret_02_limit_bounds_not_dump():
    entries = [_entry(entry_id=f"e{i}") for i in range(100)]
    src = DeterministicDiaryContextSource(_RecordingRepository(entries))
    result = src.retrieve(DiaryRetrievalQuery(limit=3))
    assert len(result) == 3


# AT-RET-03 / AT-RET-04: candidate has no admission field.
def test_at_ret_03_04_no_admission_field():
    fields = {f.name for f in dataclasses.fields(DiaryRetrievalCandidate)}
    assert fields == {"entry", "ranking"}
    assert "selected" not in fields
    assert "admitted" not in fields


# RED-RET-05: entry is preserved field-for-field (no mutation).
def test_red_ret_05_entry_not_mutated():
    entry = _entry(body="exact original body")
    src = DeterministicDiaryContextSource(_RecordingRepository([entry]))
    (candidate,) = src.retrieve(DiaryRetrievalQuery(limit=1))
    assert candidate.entry.body == "exact original body"
    assert candidate.entry.entry_id == entry.entry_id
    assert candidate.entry.source_refs == entry.source_refs
    assert candidate.entry.provenance == entry.provenance


# RED-RET-06: no synthetic truth — each candidate is an independent immutable reference.
def test_red_ret_06_no_synthetic_truth():
    a = _entry(entry_id="a", body="A")
    b = _entry(entry_id="b", body="B")
    src = DeterministicDiaryContextSource(_RecordingRepository([a, b]))
    result = src.retrieve(DiaryRetrievalQuery(limit=10))
    ids = {c.entry.entry_id for c in result}
    assert ids == {"a", "b"}  # no fused "a+b" entry


# RED-RET-07: query has no hidden semantic injection slot.
def test_red_ret_07_query_no_semantic_slot():
    fields = {f.name for f in dataclasses.fields(DiaryRetrievalQuery)}
    assert fields == {"query_text", "as_of", "before", "limit"}


# RED-RET-08: deterministic ranking — same query → same ordering.
def test_red_ret_08_deterministic_ordering():
    entries = [_entry(entry_id="a", body="x"), _entry(entry_id="b", body="y"), _entry(entry_id="c", body="z")]
    src = DeterministicDiaryContextSource(_RecordingRepository(entries))
    q = DiaryRetrievalQuery(limit=10)
    r1 = [c.entry.entry_id for c in src.retrieve(q)]
    r2 = [c.entry.entry_id for c in src.retrieve(q)]
    assert r1 == r2


# Deterministic ranking: recency from explicit as_of (no hidden wall-clock in _rank).
def test_recency_uses_explicit_as_of():
    older = _entry(entry_id="older", reflection_time="2026-08-10T00:00:00+08:00")
    newer = _entry(entry_id="newer", reflection_time="2026-08-17T00:00:00+08:00")
    src = DeterministicDiaryContextSource(_RecordingRepository([older, newer]))
    result = src.retrieve(DiaryRetrievalQuery(as_of="2026-08-17T00:00:00+08:00", limit=10))
    assert result[0].entry.entry_id == "newer"


# RET-TIME-01: before narrows the eligible set by created_at.
def test_before_filters_by_created_at():
    old = _entry(entry_id="old", created_at="2026-08-10T00:00:00+08:00")
    new = _entry(entry_id="new", created_at="2026-08-17T00:00:00+08:00")
    src = DeterministicDiaryContextSource(_RecordingRepository([old, new]))
    result = src.retrieve(DiaryRetrievalQuery(before="2026-08-15T00:00:00+08:00", limit=10))
    ids = {c.entry.entry_id for c in result}
    assert ids == {"old"}


# Query validation: negative limit fails closed.
def test_negative_limit_fails_closed():
    import pytest

    src = DeterministicDiaryContextSource(_RecordingRepository([_entry()]))
    with pytest.raises(ValueError, match="limit must be non-negative"):
        src.retrieve(DiaryRetrievalQuery(limit=-1))


# Query validation: naive datetime (no timezone) fails closed.
def test_naive_datetime_fails_closed():
    import pytest

    src = DeterministicDiaryContextSource(_RecordingRepository([_entry()]))
    with pytest.raises(ValueError, match="must be offset-aware"):
        src.retrieve(DiaryRetrievalQuery(as_of="2026-08-17T12:00:00"))
    with pytest.raises(ValueError, match="must be offset-aware"):
        src.retrieve(DiaryRetrievalQuery(before="2026-08-17T12:00:00"))
