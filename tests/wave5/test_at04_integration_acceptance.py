"""Wave5 AT-04 Integration Acceptance — voice reconnect UUID identity.

IA verifies the integrated Core management/runtime/storage/recovery path after
R0 + remediation + R1. It does not exercise UI, TTS, S2S media quality, or AT-05.

TC mapping:
- TC-AT04-IA-001 real management/runtime path creates distinct turn IDs after reconnect
- TC-AT04-IA-002 real retry path is idempotent and does not duplicate
- TC-AT04-IA-003 real conflict path rejects and preserves canonical transcript
- TC-AT04-IA-004 stale reconnect conversation_id is rejected via governed surface
- TC-AT04-IA-005 fresh recovery preserves collision-free canonical turn identity
"""

from __future__ import annotations

import pytest

from julia_core.conversation_state.repository import ConversationNotFoundError, TurnConflictError
from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.conversation_management_service import (
    ConversationManagementService,
    ConversationNotFoundError as ManagementConversationNotFoundError,
)
from julia_core.runtime.conversation_runtime import ConversationRuntime


class _FakeIdempotencyPort:
    def __init__(self):
        self._reserved: dict[str, str] = {}

    def get_or_reserve(self, key: str, candidate: str) -> str:
        return self._reserved.setdefault(key, candidate)


def _stack(root):
    repo = StorageV2ConversationRepository(str(root))
    rt = ConversationRuntime(repository=repo)
    svc = ConversationManagementService(rt, _FakeIdempotencyPort())
    return repo, rt, svc


def _voice_turn(turn_id: str, user: str, **metadata) -> dict:
    turn = {
        "turn_id": turn_id,
        "modality": "voice",
        "user_content": user,
        "assistant_content": f"ia-ack:{user}",
        "assistant_status": "completed",
    }
    turn.update(metadata)
    return turn


def _users(messages: list[dict]) -> list[dict]:
    return [m for m in messages if m["role"] == "user"]


def test_tc_at04_ia_001_real_reconnect_path_distinct_turn_ids(tmp_path):
    """TC-AT04-IA-001: real path: create → voice reconnect turns → read."""
    repo, rt, svc = _stack(tmp_path)
    try:
        cid = svc.create(idempotency_key="at04-ia-001", title="AT04 IA reconnect")["id"]
        reconnect_inputs = [
            ("voice-ia-uuid-001", "IA voice after connect", "voice-session-1"),
            ("voice-ia-uuid-002", "IA voice after reconnect A", "voice-session-2"),
            ("voice-ia-uuid-003", "IA voice after reconnect B", "voice-session-3"),
        ]

        for tid, content, session_id in reconnect_inputs:
            rt.append_external_turns(cid, [_voice_turn(tid, content, voice_session_id=session_id)])

        messages = svc.get_messages(cid, max_messages=50)
        users = _users(messages)
        assert [m["turn_id"] for m in users] == [i[0] for i in reconnect_inputs]
        assert [m["content"] for m in users] == [i[1] for i in reconnect_inputs]
        assert len({m["turn_id"] for m in users}) == len(users) == 3
        assert {m["conversation_id"] for m in messages} == {cid}
    finally:
        repo.close()


def test_tc_at04_ia_002_real_retry_path_idempotent_no_duplicate(tmp_path):
    """TC-AT04-IA-002: same logical voice retry does not duplicate."""
    repo, rt, svc = _stack(tmp_path)
    try:
        cid = svc.create(idempotency_key="at04-ia-002", title="AT04 IA retry")["id"]
        first = rt.append_external_turns(cid, [_voice_turn("voice-ia-retry", "same retry utterance")])
        retry = rt.append_external_turns(cid, [_voice_turn("voice-ia-retry", "same retry utterance")])

        users = _users(svc.get_messages(cid))
        assert first["appended_turn_ids"] == ["voice-ia-retry"]
        assert retry["appended_turn_ids"] == []
        assert retry["skipped_turn_ids"] == ["voice-ia-retry"]
        assert [(m["turn_id"], m["content"]) for m in users] == [
            ("voice-ia-retry", "same retry utterance")
        ]
    finally:
        repo.close()


def test_tc_at04_ia_003_real_conflict_path_rejects_preserves_transcript(tmp_path):
    """TC-AT04-IA-003: same turn_id + different content rejects, no mutation."""
    repo, rt, svc = _stack(tmp_path)
    try:
        cid = svc.create(idempotency_key="at04-ia-003", title="AT04 IA conflict")["id"]
        rt.append_external_turns(cid, [_voice_turn("voice-ia-conflict", "original IA utterance")])
        before = svc.get_messages(cid)

        with pytest.raises(TurnConflictError):
            rt.append_external_turns(cid, [_voice_turn("voice-ia-conflict", "mutated IA utterance")])

        after = svc.get_messages(cid)
        assert after == before
        assert [m["content"] for m in _users(after)] == ["original IA utterance"]
    finally:
        repo.close()


def test_tc_at04_ia_004_stale_reconnect_conversation_id_rejected_no_ghost(tmp_path):
    """TC-AT04-IA-004: stale reconnect id cannot manufacture conversation truth."""
    repo, rt, svc = _stack(tmp_path)
    try:
        stale_cid = "stale-ia-reconnect-cid"

        with pytest.raises(ConversationNotFoundError):
            rt.process_turn(
                conversation_id=stale_cid,
                turn_id="voice-ia-stale-turn",
                modality="voice",
                input="ghost IA utterance",
                cognitive_fn=lambda *_args: "ack",
            )

        with pytest.raises(ManagementConversationNotFoundError):
            svc.get(stale_cid)
        assert rt.get_conversation(stale_cid) is None
        assert rt.get_messages(stale_cid) == []
    finally:
        repo.close()


def test_tc_at04_ia_005_fresh_recovery_preserves_collision_free_turn_identity(tmp_path):
    """TC-AT04-IA-005: fresh runtime reads same collision-free transcript."""
    repo1, rt1, svc1 = _stack(tmp_path)
    cid = svc1.create(idempotency_key="at04-ia-005", title="AT04 IA recovery")["id"]
    for idx in range(4):
        rt1.append_external_turns(
            cid,
            [_voice_turn(f"voice-ia-recovered-{idx}", f"IA recovered utterance {idx}")],
        )
    before = svc1.get_messages(cid)
    repo1.close()

    repo2, _rt2, svc2 = _stack(tmp_path)
    try:
        after = svc2.get_messages(cid)
        before_users = _users(before)
        after_users = _users(after)
        assert [m["turn_id"] for m in after_users] == [m["turn_id"] for m in before_users]
        assert [m["content"] for m in after_users] == [m["content"] for m in before_users]
        assert len({m["turn_id"] for m in after_users}) == len(after_users) == 4
        assert len(after) == len(before) == 8
    finally:
        repo2.close()
