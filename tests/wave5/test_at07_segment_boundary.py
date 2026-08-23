"""Wave5 AT-07-R1 — Segment boundary permanent evidence.

R1 proves physical segment rotation does not change canonical conversation
semantics. It does not test AT-08 pagination, compaction, search optimization,
or transcript redesign.

TC mapping:
- TC-AT07-R1-001 rotation creates multiple transcript segment files
- TC-AT07-R1-002 canonical order preserved across segment boundary
- TC-AT07-R1-003 fresh runtime recovery reads all segments unchanged
- TC-AT07-R1-004 Context OS active tail unchanged by segment boundary
- TC-AT07-R1-005 segment filenames/details are not exposed in runtime/management DTOs
- TC-AT07-R1-006 text/voice turns across segment boundary remain one conversation
- TC-AT07-R1-007 message record is never split across segments
- TC-AT07-R1-008 derived metadata sabotage cannot hide durable segment files
"""

from __future__ import annotations

import json

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime
from conversation_management import ConversationManagementService
from julia_core.runtime.conversation_runtime import ConversationRuntime


class _FakeIdempotencyPort:
    def __init__(self):
        self._reserved: dict[str, str] = {}

    def get_or_reserve(self, key: str, candidate: str) -> str:
        return self._reserved.setdefault(key, candidate)


def _stack(root, *, segment_max_messages=4, segment_max_bytes=33_554_432):
    repo = StorageV2ConversationRepository(
        str(root),
        segment_max_messages=segment_max_messages,
        segment_max_bytes=segment_max_bytes,
    )
    rt = ConversationRuntime(repository=repo)
    svc = ConversationManagementService(rt, _FakeIdempotencyPort())
    return repo, rt, svc


def _mock_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    return f"ack:{modality}:{text}"


def _voice_turn(turn_id: str, user: str, assistant: str | None = None) -> dict:
    return {
        "turn_id": turn_id,
        "modality": "voice",
        "user_content": user,
        "assistant_content": assistant if assistant is not None else f"voice-ack:{user}",
        "assistant_status": "completed",
    }


def _segment_paths(root, cid: str):
    return sorted((root / cid).glob("transcript-*.jsonl"))


def _segment_names(root, cid: str) -> list[str]:
    return [p.name for p in _segment_paths(root, cid)]


def _canonical_records(root, cid: str) -> list[dict]:
    records: list[dict] = []
    for path in _segment_paths(root, cid):
        for line in path.read_text().splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


def _texts(messages: list[dict]) -> str:
    return "\n".join(str(m.get("content", "")) for m in messages)


def test_tc_at07_r1_001_rotation_creates_multiple_transcript_segments(tmp_path):
    repo, rt, svc = _stack(tmp_path, segment_max_messages=3)
    try:
        cid = svc.create(idempotency_key="at07-r1-001", title="AT07 rotation")["id"]
        for idx in range(7):
            rt.accept_user_turn(
                conversation_id=cid,
                turn_id=f"r1-001-{idx:03d}",
                modality="text",
                content=f"rotation_{idx:03d}",
            )

        assert _segment_names(tmp_path, cid) == [
            "transcript-000001.jsonl",
            "transcript-000002.jsonl",
            "transcript-000003.jsonl",
        ]
        assert len(_canonical_records(tmp_path, cid)) == 7
    finally:
        repo.close()


def test_tc_at07_r1_002_canonical_order_preserved_across_segment_boundary(tmp_path):
    repo, rt, svc = _stack(tmp_path, segment_max_messages=4)
    try:
        cid = svc.create(idempotency_key="at07-r1-002", title="AT07 order")["id"]
        for idx in range(10):
            rt.accept_user_turn(
                conversation_id=cid,
                turn_id=f"r1-002-{idx:03d}",
                modality="text",
                content=f"ordered_{idx:03d}",
            )

        messages = svc.get_messages(cid, max_messages=50)
        assert [m["content"] for m in messages] == [f"ordered_{idx:03d}" for idx in range(10)]
        assert [r["sequence"] for r in _canonical_records(tmp_path, cid)] == list(range(1, 11))
        assert len({m["message_id"] for m in messages}) == 10
    finally:
        repo.close()


def test_tc_at07_r1_003_fresh_runtime_recovery_reads_all_segments_unchanged(tmp_path):
    repo1, rt1, svc1 = _stack(tmp_path, segment_max_messages=2)
    cid = svc1.create(idempotency_key="at07-r1-003", title="AT07 recovery")["id"]
    for idx in range(6):
        rt1.accept_user_turn(
            conversation_id=cid,
            turn_id=f"r1-003-{idx:03d}",
            modality="text",
            content=f"recover_{idx:03d}",
        )
    before_segments = _segment_names(tmp_path, cid)
    repo1.close()

    repo2, _rt2, svc2 = _stack(tmp_path, segment_max_messages=2)
    try:
        messages = svc2.get_messages(cid, max_messages=100)
        assert before_segments == [
            "transcript-000001.jsonl",
            "transcript-000002.jsonl",
            "transcript-000003.jsonl",
        ]
        assert [m["content"] for m in messages] == [f"recover_{idx:03d}" for idx in range(6)]
        assert {m["conversation_id"] for m in messages} == {cid}
    finally:
        repo2.close()


