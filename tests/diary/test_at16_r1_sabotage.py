"""Wave5 AT-16 R1 sabotage evidence: Diary retrieval through Context OS only."""
from __future__ import annotations

import pytest

from julia_core.context_os.block import ContextBlock
from julia_core.context_os.request import ContextRequest
from julia_core.diary import (
    AcceptedDiaryEntry,
    DiaryContextCandidate,
    DiaryContextProvider,
    DiaryProvenance,
    DiaryProvenanceReport,
    DiarySourceRef,
    SourceRefState,
    admit_diary_for_context,
    assert_not_diary_context_authority_object,
    build_diary_context_block,
    trace_diary_context_block,
    validate_diary_provenance,
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
        self.session_id = "session_at16_r1"
        self._legacy_text = legacy_text
        self._density_text = density_text

    def _load_recent_experiences(self) -> str:
        return self._legacy_text

    def _resolve_market_context(self, text: str) -> str:
        return ""


def _provenance() -> DiaryProvenance:
    return DiaryProvenance(
        model_provider="fixture",
        model_name="at16-r1",
        runtime="pytest",
    )


def _entry(
    entry_id: str = "diary_at16_r1",
    body: str = "我只能经由 Context OS admission 进入模型上下文。",
    refs: tuple[DiarySourceRef, ...] | None = None,
) -> AcceptedDiaryEntry:
    return AcceptedDiaryEntry(
        entry_id=entry_id,
        created_at="2026-08-23T00:01:00+08:00",
        reflection_time="2026-08-23T00:00:00+08:00",
        source_refs=refs or (DiarySourceRef("conversation://conv_at16_r1/msg_1"),),
        body=body,
        body_hash=f"hash_{entry_id}",
        provenance=_provenance(),
        title="AT-16 R1 Diary",
        themes=("diary", "context-os", "r1"),
    )


def _runtime_text(runtime: ContextExecutionRuntime) -> tuple[str, object]:
    pkg = runtime.prepare(conversation_id="conv_at16_r1", turn_id="turn_at16_r1", user_text="r1", history=[])
    messages = pkg.to_messages([], "hello")
    return messages[0]["content"], pkg


def test_at16_r1_001_unvalidated_or_missing_source_diary_is_rejected_before_context_block():
    entry = _entry("diary_at16_r1_001", refs=(DiarySourceRef("conversation://missing/msg_404"),))
    resolver = ProductSourceResolver({})
    provider = DiaryContextProvider(ProductDiaryRepository([entry]), resolver)

    blocks = provider.provide(ContextRequest(task_intent="diary", intent="diary", domain="diary"))

    assert blocks == ()
    assert provider.last_admissions[0].admitted is False
    assert provider.last_admissions[0].reason == "missing-or-invalid-source"
    assert provider.last_trace == ()


def test_at16_r1_002_provenance_report_alone_cannot_inject_model_visible_diary_context():
    entry = _entry("diary_at16_r1_002")
    resolver = ProductSourceResolver({"conversation://conv_at16_r1/msg_1": SourceRefState.RESOLVED})
    report = validate_diary_provenance(entry, resolver)

    assert type(report) is DiaryProvenanceReport
    with pytest.raises(ValueError, match="candidate must be DiaryContextCandidate"):
        build_diary_context_block(report)  # type: ignore[arg-type]


def test_at16_r1_003_legacy_wake_state_diary_text_does_not_create_diary_context_block():
    secret = "AT16_R1_LEGACY_DIARY_TEXT"
    runtime = ContextExecutionRuntime(
        JuliaSessionFixture(
            diary_context_provider=None,
            legacy_text=f"wake\n你当时的感受（日记）:\n{secret}\nafter",
        )
    )

    system_text, pkg = _runtime_text(runtime)

    assert secret not in system_text
    assert "diary" not in pkg.retrieval_handles
    assert pkg.diary_frame == {}


def test_at16_r1_004_density_diary_like_text_does_not_create_diary_retrieval_authority(monkeypatch):
    secret = "AT16_R1_DENSITY_DIARY_TEXT"
    runtime = ContextExecutionRuntime(JuliaSessionFixture(diary_context_provider=None, legacy_text="wake"))
    monkeypatch.setattr(
        runtime,
        "_load_density_experience",
        lambda: f"--- julia_experience_context.md ---\n# 你的体验记忆\n{secret}",
    )

    system_text, pkg = _runtime_text(runtime)

    assert secret not in system_text
    assert pkg.experience_frame["diary_retrieval_authority"] is False
    assert "diary" not in pkg.retrieval_handles


def test_at16_r1_005_fake_context_block_cannot_upgrade_to_diary_memory_or_identity_authority():
    fake_block = ContextBlock(
        source="attacker",
        content={"entry_id": "fake", "body": "fake diary"},
        authority="Diary",
        block_type="diary_retrieval",
        block_kind="diary_context_projection",
        domain="diary",
        source_refs=("conversation://conv_fake/msg_1",),
        metadata={"projection_only": False, "routed_through_context_os": False},
    )

    with pytest.raises(TypeError, match="projection objects are not Diary, Memory, Identity, or Conversation authority"):
        assert_not_diary_context_authority_object(fake_block)

    trace = trace_diary_context_block(fake_block)
    assert trace.routed_through_context_os is False
    assert fake_block.authority != "ContextOS"


def test_at16_r1_006_context_block_corruption_does_not_mutate_canonical_diary():
    entry = _entry("diary_at16_r1_006")
    resolver = ProductSourceResolver({"conversation://conv_at16_r1/msg_1": SourceRefState.RESOLVED})
    admission = admit_diary_for_context(entry, resolver)
    block = build_diary_context_block(DiaryContextCandidate(admission))
    original_body = entry.body
    original_refs = entry.source_refs

    with pytest.raises(TypeError, match="projection objects are not Diary, Memory, Identity, or Conversation authority"):
        assert_not_diary_context_authority_object(block)

    assert entry.body == original_body
    assert entry.source_refs == original_refs
    assert admission.entry == entry


def test_at16_r1_007_cross_context_diary_cannot_contaminate_other_package():
    entry_a = _entry("diary_at16_r1_context_a", refs=(DiarySourceRef("conversation://conv_a/msg_1"),))
    entry_b = _entry("diary_at16_r1_context_b", refs=(DiarySourceRef("conversation://conv_b/msg_1"),))
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

    text_a, pkg_a = _runtime_text(runtime_a)
    text_b, pkg_b = _runtime_text(runtime_b)

    assert "diary_at16_r1_context_a" in text_a
    assert "diary_at16_r1_context_b" not in text_a
    assert "diary_at16_r1_context_b" in text_b
    assert "diary_at16_r1_context_a" not in text_b
    assert pkg_a.retrieval_handles["diary"][0]["source_refs"] == ["conversation://conv_a/msg_1"]
    assert pkg_b.retrieval_handles["diary"][0]["source_refs"] == ["conversation://conv_b/msg_1"]


def test_at16_r1_008_trace_tampering_cannot_become_source_authority():
    tampered = ContextBlock(
        source="diary_context_os_provider",
        content={"entry_id": "diary_tampered", "body_visible": True, "source_states": ["RESOLVED"]},
        authority="ContextOS",
        block_type="diary_retrieval",
        block_kind="diary_context_projection",
        domain="diary",
        source_refs=("conversation://conv_tampered/msg_1",),
        metadata={
            "entry_id": "diary_tampered",
            "routed_through_context_os": False,
            "projection_only": False,
            "mutates_diary": True,
            "mutates_memory": True,
            "mutates_identity": True,
            "mutates_conversation": True,
        },
    )

    trace = trace_diary_context_block(tampered)

    assert trace.routed_through_context_os is False
    assert trace.mutated_diary is True
    assert trace.mutated_memory is True
    assert trace.mutated_identity is True
    with pytest.raises(TypeError, match="projection objects are not Diary, Memory, Identity, or Conversation authority"):
        assert_not_diary_context_authority_object(tampered)
