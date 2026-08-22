"""Wave5 AT-07 Minimal Remediation — StorageV2 segment rotation.

These tests verify the minimal physical rotation fix for the P0 gap found in
AT-07 Audit. They are remediation evidence, not final R1/IA freeze evidence.
"""

from __future__ import annotations

import json

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.conversation_runtime import ConversationRuntime


def _segment_names(root, cid: str) -> list[str]:
    return sorted(p.name for p in (root / cid).glob("transcript-*.jsonl"))


def _segment_lines(root, cid: str, segment_name: str) -> list[str]:
    return (root / cid / segment_name).read_text().splitlines()


def test_at07_rem_rotation_creates_second_segment_at_message_boundary(tmp_path):
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=3)
    try:
        repo.create_with_id("at07_rem")
        for idx in range(5):
            repo.add_message("at07_rem", "user", f"msg_{idx:03d}", turn_id=f"turn_{idx:03d}")

        assert _segment_names(tmp_path, "at07_rem") == [
            "transcript-000001.jsonl",
            "transcript-000002.jsonl",
        ]
        assert len(_segment_lines(tmp_path, "at07_rem", "transcript-000001.jsonl")) == 3
        assert len(_segment_lines(tmp_path, "at07_rem", "transcript-000002.jsonl")) == 2
    finally:
        repo.close()


def test_at07_rem_canonical_order_preserved_across_segments(tmp_path):
    repo = StorageV2ConversationRepository(tmp_path, segment_max_messages=4)
    try:
        repo.create_with_id("at07_order")
        for idx in range(10):
            repo.add_message("at07_order", "user", f"ordered_{idx:03d}", turn_id=f"turn_{idx:03d}")

        msgs = repo.get_messages("at07_order")
        assert [m.content for m in msgs] == [f"ordered_{idx:03d}" for idx in range(10)]
        canonical = []
        for segment in _segment_names(tmp_path, "at07_order"):
            canonical.extend(json.loads(line) for line in _segment_lines(tmp_path, "at07_order", segment))
        assert [m["sequence"] for m in canonical] == list(range(1, 11))
    finally:
        repo.close()


def test_at07_rem_fresh_runtime_recovery_reads_all_segments(tmp_path):
    repo1 = StorageV2ConversationRepository(tmp_path, segment_max_messages=2)
    rt1 = ConversationRuntime(repository=repo1)
    cid = rt1.create_conversation(title="AT07 recovery").conversation_id
    for idx in range(5):
        rt1.accept_user_turn(
            conversation_id=cid,
            turn_id=f"turn_{idx:03d}",
            modality="text",
            content=f"recover_{idx:03d}",
        )
    repo1.close()

    repo2 = StorageV2ConversationRepository(tmp_path, segment_max_messages=2)
    rt2 = ConversationRuntime(repository=repo2)
    try:
        assert _segment_names(tmp_path, cid) == [
            "transcript-000001.jsonl",
            "transcript-000002.jsonl",
            "transcript-000003.jsonl",
        ]
        msgs = rt2.get_messages(cid)
        assert [m["content"] for m in msgs] == [f"recover_{idx:03d}" for idx in range(5)]
        assert {m["conversation_id"] for m in msgs} == {cid}
    finally:
        repo2.close()


def test_at07_rem_oversized_single_record_is_not_split(tmp_path):
    repo = StorageV2ConversationRepository(
        tmp_path,
        segment_max_messages=10,
        segment_max_bytes=64,
    )
    try:
        repo.create_with_id("at07_oversized")
        large_content = "X" * 512
        repo.add_message("at07_oversized", "user", large_content, turn_id="large")
        repo.add_message("at07_oversized", "user", "small-after", turn_id="small")

        segments = _segment_names(tmp_path, "at07_oversized")
        assert segments == ["transcript-000001.jsonl", "transcript-000002.jsonl"]
        first_lines = _segment_lines(tmp_path, "at07_oversized", "transcript-000001.jsonl")
        second_lines = _segment_lines(tmp_path, "at07_oversized", "transcript-000002.jsonl")
        assert len(first_lines) == 1
        assert len(second_lines) == 1
        assert json.loads(first_lines[0])["content"] == large_content
        assert json.loads(second_lines[0])["content"] == "small-after"
    finally:
        repo.close()
