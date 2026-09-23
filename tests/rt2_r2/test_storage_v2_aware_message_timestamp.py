from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from julia_core.conversation_state.storage_v2_repository import (
    StorageV2ConversationRepository,
)
from julia_core.runtime.conversation_runtime import ConversationRuntime


def _raw_messages(base: Path, conversation_id: str) -> list[dict]:
    return [
        json.loads(line)
        for path in sorted(base.glob(f"{conversation_id}/transcript-*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def test_new_storage_v2_canonical_message_timestamp_is_timezone_aware(tmp_path):
    repository = StorageV2ConversationRepository(tmp_path)
    repository.create_with_id("aware-new")
    repository.add_message(
        "aware-new",
        "user",
        "current turn",
        turn_id="turn-new",
        status="completed",
    )

    created_at = _raw_messages(tmp_path, "aware-new")[0]["created_at"]
    parsed = datetime.fromisoformat(created_at)
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() is not None
    repository.close()


def test_storage_v2_timestamp_round_trip_and_restart_are_exact(tmp_path):
    repository = StorageV2ConversationRepository(tmp_path)
    repository.create_with_id("aware-restart")
    repository.add_message(
        "aware-restart",
        "user",
        "persist exact event time",
        turn_id="turn-restart",
    )
    original = _raw_messages(tmp_path, "aware-restart")[0]["created_at"]
    assert repository.get_messages("aware-restart")[0].created_at == original
    repository.close()

    reopened = StorageV2ConversationRepository(tmp_path)
    assert reopened.get_messages("aware-restart")[0].created_at == original
    reopened.close()


def test_existing_naive_historical_timestamp_is_read_unchanged(tmp_path):
    conversation_dir = tmp_path / "historical"
    conversation_dir.mkdir()
    historical = {
        "schema_version": 2,
        "sequence": 1,
        "message_id": "msg_historical_000001",
        "conversation_id": "historical",
        "turn_id": "turn-historical",
        "role": "user",
        "modality": "text",
        "content": "historical event",
        "status": "completed",
        "created_at": "2026-09-23T11:41:45",
    }
    (conversation_dir / "transcript-000001.jsonl").write_text(
        json.dumps(historical, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    repository = StorageV2ConversationRepository(tmp_path)
    assert repository.get_messages("historical")[0].created_at == historical["created_at"]
    assert _raw_messages(tmp_path, "historical")[0]["created_at"] == historical["created_at"]
    repository.close()


def test_turn_replay_does_not_create_a_new_timestamp_or_message(tmp_path):
    repository = StorageV2ConversationRepository(tmp_path)
    runtime = ConversationRuntime(repository=repository)
    runtime.create_conversation("idempotent")

    def cognition(text, history, conversation_id, turn_id, modality, interaction):
        return "accepted"

    first = runtime.process_turn(
        conversation_id="idempotent",
        turn_id="turn-idempotent",
        modality="text",
        input="same question",
        cognitive_fn=cognition,
    )
    replay = runtime.process_turn(
        conversation_id="idempotent",
        turn_id="turn-idempotent",
        modality="text",
        input="same question",
        cognitive_fn=cognition,
    )
    messages = _raw_messages(tmp_path, "idempotent")
    users = [message for message in messages if message["role"] == "user"]

    assert first.user_message_id == replay.user_message_id
    assert len(users) == 1
    assert users[0]["created_at"] == repository.get_messages("idempotent")[0].created_at
    repository.close()
