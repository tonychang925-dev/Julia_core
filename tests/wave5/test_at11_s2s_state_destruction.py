"""AT-11 — S2S state destruction (v1.0 plan definition).

Restart/reconnect S2S. Completed continuity preserved WITHOUT S2S history
transfer.

Frozen boundary (from audit):

    S2S runtime/media state != conversation continuity authority

Required direction:
    Core canonical conversation state → new S2S live session bound by
    conversation_id (history lives in Core, not S2S).

Forbidden direction:
    old S2S session chat/history/workspace → restored continuity.

Layer 1 verification (ConversationRuntime layer):
    1. voice turns written to canonical (modality="voice")
    2. S2S state destruction: new connection carries NO history, only
       conversation_id
    3. resume → full conversation restored from Core (zero loss)
    4. S2S holds no transcript authority
"""

from __future__ import annotations

from pathlib import Path

import pytest

from julia_core.conversation_state.legacy_json_repository import LegacyJsonConversationRepository
from julia_core.runtime.conversation_runtime import ConversationRuntime


def _runtime(repo_path: Path) -> ConversationRuntime:
    return ConversationRuntime(repository=LegacyJsonConversationRepository(str(repo_path)))


def _mock_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    return f"ack:{modality}:{text}"


@pytest.fixture()
def repo_path(tmp_path):
    return tmp_path / "conversations.json"


def _voice_turn(rt, cid, tid, content):
    return rt.process_turn(
        conversation_id=cid, turn_id=tid, modality="voice",
        input=content, cognitive_fn=_mock_cognitive,
    )


def test_at11_s2s_state_destruction_preserves_continuity(repo_path):
    """S2S restart/reconnect: completed continuity survives in Core."""
    rt = _runtime(repo_path)
    cid = rt.create_conversation().conversation_id
    _voice_turn(rt, cid, "v1", "你好 Julia")
    _voice_turn(rt, cid, "v2", "今天天气如何")

    # S2S state destruction: old S2S session is gone. A NEW connection brings
    # ONLY conversation_id — no history replay/transfer from S2S.
    rt2 = _runtime(repo_path)  # new runtime = new S2S session context
    history = rt2.get_canonical_history(cid)

    # Completed continuity preserved without S2S history transfer.
    users = [m for m in history if m["role"] == "user"]
    assert len(users) == 2
    assert [m["content"] for m in users] == ["你好 Julia", "今天天气如何"]
    # Modality preserved (voice turns stayed voice).
    assert all(m["modality"] == "voice" for m in users)


def test_at11_no_s2s_history_authority(repo_path):
    """S2S layer must not hold transcript authority — Core is the source."""
    rt = _runtime(repo_path)
    cid = rt.create_conversation().conversation_id
    _voice_turn(rt, cid, "v1", "hello")

    # A destroyed S2S session contributes nothing: new connection has no
    # history to transfer. Core canonical state is the sole source.
    rt2 = _runtime(repo_path)
    assert len(rt2.get_canonical_history(cid)) == 2  # user + assistant from Core
    # conversation_id is the only binding token (like S2S WS bind).
    assert rt2.get_conversation(cid) is not None


def test_at11_conversation_survives_s2s_restart_loop(repo_path):
    """Multiple S2S restarts: canonical conversation never degraded."""
    rt = _runtime(repo_path)
    cid = rt.create_conversation().conversation_id
    for i in range(3):
        _voice_turn(rt, cid, f"v{i}", f"turn-{i}")

    # Simulate repeated S2S reconnect cycles; each new session re-reads from Core.
    for _ in range(3):
        rt_cycle = _runtime(repo_path)
        assert len(rt_cycle.get_canonical_history(cid)) == 6  # 3 turns intact

    # No duplicates from reconnect (each cycle is a fresh reader, not a writer).
    rt_final = _runtime(repo_path)
    users = [m for m in rt_final.get_canonical_history(cid) if m["role"] == "user"]
    assert len(users) == 3
