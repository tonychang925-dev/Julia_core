from __future__ import annotations

import pytest

from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime


class _Capability:
    class registry:
        @staticmethod
        def all():
            return []

    def invocation_policy(self):
        return {
            "invocation_protocol": {
                "format": "```tool_call\n{JSON}\n```",
                "structured_call_required": True,
                "raw_user_text_routing": False,
            },
            "epistemic_rules": {
                "file": {
                    "capability_prefix": "file.*",
                    "requires_explicit_user_intent": True,
                },
                "external_evidence": {
                    "capability_prefixes": ["market.*", "research.*"],
                    "read_only": True,
                    "julia_may_request_when_evidence_missing": True,
                    "explicit_user_request_requires_execution": True,
                    "explicit_request_rule": "explicit external evidence must execute before final text",
                },
            },
            "evidence_role": {
                "tool_result_is_evidence_not_final_judgment": True,
                "julia_second_pass_interpretation_required": True,
            },
            "limits": {"max_tool_calls_per_model_response": 1},
        }


class _Persona:
    def get_traits_for_injection(self):
        return ""


class _Session:
    persona = _Persona()
    capability = _Capability()

    def _load_recent_experiences(self):
        return ""


def _message(
    *,
    message_id: str = "msg-current-user",
    conversation_id: str = "conv-current",
    turn_id: str = "turn-current",
    role: str = "user",
    created_at: str = "2026-09-23T10:15:30.123456+08:00",
):
    return {
        "message_id": message_id,
        "conversation_id": conversation_id,
        "turn_id": turn_id,
        "role": role,
        "status": "completed",
        "created_at": created_at,
        "content": "message",
    }


def _prepare(history: list[dict]):
    return ContextExecutionRuntime(_Session()).prepare(
        conversation_id="conv-current",
        turn_id="turn-current",
        user_text="查一下 600519 今天的行情",
        history=history,
    )


def _anchor(package):
    return (
        package.situation_frame.get("current_turn_timestamp"),
        package.situation_frame.get("current_date"),
        package.situation_frame.get("utc_offset"),
    )


def test_aware_exact_current_user_turn_is_projected_with_provenance():
    package = _prepare([
        _message(
            message_id="msg-old",
            turn_id="turn-old",
            created_at="2026-09-22T09:00:00+08:00",
        ),
        _message(message_id="msg-current-user"),
    ])

    assert _anchor(package) == (
        "2026-09-23T10:15:30.123456+08:00",
        "2026-09-23",
        "+08:00",
    )
    temporal = [
        entry
        for entry in package.provenance
        if entry["source_ref"] == "C02 canonical current user ConversationMessage"
    ]
    assert temporal == [{
        "frame": "situation",
        "source_ref": "C02 canonical current user ConversationMessage",
        "canonical_ref": (
            "conversation:conv-current:turn:turn-current:message:msg-current-user"
        ),
        "reason": "C03 current-turn temporal projection",
        "stage": 0,
        "token_estimate": 0,
    }]


@pytest.mark.parametrize(
    "history",
    [
        [_message(message_id="naive", created_at="2026-09-23T10:15:30")],
        [_message(message_id="malformed", created_at="2026-09-23 not-a-timestamp")],
        [_message(message_id="old", turn_id="turn-old", created_at="2026-09-22T09:00:00+08:00")],
        [_message(message_id="assistant", role="assistant", created_at="2026-09-23T11:00:00+08:00")],
        [_message(message_id="foreign", conversation_id="conv-foreign", created_at="2026-09-23T12:00:00+09:00")],
        [
            _message(message_id="duplicate-a", created_at="2026-09-23T10:15:30.123456+08:00"),
            _message(message_id="duplicate-b", created_at="2026-09-23T10:15:31.123456+08:00"),
        ],
    ],
    ids=["naive", "malformed", "previous-turn", "assistant", "foreign", "ambiguous"],
)
def test_invalid_or_non_current_authority_is_omitted(history):
    package = _prepare(history)

    assert all(value is None for value in _anchor(package))
    temporal_failures = [
        failure
        for failure in package._frame_failures
        if failure["frame"] == "situation:temporal"
    ]
    if history[0].get("created_at") in {
        "2026-09-23T10:15:30",
        "2026-09-23 not-a-timestamp",
    } or len(history) == 2:
        assert temporal_failures
        assert temporal_failures[-1]["required"] is False


def test_same_canonical_message_replay_projects_identical_temporal_anchor():
    history = [_message()]
    first = _prepare(history)
    second = _prepare(history)

    assert _anchor(first) == _anchor(second)


def test_actual_model_message_path_renders_temporal_anchor():
    package = _prepare([_message()])
    system_message = package.to_messages([], "query")[0]

    assert system_message["role"] == "system"
    assert "current_turn_timestamp: 2026-09-23T10:15:30.123456+08:00" in system_message["content"]
    assert "current_date: 2026-09-23" in system_message["content"]
    assert "utc_offset: +08:00" in system_message["content"]
