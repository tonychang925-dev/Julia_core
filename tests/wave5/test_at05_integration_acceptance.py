"""Wave5 AT-05 Integration Acceptance — retry idempotency.

IA verifies the integrated management/runtime/storage/recovery path for retry
idempotency. It does not test reconnect UUID generation, segment rotation,
pagination, provider retry policy, or retry UX.

TC mapping:
- TC-AT05-IA-001 real management/runtime retry path is exactly-once
- TC-AT05-IA-002 real restart/recovery retry path remains exactly-once
- TC-AT05-IA-003 real conflict path rejects and preserves canonical transcript
- TC-AT05-IA-004 real metadata variation retry cannot create new history
- TC-AT05-IA-005 real partial failure retry has no duplicate or phantom completion
"""

from __future__ import annotations

import pytest

from julia_core.conversation_state.repository import TurnConflictError
from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from conversation_management import ConversationManagementService
from julia_core.runtime.conversation_runtime import ConversationRuntime


class _FakeIdempotencyPort:
    def __init__(self):
        self._reserved: dict[str, str] = {}

    def get_or_reserve(self, key: str, candidate: str) -> str:
        return self._reserved.setdefault(key, candidate)


def _stack(root, port=None):
    repo = StorageV2ConversationRepository(str(root))
    rt = ConversationRuntime(repository=repo)
    svc = ConversationManagementService(rt, port or _FakeIdempotencyPort())
    return repo, rt, svc


def _mock_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    return f"ia-ack:{modality}:{text}"


def _failing_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    raise RuntimeError("simulated IA assistant failure")


def _voice_turn(turn_id: str, user: str, assistant: str | None = None, **metadata) -> dict:
    turn = {
        "turn_id": turn_id,
        "modality": "voice",
        "user_content": user,
        "assistant_content": assistant if assistant is not None else f"ia-voice-ack:{user}",
        "assistant_status": "completed",
    }
    turn.update(metadata)
    return turn


def _turn_messages(messages: list[dict], tid: str) -> list[dict]:
    return [m for m in messages if m["turn_id"] == tid]


def _roles(messages: list[dict]) -> list[str]:
    return [m["role"] for m in messages]


def test_tc_at05_ia_001_real_management_runtime_retry_path_exactly_once(tmp_path):
    """TC-AT05-IA-001: management create → runtime retry → management read."""
    repo, rt, svc = _stack(tmp_path)
    try:
        cid = svc.create(idempotency_key="at05-ia-001", title="AT05 IA retry")["id"]

        first = rt.process_turn(
            conversation_id=cid,
            turn_id="at05-ia-retry",
            modality="text",
            input="same IA logical turn",
            cognitive_fn=_mock_cognitive,
        )
        retry = rt.process_turn(
            conversation_id=cid,
            turn_id="at05-ia-retry",
            modality="text",
            input="same IA logical turn",
            cognitive_fn=_mock_cognitive,
        )

        messages = _turn_messages(svc.get_messages(cid, max_messages=50), "at05-ia-retry")
        assert retry.user_message_id == first.user_message_id
        assert retry.assistant_message_id == first.assistant_message_id
        assert _roles(messages) == ["user", "assistant"]
        assert [(m["content"], m["status"]) for m in messages] == [
            ("same IA logical turn", "completed"),
            ("ia-ack:text:same IA logical turn", "completed"),
        ]
    finally:
        repo.close()


def test_tc_at05_ia_002_real_restart_recovery_retry_path_exactly_once(tmp_path):
    """TC-AT05-IA-002: fresh runtime over same repository reconciles retry."""
    port = _FakeIdempotencyPort()
    repo1, rt1, svc1 = _stack(tmp_path, port)
    cid = svc1.create(idempotency_key="at05-ia-002", title="AT05 IA restart")["id"]
    first = rt1.process_turn(
        conversation_id=cid,
        turn_id="at05-ia-restart-retry",
        modality="text",
        input="persisted IA logical turn",
        cognitive_fn=_mock_cognitive,
    )
    repo1.close()

    repo2, rt2, svc2 = _stack(tmp_path, port)
    try:
        # Management open/read proves the new runtime is attached to the same
        # canonical conversation before retrying through governed runtime.
        assert svc2.open(cid)["id"] == cid
        retry = rt2.process_turn(
            conversation_id=cid,
            turn_id="at05-ia-restart-retry",
            modality="text",
            input="persisted IA logical turn",
            cognitive_fn=_mock_cognitive,
        )

        messages = _turn_messages(svc2.get_messages(cid, max_messages=50), "at05-ia-restart-retry")
        assert retry.user_message_id == first.user_message_id
        assert retry.assistant_message_id == first.assistant_message_id
        assert _roles(messages) == ["user", "assistant"]
    finally:
        repo2.close()


