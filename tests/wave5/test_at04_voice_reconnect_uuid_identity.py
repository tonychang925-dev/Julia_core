"""Wave5 AT-04-R1 — Voice reconnect UUID identity sabotage evidence.

R1 proves attacks against canonical turn identity fail closed after minimal
remediation. It does not test AT-05 retry idempotency beyond the AT-04 identity
boundary, nor voice/S2S/TTS UX behavior.

TC mapping:
- TC-AT04-R1-001 repeated reconnect simulation uses distinct canonical turn_id
- TC-AT04-R1-002 same turn_id + same content is idempotent retry / no duplicate
- TC-AT04-R1-003 same turn_id + different content conflicts on all backends
- TC-AT04-R1-004 stale reconnect conversation_id rejects / no ghost conversation
- TC-AT04-R1-005 transport/session ids cannot be canonical turn_id authority
- TC-AT04-R1-006 fresh runtime recovery preserves collision-free turn identity
"""

from __future__ import annotations

from pathlib import Path

import pytest

from julia_core.conversation_state.legacy_json_repository import LegacyJsonConversationRepository
from julia_core.conversation_state.repository import ConversationNotFoundError, TurnConflictError
from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.conversation_runtime import ConversationRuntime


def _voice_turn(turn_id: str, user: str, assistant: str | None = None, **metadata) -> dict:
    turn = {
        "turn_id": turn_id,
        "modality": "voice",
        "user_content": user,
        "assistant_content": assistant if assistant is not None else f"ack:{user}",
        "assistant_status": "completed",
    }
    turn.update(metadata)
    return turn


def _mock_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    return f"ack:{modality}:{text}"


def _storage_v2(root: Path):
    repo = StorageV2ConversationRepository(str(root))
    return repo, ConversationRuntime(repository=repo)


def _legacy(root: Path):
    repo = LegacyJsonConversationRepository(root / "legacy.json")
    return repo, ConversationRuntime(repository=repo)


def _user_messages(rt: ConversationRuntime, cid: str) -> list[dict]:
    return [m for m in rt.get_canonical_history(cid) if m["role"] == "user"]


def test_tc_at04_r1_001_repeated_reconnect_distinct_utterances_get_distinct_turn_ids(tmp_path):
    repo, rt = _storage_v2(tmp_path)
    try:
        cid = rt.create_conversation(title="AT04 reconnect distinct").conversation_id
        reconnect_turns = [
            ("voice-turn-uuid-001", "voice utterance after connect 1", "voice-session-A"),
            ("voice-turn-uuid-002", "voice utterance after reconnect 2", "voice-session-B"),
            ("voice-turn-uuid-003", "voice utterance after reconnect 3", "voice-session-C"),
        ]

        for tid, utterance, voice_session_id in reconnect_turns:
            rt.append_external_turns(
                cid,
                [_voice_turn(tid, utterance, voice_session_id=voice_session_id)],
            )

        users = _user_messages(rt, cid)
        assert [m["turn_id"] for m in users] == [t[0] for t in reconnect_turns]
        assert len({m["turn_id"] for m in users}) == 3
        assert [m["content"] for m in users] == [t[1] for t in reconnect_turns]
        assert {m["conversation_id"] for m in rt.get_canonical_history(cid)} == {cid}
    finally:
        repo.close()


@pytest.mark.parametrize("repo_factory", [_storage_v2, _legacy], ids=["storage_v2", "legacy"])
def test_tc_at04_r1_002_same_turn_same_content_idempotent_no_duplicate(tmp_path, repo_factory):
    repo, rt = repo_factory(tmp_path)
    try:
        cid = rt.create_conversation(title="AT04 idempotent retry").conversation_id
        first = rt.append_external_turns(cid, [_voice_turn("voice-retry-uuid", "same logical utterance")])
        retry = rt.append_external_turns(cid, [_voice_turn("voice-retry-uuid", "same logical utterance")])

        assert first["appended_turn_ids"] == ["voice-retry-uuid"]
        assert retry["appended_turn_ids"] == []
        assert retry["skipped_turn_ids"] == ["voice-retry-uuid"]
        assert len(rt.get_canonical_history(cid)) == 2
    finally:
        if hasattr(repo, "close"):
            repo.close()


