"""Wave5 AT-06-R1 — Cross-conversation sabotage permanent evidence.

R1 proves conversation boundary attacks fail closed after minimal Context OS
remediation. It does not test AT-07 segment rotation, AT-08 pagination,
search optimization, authorization redesign, encryption, or Electron redesign.

TC mapping:
- TC-AT06-R1-001 foreign history injection cannot become provider-visible
- TC-AT06-R1-002 foreign retrieval/search candidate cannot be used as current transcript
- TC-AT06-R1-003 unscoped history/cache item cannot default to active conversation
- TC-AT06-R1-004 client/session cache contamination cannot enter active context
- TC-AT06-R1-005 empty ActiveTail does not fallback to unsafe caller history
- TC-AT06-R1-006 storage A/B marker isolation through canonical reads and recovery
- TC-AT06-R1-007 search marker-specific query returns only matching conversation handle
- TC-AT06-R1-008 runtime interaction cache remains conversation scoped
"""

from __future__ import annotations

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime
from julia_core.runtime.conversation_runtime import ConversationRuntime


ALPHA = "ALPHA_PRIVATE_MARKER_001"
BETA = "BETA_PRIVATE_MARKER_002"


def _mock_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    return f"ack:{text}"


def _stack(root):
    repo = StorageV2ConversationRepository(str(root))
    rt = ConversationRuntime(repository=repo)
    return repo, rt


def _mixed_history():
    return [
        {"role": "user", "conversation_id": "conv_A", "turn_id": "a1", "content": ALPHA},
        {"role": "assistant", "conversation_id": "conv_A", "turn_id": "a1", "content": "ack A"},
        {"role": "user", "conversation_id": "conv_B", "turn_id": "b1", "content": BETA},
        {"role": "assistant", "conversation_id": "conv_B", "turn_id": "b1", "content": "ack B"},
    ]


def _visible_text(messages: list[dict]) -> str:
    return "\n".join(str(m.get("content", "")) for m in messages)


def _prepare_visible(conversation_id: str, history: list[dict], user_text: str = "question"):
    ctx = ContextExecutionRuntime(None)
    pkg = ctx.prepare(
        conversation_id=conversation_id,
        turn_id="sabotage-turn",
        user_text=user_text,
        history=history,
        modality="text",
    )
    messages = pkg.to_messages(history, user_text)
    return pkg, messages, _visible_text(messages)


def test_tc_at06_r1_001_foreign_history_injection_not_provider_visible():
    """TC-AT06-R1-001: conv_A history injected into conv_B is quarantined."""
    pkg, messages, visible = _prepare_visible("conv_B", _mixed_history(), "question B")

    assert ALPHA not in visible
    assert BETA in visible
    assert pkg.active_tail_turn_ids == ["b1", "b1"]
    assert all(m.get("conversation_id") in (None, "conv_B") for m in messages)
    assert [p for p in pkg.provenance if p["frame"] == "conversation_boundary"]


def test_tc_at06_r1_002_foreign_search_candidate_not_current_transcript_authority():
    """TC-AT06-R1-002: search/retrieval candidate from A cannot seed B."""
    search_candidate_from_a = [
        {
            "role": "user",
            "conversation_id": "conv_A",
            "turn_id": "search-hit-a1",
            "content": ALPHA,
            "source": "derived_search_candidate",
            "rank": 1,
        }
    ]

    pkg, messages, visible = _prepare_visible("conv_B", search_candidate_from_a, "question B")

    assert ALPHA not in visible
    assert pkg.active_tail_turn_ids == []
    assert messages == [
        {"role": "system", "content": "[situation]\nmodality: text"},
        {"role": "user", "content": "question B"},
    ]


def test_tc_at06_r1_003_unscoped_history_cannot_default_to_active_conversation():
    """TC-AT06-R1-003: missing conversation_id is not implicit permission."""
    unscoped = [
        {"role": "user", "turn_id": "unscoped-a", "content": ALPHA},
        {"role": "assistant", "turn_id": "unscoped-a", "content": "cached ack"},
    ]

    pkg, messages, visible = _prepare_visible("conv_B", unscoped, "question B")

    assert ALPHA not in visible
    assert pkg.active_tail_turn_ids == []
    assert messages[-1] == {"role": "user", "content": "question B"}


def test_tc_at06_r1_004_client_session_cache_contamination_cannot_enter_active_context():
    """TC-AT06-R1-004: Electron/session cache simulation has no authority."""
    electron_cache = {
        "current_conversation_id": "conv_B",
        "history": [
            {"role": "user", "conversation_id": "conv_A", "turn_id": "cache-a", "content": ALPHA},
            {"role": "assistant", "conversation_id": "conv_A", "turn_id": "cache-a", "content": "cached A"},
            {"role": "user", "conversation_id": "conv_B", "turn_id": "cache-b", "content": BETA},
        ],
    }

    pkg, _messages, visible = _prepare_visible(
        electron_cache["current_conversation_id"],
        electron_cache["history"],
        "question B",
    )

    assert ALPHA not in visible
    assert BETA in visible
    assert pkg.active_tail_turn_ids == ["cache-b"]


