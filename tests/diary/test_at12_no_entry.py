"""Wave5 AT-12 minimal remediation tests: NO_ENTRY creates no Diary artifact."""
from __future__ import annotations

from pathlib import Path
from typing import get_args, get_type_hints

import pytest

from julia_core.capability.diary_writer import DiaryWriter
from julia_core.diary import (
    AcceptedDiaryEntry,
    DiaryCandidate,
    DiaryRepository,
    DiarySourceRef,
    NoEntry,
    NO_ENTRY,
    ReflectionOpportunity,
    ReflectionResult,
    decide_trivial_reflection,
)


def test_at12_remed_no_entry_is_explicit_terminal_result():
    result = decide_trivial_reflection(
        ReflectionOpportunity(
            trigger_id="trig_trivial_day",
            reflection_type="daily",
            reflection_time="2026-08-23T00:00:00+08:00",
            reason="daily scheduled reflection opportunity with no significance markers",
        )
    )

    assert result is NO_ENTRY
    assert isinstance(result, NoEntry)
    assert result is not None
    assert result is not False
    assert result != ""


def test_at12_remed_no_entry_creates_no_canonical_diary_artifact(tmp_path: Path):
    diary_root = tmp_path / "memory" / "diary"
    diary_root.mkdir(parents=True)

    result = decide_trivial_reflection(
        ReflectionOpportunity(
            trigger_id="trig_empty_fs",
            reflection_type="daily",
            reflection_time="2026-08-23T00:00:00+08:00",
        )
    )

    assert result is NO_ENTRY
    assert list(diary_root.rglob("*")) == []


def test_at12_remed_reflection_result_never_accepts_accepted_entry():
    args = get_args(ReflectionResult)
    assert NoEntry in args
    assert DiaryCandidate in args
    assert AcceptedDiaryEntry not in args


def test_at12_remed_repository_accepts_accepted_entry_only():
    hints = get_type_hints(DiaryRepository.append_accepted)
    assert hints["entry"] is AcceptedDiaryEntry
    assert hints["entry"] is not DiaryCandidate
    assert hints["entry"] is not NoEntry


def test_at12_remed_candidate_requires_source_refs():
    with pytest.raises(ValueError):
        DiaryCandidate(
            candidate_id="cand_no_sources",
            reflection_time="2026-08-23T00:00:00+08:00",
            source_refs=(),
            body="This should not pass without sources.",
            provenance=None,
        )


def test_at12_remed_legacy_direct_writer_fails_closed(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("julia_core.capability.diary_writer.MEMORY_DIR", tmp_path)

    with pytest.raises(RuntimeError, match="Legacy DiaryWriter.save_diary is disabled"):
        DiaryWriter.save_diary("# fake diary", "2026-08-23")

    assert list(tmp_path.rglob("*")) == []


def test_at12_remed_no_physical_path_in_source_ref():
    ref = DiarySourceRef("conversation://conv_A/msg_1")
    assert set(vars(ref)) == {"uri"}
    assert "memory/diary" not in ref.uri
