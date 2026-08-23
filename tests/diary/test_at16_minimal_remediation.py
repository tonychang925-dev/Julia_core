"""Wave5 AT-16 Minimal Remediation: Diary retrieval through Context OS only."""
from __future__ import annotations

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
    trace_diary_context_block,
)
from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime


class ProductDiaryRepository:
    def __init__(self, entries: list[AcceptedDiaryEntry] | None = None) -> None:
        self._entries = {entry.entry_id: entry for entry in entries or []}

    def get(self, entry_id: str) -> AcceptedDiaryEntry | None:
        return self._entries.get(entry_id)

    def list_entries(self, *, before=None, after=None, limit=None) -> list[AcceptedDiaryEntry]:
        entries = list(self._entries.values())
        return entries[:limit] if limit is not None else entries


class ProductSourceResolver:
    def __init__(self, states: dict[str, SourceRefState]) -> None:
        self.states = dict(states)
        self.calls: list[str] = []

    def resolve(self, source_ref: DiarySourceRef) -> SourceRefState:
        self.calls.append(source_ref.uri)
        return self.states.get(source_ref.uri, SourceRefState.MISSING)


class PersonaFixture:
    def get_traits_for_injection(self) -> str:
        return "persona fixture"


class CapabilityFixture:
    def tool_manifest(self) -> str:
        return ""


class JuliaSessionFixture:
    def __init__(self, diary_context_provider=None, legacy_text: str = "", density_text: str = "") -> None:
        self.persona = PersonaFixture()
        self.capability = CapabilityFixture()
        self.diary_context_provider = diary_context_provider
        self.session_id = "session_at16"
        self._legacy_text = legacy_text
        self._density_text = density_text

    def _load_recent_experiences(self) -> str:
        return self._legacy_text

    def _resolve_market_context(self, text: str) -> str:
        return ""


def _provenance() -> DiaryProvenance:
    return DiaryProvenance(
        model_provider="fixture",
        model_name="at16-minimal",
        runtime="pytest",
    )


def _entry(
    entry_id: str = "diary_at16",
    body: str = "我只可以通过 Context OS governed source assembly 进入模型上下文。",
    refs: tuple[DiarySourceRef, ...] | None = None,
) -> AcceptedDiaryEntry:
    return AcceptedDiaryEntry(
        entry_id=entry_id,
        created_at="2026-08-23T00:01:00+08:00",
        reflection_time="2026-08-23T00:00:00+08:00",
        source_refs=refs or (DiarySourceRef("conversation://conv_at16/msg_1"),),
        body=body,
        body_hash="hash_at16",
        provenance=_provenance(),
        title="AT-16 Context OS Diary",
        themes=("diary", "context-os"),
    )


def test_at16_remed_001_governed_diary_provider_builds_context_block_after_provenance_validation():
    entry = _entry("diary_at16_001")
    resolver = ProductSourceResolver({"conversation://conv_at16/msg_1": SourceRefState.RESOLVED})

    admission = admit_diary_for_context(entry, resolver)
    candidate = DiaryContextCandidate(admission)
    block = build_diary_context_block(candidate)
    trace = trace_diary_context_block(block)

    assert admission.admitted is True
    assert admission.body_visible is True
    assert block.domain == "diary"
    assert block.authority == "ContextOS"
    assert block.block_kind == "diary_context_projection"
    assert block.metadata["projection_only"] is True
    assert trace.routed_through_context_os is True
    assert trace.mutated_diary is False
    assert trace.mutated_memory is False
    assert resolver.calls == ["conversation://conv_at16/msg_1"]


def test_at16_remed_002_missing_source_ref_rejected_before_context_block_creation():
    entry = _entry("diary_at16_002", refs=(DiarySourceRef("conversation://conv_missing/msg_404"),))
    resolver = ProductSourceResolver({})

    admission = admit_diary_for_context(entry, resolver)

    assert admission.admitted is False
    assert admission.reason == "missing-or-invalid-source"
    with pytest.raises(ValueError, match="rejected Diary admission cannot become"):
        DiaryContextCandidate(admission)


def test_at16_remed_003_context_block_projection_cannot_be_used_as_authority_object():
    entry = _entry("diary_at16_003")
    admission = admit_diary_for_context(entry, ProductSourceResolver({"conversation://conv_at16/msg_1": SourceRefState.RESOLVED}))
    block = build_diary_context_block(DiaryContextCandidate(admission))

    assert type(block) is ContextBlock
    with pytest.raises(TypeError, match="projection objects are not Diary, Memory, Identity, or Conversation authority"):
        assert_not_diary_context_authority_object(block)


