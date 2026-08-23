"""Wave5 AT-07 Integration Acceptance — segment boundary.

IA verifies the integrated management/runtime/StorageV2 rotation/recovery/
Context OS path. It does not test AT-08 pagination, compaction, search
optimization, or transcript redesign.

TC mapping:
- TC-AT07-IA-001 real management/runtime path creates multiple segments without changing conversation
- TC-AT07-IA-002 real read path across segments has zero missing/duplicate and canonical order
- TC-AT07-IA-003 real fresh runtime recovery restores same conversation across segments
- TC-AT07-IA-004 real Context OS path is unchanged by segment layout
- TC-AT07-IA-005 real mixed text/voice path across segment boundary remains one conversation
"""

from __future__ import annotations

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime
from conversation_management import ConversationManagementService
from julia_core.runtime.conversation_runtime import ConversationRuntime


class _FakeIdempotencyPort:
    def __init__(self):
        self._reserved: dict[str, str] = {}

    def get_or_reserve(self, key: str, candidate: str) -> str:
        return self._reserved.setdefault(key, candidate)


def _stack(root, *, port=None, segment_max_messages=4):
    repo = StorageV2ConversationRepository(
        str(root),
        segment_max_messages=segment_max_messages,
    )
    rt = ConversationRuntime(repository=repo)
    svc = ConversationManagementService(rt, port or _FakeIdempotencyPort())
    return repo, rt, svc


def _mock_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    return f"ia-ack:{modality}:{text}"


def _voice_turn(turn_id: str, user: str) -> dict:
    return {
        "turn_id": turn_id,
        "modality": "voice",
        "user_content": user,
        "assistant_content": f"ia-voice-ack:{user}",
        "assistant_status": "completed",
    }


def _segments(root, cid: str) -> list[str]:
    return sorted(p.name for p in (root / cid).glob("transcript-*.jsonl"))


def _turns(messages: list[dict]) -> list[tuple[str, str, str, str]]:
    return [(m["role"], m["turn_id"], m["modality"], m["content"]) for m in messages]


def test_tc_at07_ia_001_real_management_runtime_path_rotates_without_changing_conversation(tmp_path):
    """TC-AT07-IA-001: create via management, append via runtime, rotate."""
    repo, rt, svc = _stack(tmp_path, segment_max_messages=3)
    try:
        cid = svc.create(idempotency_key="at07-ia-001", title="AT07 IA rotation")["id"]
        for idx in range(7):
            rt.accept_user_turn(
                conversation_id=cid,
                turn_id=f"ia-001-{idx:03d}",
                modality="text",
                content=f"ia_rotation_{idx:03d}",
            )

        detail = svc.get(cid)
        messages = svc.get_messages(cid, max_messages=20)
        assert detail["id"] == cid
        assert _segments(tmp_path, cid) == [
            "transcript-000001.jsonl",
            "transcript-000002.jsonl",
            "transcript-000003.jsonl",
        ]
        assert {m["conversation_id"] for m in messages} == {cid}
        assert [m["content"] for m in messages] == [f"ia_rotation_{idx:03d}" for idx in range(7)]
    finally:
        repo.close()


def test_tc_at07_ia_002_real_read_path_across_segments_zero_missing_duplicate_ordered(tmp_path):
    """TC-AT07-IA-002: management read over rotated storage is one transcript."""
    repo, rt, svc = _stack(tmp_path, segment_max_messages=5)
    try:
        cid = svc.create(idempotency_key="at07-ia-002", title="AT07 IA read")["id"]
        expected = []
        for idx in range(13):
            content = f"ia_read_{idx:03d}"
            expected.append(content)
            rt.accept_user_turn(
                conversation_id=cid,
                turn_id=f"ia-002-{idx:03d}",
                modality="text",
                content=content,
            )

        messages = svc.get_messages(cid, max_messages=100)
        contents = [m["content"] for m in messages]
        assert _segments(tmp_path, cid) == [
            "transcript-000001.jsonl",
            "transcript-000002.jsonl",
            "transcript-000003.jsonl",
        ]
        assert contents == expected
        assert len(contents) == len(set(contents)) == 13
        assert [m["turn_id"] for m in messages] == [f"ia-002-{idx:03d}" for idx in range(13)]
    finally:
        repo.close()