def test_tc_at06_r1_005_empty_active_tail_does_not_fallback_to_unsafe_history():
    """TC-AT06-R1-005: empty admitted tail must not render caller history."""
    only_foreign_and_unscoped = [
        {"role": "user", "conversation_id": "conv_A", "turn_id": "a1", "content": ALPHA},
        {"role": "user", "turn_id": "unscoped", "content": "UNSCOPED_CACHE_SECRET"},
    ]

    pkg, messages, visible = _prepare_visible("conv_B", only_foreign_and_unscoped, "question B")

    assert ALPHA not in visible
    assert "UNSCOPED_CACHE_SECRET" not in visible
    assert pkg.active_tail_turn_ids == []
    assert messages == [
        {"role": "system", "content": "[situation]\nmodality: text"},
        {"role": "user", "content": "question B"},
    ]


def test_tc_at06_r1_006_storage_marker_isolation_through_reads_and_recovery(tmp_path):
    """TC-AT06-R1-006: canonical storage and fresh recovery keep A/B separate."""
    repo1, rt1 = _stack(tmp_path)
    cid_a = rt1.create_conversation(title="AT06 A").conversation_id
    cid_b = rt1.create_conversation(title="AT06 B").conversation_id
    rt1.process_turn(conversation_id=cid_a, turn_id="a1", modality="text", input=ALPHA, cognitive_fn=_mock_cognitive)
    rt1.process_turn(conversation_id=cid_b, turn_id="b1", modality="text", input=BETA, cognitive_fn=_mock_cognitive)
    repo1.close()

    repo2, rt2 = _stack(tmp_path)
    try:
        a_text = _visible_text(rt2.get_messages(cid_a))
        b_text = _visible_text(rt2.get_messages(cid_b))
        assert ALPHA in a_text
        assert BETA not in a_text
        assert BETA in b_text
        assert ALPHA not in b_text
    finally:
        repo2.close()


def test_tc_at06_r1_007_search_marker_specific_returns_only_matching_handle(tmp_path):
    """TC-AT06-R1-007: marker-specific search does not cross-return handles."""
    repo, rt = _stack(tmp_path)
    try:
        cid_a = rt.create_conversation(title="AT06 A").conversation_id
        cid_b = rt.create_conversation(title="AT06 B").conversation_id
        rt.process_turn(conversation_id=cid_a, turn_id="a1", modality="text", input=ALPHA, cognitive_fn=_mock_cognitive)
        rt.process_turn(conversation_id=cid_b, turn_id="b1", modality="text", input=BETA, cognitive_fn=_mock_cognitive)

        alpha_hits = rt.search_conversations(ALPHA)
        beta_hits = rt.search_conversations(BETA)
        broad_hits = rt.search_conversations("PRIVATE_MARKER")

        assert [h.conversation_id for h in alpha_hits] == [cid_a]
        assert [h.conversation_id for h in beta_hits] == [cid_b]
        assert {h.conversation_id for h in broad_hits} == {cid_a, cid_b}
    finally:
        repo.close()


def test_tc_at06_r1_008_runtime_interaction_cache_is_conversation_scoped(tmp_path):
    """TC-AT06-R1-008: interaction cache A cannot seed B, and rebuild is scoped."""
    repo1, rt1 = _stack(tmp_path)
    cid_a = rt1.create_conversation(title="AT06 cache A").conversation_id
    cid_b = rt1.create_conversation(title="AT06 cache B").conversation_id
    rt1.process_turn(conversation_id=cid_a, turn_id="a1", modality="text", input="你是谁？ " + ALPHA, cognitive_fn=_mock_cognitive)
    rt1.process_turn(conversation_id=cid_b, turn_id="b1", modality="text", input="ordinary B turn", cognitive_fn=_mock_cognitive)

    state_a = rt1.get_interaction_state(cid_a)
    state_b = rt1.get_interaction_state(cid_b)
    assert state_a.identity_checks >= 1
    assert state_b.identity_checks == 0
    repo1.close()

    repo2, rt2 = _stack(tmp_path)
    try:
        rebuilt_a = rt2.get_interaction_state(cid_a)
        rebuilt_b = rt2.get_interaction_state(cid_b)
        assert rebuilt_a.identity_checks >= 1
        assert rebuilt_b.identity_checks == 0
    finally:
        repo2.close()
