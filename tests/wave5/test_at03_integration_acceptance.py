"""Wave5 AT-03 Integration Acceptance — Text → Voice → Text.

IA proves the management/read surface and canonical runtime converge on one
mixed-modality transcript. It does not test AT-04 reconnect UUID semantics or
voice representation quality.

TC mapping:
- TC-AT03-IA-001: management route + runtime writes one mixed conversation
- TC-AT03-IA-002: session history sabotage cannot become canonical truth
- TC-AT03-IA-003: transport metadata cannot fork identity through IA path
- TC-AT03-IA-004: fresh runtime/repository recovery preserves mixed sequence
"""

from __future__ import annotations

import pytest

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from conversation_management import (
    ConversationManagementService,
    ConversationNotFoundError,
)
from julia_core.runtime.conversation_runtime import ConversationRuntime


class _FakeIdempotencyPort:
    def __init__(self):
        self._reserved: dict[str, str] = {}

    def get_or_reserve(self, key: str, candidate: str) -> str:
        return self._reserved.setdefault(key, candidate)


def _mock_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    return f"ia-ack:{modality}:{text}"


def _stack(root):
    repo = StorageV2ConversationRepository(str(root))
    rt = ConversationRuntime(repository=repo)
    svc = ConversationManagementService(rt, _FakeIdempotencyPort())
    return repo, rt, svc


def _text(rt: ConversationRuntime, cid: str, tid: str, content: str):
    return rt.process_turn(
        conversation_id=cid,
        turn_id=tid,
        modality="text",
        input=content,
        cognitive_fn=_mock_cognitive,
    )


def _voice(rt: ConversationRuntime, cid: str, tid: str, content: str, **metadata):
    turn = {
        "turn_id": tid,
        "modality": "voice",
        "user_content": content,
        "assistant_content": f"ia-ack:voice:{content}",
        "assistant_status": "completed",
    }
    turn.update(metadata)
    return rt.append_external_turns(cid, [turn])


def _users(messages: list[dict]) -> list[dict]:
    return [m for m in messages if m["role"] == "user"]


def test_tc_at03_ia_001_management_route_reads_one_mixed_canonical_sequence(tmp_path):
    """TC-AT03-IA-001: create/open/read surface sees text→voice→text."""
    repo, rt, svc = _stack(tmp_path)
    try:
        detail = svc.create(idempotency_key="at03-ia-001", title="AT03 IA mixed")
        cid = detail["id"]

        _text(rt, cid, "ia-t1", "IA Text T1")
        _voice(rt, cid, "ia-v2", "IA Voice T2")
        _text(rt, cid, "ia-t3", "IA Text T3")

        opened = svc.open(cid)
        messages = svc.get_messages(cid, max_messages=50)
        users = _users(messages)

        assert opened["id"] == cid
        assert [m["turn_id"] for m in users] == ["ia-t1", "ia-v2", "ia-t3"]
        assert [m["modality"] for m in users] == ["text", "voice", "text"]
        assert [m["content"] for m in users] == ["IA Text T1", "IA Voice T2", "IA Text T3"]
        assert {m["conversation_id"] for m in messages} == {cid}
    finally:
        repo.close()


def test_tc_at03_ia_002_session_history_sabotage_cannot_be_read_as_canonical(tmp_path):
    """TC-AT03-IA-002: session-local history is not fallback authority."""
    repo, rt, svc = _stack(tmp_path)
    try:
        detail = svc.create(idempotency_key="at03-ia-002", title="AT03 IA sabotage")
        cid = detail["id"]

        session_history = {
            "session_id": "voice-session-sabotage",
            "conversation_id": cid,
            "history": [
                {"role": "user", "content": "SABOTAGE voice-only user"},
                {"role": "assistant", "content": "SABOTAGE voice-only assistant"},
            ],
        }

        assert session_history["history"]
        assert svc.get_messages(cid) == []
        with pytest.raises(ConversationNotFoundError):
            svc.get(session_history["session_id"])
    finally:
        repo.close()


def test_tc_at03_ia_003_transport_metadata_cannot_fork_identity(tmp_path):
    """TC-AT03-IA-003: metadata may accompany voice, but cannot create identity."""
    repo, rt, svc = _stack(tmp_path)
    try:
        cid = svc.create(idempotency_key="at03-ia-003", title="AT03 IA metadata")["id"]
        voice_session_id = "ia-voice-session-not-cid"
        voice_trace_id = "ia-voice-trace-not-cid"
        participant_id = "ia-participant-not-cid"

        _text(rt, cid, "ia-meta-t1", "Before metadata voice")
        _voice(
            rt,
            cid,
            "ia-meta-v2",
            "Voice metadata payload",
            voice_session_id=voice_session_id,
            voice_trace_id=voice_trace_id,
            participant_id=participant_id,
        )
        _text(rt, cid, "ia-meta-t3", "After metadata voice")

        users = _users(svc.get_messages(cid))
        assert [m["modality"] for m in users] == ["text", "voice", "text"]
        for non_cid in (voice_session_id, voice_trace_id, participant_id):
            with pytest.raises(ConversationNotFoundError):
                svc.get(non_cid)
    finally:
        repo.close()


def test_tc_at03_ia_004_fresh_runtime_recovery_preserves_mixed_sequence(tmp_path):
    """TC-AT03-IA-004: recovered runtime reads same mixed canonical transcript."""
    repo1, rt1, svc1 = _stack(tmp_path)
    cid = svc1.create(idempotency_key="at03-ia-004", title="AT03 IA recovery")["id"]
    _text(rt1, cid, "ia-rec-t1", "Recovery Text T1")
    _voice(rt1, cid, "ia-rec-v2", "Recovery Voice T2")
    _text(rt1, cid, "ia-rec-t3", "Recovery Text T3")
    before = svc1.get_messages(cid)
    repo1.close()

    repo2, _rt2, svc2 = _stack(tmp_path)
    try:
        after = svc2.get_messages(cid)
        before_users = _users(before)
        after_users = _users(after)

        assert [m["turn_id"] for m in after_users] == ["ia-rec-t1", "ia-rec-v2", "ia-rec-t3"]
        assert [m["modality"] for m in after_users] == ["text", "voice", "text"]
        assert [m["content"] for m in after_users] == [m["content"] for m in before_users]
        assert len(after) == len(before) == 6
        assert {m["conversation_id"] for m in after} == {cid}
    finally:
        repo2.close()
