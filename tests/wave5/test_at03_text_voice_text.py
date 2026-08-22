"""Wave5 AT-03 — Text → Voice → Text canonical sequence acceptance.

AT-03 freezes one narrow invariant:
voice is a conversation modality, not a conversation authority.

TC mapping:
- TC-AT03-R1-001: canonical mixed modality sequence
- TC-AT03-R1-002: voice shortcut/session history cannot create canonical history
- TC-AT03-R1-003: session-local history cannot recover canonical transcript
- TC-AT03-R1-004: voice transport metadata cannot fork conversation identity
- TC-AT03-R1-005: mixed lane remains one canonical repository sequence
"""

from __future__ import annotations

import pytest

import julia_core.runtime.conversation_runtime as crt_module
from julia_core.conversation_state.legacy_json_repository import LegacyJsonConversationRepository
from julia_core.runtime.conversation_runtime import (
    ConversationRuntime,
    configure_conversation_runtime,
    get_conversation_runtime,
)


def _mock_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    return f"ack:{modality}:{text}"


@pytest.fixture(autouse=True)
def _fresh_runtime(tmp_path):
    """Fresh canonical repository per test; no product/session cache involved."""
    crt_module._runtime = None
    repo = LegacyJsonConversationRepository(tmp_path / "at03_conversations.json")
    configure_conversation_runtime(repo)
    yield repo
    crt_module._runtime = None


def _append_text(rt: ConversationRuntime, cid: str, tid: str, content: str):
    return rt.process_turn(
        conversation_id=cid,
        turn_id=tid,
        modality="text",
        input=content,
        cognitive_fn=_mock_cognitive,
    )


def _append_voice(rt: ConversationRuntime, cid: str, tid: str, content: str, **metadata):
    turn = {
        "turn_id": tid,
        "modality": "voice",
        "user_content": content,
        "assistant_content": f"ack:voice:{content}",
        "assistant_status": "completed",
    }
    turn.update(metadata)
    return rt.append_external_turns(cid, [turn])


def _user_messages(rt: ConversationRuntime, cid: str) -> list[dict]:
    return [m for m in rt.get_canonical_history(cid) if m["role"] == "user"]


def test_tc_at03_r1_001_canonical_text_voice_text_sequence():
    """TC-AT03-R1-001: Text T1 → Voice T2 → Text T3 is one sequence."""
    rt = get_conversation_runtime()
    conv = rt.create_conversation("AT-03 R1 mixed sequence")
    cid = conv.conversation_id

    _append_text(rt, cid, "at03-t1", "Text T1")
    _append_voice(rt, cid, "at03-v2", "Voice T2")
    _append_text(rt, cid, "at03-t3", "Text T3")

    users = _user_messages(rt, cid)

    assert [m["turn_id"] for m in users] == ["at03-t1", "at03-v2", "at03-t3"]
    assert [m["modality"] for m in users] == ["text", "voice", "text"]
    assert [m["content"] for m in users] == ["Text T1", "Voice T2", "Text T3"]
    assert {m["conversation_id"] for m in rt.get_canonical_history(cid)} == {cid}


def test_tc_at03_r1_002_voice_shortcut_history_cannot_create_canonical_history():
    """TC-AT03-R1-002: a voice/session shortcut alone is not canonical."""
    rt = get_conversation_runtime()

    voice_shortcut_history = {
        "voice_session_id": "voice-session-at03-shortcut",
        "history": [{"role": "user", "content": "Voice shortcut only"}],
    }

    assert voice_shortcut_history["history"]
    assert rt.get_conversation("voice-session-at03-shortcut") is None
    assert rt.get_canonical_history("voice-session-at03-shortcut") == []


def test_tc_at03_r1_003_session_history_cannot_recover_canonical_transcript(tmp_path):
    """TC-AT03-R1-003: session-local history is not a recovery source."""
    repo_path = tmp_path / "canonical.json"
    repo = LegacyJsonConversationRepository(repo_path)
    rt = ConversationRuntime(repository=repo)
    conv = rt.create_conversation("AT-03 recovery boundary")
    cid = conv.conversation_id

    session_local_history = {
        "session_id": "transport-session-001",
        "conversation_id": cid,
        "history": [{"role": "user", "content": "not committed"}],
    }

    # Simulate restart from canonical repository only.
    rt_after_restart = ConversationRuntime(repository=LegacyJsonConversationRepository(repo_path))

    assert session_local_history["history"][0]["content"] == "not committed"
    assert rt_after_restart.get_canonical_history(cid) == []


def test_tc_at03_r1_004_transport_metadata_cannot_fork_conversation_identity():
    """TC-AT03-R1-004: voice transport metadata is provenance, not identity."""
    rt = get_conversation_runtime()
    conv = rt.create_conversation("AT-03 metadata boundary")
    cid = conv.conversation_id

    _append_text(rt, cid, "at03-meta-t1", "Text before voice")
    _append_voice(
        rt,
        cid,
        "at03-meta-v2",
        "Voice with transport metadata",
        voice_session_id="voice-session-should-not-be-conversation",
        voice_trace_id="voice-trace-should-not-be-conversation",
        participant_id="participant-should-not-be-conversation",
    )
    _append_text(rt, cid, "at03-meta-t3", "Text after voice")

    users = _user_messages(rt, cid)

    assert [m["turn_id"] for m in users] == [
        "at03-meta-t1",
        "at03-meta-v2",
        "at03-meta-t3",
    ]
    assert rt.get_conversation("voice-session-should-not-be-conversation") is None
    assert rt.get_conversation("voice-trace-should-not-be-conversation") is None
    assert rt.get_conversation("participant-should-not-be-conversation") is None


def test_tc_at03_r1_005_mixed_lane_is_single_canonical_repository_sequence():
    """TC-AT03-R1-005: canonical repository has one mixed lane, not split stores."""
    rt = get_conversation_runtime()
    conv = rt.create_conversation("AT-03 single lane")
    cid = conv.conversation_id

    _append_text(rt, cid, "at03-lane-t1", "Lane Text T1")
    _append_voice(rt, cid, "at03-lane-v2", "Lane Voice T2")
    _append_text(rt, cid, "at03-lane-t3", "Lane Text T3")

    canonical = rt.get_canonical_history(cid)
    user_messages = [m for m in canonical if m["role"] == "user"]
    assistant_messages = [m for m in canonical if m["role"] == "assistant"]

    assert len(canonical) == 6
    assert len(user_messages) == 3
    assert len(assistant_messages) == 3
    assert [m["modality"] for m in canonical] == [
        "text", "text", "voice", "voice", "text", "text",
    ]
    assert [m["turn_id"] for m in canonical] == [
        "at03-lane-t1", "at03-lane-t1",
        "at03-lane-v2", "at03-lane-v2",
        "at03-lane-t3", "at03-lane-t3",
    ]
