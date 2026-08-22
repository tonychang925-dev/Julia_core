"""Wave5 AT-04 minimal remediation tests — turn_id conflict fail-closed.

These are remediation tests, not R1/IA freeze evidence.

TC mapping:
- TC-AT04-REM-P0G1-001: StorageV2 same turn_id + same content is idempotent.
- TC-AT04-REM-P0G1-002: StorageV2 same turn_id + different content conflicts.
- TC-AT04-REM-P0G1-003: Legacy and StorageV2 agree on conflict semantics.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from julia_core.conversation_state.legacy_json_repository import LegacyJsonConversationRepository
from julia_core.conversation_state.repository import TurnConflictError
from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.conversation_runtime import ConversationRuntime


def _voice_turn(turn_id: str, user: str, assistant: str = "ack") -> dict:
    return {
        "turn_id": turn_id,
        "modality": "voice",
        "user_content": user,
        "assistant_content": assistant,
        "assistant_status": "completed",
    }


def _new_storage_v2(root: Path):
    repo = StorageV2ConversationRepository(str(root))
    return repo, ConversationRuntime(repository=repo)


def _new_legacy(root: Path):
    repo = LegacyJsonConversationRepository(root / "legacy.json")
    return repo, ConversationRuntime(repository=repo)


def test_tc_at04_rem_p0g1_001_storage_v2_same_turn_same_content_idempotent(tmp_path):
    repo, rt = _new_storage_v2(tmp_path)
    try:
        cid = rt.create_conversation(title="AT04 same content").conversation_id
        first = rt.append_external_turns(cid, [_voice_turn("voice-retry-1", "same utterance")])
        retry = rt.append_external_turns(cid, [_voice_turn("voice-retry-1", "same utterance")])

        assert first["appended_turn_ids"] == ["voice-retry-1"]
        assert retry["appended_turn_ids"] == []
        assert retry["skipped_turn_ids"] == ["voice-retry-1"]
        assert len(rt.get_canonical_history(cid)) == 2
    finally:
        repo.close()


@pytest.mark.parametrize("repo_factory", [_new_storage_v2, _new_legacy], ids=["storage_v2", "legacy"])
def test_tc_at04_rem_p0g1_002_same_turn_different_content_conflicts(tmp_path, repo_factory):
    repo, rt = repo_factory(tmp_path)
    try:
        cid = rt.create_conversation(title="AT04 conflict").conversation_id
        rt.append_external_turns(cid, [_voice_turn("voice-collision-1", "first utterance", "ack first")])

        with pytest.raises(TurnConflictError):
            rt.append_external_turns(cid, [_voice_turn("voice-collision-1", "second utterance", "ack second")])

        history = rt.get_canonical_history(cid)
        assert [m["content"] for m in history] == ["first utterance", "ack first"]
    finally:
        if hasattr(repo, "close"):
            repo.close()


def test_tc_at04_rem_p0g1_003_storage_v2_same_user_different_assistant_conflicts(tmp_path):
    repo, rt = _new_storage_v2(tmp_path)
    try:
        cid = rt.create_conversation(title="AT04 assistant conflict").conversation_id
        rt.append_external_turns(cid, [_voice_turn("voice-collision-2", "same utterance", "ack original")])

        with pytest.raises(TurnConflictError):
            rt.append_external_turns(cid, [_voice_turn("voice-collision-2", "same utterance", "ack changed")])

        assert [m["content"] for m in rt.get_canonical_history(cid)] == ["same utterance", "ack original"]
    finally:
        repo.close()
