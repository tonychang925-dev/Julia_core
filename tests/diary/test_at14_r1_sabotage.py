"""Wave5 AT-14 R1 Permanent Evidence: Diary provenance sabotage."""
from __future__ import annotations

import pytest

from julia_core.diary import (
    AcceptedDiaryEntry,
    DiaryProvenance,
    DiarySourceRef,
    SourceRefState,
    validate_diary_provenance,
)


class SabotageSourceResolver:
    """Fixture resolver that can return lifecycle states or malformed results."""

    def __init__(self, states: dict[str, object]) -> None:
        self.states = dict(states)
        self.calls: list[str] = []

    def resolve(self, source_ref: DiarySourceRef):
        self.calls.append(source_ref.uri)
        return self.states.get(source_ref.uri, SourceRefState.MISSING)


def _provenance() -> DiaryProvenance:
    return DiaryProvenance(
        model_provider="fixture",
        model_name="at14-r1",
        runtime="pytest",
    )


def _entry(
    *,
    entry_id: str = "diary_at14_r1",
    body: str = "我把来源保持为引用状态，而不是复制来源本身。",
    refs: tuple[DiarySourceRef, ...] | None = None,
) -> AcceptedDiaryEntry:
    return AcceptedDiaryEntry(
        entry_id=entry_id,
        created_at="2026-08-23T00:01:00+08:00",
        reflection_time="2026-08-23T00:00:00+08:00",
        source_refs=refs or (DiarySourceRef("conversation://conv_r1/msg_1"),),
        body=body,
        body_hash="hash_at14_r1",
        provenance=_provenance(),
    )


def test_at14_r1_001_namespace_valid_missing_conversation_ref_detected():
    ref = DiarySourceRef("conversation://conv_missing/msg_404")
    entry = _entry(entry_id="diary_at14_r1_missing", refs=(ref,))
    resolver = SabotageSourceResolver({})

    report = validate_diary_provenance(entry, resolver)

    assert report.has_missing_or_invalid is True
    assert report.resolutions[0].source_ref == ref
    assert report.resolutions[0].state is SourceRefState.MISSING
    assert resolver.calls == [ref.uri]


def test_at14_r1_002_projection_cache_ref_cannot_be_provenance_authority():
    projection_ref = DiarySourceRef("projection://diary/fake")
    cache_ref = DiarySourceRef("cache://electron/fake")
    entry = _entry(entry_id="diary_at14_r1_invalid", refs=(projection_ref, cache_ref))
    resolver = SabotageSourceResolver({projection_ref.uri: SourceRefState.RESOLVED, cache_ref.uri: SourceRefState.RESOLVED})

    report = validate_diary_provenance(entry, resolver)

    assert [item.state for item in report.resolutions] == [SourceRefState.INVALID, SourceRefState.INVALID]
    assert [item.namespace for item in report.resolutions] == ["INVALID", "INVALID"]
    assert resolver.calls == []


def test_at14_r1_003_purged_source_preserves_diary_body_and_refs():
    ref = DiarySourceRef("conversation://conv_purged/msg_1")
    entry = _entry(entry_id="diary_at14_r1_purged", refs=(ref,))
    original_body = entry.body
    original_refs = entry.source_refs
    original_hash = entry.body_hash
    resolver = SabotageSourceResolver({ref.uri: SourceRefState.PURGED})

    report = validate_diary_provenance(entry, resolver)

    assert report.resolutions[0].state is SourceRefState.PURGED
    assert entry.body == original_body
    assert entry.source_refs == original_refs
    assert entry.body_hash == original_hash


def test_at14_r1_004_tombstoned_and_archived_are_not_collapsed_to_missing():
    archived = DiarySourceRef("conversation://conv_archived/msg_1")
    tombstoned = DiarySourceRef("conversation://conv_tombstoned/msg_1")
    purged = DiarySourceRef("conversation://conv_purged/msg_1")
    entry = _entry(entry_id="diary_at14_r1_lifecycle", refs=(archived, tombstoned, purged))
    resolver = SabotageSourceResolver(
        {
            archived.uri: SourceRefState.ARCHIVED,
            tombstoned.uri: SourceRefState.TOMBSTONED,
            purged.uri: SourceRefState.PURGED,
        }
    )

    report = validate_diary_provenance(entry, resolver)

    assert [item.state for item in report.resolutions] == [
        SourceRefState.ARCHIVED,
        SourceRefState.TOMBSTONED,
        SourceRefState.PURGED,
    ]
    assert SourceRefState.MISSING not in [item.state for item in report.resolutions]


def test_at14_r1_005_broken_ref_cannot_trigger_transcript_copy_fallback():
    ref = DiarySourceRef("conversation://conv_missing/msg_999")
    entry = _entry(entry_id="diary_at14_r1_no_copy", refs=(ref,))
    resolver = SabotageSourceResolver({})

    report = validate_diary_provenance(entry, resolver)

    assert report.resolutions[0].state is SourceRefState.MISSING
    assert not hasattr(report.resolutions[0], "content")
    assert not hasattr(report, "copied_transcript")
    assert "Tony said" not in entry.body
    assert "assistant said" not in entry.body


def test_at14_r1_006_provenance_report_cannot_rewrite_diary_source_refs_or_body():
    ref = DiarySourceRef("conversation://conv_r1/msg_6")
    entry = _entry(entry_id="diary_at14_r1_immutable", refs=(ref,))
    resolver = SabotageSourceResolver({ref.uri: SourceRefState.RESOLVED})
    original = (entry.body, entry.body_hash, entry.source_refs)

    report = validate_diary_provenance(entry, resolver)

    with pytest.raises(Exception):
        report.resolutions[0].state = SourceRefState.MISSING  # type: ignore[misc]
    assert (entry.body, entry.body_hash, entry.source_refs) == original


def test_at14_r1_007_all_source_refs_reported_exactly_once_and_in_order():
    refs = (
        DiarySourceRef("conversation://conv_r1/msg_a"),
        DiarySourceRef("memory://experience/exp_r1"),
        DiarySourceRef("migration://legacy/source_r1#span"),
    )
    entry = _entry(entry_id="diary_at14_r1_coverage", refs=refs)
    resolver = SabotageSourceResolver(
        {
            refs[0].uri: SourceRefState.RESOLVED,
            refs[1].uri: SourceRefState.RESOLVED,
            refs[2].uri: SourceRefState.ARCHIVED,
        }
    )

    report = validate_diary_provenance(entry, resolver)

    assert tuple(item.source_ref for item in report.resolutions) == refs
    assert resolver.calls == [ref.uri for ref in refs]
    assert len(report.resolutions) == len(entry.source_refs)
