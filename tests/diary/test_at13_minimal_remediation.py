"""Wave5 AT-13 Minimal Remediation: significant event authority boundary."""
from __future__ import annotations

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


class DurableRecordingDiaryRepository:
    """Fixture repository: normal append means DIARY_DURABLE and observable."""

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


class PoisonedDiaryRepository(DurableRecordingDiaryRepository):
    """Append returns but does not make the entry observable."""

    def append_accepted(self, entry: AcceptedDiaryEntry) -> None:
        if type(entry) is not AcceptedDiaryEntry:
            raise TypeError("AcceptedDiaryEntry only")
        self.append_calls.append(entry)


def _provenance() -> DiaryProvenance:
    return DiaryProvenance(
        model_provider="fixture",
        model_name="at13-minimal",
        runtime="pytest",
    )


def _event(
    *,
    event_id: str = "evt_at13_001",
    body: str = "我意识到今天这个决定改变了我理解 Tony 项目的方式。",
    refs: tuple[DiarySourceRef, ...] | None = None,
) -> GroundedSignificantEvent:
    return GroundedSignificantEvent(
        event_id=event_id,
        reflection_time="2026-08-23T00:00:00+08:00",
        source_refs=refs or (DiarySourceRef("conversation://conv_at13/msg_1"),),
        reflective_body=body,
        provenance=_provenance(),
        title="AT-13 meaningful event",
        themes=("wave5", "diary"),
        relationship_significance="我对这件事的理解发生了变化。",
    )


def _acceptance() -> DiaryGovernanceAcceptance:
    return DiaryGovernanceAcceptance(
        governance_id="gov_at13_001",
        accepted_at="2026-08-23T00:01:00+08:00",
        accepted_by="diary-governance-fixture",
        reason="grounded first-person reflection with canonical source refs",
    )


def test_at13_remed_001_significant_event_creates_candidate_not_entry():
    event = _event()

    candidate = create_diary_candidate(event)

    assert type(candidate) is DiaryCandidate
    assert type(candidate) is not AcceptedDiaryEntry
    assert candidate.candidate_id == "cand_evt_at13_001"
    assert candidate.source_refs == event.source_refs
    assert candidate.body == event.reflective_body


def test_at13_remed_002_candidate_requires_explicit_governance_promotion():
    candidate = create_diary_candidate(_event(event_id="evt_at13_002"))

    with pytest.raises(ValueError, match="acceptance must be DiaryGovernanceAcceptance"):
        promote_candidate_to_accepted_entry(candidate, None)  # type: ignore[arg-type]

    accepted = promote_candidate_to_accepted_entry(candidate, _acceptance())
    assert type(accepted) is AcceptedDiaryEntry
    assert accepted.governance_status == "accepted"
    assert accepted.entry_id.startswith("diary_")
    assert accepted.source_refs == candidate.source_refs


def test_at13_remed_003_transcript_summary_cannot_be_candidate_or_accepted_diary():
    with pytest.raises(ValueError, match="first-person reflection, not transcript summary"):
        _event(body="Conversation summary: Tony said X, assistant said Y.")

    valid_candidate = create_diary_candidate(_event(event_id="evt_at13_003"))
    object.__setattr__(valid_candidate, "body", "本次对话总结：Tony 说了 X，Julia 回答了 Y。")
    with pytest.raises(ValueError, match="first-person reflection, not transcript summary"):
        promote_candidate_to_accepted_entry(valid_candidate, _acceptance())


def test_at13_remed_004_source_refs_must_use_canonical_namespaces():
    with pytest.raises(ValueError, match="canonical source namespaces"):
        _event(refs=(DiarySourceRef("projection://diary_ui/fake"),))

    with pytest.raises(ValueError, match="canonical source namespaces"):
        _event(refs=(DiarySourceRef("cache://electron/fake"),))

    candidate = create_diary_candidate(
        _event(
            event_id="evt_at13_004",
            refs=(DiarySourceRef("memory://experience/exp_at13"),),
        )
    )
    accepted = promote_candidate_to_accepted_entry(candidate, _acceptance())
    assert accepted.source_refs[0].uri == "memory://experience/exp_at13"


def test_at13_remed_005_diary_durable_is_final_canonical_boundary():
    repo = DurableRecordingDiaryRepository()
    accepted = promote_candidate_to_accepted_entry(create_diary_candidate(_event(event_id="evt_at13_005")), _acceptance())

    assert repo.list_entries() == []

    commit = commit_accepted_entry_durable(accepted, repo)

    assert commit.durable is True
    assert commit.entry_id == accepted.entry_id
    assert repo.get(accepted.entry_id) == accepted
    assert repo.list_entries() == [accepted]


def test_at13_remed_006_durable_failure_fails_closed():
    repo = PoisonedDiaryRepository()
    accepted = promote_candidate_to_accepted_entry(create_diary_candidate(_event(event_id="evt_at13_006")), _acceptance())

    with pytest.raises(RuntimeError, match="DIARY_DURABLE was not established"):
        commit_accepted_entry_durable(accepted, repo)

    assert repo.get(accepted.entry_id) is None
    assert repo.list_entries() == []
