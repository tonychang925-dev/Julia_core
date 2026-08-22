"""Wave5 AT-06 Integration Acceptance — cross-conversation sabotage.

IA verifies the integrated management/runtime/storage/Context OS/provider-handoff
path. It does not test AT-07 segment rotation, search optimization,
authorization redesign, encryption, or Electron architecture redesign.

TC mapping:
- TC-AT06-IA-001 real B request with injected A history has zero A provider-visible marker
- TC-AT06-IA-002 real search candidate from A cannot become B visible context
- TC-AT06-IA-003 real fresh runtime/repository recovery preserves A/B isolation
- TC-AT06-IA-004 real client/session cache simulation cannot become Context OS authority
- TC-AT06-IA-005 real provider handoff sees only current conversation authority
"""

from __future__ import annotations

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime
from julia_core.runtime.conversation_management_service import ConversationManagementService
from julia_core.runtime.conversation_runtime import ConversationRuntime


ALPHA = "ALPHA_PRIVATE_MARKER_001"
BETA = "BETA_PRIVATE_MARKER_002"


class _FakeIdempotencyPort:
    def __init__(self):
        self._reserved: dict[str, str] = {}

    def get_or_reserve(self, key: str, candidate: str) -> str:
        return self._reserved.setdefault(key, candidate)


class _CapturingProvider:
    def __init__(self):
        self.last_messages: list[dict] = []

    def chat(self, messages: list[dict], cognitive_mode: str = "") -> str:
        self.last_messages = list(messages)
        return "captured"


def _stack(root, port=None):
    repo = StorageV2ConversationRepository(str(root))
    rt = ConversationRuntime(repository=repo)
    svc = ConversationManagementService(rt, port or _FakeIdempotencyPort())
    return repo, rt, svc


def _mock_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    return f"ia-ack:{text}"


def _visible_text(messages: list[dict]) -> str:
    return "\n".join(str(m.get("content", "")) for m in messages)


def _prepare_context(conversation_id: str, history: list[dict], user_text: str = "question"):
    ctx = ContextExecutionRuntime(None)
    pkg = ctx.prepare(
        conversation_id=conversation_id,
        turn_id="at06-ia-turn",
        user_text=user_text,
        history=history,
        modality="text",
    )
    messages = pkg.to_messages(history, user_text)
    return pkg, messages, _visible_text(messages)


def _seed_ab(rt: ConversationRuntime, svc: ConversationManagementService):
    cid_a = svc.create(idempotency_key="at06-ia-A", title="AT06 IA A")["id"]
    cid_b = svc.create(idempotency_key="at06-ia-B", title="AT06 IA B")["id"]
    rt.process_turn(conversation_id=cid_a, turn_id="a1", modality="text", input=ALPHA, cognitive_fn=_mock_cognitive)
    rt.process_turn(conversation_id=cid_b, turn_id="b1", modality="text", input=BETA, cognitive_fn=_mock_cognitive)
    return cid_a, cid_b


def test_tc_at06_ia_001_real_b_request_with_injected_a_history_zero_a_visible(tmp_path):
    """TC-AT06-IA-001: management/runtime messages + injected A → B context."""
    repo, rt, svc = _stack(tmp_path)
    try:
        cid_a, cid_b = _seed_ab(rt, svc)
        injected_history = svc.get_messages(cid_a, max_messages=50) + svc.get_messages(cid_b, max_messages=50)

        pkg, messages, visible = _prepare_context(cid_b, injected_history, "B follow-up")

        assert ALPHA not in visible
        assert BETA in visible
        assert all(m.get("conversation_id") in (None, cid_b) for m in messages)
        assert [p for p in pkg.provenance if p["frame"] == "conversation_boundary"]
    finally:
        repo.close()


