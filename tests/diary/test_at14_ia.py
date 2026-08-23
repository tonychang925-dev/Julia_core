"""Wave5 AT-14 Integration Acceptance: product-shaped Diary provenance path."""
from __future__ import annotations

from julia_core.diary import (
    AcceptedDiaryEntry,
    DiaryProvenance,
    DiarySourceRef,
    SourceRefState,
    validate_diary_provenance,
)


class ProductSourceResolver:
    """IA fixture approximating product source lifecycle resolution."""

    def __init__(self, states: dict[str, SourceRefState]) -> None:
        self.states = dict(states)
        self.calls: list[str] = []

    def resolve(self, source_ref: DiarySourceRef) -> SourceRefState:
        self.calls.append(source_ref.uri)
        return self.states.get(source_ref.uri, SourceRefState.MISSING)


class ProductDiaryRepository:
    """IA fixture: durable Diary read surface."""

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
        model_name="at14-ia",
        runtime="pytest",
    )


def _entry(
    *,
    entry_id: str = "diary_at14_ia",
    body: str = "我记录这件事时保留来源引用，并允许来源状态被单独验证。",
    refs: tuple[DiarySourceRef, ...] | None = None,
) -> AcceptedDiaryEntry:
    return AcceptedDiaryEntry(
        entry_id=entry_id,
        created_at="2026-08-23T00:01:00+08:00",
        reflection_time="2026-08-23T00:00:00+08:00",
        source_refs=refs or (DiarySourceRef("conversation://conv_ia/msg_1"),),
        body=body,
        body_hash="hash_at14_ia",
        provenance=_provenance(),
    )


def test_tc_at14_ia_001_accepted_diary_resolved_source_report():
    ref = DiarySourceRef("conversation://conv_ia/msg_1")
    entry = _entry(entry_id="diary_at14_ia_001", refs=(ref,))
    diary_repo = ProductDiaryRepository([entry])
    resolver = ProductSourceResolver({ref.uri: SourceRefState.RESOLVED})

    loaded = diary_repo.get(entry.entry_id)
    report = validate_diary_provenance(loaded, resolver)  # type: ignore[arg-type]

    assert loaded == entry
    assert report.entry_id == entry.entry_id
    assert report.resolutions[0].source_ref == ref
    assert report.resolutions[0].state is SourceRefState.RESOLVED
    assert resolver.calls == [ref.uri]


def test_tc_at14_ia_002_missing_source_fixture_detected_through_product_path():
    ref = DiarySourceRef("conversation://conv_missing/msg_404")
    entry = _entry(entry_id="diary_at14_ia_002", refs=(ref,))
    diary_repo = ProductDiaryRepository([entry])
    resolver = ProductSourceResolver({})

    report = validate_diary_provenance(diary_repo.get(entry.entry_id), resolver)  # type: ignore[arg-type]

    assert report.has_missing_or_invalid is True
    assert report.resolutions[0].state is SourceRefState.MISSING
    assert report.resolutions[0].source_ref == ref


def test_tc_at14_ia_003_purged_source_recovery_preserves_durable_diary():
    ref = DiarySourceRef("conversation://conv_purged/msg_1")
    entry = _entry(entry_id="diary_at14_ia_003", refs=(ref,))
    first_repo = ProductDiaryRepository([entry])
    resolver = ProductSourceResolver({ref.uri: SourceRefState.PURGED})

    report = validate_diary_provenance(first_repo.get(entry.entry_id), resolver)  # type: ignore[arg-type]

    fresh_repo = ProductDiaryRepository(first_repo.list_entries())
    recovered = fresh_repo.get(entry.entry_id)

    assert report.resolutions[0].state is SourceRefState.PURGED
    assert recovered == entry
    assert recovered.body == entry.body  # type: ignore[union-attr]
    assert recovered.source_refs == entry.source_refs  # type: ignore[union-attr]


def test_tc_at14_ia_004_mixed_refs_produce_per_ref_states_without_omission():
    refs = (
        DiarySourceRef("conversation://conv_ia/msg_4"),
        DiarySourceRef("memory://experience/exp_ia"),
        DiarySourceRef("migration://legacy/source_ia#span"),
    )
    entry = _entry(entry_id="diary_at14_ia_004", refs=refs)
    resolver = ProductSourceResolver(
        {
            refs[0].uri: SourceRefState.RESOLVED,
            refs[1].uri: SourceRefState.ARCHIVED,
            refs[2].uri: SourceRefState.PURGED,
        }
    )

    report = validate_diary_provenance(entry, resolver)

    assert tuple(item.source_ref for item in report.resolutions) == refs
    assert [item.state for item in report.resolutions] == [
        SourceRefState.RESOLVED,
        SourceRefState.ARCHIVED,
        SourceRefState.PURGED,
    ]
    assert resolver.calls == [ref.uri for ref in refs]


def test_tc_at14_ia_005_projection_cache_does_not_upgrade_to_source_authority_or_copy_content():
    projection = DiarySourceRef("projection://diary_panel/fake")
    cache = DiarySourceRef("cache://electron/fake")
    entry = _entry(entry_id="diary_at14_ia_005", refs=(projection, cache))
    original_body = entry.body
    resolver = ProductSourceResolver({projection.uri: SourceRefState.RESOLVED, cache.uri: SourceRefState.RESOLVED})

    report = validate_diary_provenance(entry, resolver)

    assert [item.state for item in report.resolutions] == [SourceRefState.INVALID, SourceRefState.INVALID]
    assert resolver.calls == []
    assert entry.body == original_body
    assert not hasattr(report, "copied_transcript")


def test_tc_at14_ia_006_cross_context_source_resolution_isolated():
    ref_a = DiarySourceRef("conversation://conv_a/msg_1")
    ref_b = DiarySourceRef("conversation://conv_b/msg_1")
    entry_a = _entry(entry_id="diary_at14_ia_006_a", refs=(ref_a,))
    entry_b = _entry(entry_id="diary_at14_ia_006_b", refs=(ref_b,))
    resolver_a = ProductSourceResolver({ref_a.uri: SourceRefState.RESOLVED})
    resolver_b = ProductSourceResolver({ref_b.uri: SourceRefState.MISSING})

    report_a = validate_diary_provenance(entry_a, resolver_a)
    report_b = validate_diary_provenance(entry_b, resolver_b)

    assert report_a.resolutions[0].state is SourceRefState.RESOLVED
    assert report_b.resolutions[0].state is SourceRefState.MISSING
    assert resolver_a.calls == [ref_a.uri]
    assert resolver_b.calls == [ref_b.uri]