def test_tc_at05_ia_003_real_conflict_path_rejects_preserves_transcript(tmp_path):
    """TC-AT05-IA-003: same identity + different content is conflict."""
    repo, rt, svc = _stack(tmp_path)
    try:
        cid = svc.create(idempotency_key="at05-ia-003", title="AT05 IA conflict")["id"]
        rt.process_turn(
            conversation_id=cid,
            turn_id="at05-ia-conflict",
            modality="text",
            input="original IA content",
            cognitive_fn=_mock_cognitive,
        )
        before = svc.get_messages(cid, max_messages=50)

        with pytest.raises(TurnConflictError):
            rt.process_turn(
                conversation_id=cid,
                turn_id="at05-ia-conflict",
                modality="text",
                input="mutated IA content",
                cognitive_fn=_mock_cognitive,
            )

        assert svc.get_messages(cid, max_messages=50) == before
    finally:
        repo.close()


def test_tc_at05_ia_004_real_metadata_variation_retry_cannot_create_history(tmp_path):
    """TC-AT05-IA-004: request/transport retry metadata is not authority."""
    repo, rt, svc = _stack(tmp_path)
    try:
        cid = svc.create(idempotency_key="at05-ia-004", title="AT05 IA metadata")["id"]

        first = rt.append_external_turns(
            cid,
            [_voice_turn(
                "at05-ia-metadata",
                "metadata-stable voice content",
                request_id="req-A",
                retry_count=0,
                transport_session_id="transport-A",
            )],
        )
        retry = rt.append_external_turns(
            cid,
            [_voice_turn(
                "at05-ia-metadata",
                "metadata-stable voice content",
                request_id="req-B",
                retry_count=5,
                transport_session_id="transport-B",
            )],
        )

        messages = _turn_messages(svc.get_messages(cid, max_messages=50), "at05-ia-metadata")
        assert first["appended_turn_ids"] == ["at05-ia-metadata"]
        assert retry["appended_turn_ids"] == []
        assert retry["skipped_turn_ids"] == ["at05-ia-metadata"]
        assert _roles(messages) == ["user", "assistant"]
    finally:
        repo.close()


def test_tc_at05_ia_005_real_partial_failure_retry_no_duplicate_or_phantom_completion(tmp_path):
    """TC-AT05-IA-005: failed assistant retry cannot forge completed history."""
    repo, rt, svc = _stack(tmp_path)
    try:
        cid = svc.create(idempotency_key="at05-ia-005", title="AT05 IA partial")["id"]

        failed = rt.process_turn(
            conversation_id=cid,
            turn_id="at05-ia-partial",
            modality="text",
            input="accepted user with failed assistant",
            cognitive_fn=_failing_cognitive,
        )
        retry = rt.process_turn(
            conversation_id=cid,
            turn_id="at05-ia-partial",
            modality="text",
            input="accepted user with failed assistant",
            cognitive_fn=_mock_cognitive,
        )

        all_messages = _turn_messages(svc.get_messages(cid, max_messages=50), "at05-ia-partial")
        completed_history = _turn_messages(rt.get_canonical_history(cid), "at05-ia-partial")
        assert failed.status == "failed"
        assert retry.user_message_id == failed.user_message_id
        assert retry.assistant_message_id == failed.assistant_message_id
        assert [(m["role"], m["status"], m["content"]) for m in all_messages] == [
            ("user", "completed", "accepted user with failed assistant"),
            ("assistant", "failed", ""),
        ]
        assert [(m["role"], m["status"], m["content"]) for m in completed_history] == [
            ("user", "completed", "accepted user with failed assistant"),
        ]
    finally:
        repo.close()