def test_at16_remed_004_runtime_routes_diary_into_model_context_with_trace_only_through_provider():
    entry = _entry("diary_at16_004")
    provider = DiaryContextProvider(
        ProductDiaryRepository([entry]),
        ProductSourceResolver({"conversation://conv_at16/msg_1": SourceRefState.RESOLVED}),
    )
    runtime = ContextExecutionRuntime(JuliaSessionFixture(diary_context_provider=provider))

    pkg = runtime.prepare(
        conversation_id="conv_at16",
        turn_id="turn_at16_004",
        user_text="use diary context if governed",
        history=[],
    )
    messages = pkg.to_messages([], "hello")
    system_text = messages[0]["content"]

    assert "diary_at16_004" in system_text
    assert entry.body in system_text
    assert pkg.diary_frame["routed_through_context_os"] is True
    assert pkg.diary_frame["projection_only"] is True
    assert pkg.retrieval_handles["diary"][0]["routed_through_context_os"] is True
    assert any(item["frame"] == "diary" for item in pkg.provenance)


def test_at16_remed_005_legacy_wake_state_diary_text_is_contained_without_provider():
    legacy_secret = "LEGACY_DIARY_SECRET_SHOULD_NOT_REACH_MODEL"
    session = JuliaSessionFixture(
        diary_context_provider=None,
        legacy_text=f"wake intro\n你当时的感受（日记）:\n{legacy_secret}\nwake outro",
    )
    runtime = ContextExecutionRuntime(session)

    pkg = runtime.prepare(
        conversation_id="conv_at16",
        turn_id="turn_at16_005",
        user_text="no governed diary provider",
        history=[],
    )
    system_text = pkg.to_messages([], "hello")[0]["content"]

    assert legacy_secret not in system_text
    assert "wake intro" in system_text
    assert "wake outro" in system_text
    assert "diary" not in pkg.retrieval_handles


def test_at16_remed_006_density_diary_like_text_is_not_diary_retrieval_authority(monkeypatch):
    density_secret = "DENSITY_DIARY_SECRET_SHOULD_NOT_REACH_MODEL"
    session = JuliaSessionFixture(diary_context_provider=None, legacy_text="wake intro")
    runtime = ContextExecutionRuntime(session)
    monkeypatch.setattr(
        runtime,
        "_load_density_experience",
        lambda: f"--- julia_experience_context.md ---\n# 你的体验记忆\n{density_secret}",
    )

    pkg = runtime.prepare(
        conversation_id="conv_at16",
        turn_id="turn_at16_006",
        user_text="density context",
        history=[],
    )
    system_text = pkg.to_messages([], "hello")[0]["content"]

    assert density_secret not in system_text
    assert pkg.experience_frame["diary_retrieval_authority"] is False
    assert "diary" not in pkg.retrieval_handles


def test_at16_remed_007_cross_context_diary_provider_does_not_leak_between_runtimes():
    entry_a = _entry("diary_at16_context_a", refs=(DiarySourceRef("conversation://conv_a/msg_1"),))
    entry_b = _entry("diary_at16_context_b", refs=(DiarySourceRef("conversation://conv_b/msg_1"),))
    runtime_a = ContextExecutionRuntime(
        JuliaSessionFixture(
            diary_context_provider=DiaryContextProvider(
                ProductDiaryRepository([entry_a]),
                ProductSourceResolver({"conversation://conv_a/msg_1": SourceRefState.RESOLVED}),
            )
        )
    )
    runtime_b = ContextExecutionRuntime(
        JuliaSessionFixture(
            diary_context_provider=DiaryContextProvider(
                ProductDiaryRepository([entry_b]),
                ProductSourceResolver({"conversation://conv_b/msg_1": SourceRefState.RESOLVED}),
            )
        )
    )

    text_a = runtime_a.prepare(conversation_id="conv_a", turn_id="turn_a", user_text="a", history=[]).to_messages([], "a")[0]["content"]
    text_b = runtime_b.prepare(conversation_id="conv_b", turn_id="turn_b", user_text="b", history=[]).to_messages([], "b")[0]["content"]

    assert "diary_at16_context_a" in text_a
    assert "diary_at16_context_b" not in text_a
    assert "diary_at16_context_b" in text_b
    assert "diary_at16_context_a" not in text_b
