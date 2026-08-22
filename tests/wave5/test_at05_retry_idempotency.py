"""Wave5 AT-05-R1 — Retry idempotency permanent acceptance evidence.

R1 proves same canonical turn identity retry has exactly one canonical effect.
It does not test reconnect UUID generation (AT-04), segment rotation (AT-07),
pagination (AT-08), provider retry strategy, or retry UX.

TC mapping:
- TC-AT05-R1-001 same text turn retry returns same user and assistant message IDs
- TC-AT05-R1-002 same text turn retry leaves exactly one user and one assistant message
- TC-AT05-R1-003 concurrent same turn retry converges to one canonical turn
- TC-AT05-R1-004 external/voice identical turn batch retry skips without duplicate user/assistant
- TC-AT05-R1-005 same turn_id with different content conflicts and leaves transcript unchanged
- TC-AT05-R1-006 fresh runtime retry after completed turn recovery remains exactly-once
- TC-AT05-R1-007 same turn_id in different conversations is isolated
- TC-AT05-R1-008 partial/failed assistant retry does not duplicate canonical effects
- TC-AT05-R1-009 retry metadata changes cannot create new canonical history
"""

from __future__ import annotations

import threading

import pytest

from julia_core.conversation_state.legacy_json_repository import LegacyJsonConversationRepository
from julia_core.conversation_state.repository import TurnConflictError
from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.conversation_runtime import ConversationRuntime


def _stack(root):
    repo = StorageV2ConversationRepository(str(root))
    rt = ConversationRuntime(repository=repo)
    return repo, rt


def _legacy_stack(root):
    repo = LegacyJsonConversationRepository(root / "legacy.json")
    rt = ConversationRuntime(repository=repo)
    return repo, rt


def _mock_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    return f"ack:{modality}:{text}"


def _failing_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    raise RuntimeError("simulated assistant failure")


def _voice_turn(turn_id: str, user: str, assistant: str | None = None, **metadata) -> dict:
    turn = {
        "turn_id": turn_id,
        "modality": "voice",
        "user_content": user,
        "assistant_content": assistant if assistant is not None else f"voice-ack:{user}",
        "assistant_status": "completed",
    }
    turn.update(metadata)
    return turn


def _turn_messages(rt: ConversationRuntime, cid: str, tid: str) -> list[dict]:
    return [m for m in rt.get_messages(cid) if m["turn_id"] == tid]


def _roles(messages: list[dict]) -> list[str]:
    return [m["role"] for m in messages]


def test_tc_at05_r1_001_same_text_retry_returns_same_message_ids(tmp_path):
    repo, rt = _stack(tmp_path)
    try:
        cid = rt.create_conversation(title="AT05 same ids").conversation_id

        first = rt.process_turn(
            conversation_id=cid,
            turn_id="at05-same-ids",
            modality="text",
            input="same canonical content",
            cognitive_fn=_mock_cognitive,
        )
        retry = rt.process_turn(
            conversation_id=cid,
            turn_id="at05-same-ids",
            modality="text",
            input="same canonical content",
            cognitive_fn=_mock_cognitive,
        )

        assert retry.user_message_id == first.user_message_id
        assert retry.assistant_message_id == first.assistant_message_id
        assert retry.assistant_content == first.assistant_content
    finally:
        repo.close()


def test_tc_at05_r1_002_completed_text_retry_exactly_one_user_one_assistant(tmp_path):
    repo, rt = _stack(tmp_path)
    try:
        cid = rt.create_conversation(title="AT05 exactly once").conversation_id

        for _ in range(3):
            rt.process_turn(
                conversation_id=cid,
                turn_id="at05-exactly-once",
                modality="text",
                input="repeat same logical turn",
                cognitive_fn=_mock_cognitive,
            )

        messages = _turn_messages(rt, cid, "at05-exactly-once")
        assert _roles(messages).count("user") == 1
        assert _roles(messages).count("assistant") == 1
        assert [(m["role"], m["content"], m["status"]) for m in messages] == [
            ("user", "repeat same logical turn", "completed"),
            ("assistant", "ack:text:repeat same logical turn", "completed"),
        ]
    finally:
        repo.close()


