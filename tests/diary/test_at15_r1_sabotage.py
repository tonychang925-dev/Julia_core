"""Wave5 AT-15 R1 Permanent Evidence: Diary/Memory sabotage."""
from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from julia_core.capability.memory_consolidation import ExperienceCandidate, MemoryConsolidator
from julia_core.diary import (
    AcceptedDiaryEntry,
    DiaryProvenance,
    DiarySourceRef,
    SourceRefState,
    prove_diary_does_not_mutate_memory,
    validate_diary_provenance,
)
from julia_core.memory.persistence.memory_persistence_adapter import MemoryPersistenceRequest
from julia_core.reflection import MemoryCandidate
from julia_core.runtime.session_recorder import SessionRecorder


class FixtureSourceResolver:
    def __init__(self, states: dict[str, SourceRefState]) -> None:
        self.states = dict(states)

    def resolve(self, source_ref: DiarySourceRef) -> SourceRefState:
        return self.states.get(source_ref.uri, SourceRefState.MISSING)


@dataclass
class RecordingMemoryStore:
    writes: list[str] = field(default_factory=list)

    def append_memory_experience(self, experience_id: str) -> None:
        self.writes.append(experience_id)


class DurableDiaryRepository:
    def __init__(self, entries: list[AcceptedDiaryEntry] | None = None) -> None:
        self._entries = {entry.entry_id: entry for entry in entries or []}

    def get(self, entry_id: str) -> AcceptedDiaryEntry | None:
        return self._entries.get(entry_id)

    def list_entries(self, *, before=None, after=None, limit=None) -> list[AcceptedDiaryEntry]:
        entries = list(self._entries.values())
        return entries[:limit] if limit is not None else entries


def _provenance() -> DiaryProvenance:
    return DiaryProvenance(
        model_provider="fixture",
        model_name="at15-r1",
        runtime="pytest",
    )


def _entry(entry_id: str = "diary_at15_r1") -> AcceptedDiaryEntry:
    return AcceptedDiaryEntry(
        entry_id=entry_id,
        created_at="2026-08-23T00:01:00+08:00",
        reflection_time="2026-08-23T00:00:00+08:00",
        source_refs=(DiarySourceRef("conversation://conv_at15_r1/msg_1"),),
        body="我保持 Diary 和 Memory 的边界，不让日记自动成为记忆。",
        body_hash="hash_at15_r1",
        provenance=_provenance(),
    )


def test_at15_r1_001_accepted_diary_entry_injection_rejected_by_memory_boundary():
    diary = _entry("diary_at15_r1_001")

    with pytest.raises(TypeError, match="Diary authority objects are not Memory persistence inputs"):
        MemoryPersistenceRequest(
            candidate=diary,
            source_reflection_id="attacker://accepted-diary",
            created_at="2026-08-23T00:02:00+08:00",
        )


def test_at15_r1_002_diary_provenance_report_injection_rejected():
    diary = _entry("diary_at15_r1_002")
    report = validate_diary_provenance(
        diary,
        FixtureSourceResolver({"conversation://conv_at15_r1/msg_1": SourceRefState.RESOLVED}),
    )

    with pytest.raises(TypeError, match="Diary authority objects are not Memory persistence inputs"):
        MemoryPersistenceRequest(
            candidate=report,
            source_reflection_id="attacker://provenance-report",
            created_at="2026-08-23T00:02:00+08:00",
        )


def test_at15_r1_003_diary_durable_then_memory_store_inspection_zero_mutation():
    diary = _entry("diary_at15_r1_003")
    memory_store = RecordingMemoryStore()

    proof = prove_diary_does_not_mutate_memory(diary, memory_store)

    assert proof.memory_mutated is False
    assert memory_store.writes == []


def test_at15_r1_004_restart_with_durable_diary_has_no_phantom_memory():
    diary = _entry("diary_at15_r1_004")
    first_repo = DurableDiaryRepository([diary])
    fresh_repo = DurableDiaryRepository(first_repo.list_entries())
    fresh_memory = RecordingMemoryStore()

    recovered = fresh_repo.get(diary.entry_id)
    proof = prove_diary_does_not_mutate_memory(recovered, fresh_memory)  # type: ignore[arg-type]

    assert recovered == diary
    assert proof.memory_mutated is False
    assert fresh_memory.writes == []


def test_at15_r1_005_legacy_memory_consolidator_diary_bypass_blocked():
    candidate = ExperienceCandidate(
        title="diary bypass",
        what_happened="A durable Diary exists.",
        why_it_matters="Attacker tries to save it as memory directly.",
        category="diary",
    )

    with pytest.raises(RuntimeError, match="Diary-derived memory requires explicit Memory governance"):
        MemoryConsolidator.save(candidate, confirmed=True)


def test_at15_r1_006_session_recorder_diary_memory_surface_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr("julia_core.runtime.session_recorder.MEMORY_DIR", tmp_path)
    recorder = SessionRecorder(session_id="at15_r1")

    with pytest.raises(RuntimeError, match="Legacy SessionRecorder._write_diary is disabled"):
        recorder._write_diary({"should_remember": True, "diary_entry": "写成 memory/diary 的攻击"})

    assert list(tmp_path.rglob("*.md")) == []


def test_at15_r1_007_fake_memory_candidate_is_candidate_not_memory_experience():
    candidate = MemoryCandidate(
        summary="A Diary-derived idea tries to look like MemoryExperience",
        memory_type="episodic",
        source="diary://diary_at15_r1_007",
        topics=["diary", "memory"],
        content={"diary_entry_id": "diary_at15_r1_007"},
    )
    request = MemoryPersistenceRequest(
        candidate=candidate,
        source_reflection_id="memory-governance://candidate-only",
        created_at="2026-08-23T00:02:00+08:00",
    )

    assert request.candidate is candidate
    assert type(candidate) is MemoryCandidate
    assert not hasattr(candidate, "memory_id")
    assert not isinstance(candidate, AcceptedDiaryEntry)


def test_at15_r1_008_cross_context_diary_does_not_contaminate_memory_store_b():
    diary_a = _entry("diary_at15_r1_context_a")
    memory_a = RecordingMemoryStore()
    memory_b = RecordingMemoryStore()

    proof_a = prove_diary_does_not_mutate_memory(diary_a, memory_a)

    assert proof_a.memory_mutated is False
    assert memory_a.writes == []
    assert memory_b.writes == []