def test_tc_at07_r1_004_context_os_active_tail_unchanged_by_segment_boundary(tmp_path):
    repo, rt, svc = _stack(tmp_path, segment_max_messages=3)
    try:
        cid = svc.create(idempotency_key="at07-r1-004", title="AT07 context")["id"]
        for idx in range(8):
            rt.accept_user_turn(
                conversation_id=cid,
                turn_id=f"r1-004-{idx:03d}",
                modality="text",
                content=f"context_{idx:03d}",
            )

        history = rt.get_canonical_history(cid)
        pkg = ContextExecutionRuntime(None).prepare(
            conversation_id=cid,
            turn_id="r1-004-next",
            user_text="continue",
            history=history,
            modality="text",
        )
        messages = pkg.to_messages(history, "continue")
        visible = _texts(messages)

        assert len(_segment_names(tmp_path, cid)) == 3
        for idx in range(8):
            assert f"context_{idx:03d}" in visible
        assert pkg.active_tail_turn_ids == [f"r1-004-{idx:03d}" for idx in range(8)]
    finally:
        repo.close()


def test_tc_at07_r1_005_segment_details_not_exposed_in_runtime_management_dtos(tmp_path):
    repo, rt, svc = _stack(tmp_path, segment_max_messages=2)
    try:
        cid = svc.create(idempotency_key="at07-r1-005", title="AT07 DTO")["id"]
        for idx in range(5):
            rt.accept_user_turn(
                conversation_id=cid,
                turn_id=f"r1-005-{idx:03d}",
                modality="text",
                content=f"dto_{idx:03d}",
            )

        detail = svc.get(cid)
        messages = svc.get_messages(cid, max_messages=20)
        payload_text = json.dumps({"detail": detail, "messages": messages}, ensure_ascii=False)

        assert len(_segment_names(tmp_path, cid)) == 3
        assert "transcript-" not in payload_text
        assert ".jsonl" not in payload_text
        assert "segment" not in payload_text.lower()
    finally:
        repo.close()


def test_tc_at07_r1_006_text_voice_across_boundary_one_canonical_sequence(tmp_path):
    repo, rt, svc = _stack(tmp_path, segment_max_messages=3)
    try:
        cid = svc.create(idempotency_key="at07-r1-006", title="AT07 modality")["id"]
        rt.process_turn(
            conversation_id=cid,
            turn_id="text-before-boundary",
            modality="text",
            input="text before boundary",
            cognitive_fn=_mock_cognitive,
        )
        rt.append_external_turns(cid, [_voice_turn("voice-at-boundary", "voice at boundary")])
        rt.process_turn(
            conversation_id=cid,
            turn_id="text-after-boundary",
            modality="text",
            input="text after boundary",
            cognitive_fn=_mock_cognitive,
        )

        messages = svc.get_messages(cid, max_messages=20)
        assert _segment_names(tmp_path, cid) == ["transcript-000001.jsonl", "transcript-000002.jsonl"]
        assert [(m["role"], m["turn_id"], m["modality"], m["content"]) for m in messages] == [
            ("user", "text-before-boundary", "text", "text before boundary"),
            ("assistant", "text-before-boundary", "text", "ack:text:text before boundary"),
            ("user", "voice-at-boundary", "voice", "voice at boundary"),
            ("assistant", "voice-at-boundary", "voice", "voice-ack:voice at boundary"),
            ("user", "text-after-boundary", "text", "text after boundary"),
            ("assistant", "text-after-boundary", "text", "ack:text:text after boundary"),
        ]
        assert {m["conversation_id"] for m in messages} == {cid}
    finally:
        repo.close()


def test_tc_at07_r1_007_message_record_never_split_across_segments(tmp_path):
    repo, rt, svc = _stack(tmp_path, segment_max_messages=10, segment_max_bytes=96)
    try:
        cid = svc.create(idempotency_key="at07-r1-007", title="AT07 atom")["id"]
        large = "L" * 512
        rt.accept_user_turn(
            conversation_id=cid,
            turn_id="large-record",
            modality="text",
            content=large,
        )
        rt.accept_user_turn(
            conversation_id=cid,
            turn_id="after-large-record",
            modality="text",
            content="after large",
        )

        segments = _segment_names(tmp_path, cid)
        assert segments == ["transcript-000001.jsonl", "transcript-000002.jsonl"]
        first_records = [json.loads(line) for line in (tmp_path / cid / segments[0]).read_text().splitlines()]
        second_records = [json.loads(line) for line in (tmp_path / cid / segments[1]).read_text().splitlines()]
        assert len(first_records) == 1
        assert len(second_records) == 1
        assert first_records[0]["content"] == large
        assert second_records[0]["content"] == "after large"
    finally:
        repo.close()


def test_tc_at07_r1_008_derived_metadata_sabotage_cannot_hide_later_segment(tmp_path):
    repo1, rt1, svc1 = _stack(tmp_path, segment_max_messages=2)
    cid = svc1.create(idempotency_key="at07-r1-008", title="AT07 metadata")["id"]
    for idx in range(5):
        rt1.accept_user_turn(
            conversation_id=cid,
            turn_id=f"r1-008-{idx:03d}",
            modality="text",
            content=f"metadata_{idx:03d}",
        )
    assert _segment_names(tmp_path, cid) == [
        "transcript-000001.jsonl",
        "transcript-000002.jsonl",
        "transcript-000003.jsonl",
    ]
    repo1._cat.execute(
        "UPDATE conversations SET message_count = ?, last_sequence = ? WHERE id = ?",
        (2, 2, cid),
    )
    repo1._cat.commit()
    repo1.close()

    repo2, _rt2, svc2 = _stack(tmp_path, segment_max_messages=2)
    try:
        messages = svc2.get_messages(cid, max_messages=100)
        assert [m["content"] for m in messages] == [f"metadata_{idx:03d}" for idx in range(5)]
        assert _segment_names(tmp_path, cid)[-1] == "transcript-000003.jsonl"
    finally:
        repo2.close()
