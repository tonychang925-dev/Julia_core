"""Wave5 AT-14 Minimal Remediation: Diary provenance source resolution."""
from __future__ import annotations

from julia_core.diary import (
    AcceptedDiaryEntry,
    DiaryProvenance,
    DiarySourceRef,
    SourceRefState,
    validate_diary_provenance,
)


class FixtureSourceResolver:
    """Fixture-backed resolver mapping source_ref URI to lifecycle state."""

    def __init__(self, states: dict[str, SourceRefState]) -> None:
        self.states = dict(states)
        self.calls: list[str] = []

    def resolve(self, source_ref: DiarySourceRef) -> SourceRefState:
        self.calls.append(source_ref.uri)
        return self.states.get(source_ref.uri, SourceRefState.MISSING)


def _provenance() -> DiaryProvenance:
    return DiaryProvenance(
        model_provider="fixture",
        model_name="at14-minimal",
        runtime="pytest",
    )


def _entry(
    *,
    entry_id: str = "diary_at14",
    body: str = "我保留这条日记的来源引用，而不是复制来源内容。",
    refs: tuple[DiarySourceRef, ...] | None = None,
) -> AcceptedDiaryEntry:
    return AcceptedDiaryEntry(
        entry_id=entry_id,
        created_at="2026-08-23T00:01:00+08:00",
        reflection_time="2026-08-23T00:00:00+08:00",
        source_refs=refs or (DiarySourceRef("conversation://conv_at14/msg_1"),),
        body=body,
        body_hash="hash_at14",
        provenance=_provenance(),
    )


def test_at14_remed_001_resolved_source_ref_reports_explicit_state():
    ref = DiarySourceRef("conversation://conv_at14/msg_1")
    entry = _entry(refs=(ref,))
    resolver = FixtureSourceResolver({ref.uri: SourceRefState.RESOLVED})

    report = validate_diary_provenance(entry, resolver)

    assert report.entry_id == entry.entry_id
    assert len(report.resolutions) == 1
    assert report.resolutions[0].source_ref == ref
    assert report.resolutions[0].state is SourceRefState.RESOLVED
    assert report.resolutions[0].namespace == "conversation"
    assert resolver.calls == [ref.uri]


def test_at14_remed_002_missing_canonical_looking_ref_detected_not_silent():
    ref = DiarySourceRef("conversation://conv_missing/msg_404")
    entry = _entry(entry_id="diary_at14_missing", refs=(ref,))
    resolver = FixtureSourceResolver({})

    report = validate_diary_provenance(entry, resolver)

    assert report.has_missing_or_invalid is True
    assert report.resolutions[0].state is SourceRefState.MISSING
    assert report.resolutions[0].source_ref == ref
    assert resolver.calls == [ref.uri]


def test_at14_remed_003_purged_source_preserves_diary_without_rewrite():
    ref = DiarySourceRef("conversation://conv_purged/msg_1")
    entry = _entry(entry_id="diary_at14_purged", refs=(ref,))
    original_body = entry.body
    original_refs = entry.source_refs
    resolver = FixtureSourceResolver({ref.uri: SourceRefState.PURGED})

    report = validate_diary_provenance(entry, resolver)

    assert report.resolutions[0].state is SourceRefState.PURGED
    assert entry.body == original_body
    assert entry.source_refs == original_refs


def test_at14_remed_004_archived_and_tombstoned_are_distinct_lifecycle_states():
    archived = DiarySourceRef("conversation://conv_archived/msg_1")
    tombstoned = DiarySourceRef("conversation://conv_tombstoned/msg_1")
    entry = _entry(entry_id="diary_at14_lifecycle", refs=(archived, tombstoned))
    resolver = FixtureSourceResolver(
        {
            archived.uri: SourceRefState.ARCHIVED,
            tombstoned.uri: SourceRefState.TOMBSTONED,
        }
    )

    report = validate_diary_provenance(entry, resolver)

    assert [item.state for item in report.resolutions] == [SourceRefState.ARCHIVED, SourceRefState.TOMBSTONED]
    assert [item.source_ref for item in report.resolutions] == [archived, tombstoned]
    assert resolver.calls == [archived.uri, tombstoned.uri]


def test_at14_remed_005_invalid_projection_ref_reported_without_resolver_trust():
    ref = DiarySourceRef("projection://diary_ui/fake")
    entry = _entry(entry_id="diary_at14_invalid", refs=(ref,))
    resolver = FixtureSourceResolver({ref.uri: SourceRefState.RESOLVED})

    report = validate_diary_provenance(entry, resolver)

    assert report.has_missing_or_invalid is True
    assert report.resolutions[0].state is SourceRefState.INVALID
    assert report.resolutions[0].namespace == "INVALID"
    assert resolver.calls == []


def test_at14_remed_006_provenance_validation_does_not_copy_transcript_content_or_mutate_diary():
    ref = DiarySourceRef("conversation://conv_missing/msg_999")
    entry = _entry(entry_id="diary_at14_no_copy", refs=(ref,))
    original_body = entry.body
    original_hash = entry.body_hash
    resolver = FixtureSourceResolver({})

    report = validate_diary_provenance(entry, resolver)

    assert report.resolutions[0].state is SourceRefState.MISSING
    assert not hasattr(report.resolutions[0], "content")
    assert "Tony said" not in entry.body
    assert entry.body == original_body
    assert entry.body_hash == original_hash
    assert entry.source_refs == (ref,)