def test_tc_at05_r1_003_concurrent_same_turn_retry_converges_to_one_turn(tmp_path):
    repo, rt = _legacy_stack(tmp_path)
    try:
        cid = rt.create_conversation(title="AT05 concurrent").conversation_id
        results = []
        errors = []

        def submit():
            try:
                results.append(rt.process_turn(
                    conversation_id=cid,
                    turn_id="at05-concurrent",
                    modality="text",
                    input="concurrent same logical turn",
                    cognitive_fn=_mock_cognitive,
                ))
            except Exception as exc:  # pragma: no cover - assertion below reports it
                errors.append(exc)

        threads = [threading.Thread(target=submit) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert errors == []
        assert len(results) == 8
        assert {r.user_message_id for r in results}
        assert len({r.user_message_id for r in results}) == 1
        assert len({r.assistant_message_id for r in results}) == 1
        messages = _turn_messages(rt, cid, "at05-concurrent")
        assert _roles(messages) == ["user", "assistant"]
    finally:
        if hasattr(repo, "close"):
            repo.close()


def test_tc_at05_r1_004_external_voice_retry_skips_without_duplicate_messages(tmp_path):
    repo, rt = _stack(tmp_path)
    try:
        cid = rt.create_conversation(title="AT05 voice retry").conversation_id
        turn = _voice_turn("at05-voice-retry", "same voice retry", "voice ack")

        first = rt.append_external_turns(cid, [turn])
        retry = rt.append_external_turns(cid, [turn])

        assert first["appended_turn_ids"] == ["at05-voice-retry"]
        assert retry["appended_turn_ids"] == []
        assert retry["skipped_turn_ids"] == ["at05-voice-retry"]
        messages = _turn_messages(rt, cid, "at05-voice-retry")
        assert [(m["role"], m["content"], m["status"]) for m in messages] == [
            ("user", "same voice retry", "completed"),
            ("assistant", "voice ack", "completed"),
        ]
    finally:
        repo.close()


def test_tc_at05_r1_005_same_identity_different_content_conflicts_zero_mutation(tmp_path):
    repo, rt = _stack(tmp_path)
    try:
        cid = rt.create_conversation(title="AT05 conflict").conversation_id
        rt.process_turn(
            conversation_id=cid,
            turn_id="at05-conflict",
            modality="text",
            input="original canonical content",
            cognitive_fn=_mock_cognitive,
        )
        before = rt.get_messages(cid)

        with pytest.raises(TurnConflictError):
            rt.process_turn(
                conversation_id=cid,
                turn_id="at05-conflict",
                modality="text",
                input="mutated retry content",
                cognitive_fn=_mock_cognitive,
            )

        assert rt.get_messages(cid) == before
    finally:
        repo.close()


def test_tc_at05_r1_006_fresh_runtime_retry_after_completed_turn_is_exactly_once(tmp_path):
    repo1, rt1 = _stack(tmp_path)
    cid = rt1.create_conversation(title="AT05 fresh runtime").conversation_id
    first = rt1.process_turn(
        conversation_id=cid,
        turn_id="at05-restart-retry",
        modality="text",
        input="persisted before restart",
        cognitive_fn=_mock_cognitive,
    )
    repo1.close()

    repo2, rt2 = _stack(tmp_path)
    try:
        retry = rt2.process_turn(
            conversation_id=cid,
            turn_id="at05-restart-retry",
            modality="text",
            input="persisted before restart",
            cognitive_fn=_mock_cognitive,
        )

        assert retry.user_message_id == first.user_message_id
        assert retry.assistant_message_id == first.assistant_message_id
        messages = _turn_messages(rt2, cid, "at05-restart-retry")
        assert _roles(messages) == ["user", "assistant"]
    finally:
        repo2.close()


def test_tc_at05_r1_007_same_turn_id_in_different_conversations_is_isolated(tmp_path):
    repo, rt = _stack(tmp_path)
    try:
        cid_a = rt.create_conversation(title="AT05 conv A").conversation_id
        cid_b = rt.create_conversation(title="AT05 conv B").conversation_id

        result_a = rt.process_turn(
            conversation_id=cid_a,
            turn_id="shared-turn-string",
            modality="text",
            input="content in conversation A",
            cognitive_fn=_mock_cognitive,
        )
        result_b = rt.process_turn(
            conversation_id=cid_b,
            turn_id="shared-turn-string",
            modality="text",
            input="content in conversation B",
            cognitive_fn=_mock_cognitive,
        )

        assert result_a.conversation_id == cid_a
        assert result_b.conversation_id == cid_b
        assert result_a.user_message_id != result_b.user_message_id
        assert [m["content"] for m in _turn_messages(rt, cid_a, "shared-turn-string") if m["role"] == "user"] == [
            "content in conversation A"
        ]
        assert [m["content"] for m in _turn_messages(rt, cid_b, "shared-turn-string") if m["role"] == "user"] == [
            "content in conversation B"
        ]
    finally:
        repo.close()


def test_tc_at05_r1_008_partial_failed_assistant_retry_no_duplicate_or_phantom_completion(tmp_path):
    repo, rt = _stack(tmp_path)
    try:
        cid = rt.create_conversation(title="AT05 partial retry").conversation_id

        failed = rt.process_turn(
            conversation_id=cid,
            turn_id="at05-partial",
            modality="text",
            input="durable user before assistant failure",
            cognitive_fn=_failing_cognitive,
        )
        retry = rt.process_turn(
            conversation_id=cid,
            turn_id="at05-partial",
            modality="text",
            input="durable user before assistant failure",
            cognitive_fn=_mock_cognitive,
        )

        messages = _turn_messages(rt, cid, "at05-partial")
        completed_history = [m for m in rt.get_canonical_history(cid) if m["turn_id"] == "at05-partial"]

        assert failed.status == "failed"
        assert retry.user_message_id == failed.user_message_id
        assert retry.assistant_message_id == failed.assistant_message_id
        assert _roles(messages).count("user") == 1
        assert _roles(messages).count("assistant") == 1
        assert [(m["role"], m["status"], m["content"]) for m in messages] == [
            ("user", "completed", "durable user before assistant failure"),
            ("assistant", "failed", ""),
        ]
        # Canonical completed history must not invent a successful assistant
        # message merely because the same turn was retried.
        assert [(m["role"], m["content"], m["status"]) for m in completed_history] == [
            ("user", "durable user before assistant failure", "completed")
        ]
    finally:
        repo.close()


def test_tc_at05_r1_009_retry_metadata_changes_cannot_create_new_history(tmp_path):
    repo, rt = _stack(tmp_path)
    try:
        cid = rt.create_conversation(title="AT05 metadata").conversation_id

        first = rt.append_external_turns(
            cid,
            [_voice_turn(
                "at05-metadata-retry",
                "metadata is not retry authority",
                request_id="request-1",
                retry_count=0,
                transport_session_id="transport-A",
            )],
        )
        retry = rt.append_external_turns(
            cid,
            [_voice_turn(
                "at05-metadata-retry",
                "metadata is not retry authority",
                request_id="request-2",
                retry_count=3,
                transport_session_id="transport-B",
            )],
        )

        assert first["appended_turn_ids"] == ["at05-metadata-retry"]
        assert retry["appended_turn_ids"] == []
        assert retry["skipped_turn_ids"] == ["at05-metadata-retry"]
        messages = _turn_messages(rt, cid, "at05-metadata-retry")
        assert _roles(messages) == ["user", "assistant"]
    finally:
        repo.close()
