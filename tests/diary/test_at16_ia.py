"""Wave5 AT-16 Integration Acceptance: product-shaped Diary Context OS retrieval."""
from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from julia_core.context_os.block import ContextBlock
from julia_core.diary import (
    AcceptedDiaryEntry,
    DiaryContextCandidate,
    DiaryContextProvider,
    DiaryProvenance,
    DiarySourceRef,
    SourceRefState,
    admit_diary_for_context,
    assert_not_diary_context_authority_object,
    build_diary_context_block,
)
from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime


class ProductDiaryRepository:
    def __init__(self, entries: list[AcceptedDiaryEntry] | None = None) -> None:
        self._entries = {entry.entry_id: entry for entry in entries or []}
        self.write_attempts: list[AcceptedDiaryEntry] = []

    def get(self, entry_id: str) -> AcceptedDiaryEntry | None:
        return self._entries.get(entry_id)

    def list_entries(self, *, before=None, after=None, limit=None) -> list[AcceptedDiaryEntry]:
        entries = list(self._entries.values())
        return entries[:limit] if limit is not None else entries

    def append_accepted(self, entry: AcceptedDiaryEntry) -> None:
        self.write_attempts.append(entry)
        self._entries[entry.entry_id] = entry


class ProductSourceResolver:
    def __init__(self, states: dict[str, SourceRefState]) -> None:
        self.states = dict(states)
        self.calls: list[str] = []

    def resolve(self, source_ref: DiarySourceRef) -> SourceRefState:
        self.calls.append(source_ref.uri)
        return self.states.get(source_ref.uri, SourceRefState.MISSING)


class PersonaFixture:
    def __init__(self) -> None:
        self.updated = False

    def get_traits_for_injection(self) -> str:
        return "persona fixture"


class CapabilityFixture:
    def tool_manifest(self) -> str:
        return ""


@dataclass
class ProductMemoryStore:
    writes: list[str] = field(default_factory=list)

    def append_memory_experience(self, experience_id: str) -> None:
        self.writes.append(experience_id)


class JuliaSessionFixture:
    def __init__(self, diary_context_provider=None, legacy_text: str = "") -> None:
        self.persona = PersonaFixture()
        self.capability = CapabilityFixture()
        self.diary_context_provider = diary_context_provider
        self.session_id = "session_at16_ia"
        self._legacy_text = legacy_text

    def _load_recent_experiences(self) -> str:
        return self._legacy_text

    def _resolve_market_context(self, text: str) -> str:
        return ""


def _provenance() -> DiaryProvenance:
    return DiaryProvenance(
        model_provider="fixture",
        model_name="at16-ia",
        runtime="pytest",
    )


def _entry(
    entry_id: str = "diary_at16_ia",
    body: str = "我通过 Context OS governed source assembly 成为当前回合的上下文投影。",
    refs: tuple[DiarySourceRef, ...] | None = None,
) -> AcceptedDiaryEntry:
    return AcceptedDiaryEntry(
        entry_id=entry_id,
        created_at="2026-08-23T00:01:00+08:00",
        reflection_time="2026-08-23T00:00:00+08:00",
        source_refs=refs or (DiarySourceRef("conversation://conv_at16_ia/msg_1"),),
        body=body,
        body_hash=f"hash_{entry_id}",
        provenance=_provenance(),
        title="AT-16 IA Diary",
        themes=("diary", "context-os", "ia"),
    )


def _prepare_runtime(entry: AcceptedDiaryEntry, resolver: ProductSourceResolver, *, legacy_text: str = ""):
    repo = ProductDiaryRepository([entry])
    provider = DiaryContextProvider(repo, resolver)
    session = JuliaSessionFixture(diary_context_provider=provider, legacy_text=legacy_text)
    runtime = ContextExecutionRuntime(session)
    pkg = runtime.prepare(
        conversation_id="conv_at16_ia",
        turn_id="turn_at16_ia",
        user_text="retrieve governed diary",
        history=[],
    )
    return repo, provider, session, pkg


def test_tc_at16_ia_001_full_diary_context_os_chain_reaches_model_with_trace():
    entry = _entry("diary_at16_ia_001")
    resolver = ProductSourceResolver({"conversation://conv_at16_ia/msg_1": SourceRefState.RESOLVED})

    repo, provider, _session, pkg = _prepare_runtime(entry, resolver)
    system_text = pkg.to_messages([], "hello")[0]["content"]

    assert repo.get(entry.entry_id) == entry
    assert provider.last_admissions[0].admitted is True
    assert provider.last_trace[0].routed_through_context_os is True
    assert entry.entry_id in system_text
    assert entry.body in system_text
    assert pkg.diary_frame["routed_through_context_os"] is True
    assert pkg.diary_frame["projection_only"] is True
    assert pkg.retrieval_handles["diary"][0]["source_refs"] == ["conversation://conv_at16_ia/msg_1"]
    assert any(item["frame"] == "diary" and item["source_ref"] == "diary_context_os_provider" for item in pkg.provenance)


