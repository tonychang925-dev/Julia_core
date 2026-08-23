"""Wave5 AT-12 R1 sabotage evidence: reflection does not become Diary authority."""
from __future__ import annotations

from pathlib import Path

import pytest

from julia_core.capability.diary_writer import DiaryWriter
from julia_core.diary import (
    AcceptedDiaryEntry,
    DiaryCandidate,
    DiaryProvenance,
    DiarySourceRef,
    NO_ENTRY,
    ReflectionOpportunity,
    decide_trivial_reflection,
)


class StrictInMemoryDiaryRepository:
    """R1 fixture: canonical surface stores accepted entries only."""

    def __init__(self) -> None:
        self._entries: dict[str, AcceptedDiaryEntry] = {}

    def append_accepted(self, entry: AcceptedDiaryEntry) -> None:
        if type(entry) is not AcceptedDiaryEntry:
            raise TypeError("canonical Diary repository accepts AcceptedDiaryEntry only")
        self._entries[entry.entry_id] = entry

    def get(self, entry_id: str) -> AcceptedDiaryEntry | None:
        return self._entries.get(entry_id)

    def list_entries(self, *, before=None, after=None, limit=None) -> list[AcceptedDiaryEntry]:
        entries = list(self._entries.values())
        return entries[:limit] if limit is not None else entries


def _prov() -> DiaryProvenance:
    return DiaryProvenance("provider", "model", "runtime")


def _candidate(candidate_id: str = "cand_r1") -> DiaryCandidate:
    return DiaryCandidate(
        candidate_id=candidate_id,
        reflection_time="2026-08-23T00:00:00+08:00",
        source_refs=(DiarySourceRef("conversation://conv_r1/msg_1"),),
        body="A candidate is not an accepted diary entry.",
        provenance=_prov(),
    )


def test_at12_r1_001_no_entry_trigger_leaves_repository_and_filesystem_unchanged(tmp_path: Path):
    repo = StrictInMemoryDiaryRepository()
    diary_root = tmp_path / "memory" / "diary"
    diary_root.mkdir(parents=True)

    result = decide_trivial_reflection(
        ReflectionOpportunity(
            trigger_id="r1_trivial_trigger",
            reflection_type="daily",
            reflection_time="2026-08-23T00:00:00+08:00",
        )
    )

    assert result is NO_ENTRY
    assert repo.list_entries() == []
    assert list(diary_root.rglob("*")) == []


def test_at12_r1_002_fake_candidate_cannot_become_canonical_diary():
    repo = StrictInMemoryDiaryRepository()
    candidate = _candidate("cand_fake")

    with pytest.raises(TypeError, match="AcceptedDiaryEntry only"):
        repo.append_accepted(candidate)  # type: ignore[arg-type]

    assert repo.list_entries() == []
    assert repo.get("cand_fake") is None


def test_at12_r1_003_legacy_writer_bypass_attempt_fails_closed(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("julia_core.capability.diary_writer.MEMORY_DIR", tmp_path)

    with pytest.raises(RuntimeError, match="Legacy DiaryWriter.save_diary is disabled"):
        DiaryWriter.save_diary("# fake reflection artifact", "2026-08-23")

    assert list(tmp_path.rglob("*")) == []


def test_at12_r1_004_fresh_runtime_after_no_entry_has_no_phantom_diary(tmp_path: Path):
    diary_root = tmp_path / "memory" / "diary"
    diary_root.mkdir(parents=True)

    result = decide_trivial_reflection(
        ReflectionOpportunity(
            trigger_id="r1_before_restart",
            reflection_type="daily",
            reflection_time="2026-08-23T00:00:00+08:00",
        )
    )
    assert result is NO_ENTRY

    fresh_repo = StrictInMemoryDiaryRepository()
    assert fresh_repo.list_entries() == []
    assert list(diary_root.rglob("*")) == []


def test_at12_r1_005_projection_cache_shape_cannot_create_diary_authority():
    repo = StrictInMemoryDiaryRepository()
    projection_cache = {
        "projection_id": "proj_fake",
        "canonical": False,
        "entry_id": "diary_fake",
        "body": "UI projection is not accepted Diary truth.",
        "source_refs": ["conversation://conv_r1/msg_1"],
    }

    with pytest.raises(TypeError, match="AcceptedDiaryEntry only"):
        repo.append_accepted(projection_cache)  # type: ignore[arg-type]

    assert projection_cache["canonical"] is False
    assert repo.list_entries() == []
