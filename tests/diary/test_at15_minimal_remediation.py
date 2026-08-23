"""Wave5 AT-15 Minimal Remediation: Diary is not Memory."""
from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from julia_core.capability.memory_consolidation import ExperienceCandidate, MemoryConsolidator
from julia_core.diary import (
    AcceptedDiaryEntry,
    DiaryProvenance,
    DiaryProvenanceReport,
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
        model_name="at15-minimal",
        runtime="pytest",
    )


def _entry(entry_id: str = "diary_at15") -> AcceptedDiaryEntry:
    return AcceptedDiaryEntry(
        entry_id=entry_id,
        created_at="2026-08-23T00:01:00+08:00",
        reflection_time="2026-08-23T00:00:00+08:00",
        source_refs=(DiarySourceRef("conversation://conv_at15/msg_1"),),
        body="我把这条日记保留为 Diary，而不是自动变成 Memory。",
        body_hash="hash_at15",
        provenance=_provenance(),
    )


def test_at15_remed_001_accepted_diary_entry_rejected_as_memory_persistence_input():
    diary = _entry("diary_at15_001")

    with pytest.raises(TypeError, match="Diary authority objects are not Memory persistence inputs"):
        MemoryPersistenceRequest(
            candidate=diary,
            source_reflection_id="diary://diary_at15_001",
            created_at="2026-08-23T00:02:00+08:00",
        )


def test_at15_remed_002_provenance_report_rejected_as_memory_persistence_input():
    diary = _entry("diary_at15_002")
    report = validate_diary_provenance(
        diary,
        FixtureSourceResolver({"conversation://conv_at15/msg_1": SourceRefState.RESOLVED}),
    )

    assert type(report) is DiaryProvenanceReport
    with pytest.raises(TypeError, match="Diary authority objects are not Memory persistence inputs"):
        MemoryPersistenceRequest(
            candidate=report,
            source_reflection_id="diary://diary_at15_002/provenance",
            created_at="2026-08-23T00:02:00+08:00",
        )


def test_at15_remed_003_durable_and_provenance_validated_diary_leaves_memory_store_unchanged():
    diary = _entry("diary_at15_003")
    memory_store = RecordingMemoryStore()
    report = validate_diary_provenance(
        diary,
        FixtureSourceResolver({"conversation://conv_at15/msg_1": SourceRefState.RESOLVED}),
    )

    proof = prove_diary_does_not_mutate_memory(diary, memory_store)

    assert report.resolutions[0].state is SourceRefState.RESOLVED
    assert proof.memory_mutated is False
    assert memory_store.writes == []


def test_at15_remed_004_memory_candidate_remains_separate_and_requires_memory_governance():
    candidate = MemoryCandidate(
        summary="Diary insight may be considered later",
        memory_type="episodic",
        source="diary://diary_at15_004",
        topics=["diary", "memory-boundary"],
    )

    request = MemoryPersistenceRequest(
        candidate=candidate,
        source_reflection_id="memory-governance://candidate_at15_004",
        created_at="2026-08-23T00:02:00+08:00",
    )

    assert request.candidate is candidate
    assert type(candidate) is MemoryCandidate
    assert not isinstance(candidate, AcceptedDiaryEntry)


def test_at15_remed_005_legacy_memory_consolidator_rejects_diary_derived_memory_authority():
    candidate = ExperienceCandidate(
        title="Diary-derived insight",
        what_happened="A Diary entry existed.",
        why_it_matters="This would require Memory governance.",
        category="diary",
    )

    with pytest.raises(RuntimeError, match="Diary-derived memory requires explicit Memory governance"):
        MemoryConsolidator.save(candidate, confirmed=True)


def test_at15_remed_006_legacy_session_recorder_diary_memory_surface_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr("julia_core.runtime.session_recorder.MEMORY_DIR", tmp_path)
    recorder = SessionRecorder(session_id="at15")

    with pytest.raises(RuntimeError, match="Legacy SessionRecorder._write_diary is disabled"):
        recorder._write_diary({"diary_entry": "我不应该被写入 legacy memory path"})

    assert list(tmp_path.rglob("*.md")) == []


def test_at15_remed_007_fresh_runtime_does_not_auto_import_durable_diary_into_memory():
    diary = _entry("diary_at15_007")
    first_diary_repo = DurableDiaryRepository([diary])
    fresh_diary_repo = DurableDiaryRepository(first_diary_repo.list_entries())
    fresh_memory_store = RecordingMemoryStore()

    recovered = fresh_diary_repo.get(diary.entry_id)
    proof = prove_diary_does_not_mutate_memory(recovered, fresh_memory_store)  # type: ignore[arg-type]

    assert recovered == diary
    assert proof.memory_mutated is False
    assert fresh_memory_store.writes == []
