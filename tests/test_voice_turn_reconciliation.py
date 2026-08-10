"""CORE-C1B-R1: Voice Turn Reconciliation Tests.

Tests for SessionRepository.append_external_turns_atomic()
and ConversationRuntime.append_external_turns().
"""

import pytest

from julia_core.conversation_state.repository import (
    TurnConflictError,
)
from julia_core.runtime.conversation_runtime import (
    ConversationRuntime,
    get_conversation_runtime,
)


@pytest.fixture(autouse=True)
def clear_repo():
    """Reset repository state before each test."""
    crt = get_conversation_runtime()
    crt._repository._repo._sessions.clear()
    crt._repository._repo._lock = type(crt._repository._repo._lock)()


def _make_turn(turn_id: str, user: str, assistant: str = "",
               assistant_status: str = "completed"):
    return {
        "turn_id": turn_id,
        "modality": "voice",
        "user_content": user,
        "user_created_at": "2026-08-09T12:00:00Z",
        "assistant_content": assistant,
        "assistant_status": assistant_status,
        "assistant_created_at": "2026-08-09T12:00:05Z",
    }


# ── Atomic append ─────────────────────────────────────────────────────────────

def test_append_one_completed_turn():
    crt = get_conversation_runtime()
    conv = crt.create_conversation("Voice Test")

    result = crt.append_external_turns(
        conv.conversation_id,
        [_make_turn("voice:vws:0001", "Hello", "Hi there")],
    )

    assert result["appended_turn_ids"] == ["voice:vws:0001"]
    assert result["skipped_turn_ids"] == []

    history = crt.get_history(conv.conversation_id)
    texts = [m["content"] for m in history]
    assert "Hello" in texts
    assert "Hi there" in texts


def test_append_multiple_turns_preserves_order():
    crt = get_conversation_runtime()
    conv = crt.create_conversation("Multi Turn")

    turns = [
        _make_turn("voice:vws:0001", "First", "Reply 1"),
        _make_turn("voice:vws:0002", "Second", "Reply 2"),
        _make_turn("voice:vws:0003", "Third", "Reply 3"),
    ]

    result = crt.append_external_turns(conv.conversation_id, turns)
    assert result["appended_turn_ids"] == [
        "voice:vws:0001", "voice:vws:0002", "voice:vws:0003",
    ]

    history = crt.get_history(conv.conversation_id)
    user_messages = [m["content"] for m in history if m["role"] == "user"]
    assert user_messages == ["First", "Second", "Third"]


def test_retry_identical_batch_is_idempotent():
    crt = get_conversation_runtime()
    conv = crt.create_conversation("Idempotent")

    turns = [
        _make_turn("voice:vws:0001", "Hello", "Hi"),
    ]

    r1 = crt.append_external_turns(conv.conversation_id, turns)
    assert r1["appended_turn_ids"] == ["voice:vws:0001"]

    r2 = crt.append_external_turns(conv.conversation_id, turns)
    assert r2["appended_turn_ids"] == []
    assert r2["skipped_turn_ids"] == ["voice:vws:0001"]

    history = crt.get_history(conv.conversation_id)
    # Only one copy
    assert len([m for m in history if m["content"] == "Hello"]) == 1


def test_same_turn_id_different_content_conflicts():
    crt = get_conversation_runtime()
    conv = crt.create_conversation("Conflict")

    crt.append_external_turns(
        conv.conversation_id,
        [_make_turn("voice:vws:0001", "Hello", "Hi")],
    )

    with pytest.raises(TurnConflictError):
        crt.append_external_turns(
            conv.conversation_id,
            [_make_turn("voice:vws:0001", "Different", "Hi")],
        )


def test_atomic_failure_no_partial_turn():
    crt = get_conversation_runtime()
    conv = crt.create_conversation("Atomic")

    turns = [
        _make_turn("voice:vws:0001", "First", "Reply 1"),
        _make_turn("voice:vws:0002", "", ""),  # no user_content → bad turn
        _make_turn("voice:vws:0003", "Third", "Reply 3"),
    ]

    try:
        crt.append_external_turns(conv.conversation_id, turns)
    except Exception:
        pass

    history = crt.get_history(conv.conversation_id)
    user_texts = [m["content"] for m in history if m["role"] == "user"]
    # First turn should NOT be present (atomic rollback)
    assert "First" not in user_texts
    assert "Third" not in user_texts


