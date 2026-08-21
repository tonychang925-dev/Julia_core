"""STORAGE-DIA-7-R2-R1 — DiaryContextBridge sabotage tests."""
from __future__ import annotations

import dataclasses

from julia_core.diary import AcceptedDiaryEntry, DiaryProvenance, DiarySourceRef
from julia_core.diary.context_bridge import (
    PROJECTION_TTL_SECONDS,
    ContextBlockProposal,
    DiaryContextBridge,
)
from julia_core.diary.context_source import DiaryRetrievalCandidate, DiaryRetrievalRanking


def _entry(entry_id="e1", body="original body"):
    return AcceptedDiaryEntry(
        entry_id=entry_id,
        created_at="2026-08-17T00:00:00+08:00",
        reflection_time="2026-08-17T00:00:00+08:00",
        source_refs=(DiarySourceRef("handoff://handoff-1"),),
        body=body,
        body_hash="0" * 64,
        provenance=DiaryProvenance("deepseek", "deepseek-chat", "julia-assistant-wave4"),
    )


def _candidate(entry=None):
    e = entry or _entry()
    return DiaryRetrievalCandidate(e, DiaryRetrievalRanking(1.0, 1.0, 1.0))


# CTX-01: proposal has no admitted/visible field.
def test_ctx_01_no_admitted_field():
    fields = {f.name for f in dataclasses.fields(ContextBlockProposal)}
    assert fields == {"block"}
    assert "admitted" not in fields
    assert "visible" not in fields


# CTX-02: bridge only projects, does not admit.
def test_ctx_02_bridge_no_admission_surface():
    bridge = DiaryContextBridge()
    assert not hasattr(bridge, "send")
    assert not hasattr(bridge, "admit")
    assert not hasattr(bridge, "select")
    assert not hasattr(bridge, "prompt")


# CTX-03: projection does not mutate entry.
def test_ctx_03_entry_not_mutated():
    entry = _entry(body="exact original")
    DiaryContextBridge().project(_candidate(entry))
    assert entry.body == "exact original"
    assert entry.source_refs == (DiarySourceRef("handoff://handoff-1"),)


# CTX-04: content is projection metadata, not summary/inference.
def test_ctx_04_no_summary_or_inference():
    entry = _entry(body="original body")
    proposal = DiaryContextBridge().project(_candidate(entry))
    content = proposal.block.content
    assert content["body"] == "original body"
    assert "summary" not in content
    assert "realized" not in str(content)


# CTX-05 / CTX-09: short-lived, no writeback/escalation surface.
def test_ctx_05_09_ephemeral_no_escalation():
    bridge = DiaryContextBridge()
    assert not hasattr(bridge, "writeback")
    assert not hasattr(bridge, "promote")
    assert not hasattr(bridge, "store")
    proposal = bridge.project(_candidate())
    assert proposal.block.ttl_seconds == PROJECTION_TTL_SECONDS


# CTX-06 / CTX-08: no hidden authority / provider surface.
def test_ctx_06_08_no_hidden_authority():
    bridge = DiaryContextBridge()
    assert not hasattr(bridge, "persona")
    assert not hasattr(bridge, "memory")
    assert not hasattr(bridge, "provider")
    assert not hasattr(bridge, "format")


# CTX-07: deterministic projection.
def test_ctx_07_deterministic():
    entry = _entry()
    bridge = DiaryContextBridge()
    p1 = bridge.project(_candidate(entry))
    p2 = bridge.project(_candidate(entry))
    assert p1.block.content == p2.block.content
    assert p1.block.evidence_refs == p2.block.evidence_refs


# H1: evidence_refs bind to entry.source_refs (no evidence-authority swap).
def test_h1_evidence_refs_bind_to_source_refs():
    entry = _entry()
    proposal = DiaryContextBridge().project(_candidate(entry))
    assert proposal.block.evidence_refs == ("handoff://handoff-1",)
    assert proposal.block.evidence_refs == proposal.block.source_refs


# H2: ContextBlock ttl is context lifecycle; diary entry has no ttl (lifecycle untouched).
def test_h2_ttl_does_not_touch_diary():
    entry = _entry()
    proposal = DiaryContextBridge().project(_candidate(entry))
    assert proposal.block.ttl_seconds == PROJECTION_TTL_SECONDS
    assert not hasattr(entry, "ttl_seconds")
    assert not hasattr(entry, "expires_at")