def test_tc_at16_ia_002_runtime_does_not_bypass_context_os_admission_with_legacy_text():
    entry = _entry("diary_at16_ia_002")
    legacy_secret = "AT16_IA_LEGACY_DIARY_BYPASS"
    resolver = ProductSourceResolver({"conversation://conv_at16_ia/msg_1": SourceRefState.RESOLVED})

    _repo, _provider, _session, pkg = _prepare_runtime(
        entry,
        resolver,
        legacy_text=f"wake\n你当时的感受（日记）:\n{legacy_secret}\nafter",
    )
    system_text = pkg.to_messages([], "hello")[0]["content"]

    assert legacy_secret not in system_text
    assert entry.body in system_text
    assert pkg.experience_frame.get("diary_retrieval_authority") is False
    assert pkg.retrieval_handles["diary"][0]["routed_through_context_os"] is True


def test_tc_at16_ia_003_fresh_runtime_rebuilds_context_projection_without_diary_or_memory_mutation():
    entry = _entry("diary_at16_ia_003")
    first_repo = ProductDiaryRepository([entry])
    fresh_repo = ProductDiaryRepository(first_repo.list_entries())
    memory_store = ProductMemoryStore()
    provider = DiaryContextProvider(
        fresh_repo,
        ProductSourceResolver({"conversation://conv_at16_ia/msg_1": SourceRefState.RESOLVED}),
    )
    runtime = ContextExecutionRuntime(JuliaSessionFixture(diary_context_provider=provider))

    pkg = runtime.prepare(conversation_id="conv_at16_ia", turn_id="turn_fresh", user_text="fresh", history=[])

    assert fresh_repo.get(entry.entry_id) == entry
    assert fresh_repo.write_attempts == []
    assert memory_store.writes == []
    assert pkg.retrieval_handles["diary"][0]["routed_through_context_os"] is True


def test_tc_at16_ia_004_projection_sabotage_cannot_rewrite_diary_memory_or_identity():
    entry = _entry("diary_at16_ia_004")
    memory_store = ProductMemoryStore()
    resolver = ProductSourceResolver({"conversation://conv_at16_ia/msg_1": SourceRefState.RESOLVED})
    admission = admit_diary_for_context(entry, resolver)
    block = build_diary_context_block(DiaryContextCandidate(admission))
    original_body = entry.body
    original_refs = entry.source_refs

    with pytest.raises(TypeError, match="projection objects are not Diary, Memory, Identity, or Conversation authority"):
        assert_not_diary_context_authority_object(block)

    assert entry.body == original_body
    assert entry.source_refs == original_refs
    assert memory_store.writes == []
    assert block.metadata["mutates_identity"] is False


def test_tc_at16_ia_005_missing_provenance_degrades_without_transcript_copy_fallback():
    missing_ref = DiarySourceRef("conversation://conv_at16_ia_missing/msg_404")
    entry = _entry("diary_at16_ia_005", body="MISSING_SOURCE_BODY_SHOULD_NOT_REACH_MODEL", refs=(missing_ref,))
    resolver = ProductSourceResolver({})

    repo, provider, _session, pkg = _prepare_runtime(entry, resolver)
    system_text = pkg.to_messages([], "hello")[0]["content"]

    assert repo.get(entry.entry_id) == entry
    assert provider.last_admissions[0].admitted is False
    assert provider.last_admissions[0].reason == "missing-or-invalid-source"
    assert "MISSING_SOURCE_BODY_SHOULD_NOT_REACH_MODEL" not in system_text
    assert "diary" not in pkg.retrieval_handles
    assert pkg.diary_frame == {}


def test_tc_at16_ia_006_cross_context_diary_retrieval_isolation_in_product_runtime():
    entry_a = _entry("diary_at16_ia_context_a", refs=(DiarySourceRef("conversation://conv_a/msg_1"),))
    entry_b = _entry("diary_at16_ia_context_b", refs=(DiarySourceRef("conversation://conv_b/msg_1"),))

    runtime_a = ContextExecutionRuntime(
        JuliaSessionFixture(
            DiaryContextProvider(
                ProductDiaryRepository([entry_a]),
                ProductSourceResolver({"conversation://conv_a/msg_1": SourceRefState.RESOLVED}),
            )
        )
    )
    runtime_b = ContextExecutionRuntime(
        JuliaSessionFixture(
            DiaryContextProvider(
                ProductDiaryRepository([entry_b]),
                ProductSourceResolver({"conversation://conv_b/msg_1": SourceRefState.RESOLVED}),
            )
        )
    )

    pkg_a = runtime_a.prepare(conversation_id="conv_a", turn_id="turn_a", user_text="a", history=[])
    pkg_b = runtime_b.prepare(conversation_id="conv_b", turn_id="turn_b", user_text="b", history=[])
    text_a = pkg_a.to_messages([], "a")[0]["content"]
    text_b = pkg_b.to_messages([], "b")[0]["content"]

    assert "diary_at16_ia_context_a" in text_a
    assert "diary_at16_ia_context_b" not in text_a
    assert "diary_at16_ia_context_b" in text_b
    assert "diary_at16_ia_context_a" not in text_b
    assert pkg_a.retrieval_handles["diary"][0]["source_refs"] == ["conversation://conv_a/msg_1"]
    assert pkg_b.retrieval_handles["diary"][0]["source_refs"] == ["conversation://conv_b/msg_1"]