def test_tc_at06_ia_002_real_search_candidate_from_a_not_b_visible_context(tmp_path):
    """TC-AT06-IA-002: search hit exists but cannot seed B visible history."""
    repo, rt, svc = _stack(tmp_path)
    try:
        cid_a, cid_b = _seed_ab(rt, svc)
        hits = svc.search(ALPHA)
        assert [h.conversation_id for h in hits] == [cid_a]

        # Simulate a retrieval/search layer incorrectly trying to use A's
        # canonical messages as B's context input.
        candidate_payload = svc.get_messages(cid_a, max_messages=50)
        pkg, messages, visible = _prepare_context(cid_b, candidate_payload, "B asks")

        assert ALPHA not in visible
        assert BETA not in visible  # no B history was supplied, and no unsafe fallback occurs
        assert pkg.active_tail_turn_ids == []
        assert messages == [
            {"role": "system", "content": "[situation]\nmodality: text"},
            {"role": "user", "content": "B asks"},
        ]
    finally:
        repo.close()


def test_tc_at06_ia_003_real_fresh_recovery_preserves_ab_isolation(tmp_path):
    """TC-AT06-IA-003: fresh runtime/repository recovery keeps markers scoped."""
    port = _FakeIdempotencyPort()
    repo1, rt1, svc1 = _stack(tmp_path, port)
    cid_a, cid_b = _seed_ab(rt1, svc1)
    repo1.close()

    repo2, _rt2, svc2 = _stack(tmp_path, port)
    try:
        a_messages = svc2.get_messages(cid_a, max_messages=50)
        b_messages = svc2.get_messages(cid_b, max_messages=50)
        a_visible = _visible_text(a_messages)
        b_visible = _visible_text(b_messages)

        assert ALPHA in a_visible
        assert BETA not in a_visible
        assert BETA in b_visible
        assert ALPHA not in b_visible

        _pkg_b, _messages_b, context_b = _prepare_context(cid_b, b_messages, "B recovered")
        assert BETA in context_b
        assert ALPHA not in context_b
    finally:
        repo2.close()


def test_tc_at06_ia_004_real_client_session_cache_simulation_not_authority(tmp_path):
    """TC-AT06-IA-004: client/session cache cannot define B context truth."""
    repo, rt, svc = _stack(tmp_path)
    try:
        cid_a, cid_b = _seed_ab(rt, svc)
        session_cache = {
            "active_conversation_id": cid_b,
            "history": svc.get_messages(cid_a, max_messages=50) + [
                {"role": "user", "turn_id": "unscoped-cache", "content": "UNSCOPED_CLIENT_CACHE_SECRET"}
            ] + svc.get_messages(cid_b, max_messages=50),
        }

        pkg, _messages, visible = _prepare_context(
            session_cache["active_conversation_id"],
            session_cache["history"],
            "B cached follow-up",
        )

        assert ALPHA not in visible
        assert "UNSCOPED_CLIENT_CACHE_SECRET" not in visible
        assert BETA in visible
        assert all(m.get("conversation_id") == cid_b for m in pkg.active_tail_messages)
    finally:
        repo.close()


def test_tc_at06_ia_005_real_provider_handoff_only_current_conversation_authority(tmp_path):
    """TC-AT06-IA-005: final provider messages contain no foreign marker."""
    repo, rt, svc = _stack(tmp_path)
    try:
        cid_a, cid_b = _seed_ab(rt, svc)
        mixed_history = svc.get_messages(cid_a, max_messages=50) + svc.get_messages(cid_b, max_messages=50)
        pkg, messages, visible = _prepare_context(cid_b, mixed_history, "B provider handoff")

        provider = _CapturingProvider()
        reply = provider.chat(messages, cognitive_mode="at06-ia")
        provider_visible = _visible_text(provider.last_messages)

        assert reply == "captured"
        assert visible == provider_visible
        assert ALPHA not in provider_visible
        assert BETA in provider_visible
        assert provider.last_messages[-1] == {"role": "user", "content": "B provider handoff"}
        assert all(
            m.get("conversation_id") in (None, cid_b)
            for m in provider.last_messages
            if m["role"] in ("user", "assistant") and m is not provider.last_messages[-1]
        )
    finally:
        repo.close()
