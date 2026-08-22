"""Wave5 AT-04 minimal remediation tests — unknown reconnect conversation reject.

These are remediation tests, not R1/IA freeze evidence.

TC mapping:
- TC-AT04-REM-P0G2-001: process_turn rejects unknown conversation_id.
- TC-AT04-REM-P0G2-002: accept_user_turn rejects unknown conversation_id.
- TC-AT04-REM-P0G2-003: existing conversation_id still accepts voice turns.
"""

from __future__ import annotations

import pytest

from julia_core.conversation_state.repository import ConversationNotFoundError
from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.conversation_runtime import ConversationRuntime


def _mock_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    return f"ack:{modality}:{text}"


@pytest.fixture
def runtime(tmp_path):
    repo = StorageV2ConversationRepository(str(tmp_path))
    try:
        yield ConversationRuntime(repository=repo)
    finally:
        repo.close()


def test_tc_at04_rem_p0g2_001_process_turn_unknown_conversation_rejects(runtime):
    stale_cid = "stale-voice-reconnect-cid"

    with pytest.raises(ConversationNotFoundError):
        runtime.process_turn(
            conversation_id=stale_cid,
            turn_id="voice-turn-after-stale-reconnect",
            modality="voice",
            input="ghost should not persist",
            cognitive_fn=_mock_cognitive,
        )

    assert runtime.get_conversation(stale_cid) is None
    assert runtime.get_messages(stale_cid) == []


def test_tc_at04_rem_p0g2_002_accept_user_turn_unknown_conversation_rejects(runtime):
    stale_cid = "stale-accept-user-cid"

    with pytest.raises(ConversationNotFoundError):
        runtime.accept_user_turn(
            conversation_id=stale_cid,
            turn_id="voice-accept-stale",
            modality="voice",
            content="ghost accepted user",
        )

    assert runtime.get_conversation(stale_cid) is None
    assert runtime.get_messages(stale_cid) == []


def test_tc_at04_rem_p0g2_003_existing_conversation_still_accepts_voice_turn(runtime):
    cid = runtime.create_conversation(title="AT04 existing voice").conversation_id

    result = runtime.process_turn(
        conversation_id=cid,
        turn_id="voice-existing-1",
        modality="voice",
        input="valid voice utterance",
        cognitive_fn=_mock_cognitive,
    )

    assert result.status == "completed"
    users = [m for m in runtime.get_canonical_history(cid) if m["role"] == "user"]
    assert [(m["turn_id"], m["modality"], m["content"]) for m in users] == [
        ("voice-existing-1", "voice", "valid voice utterance")
    ]
