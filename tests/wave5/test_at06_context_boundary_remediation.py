"""Wave5 AT-06 Minimal P0 Remediation — Context OS conversation boundary.

These tests verify the minimal fix for the P0 gap found during AT-06 Audit.
They are remediation evidence, not AT-06 R1/IA freeze evidence.
"""

from __future__ import annotations

from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime


ALPHA = "ALPHA_PRIVATE_MARKER_001"
BETA = "BETA_PRIVATE_MARKER_002"


def _mixed_history():
    return [
        {"role": "user", "conversation_id": "conv_A", "turn_id": "a1", "content": ALPHA},
        {"role": "assistant", "conversation_id": "conv_A", "turn_id": "a1", "content": "ack A"},
        {"role": "user", "conversation_id": "conv_B", "turn_id": "b1", "content": BETA},
        {"role": "assistant", "conversation_id": "conv_B", "turn_id": "b1", "content": "ack B"},
    ]


def _visible_text(messages: list[dict]) -> str:
    return "\n".join(str(m.get("content", "")) for m in messages)


def test_at06_rem_p0_context_os_drops_foreign_history_before_provider_visible():
    ctx = ContextExecutionRuntime(None)
    pkg = ctx.prepare(
        conversation_id="conv_B",
        turn_id="b2",
        user_text="question B",
        history=_mixed_history(),
        modality="text",
    )

    messages = pkg.to_messages(_mixed_history(), "question B")
    visible = _visible_text(messages)

    assert ALPHA not in visible
    assert BETA in visible
    assert pkg.active_tail_turn_ids == ["b1", "b1"]
    assert all(m.get("conversation_id") in (None, "conv_B") for m in pkg.active_tail_messages)


def test_at06_rem_p0_boundary_provenance_records_dropped_foreign_history():
    ctx = ContextExecutionRuntime(None)
    pkg = ctx.prepare(
        conversation_id="conv_B",
        turn_id="b2",
        user_text="question B",
        history=_mixed_history(),
        modality="text",
    )

    boundary = [p for p in pkg.provenance if p["frame"] == "conversation_boundary"]
    assert boundary == [{
        "frame": "conversation_boundary",
        "source_ref": "conversation:conv_B",
        "canonical_ref": "",
        "reason": "dropped_foreign_history:2",
        "stage": 0,
        "token_estimate": 0,
    }]


def test_at06_rem_p0_governed_scoped_history_still_passes():
    ctx = ContextExecutionRuntime(None)
    scoped_history = [m for m in _mixed_history() if m["conversation_id"] == "conv_B"]

    pkg = ctx.prepare(
        conversation_id="conv_B",
        turn_id="b2",
        user_text="question B",
        history=scoped_history,
        modality="text",
    )

    messages = pkg.to_messages(scoped_history, "question B")
    visible = _visible_text(messages)

    assert ALPHA not in visible
    assert BETA in visible
    assert pkg.active_tail_turn_ids == ["b1", "b1"]
    assert [p for p in pkg.provenance if p["frame"] == "conversation_boundary"] == []


def test_at06_rem_p0_active_conversation_drops_unscoped_cache_history():
    ctx = ContextExecutionRuntime(None)
    unscoped_cache_history = [
        {"role": "user", "turn_id": "legacy1", "content": ALPHA},
        {"role": "assistant", "turn_id": "legacy1", "content": "cached ack"},
    ]

    pkg = ctx.prepare(
        conversation_id="conv_B",
        turn_id="b2",
        user_text="question B",
        history=unscoped_cache_history,
        modality="text",
    )

    visible = _visible_text(pkg.to_messages(unscoped_cache_history, "question B"))
    assert ALPHA not in visible
    assert pkg.active_tail_turn_ids == []


def test_at06_rem_p0_legacy_empty_conversation_preserves_unscoped_history():
    ctx = ContextExecutionRuntime(None)
    legacy_history = [
        {"role": "user", "turn_id": "legacy1", "content": "legacy unscoped message"},
        {"role": "assistant", "turn_id": "legacy1", "content": "legacy ack"},
    ]

    pkg = ctx.prepare(
        conversation_id="",
        turn_id="",
        user_text="question legacy",
        history=legacy_history,
        modality="text",
    )

    visible = _visible_text(pkg.to_messages(legacy_history, "question legacy"))
    assert "legacy unscoped message" in visible
    assert pkg.active_tail_turn_ids == ["legacy1", "legacy1"]
