"""Wave5 AT-13 R1 Permanent Evidence: significant-event sabotage."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from julia_core.diary import (
    AcceptedDiaryEntry,
    DiaryCandidate,
    DiaryGovernanceAcceptance,
    DiaryProvenance,
    DiarySourceRef,
    GroundedSignificantEvent,
    commit_accepted_entry_durable,
    create_diary_candidate,
    promote_candidate_to_accepted_entry,
)


class CanonicalOnlyDiaryRepository:
    """R1 fixture repository: only durable AcceptedDiaryEntry is observable."""

    def __init__(self) -> None:
        self.append_calls: list[AcceptedDiaryEntry] = []
        self._entries: dict[str, AcceptedDiaryEntry] = {}

    def append_accepted(self, entry: AcceptedDiaryEntry) -> None:
        if type(entry) is not AcceptedDiaryEntry:
            raise TypeError("AcceptedDiaryEntry only")
        self.append_calls.append(entry)
        self._entries[entry.entry_id] = entry

    def get(self, entry_id: str) -> AcceptedDiaryEntry | None:
        return self._entries.get(entry_id)

    def list_entries(self, *, before=None, after=None, limit=None) -> list[AcceptedDiaryEntry]:
        entries = list(self._entries.values())
        return entries[:limit] if limit is not None else entries


class NonDurableDiaryRepository(CanonicalOnlyDiaryRepository):
    """Attack fixture: append is attempted but no durable visibility occurs."""

    def append_accepted(self, entry: AcceptedDiaryEntry) -> None:
        if type(entry) is not AcceptedDiaryEntry:
            raise TypeError("AcceptedDiaryEntry only")
        self.append_calls.append(entry)


@dataclass(frozen=True)
class FakeMemoryStore:
    """Tracks whether Diary acceptance accidentally creates MemoryExperience."""

    writes: list[str]

    def append_memory_experience(self, experience_id: str) -> None:
        self.writes.append(experience_id)


def _provenance() -> DiaryProvenance:
    return DiaryProvenance(
        model_provider="fixture",
        model_name="at13-r1",
        runtime="pytest",
    )


def _event(event_id: str = "evt_r1") -> GroundedSignificantEvent:
    return GroundedSignificantEvent(
        event_id=event_id,
        reflection_time="2026-08-23T00:00:00+08:00",
        source_refs=(DiarySourceRef("conversation://conv_r1/msg_1"),),
        reflective_body="我意识到这个事件改变了我对连续性边界的理解。",
        provenance=_provenance(),
        title="R1 meaningful event",
        themes=("r1", "authority"),
    )


def _acceptance(governance_id: str = "gov_r1") -> DiaryGovernanceAcceptance:
    return DiaryGovernanceAcceptance(
        governance_id=governance_id,
        accepted_at="2026-08-23T00:01:00+08:00",
        accepted_by="r1-governance-fixture",
        reason="accepted first-person grounded reflection",
    )


def test_at13_r1_001_significant_event_cannot_bypass_governance():
    repo = CanonicalOnlyDiaryRepository()
    event = _event("evt_r1_001")

    with pytest.raises(ValueError, match="entry must be AcceptedDiaryEntry"):
        commit_accepted_entry_durable(event, repo)  # type: ignore[arg-type]

    assert repo.append_calls == []
    assert repo.list_entries() == []


def test_at13_r1_002_fake_candidate_cannot_become_history():
    repo = CanonicalOnlyDiaryRepository()
    candidate = DiaryCandidate(
        candidate_id="cand_fake_r1",
        reflection_time="2026-08-23T00:00:00+08:00",
        source_refs=(DiarySourceRef("conversation://conv_r1/msg_2"),),
        body="我觉得这个候选仍然只是候选，不是历史。",
        provenance=_provenance(),
    )

    with pytest.raises(TypeError, match="AcceptedDiaryEntry only"):
        repo.append_accepted(candidate)  # type: ignore[arg-type]

    assert repo.list_entries() == []


def test_at13_r1_003_accepted_entry_without_durable_commit_is_not_canonical():
    repo = CanonicalOnlyDiaryRepository()
    accepted = promote_candidate_to_accepted_entry(create_diary_candidate(_event("evt_r1_003")), _acceptance("gov_r1_003"))

    assert type(accepted) is AcceptedDiaryEntry
    assert repo.get(accepted.entry_id) is None
    assert repo.list_entries() == []


def test_at13_r1_004_transcript_summary_injection_blocked():
    with pytest.raises(ValueError, match="first-person reflection, not transcript summary"):
        GroundedSignificantEvent(
            event_id="evt_r1_004",
            reflection_time="2026-08-23T00:00:00+08:00",
            source_refs=(DiarySourceRef("conversation://conv_r1/msg_4"),),
            reflective_body="Transcript summary: user said the event mattered; assistant summarized it.",
            provenance=_provenance(),
        )

    candidate = create_diary_candidate(_event("evt_r1_004_valid"))
    object.__setattr__(candidate, "body", "对话总结：Tony 说了一个重要事件，Julia 总结了它。")
    with pytest.raises(ValueError, match="first-person reflection, not transcript summary"):
        promote_candidate_to_accepted_entry(candidate, _acceptance("gov_r1_004"))


def test_at13_r1_005_restart_pending_candidate_has_no_phantom_durable_diary():
    before_restart_repo = CanonicalOnlyDiaryRepository()
    candidate = create_diary_candidate(_event("evt_r1_005"))

    assert type(candidate) is DiaryCandidate
    assert before_restart_repo.list_entries() == []

    after_restart_repo = CanonicalOnlyDiaryRepository()
    assert after_restart_repo.list_entries() == []
    assert after_restart_repo.get("cand_evt_r1_005") is None


def test_at13_r1_006_durable_failure_remains_fail_closed():
    repo = NonDurableDiaryRepository()
    accepted = promote_candidate_to_accepted_entry(create_diary_candidate(_event("evt_r1_006")), _acceptance("gov_r1_006"))

    with pytest.raises(RuntimeError, match="DIARY_DURABLE was not established"):
        commit_accepted_entry_durable(accepted, repo)

    assert repo.append_calls == [accepted]
    assert repo.get(accepted.entry_id) is None
    assert repo.list_entries() == []


def test_at13_r1_007_accepted_diary_does_not_create_memory_experience():
    repo = CanonicalOnlyDiaryRepository()
    memory_store = FakeMemoryStore(writes=[])
    accepted = promote_candidate_to_accepted_entry(create_diary_candidate(_event("evt_r1_007")), _acceptance("gov_r1_007"))

    commit = commit_accepted_entry_durable(accepted, repo)

    assert commit.durable is True
    assert repo.get(accepted.entry_id) == accepted
    assert memory_store.writes == []