@pytest.mark.parametrize("repo_factory", [_storage_v2, _legacy], ids=["storage_v2", "legacy"])
def test_tc_at04_r1_003_same_turn_different_content_conflicts_zero_mutation(tmp_path, repo_factory):
    repo, rt = repo_factory(tmp_path)
    try:
        cid = rt.create_conversation(title="AT04 collision conflict").conversation_id
        rt.append_external_turns(cid, [_voice_turn("voice-collision-uuid", "first utterance", "ack first")])
        before = rt.get_canonical_history(cid)

        with pytest.raises(TurnConflictError):
            rt.append_external_turns(cid, [_voice_turn("voice-collision-uuid", "second utterance", "ack second")])

        after = rt.get_canonical_history(cid)
        assert after == before
        assert [m["content"] for m in after] == ["first utterance", "ack first"]
    finally:
        if hasattr(repo, "close"):
            repo.close()


def test_tc_at04_r1_004_stale_reconnect_conversation_id_rejects_no_ghost(tmp_path):
    repo, rt = _storage_v2(tmp_path)
    try:
        stale_cid = "stale-reconnect-conversation-id"

        with pytest.raises(ConversationNotFoundError):
            rt.process_turn(
                conversation_id=stale_cid,
                turn_id="voice-after-stale-reconnect",
                modality="voice",
                input="this must not create ghost truth",
                cognitive_fn=_mock_cognitive,
            )

        assert rt.get_conversation(stale_cid) is None
        assert rt.get_messages(stale_cid) == []
    finally:
        repo.close()


def test_tc_at04_r1_005_transport_ids_cannot_be_turn_identity_authority(tmp_path):
    repo, rt = _storage_v2(tmp_path)
    try:
        cid = rt.create_conversation(title="AT04 transport spoof").conversation_id
        transport_id = "voice-session-not-a-turn-authority"

        rt.append_external_turns(
            cid,
            [_voice_turn(
                "voice-canonical-turn-001",
                "canonical voice utterance",
                voice_session_id=transport_id,
                reconnect_id=transport_id,
                websocket_id=transport_id,
            )],
        )

        # Spoof attempt: use transport id as if it were a canonical turn id for
        # a different utterance. It is simply a caller-supplied turn_id and must
        # not be accepted as proof of valid reconnect identity if it collides.
        rt.append_external_turns(cid, [_voice_turn(transport_id, "first spoof utterance")])
        before = rt.get_canonical_history(cid)
        with pytest.raises(TurnConflictError):
            rt.append_external_turns(cid, [_voice_turn(transport_id, "second spoof utterance")])

        after = rt.get_canonical_history(cid)
        assert after == before
        assert [m["turn_id"] for m in _user_messages(rt, cid)] == [
            "voice-canonical-turn-001",
            transport_id,
        ]
    finally:
        repo.close()


def test_tc_at04_r1_006_fresh_runtime_recovery_preserves_collision_free_turn_identity(tmp_path):
    repo1, rt1 = _storage_v2(tmp_path)
    cid = rt1.create_conversation(title="AT04 recovery").conversation_id
    for idx in range(3):
        rt1.append_external_turns(
            cid,
            [_voice_turn(f"voice-recovered-uuid-{idx}", f"recovered utterance {idx}")],
        )
    before_users = _user_messages(rt1, cid)
    repo1.close()

    repo2, rt2 = _storage_v2(tmp_path)
    try:
        after_users = _user_messages(rt2, cid)
        assert [m["turn_id"] for m in after_users] == [m["turn_id"] for m in before_users]
        assert [m["content"] for m in after_users] == [m["content"] for m in before_users]
        assert len({m["turn_id"] for m in after_users}) == len(after_users) == 3
    finally:
        repo2.close()