def test_tc_at07_ia_003_real_fresh_runtime_recovery_same_conversation_across_segments(tmp_path):
    """TC-AT07-IA-003: fresh service/runtime over same repo recovers all segments."""
    port = _FakeIdempotencyPort()
    repo1, rt1, svc1 = _stack(tmp_path, port=port, segment_max_messages=2)
    cid = svc1.create(idempotency_key="at07-ia-003", title="AT07 IA recovery")["id"]
    for idx in range(6):
        rt1.accept_user_turn(
            conversation_id=cid,
            turn_id=f"ia-003-{idx:03d}",
            modality="text",
            content=f"ia_recover_{idx:03d}",
        )
    repo1.close()

    repo2, _rt2, svc2 = _stack(tmp_path, port=port, segment_max_messages=2)
    try:
        assert svc2.open(cid)["id"] == cid
        messages = svc2.get_messages(cid, max_messages=100)
        assert [m["content"] for m in messages] == [f"ia_recover_{idx:03d}" for idx in range(6)]
        assert {m["conversation_id"] for m in messages} == {cid}
        assert _segments(tmp_path, cid) == [
            "transcript-000001.jsonl",
            "transcript-000002.jsonl",
            "transcript-000003.jsonl",
        ]
    finally:
        repo2.close()


def test_tc_at07_ia_004_real_context_os_path_unchanged_by_segment_layout(tmp_path):
    """TC-AT07-IA-004: Context OS sees canonical history, not segment layout."""
    repo, rt, svc = _stack(tmp_path, segment_max_messages=3)
    try:
        cid = svc.create(idempotency_key="at07-ia-004", title="AT07 IA context")["id"]
        for idx in range(8):
            rt.accept_user_turn(
                conversation_id=cid,
                turn_id=f"ia-004-{idx:03d}",
                modality="text",
                content=f"ia_context_{idx:03d}",
            )

        history = rt.get_canonical_history(cid)
        pkg = ContextExecutionRuntime(None).prepare(
            conversation_id=cid,
            turn_id="ia-004-next",
            user_text="continue context",
            history=history,
            modality="text",
        )
        provider_messages = pkg.to_messages(history, "continue context")
        provider_text = "\n".join(m["content"] for m in provider_messages)

        assert len(_segments(tmp_path, cid)) == 3
        assert pkg.active_tail_turn_ids == [f"ia-004-{idx:03d}" for idx in range(8)]
        assert "transcript-" not in provider_text
        for idx in range(8):
            assert f"ia_context_{idx:03d}" in provider_text
    finally:
        repo.close()


def test_tc_at07_ia_005_real_mixed_text_voice_across_boundary_one_conversation(tmp_path):
    """TC-AT07-IA-005: text/voice/text around rotation stays one sequence."""
    repo, rt, svc = _stack(tmp_path, segment_max_messages=3)
    try:
        cid = svc.create(idempotency_key="at07-ia-005", title="AT07 IA mixed")["id"]
        rt.process_turn(
            conversation_id=cid,
            turn_id="ia-text-t1",
            modality="text",
            input="IA text before rotation",
            cognitive_fn=_mock_cognitive,
        )
        rt.append_external_turns(cid, [_voice_turn("ia-voice-t2", "IA voice at rotation")])
        rt.process_turn(
            conversation_id=cid,
            turn_id="ia-text-t3",
            modality="text",
            input="IA text after rotation",
            cognitive_fn=_mock_cognitive,
        )

        messages = svc.get_messages(cid, max_messages=20)
        assert _segments(tmp_path, cid) == ["transcript-000001.jsonl", "transcript-000002.jsonl"]
        assert _turns(messages) == [
            ("user", "ia-text-t1", "text", "IA text before rotation"),
            ("assistant", "ia-text-t1", "text", "ia-ack:text:IA text before rotation"),
            ("user", "ia-voice-t2", "voice", "IA voice at rotation"),
            ("assistant", "ia-voice-t2", "voice", "ia-voice-ack:IA voice at rotation"),
            ("user", "ia-text-t3", "text", "IA text after rotation"),
            ("assistant", "ia-text-t3", "text", "ia-ack:text:IA text after rotation"),
        ]
        assert {m["conversation_id"] for m in messages} == {cid}
    finally:
        repo.close()
