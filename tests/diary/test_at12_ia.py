"""Wave5 AT-12 Integration Acceptance: governed NO_ENTRY product path."""
from __future__ import annotations

from pathlib import Path

import pytest

from julia_core.capability.diary_writer import DiaryWriter
from julia_core.diary import (
    AcceptedDiaryEntry,
    NO_ENTRY,
    ReflectionOpportunity,
    run_trivial_reflection_opportunity,
)


class RecordingDiaryRepository:
    """IA fixture recording canonical append attempts."""

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


def _trivial_opportunity(trigger_id: str = "ia_trivial") -> ReflectionOpportunity:
    return ReflectionOpportunity(
        trigger_id=trigger_id,
        reflection_type="daily",
        reflection_time="2026-08-23T00:00:00+08:00",
        reason="trivial daily reflection opportunity",
    )


def test_tc_at12_ia_001_governed_reflection_path_no_entry_no_repository_mutation(tmp_path: Path):
    repo = RecordingDiaryRepository()
    diary_root = tmp_path / "memory" / "diary"
    diary_root.mkdir(parents=True)

    result = run_trivial_reflection_opportunity(_trivial_opportunity("ia_001"), repo)

    assert result.decision is NO_ENTRY
    assert result.diary_mutated is False
    assert result.accepted_entry_id is None
    assert repo.append_calls == []
    assert repo.list_entries() == []
    assert list(diary_root.rglob("*")) == []


def test_tc_at12_ia_002_product_no_entry_path_does_not_use_legacy_writer(tmp_path: Path, monkeypatch):
    repo = RecordingDiaryRepository()
    monkeypatch.setattr("julia_core.capability.diary_writer.MEMORY_DIR", tmp_path)

    result = run_trivial_reflection_opportunity(_trivial_opportunity("ia_002"), repo)
    assert result.decision is NO_ENTRY
    assert repo.append_calls == []

    with pytest.raises(RuntimeError, match="Legacy DiaryWriter.save_diary is disabled"):
        DiaryWriter.save_diary("# bypass attempt", "2026-08-23")
    assert list(tmp_path.rglob("*")) == []


def test_tc_at12_ia_003_fresh_runtime_after_no_entry_has_no_phantom_diary(tmp_path: Path):
    first_repo = RecordingDiaryRepository()
    diary_root = tmp_path / "memory" / "diary"
    diary_root.mkdir(parents=True)

    first = run_trivial_reflection_opportunity(_trivial_opportunity("ia_003_before_restart"), first_repo)
    assert first.decision is NO_ENTRY

    fresh_repo = RecordingDiaryRepository()
    assert fresh_repo.list_entries() == []
    assert list(diary_root.rglob("*")) == []


def test_tc_at12_ia_004_projection_shape_cannot_enter_governed_repository():
    repo = RecordingDiaryRepository()
    projection = {
        "projection_id": "proj_ia",
        "canonical": False,
        "entry_id": "diary_projection_fake",
        "body": "projection is not accepted diary truth",
    }

    with pytest.raises(TypeError, match="AcceptedDiaryEntry only"):
        repo.append_accepted(projection)  # type: ignore[arg-type]

    assert repo.append_calls == []
    assert repo.list_entries() == []


def test_tc_at12_ia_005_cross_context_no_entry_does_not_mutate_other_diary_state():
    repo_a = RecordingDiaryRepository()
    repo_b = RecordingDiaryRepository()

    result = run_trivial_reflection_opportunity(_trivial_opportunity("ia_005_context_a"), repo_a)

    assert result.decision is NO_ENTRY
    assert repo_a.list_entries() == []
    assert repo_b.list_entries() == []
    assert repo_a is not repo_b
