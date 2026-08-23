"""Wave5 AT-15 Integration Acceptance: product-shaped Diary/Memory separation."""
from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from julia_core.capability.memory_consolidation import ExperienceCandidate, MemoryConsolidator
from julia_core.diary import (
    AcceptedDiaryEntry,
    DiaryGovernanceAcceptance,
    DiaryProvenance,
    DiarySourceRef,
    GroundedSignificantEvent,
    SourceRefState,
    commit_accepted_entry_durable,
    create_diary_candidate,
    promote_candidate_to_accepted_entry,
    prove_diary_does_not_mutate_memory,
    validate_diary_provenance,
)
from julia_core.memory.persistence.memory_persistence_adapter import MemoryPersistenceRequest
from julia_core.runtime.session_recorder import SessionRecorder


class ProductDiaryRepository:
    def __init__(self, seed: list[AcceptedDiaryEntry] | None = None) -> None:
        self.append_calls: list[AcceptedDiaryEntry] = []
        self._entries = {entry.entry_id: entry for entry in seed or []}

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


class ProductSourceResolver:
    def __init__(self, states: dict[str, SourceRefState]) -> None:
        self.states = dict(states)

    def resolve(self, source_ref: DiarySourceRef) -> SourceRefState:
        return self.states.get(source_ref.uri, SourceRefState.MISSING)


@dataclass
class ProductMemoryStore:
    writes: list[str] = field(default_factory=list)

    def append_memory_experience(self, experience_id: str) -> None:
        self.writes.append(experience_id)


def _provenance() -> DiaryProvenance:
    return DiaryProvenance(
        model_provider="fixture",
        model_name="at15-ia",
        runtime="pytest",
    )


def _event(event_id: str = "evt_at15_ia") -> GroundedSignificantEvent:
    return GroundedSignificantEvent(
        event_id=event_id,
        reflection_time="2026-08-23T00:00:00+08:00",
        source_refs=(DiarySourceRef("conversation://conv_at15_ia/msg_1"),),
        reflective_body="我确认这条 Diary 即使完整可信，也不会自动成为 Memory。",
        provenance=_provenance(),
        title="AT-15 Diary Memory Boundary",
        themes=("diary", "memory-boundary"),
    )


def _acceptance(governance_id: str = "gov_at15_ia") -> DiaryGovernanceAcceptance:
    return DiaryGovernanceAcceptance(
        governance_id=governance_id,
        accepted_at="2026-08-23T00:01:00+08:00",
        accepted_by="product-diary-governance-fixture",
        reason="accepted Diary remains outside Memory authority",
    )


def _run_governed_diary_path(event_id: str, repo: ProductDiaryRepository) -> AcceptedDiaryEntry:
    candidate = create_diary_candidate(_event(event_id))
    accepted = promote_candidate_to_accepted_entry(candidate, _acceptance(f"gov_{event_id}"))
    commit = commit_accepted_entry_durable(accepted, repo)
    assert commit.durable is True
    return accepted


def test_tc_at15_ia_001_governed_diary_path_does_not_mutate_memory():
    diary_repo = ProductDiaryRepository()
    memory_store = ProductMemoryStore()

    accepted = _run_governed_diary_path("evt_at15_ia_001", diary_repo)
    proof = prove_diary_does_not_mutate_memory(accepted, memory_store)

    assert diary_repo.get(accepted.entry_id) == accepted
    assert proof.memory_mutated is False
    assert memory_store.writes == []


def test_tc_at15_ia_002_provenance_validated_diary_still_does_not_mutate_memory():
    diary_repo = ProductDiaryRepository()
    memory_store = ProductMemoryStore()
    accepted = _run_governed_diary_path("evt_at15_ia_002", diary_repo)
    resolver = ProductSourceResolver({"conversation://conv_at15_ia/msg_1": SourceRefState.RESOLVED})

    report = validate_diary_provenance(accepted, resolver)
    proof = prove_diary_does_not_mutate_memory(accepted, memory_store)

    assert report.resolutions[0].state is SourceRefState.RESOLVED
    assert proof.memory_mutated is False
    assert memory_store.writes == []


def test_tc_at15_ia_003_fresh_runtime_recovers_diary_without_memory_auto_import():
    first_repo = ProductDiaryRepository()
    accepted = _run_governed_diary_path("evt_at15_ia_003", first_repo)

    fresh_repo = ProductDiaryRepository(seed=first_repo.list_entries())
    fresh_memory = ProductMemoryStore()
    recovered = fresh_repo.get(accepted.entry_id)
    proof = prove_diary_does_not_mutate_memory(recovered, fresh_memory)  # type: ignore[arg-type]

    assert recovered == accepted
    assert proof.memory_mutated is False
    assert fresh_memory.writes == []


def test_tc_at15_ia_004_memory_request_containing_diary_authority_object_rejected():
    diary_repo = ProductDiaryRepository()
    accepted = _run_governed_diary_path("evt_at15_ia_004", diary_repo)

    with pytest.raises(TypeError, match="Diary authority objects are not Memory persistence inputs"):
        MemoryPersistenceRequest(
            candidate=accepted,
            source_reflection_id="diary://evt_at15_ia_004",
            created_at="2026-08-23T00:02:00+08:00",
        )


def test_tc_at15_ia_005_legacy_runtime_paths_blocked_for_diary_derived_memory(tmp_path, monkeypatch):
    candidate = ExperienceCandidate(
        title="legacy diary memory attempt",
        what_happened="A governed Diary exists.",
        why_it_matters="This must not bypass Memory governance.",
        category="diary",
    )
    with pytest.raises(RuntimeError, match="Diary-derived memory requires explicit Memory governance"):
        MemoryConsolidator.save(candidate, confirmed=True)

    monkeypatch.setattr("julia_core.runtime.session_recorder.MEMORY_DIR", tmp_path)
    recorder = SessionRecorder(session_id="at15_ia")
    with pytest.raises(RuntimeError, match="Legacy SessionRecorder._write_diary is disabled"):
        recorder._write_diary({"should_remember": True, "diary_entry": "legacy path"})
    assert list(tmp_path.rglob("*.md")) == []


def test_tc_at15_ia_006_cross_context_diary_does_not_contaminate_memory_state():
    repo_a = ProductDiaryRepository()
    repo_b = ProductDiaryRepository()
    memory_a = ProductMemoryStore()
    memory_b = ProductMemoryStore()

    accepted_a = _run_governed_diary_path("evt_at15_ia_006_a", repo_a)
    proof_a = prove_diary_does_not_mutate_memory(accepted_a, memory_a)

    assert repo_a.get(accepted_a.entry_id) == accepted_a
    assert repo_b.list_entries() == []
    assert proof_a.memory_mutated is False
    assert memory_a.writes == []
    assert memory_b.writes == []