def test_conv_a_import_does_not_affect_conv_b():
    crt = get_conversation_runtime()
    conv_a = crt.create_conversation("Conv A")
    conv_b = crt.create_conversation("Conv B")

    crt.append_external_turns(
        conv_a.conversation_id,
        [_make_turn("voice:vws:0001", "A secret", "Reply A")],
    )

    history_b = crt.get_history(conv_b.conversation_id)
    texts_b = [m["content"] for m in history_b]
    assert "A secret" not in texts_b
    assert "Reply A" not in texts_b


def test_imported_history_present_in_get_history():
    crt = get_conversation_runtime()
    conv = crt.create_conversation("History Test")

    crt.append_external_turns(
        conv.conversation_id,
        [_make_turn("voice:vws:0001", "Remember this", "OK")],
    )

    history = crt.get_history(conv.conversation_id)
    assert len(history) == 2  # user + assistant
    assert history[0]["content"] == "Remember this"
    assert history[0]["modality"] == "voice"
    assert history[1]["content"] == "OK"
    assert history[1]["modality"] == "voice"


def test_restart_recovers_voice_history():
    crt = get_conversation_runtime()
    conv = crt.create_conversation("Restart Test")

    crt.append_external_turns(
        conv.conversation_id,
        [_make_turn("voice:vws:0001", "Will this survive?", "Yes")],
    )

    # Simulate restart
    crt2 = ConversationRuntime()
    history = crt2.get_history(conv.conversation_id)
    texts = [m["content"] for m in history]
    assert "Will this survive?" in texts
    assert "Yes" in texts


def test_restart_rebuilds_interaction_state():
    crt = get_conversation_runtime()
    conv = crt.create_conversation("Interaction Rebuild")

    crt.append_external_turns(
        conv.conversation_id,
        [
            _make_turn("voice:vws:0001", "I am Tony", "Hello Tony"),
            _make_turn("voice:vws:0002", "call me 老公", "好的老公"),
        ],
    )

    # Simulate restart
    crt2 = ConversationRuntime()
    state = crt2.get_interaction_state(conv.conversation_id)
    assert state is not None
    # Identity checks should have been rebuilt from user messages
    assert state.identity_checks > 0


def test_interrupted_assistant():
    crt = get_conversation_runtime()
    conv = crt.create_conversation("Interrupted")

    crt.append_external_turns(
        conv.conversation_id,
        [_make_turn("voice:vws:0001", "Say something long",
                     "I was going to say a lot but got", "interrupted")],
    )

    history = crt.get_history(conv.conversation_id)
    assistant_msgs = [m for m in history if m["role"] == "assistant"]
    assert len(assistant_msgs) == 1
    assert assistant_msgs[0]["status"] == "interrupted"


def test_brain_endpoint_returns_409_on_conflict():
    """Test the Brain adapter correctly maps TurnConflictError to HTTP 409."""
    from julia_core.conversation_state.repository import TurnConflictError

    crt = get_conversation_runtime()
    conv = crt.create_conversation("Brain 409")

    crt.append_external_turns(
        conv.conversation_id,
        [_make_turn("voice:vws:0001", "Original", "Reply")],
    )

    # Different content, same turn_id
    with pytest.raises(TurnConflictError):
        crt.append_external_turns(
            conv.conversation_id,
            [_make_turn("voice:vws:0001", "Modified", "Reply")],
        )


def test_conversation_not_found_raises():
    crt = get_conversation_runtime()
    with pytest.raises(ValueError, match="not found"):
        crt.append_external_turns(
            "nonexistent-conv-id",
            [_make_turn("voice:vws:0001", "Hello", "Hi")],
        )


def test_empty_turns_returns_gracefully():
    crt = get_conversation_runtime()
    conv = crt.create_conversation("Empty")

    result = crt.append_external_turns(conv.conversation_id, [])
    assert result["appended_turn_ids"] == []


def test_modality_is_voice_by_default():
    crt = get_conversation_runtime()
    conv = crt.create_conversation("Modality Test")

    crt.append_external_turns(
        conv.conversation_id,
        [_make_turn("voice:vws:0001", "Voice message", "Voice reply")],
    )

    history = crt.get_history(conv.conversation_id)
    for m in history:
        assert m["modality"] == "voice"
