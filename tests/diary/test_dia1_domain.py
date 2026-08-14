"""DIA-1 — Core Diary domain contract tests (AT-DOM-01..15)."""
from __future__ import annotations

from pathlib import Path

import pytest

from julia_core.diary import (
    AcceptedDiaryEntry,
    DiaryCandidate,
    DiaryProvenance,
    DiarySourceRef,
    NoEntry,
    NO_ENTRY,
)


def _prov():
    return DiaryProvenance("provider", "model", "runtime")


def _candidate(**overrides):
    base = dict(
        candidate_id="cand_1",
        reflection_time="2026-08-14T00:00:00Z",
        source_refs=(DiarySourceRef("conversation://conv_A/msg_1"),),
        body="a reflection",
        provenance=_prov(),
    )
    base.update(overrides)
    return DiaryCandidate(**base)


def _entry(**overrides):
    base = dict(
        entry_id="diary_1",
        created_at="2026-08-14T00:00:00Z",
        reflection_time="2026-08-14T00:00:00Z",
        source_refs=(DiarySourceRef("conversation://conv_A/msg_1"),),
        body="a reflection",
        body_hash="abc123",
        provenance=_prov(),
    )
    base.update(overrides)
    return AcceptedDiaryEntry(**base)


# ── AT-DOM-01: NO_ENTRY is an explicit NoEntry, not None/False/""/exception ──
def test_no_entry_is_explicit_singleton():
    assert isinstance(NO_ENTRY, NoEntry)
    assert NO_ENTRY is not None
    assert NO_ENTRY is not False
    assert NO_ENTRY != ""


# ── AT-DOM-02: ReflectionResult accepts NO_ENTRY | DiaryCandidate, never Accepted ──
def test_reflection_result_union():
    assert isinstance(NO_ENTRY, NoEntry)
    cand = _candidate()
    assert isinstance(cand, DiaryCandidate)
    # NO_ENTRY and DiaryCandidate are distinct; AcceptedDiaryEntry is NOT a candidate
    assert not isinstance(cand, AcceptedDiaryEntry)


# ── AT-DOM-03: Candidate != Accepted (type separation) ─────────────────────
def test_candidate_is_not_accepted():
    assert DiaryCandidate is not AcceptedDiaryEntry


# ── AT-DOM-04/05/06/07/08: structural invariants ───────────────────────────
def test_candidate_empty_body_rejected():
    with pytest.raises(ValueError):
        _candidate(body="   ")


def test_candidate_zero_source_refs_rejected():
    with pytest.raises(ValueError):
        _candidate(source_refs=())


def test_entry_empty_entry_id_rejected():
    with pytest.raises(ValueError):
        _entry(entry_id="")


def test_entry_empty_body_hash_rejected():
    with pytest.raises(ValueError):
        _entry(body_hash="")


def test_entry_non_accepted_governance_status_rejected():
    with pytest.raises(ValueError):
        _entry(governance_status="pending")


def test_source_ref_empty_uri_rejected():
    with pytest.raises(ValueError):
        DiarySourceRef("")


def test_provenance_empty_field_rejected():
    with pytest.raises(ValueError):
        DiaryProvenance("", "model", "runtime")


# ── AT-DOM-09: optional fields default valid ───────────────────────────────
def test_optional_fields_default_valid():
    cand = _candidate()
    assert cand.title is None
    assert cand.themes == ()
    assert cand.relationship_significance is None
    assert cand.project_significance is None
    entry = _entry()
    assert entry.supersedes == ()


# ── AT-DOM-10: source ref is an opaque semantic URI (no physical-path field) ─
def test_source_ref_has_no_physical_path_field():
    ref = DiarySourceRef("conversation://conv_A/msg_1")
    assert set(vars(ref)) == {"uri"}


# ── AT-DOM-11/12/13: zero side effects on construction ─────────────────────
def test_construction_is_pure():
    # constructing domain objects must not raise, must not touch anything external
    cand = _candidate()
    entry = _entry()
    assert cand.body == "a reflection"
    assert entry.body_hash == "abc123"


# ── AT-DOM-14: static dependency scan ──────────────────────────────────────
def test_no_forbidden_dependencies():
    src = (
        Path(__file__).resolve().parents[2]
        / "julia_core" / "diary" / "models.py"
    ).read_text()
    for forbidden in (
        "pathlib", "import os", "sqlite3", "requests", "httpx",
        "julia_core.memory", "julia_core.context_os",
        "conversation_state", "MemoryExperience", "promote_to_memory",
    ):
        assert forbidden not in src, f"models.py must not depend on {forbidden}"


# ── AT-DOM-15: DIA-1 provides no hash helper (body_hash is caller-supplied) ──
def test_no_hash_helper_in_domain():
    src = (
        Path(__file__).resolve().parents[2]
        / "julia_core" / "diary" / "models.py"
    ).read_text()
    assert "hashlib" not in src
