"""RT2-R2-C — Legacy Migration Tests.

READ-ONLY source. WRITE-ONLY staging target.
Production mutation: 0.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from julia_core.conversation_state.legacy_migration import (
    migrate_legacy_conversations,
    _normalize_legacy,
    _digest_normalized,
)
from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository


@pytest.fixture
def legacy_fixture():
    """Minimal legacy-format fixture for synthetic tests."""
    return [
        {
            "id": "legacy_conv_A",
            "title": "Conversation A",
            "created_at": "2026-08-01T00:00:00",
            "updated_at": "2026-08-10T00:00:00",
            "message_count": 4,
            "messages": [
                {"message_id": "msg_A_1", "conversation_id": "legacy_conv_A",
                 "turn_id": "turn_A_1", "role": "user", "modality": "text",
                 "content": "hello", "status": "completed",
                 "created_at": "2026-08-01T10:00:00"},
                {"message_id": "msg_A_2", "conversation_id": "legacy_conv_A",
                 "turn_id": "turn_A_1", "role": "assistant", "modality": "text",
                 "content": "hi there", "status": "completed",
                 "created_at": "2026-08-01T10:00:01"},
                {"message_id": "msg_A_3", "conversation_id": "legacy_conv_A",
                 "turn_id": "turn_A_2", "role": "user", "modality": "voice",
                 "content": "voice test", "status": "completed",
                 "created_at": "2026-08-02T10:00:00"},
                {"message_id": "msg_A_4", "conversation_id": "legacy_conv_A",
                 "turn_id": "turn_A_2", "role": "assistant", "modality": "voice",
                 "content": "voice reply", "status": "interrupted",
                 "created_at": "2026-08-02T10:00:01"},
            ],
        },
        {
            "id": "legacy_conv_B",
            "title": "Empty Conversation",
            "created_at": "2026-08-05T00:00:00",
            "updated_at": "2026-08-05T00:00:00",
            "message_count": 0,
            "messages": [],
        },
    ]


# ── C-AT01: Source read-only ───────────────────────────────────────────

def test_c_at01_source_unchanged(legacy_fixture):
    """C-AT01: legacy source checksum unchanged after migration."""
    source_dir = tempfile.mkdtemp(prefix="r2c_src_")
    source_path = Path(source_dir) / "conversations.json"
    source_path.write_text(json.dumps(legacy_fixture))

    import hashlib
    sha_before = hashlib.sha256(source_path.read_bytes()).hexdigest()

    target_dir = tempfile.mkdtemp(prefix="r2c_tgt_")
    result = migrate_legacy_conversations(source_path, target_dir)
    assert result["source_unchanged"] is True

    sha_after = hashlib.sha256(source_path.read_bytes()).hexdigest()
    assert sha_before == sha_after


# ── C-AT02/03: Count + ID preservation ──────────────────────────────────

def test_c_at02_03_count_and_id(legacy_fixture):
    """C-AT02/03: conversation count and IDs preserved."""
    source_dir = tempfile.mkdtemp(prefix="r2c_")
    source_path = Path(source_dir) / "conversations.json"
    source_path.write_text(json.dumps(legacy_fixture))
    target_dir = tempfile.mkdtemp(prefix="r2c_tgt_")

    result = migrate_legacy_conversations(source_path, target_dir)
    assert result["status"] == "CUTOVER_READY"
    assert result["source_count"] == 2
    assert result["target_count"] == 2

    legacy_ids = {c["id"] for c in legacy_fixture}
    v2_repo = StorageV2ConversationRepository(target_dir)
    v2_ids = {s.id for s in v2_repo.list_all()}
    assert legacy_ids == v2_ids
    v2_repo.close()


# ── C-AT04: Message counts ─────────────────────────────────────────────

def test_c_at04_message_counts(legacy_fixture):
    """C-AT04: per-conversation message counts exact."""
    source_dir = tempfile.mkdtemp(prefix="r2c_")
    source_path = Path(source_dir) / "conversations.json"
    source_path.write_text(json.dumps(legacy_fixture))
    target_dir = tempfile.mkdtemp(prefix="r2c_tgt_")

    result = migrate_legacy_conversations(source_path, target_dir)
    assert result["source_messages"] == 4
    assert result["target_messages"] == 4

    for c in result["per_conversation"]:
        assert c["verify"] == "MATCH", f"Conversation {c['conversation_id']} mismatch"


# ── C-AT05: Content preservation ───────────────────────────────────────

def test_c_at05_content_preserved(legacy_fixture):
    """C-AT05: message_id, turn_id, role, content exact."""
    source_dir = tempfile.mkdtemp(prefix="r2c_")
    source_path = Path(source_dir) / "conversations.json"
    source_path.write_text(json.dumps(legacy_fixture))
    target_dir = tempfile.mkdtemp(prefix="r2c_tgt_")

    migrate_legacy_conversations(source_path, target_dir)
    v2_repo = StorageV2ConversationRepository(target_dir)
    session = v2_repo.get("legacy_conv_A")
    assert session is not None
    msgs = session.messages
    assert msgs[0].message_id == "msg_A_1"
    assert msgs[0].turn_id == "turn_A_1"
    assert msgs[0].role == "user"
    assert msgs[0].content == "hello"
    assert msgs[3].message_id == "msg_A_4"
    assert msgs[3].status == "interrupted"
    v2_repo.close()


# ── C-AT06: Ordering preserved ─────────────────────────────────────────

def test_c_at06_ordering(legacy_fixture):
    """C-AT06: legacy canonical ordering preserved exactly."""
    source_dir = tempfile.mkdtemp(prefix="r2c_")
    source_path = Path(source_dir) / "conversations.json"
    source_path.write_text(json.dumps(legacy_fixture))
    target_dir = tempfile.mkdtemp(prefix="r2c_tgt_")

    migrate_legacy_conversations(source_path, target_dir)
    v2_repo = StorageV2ConversationRepository(target_dir)
    msgs = v2_repo.get("legacy_conv_A").messages
    contents = [m.content for m in msgs]
    assert contents == ["hello", "hi there", "voice test", "voice reply"]
    v2_repo.close()


# ── C-AT07: Historical statuses preserved ──────────────────────────────

def test_c_at07_statuses_preserved(legacy_fixture):
    """C-AT07: legacy statuses preserved, not normalized away."""
    source_dir = tempfile.mkdtemp(prefix="r2c_")
    source_path = Path(source_dir) / "conversations.json"
    source_path.write_text(json.dumps(legacy_fixture))
    target_dir = tempfile.mkdtemp(prefix="r2c_tgt_")

    migrate_legacy_conversations(source_path, target_dir)
    v2_repo = StorageV2ConversationRepository(target_dir)
    msgs = v2_repo.get("legacy_conv_A").messages
    statuses = [m.status for m in msgs]
    assert "interrupted" in statuses, "Legacy interrupted status must be preserved"
    v2_repo.close()


# ── C-AT08: Empty conversations preserved ──────────────────────────────

def test_c_at08_empty_conversation(legacy_fixture):
    """C-AT08: empty conversations preserved."""
    source_dir = tempfile.mkdtemp(prefix="r2c_")
    source_path = Path(source_dir) / "conversations.json"
    source_path.write_text(json.dumps(legacy_fixture))
    target_dir = tempfile.mkdtemp(prefix="r2c_tgt_")

    migrate_legacy_conversations(source_path, target_dir)
    v2_repo = StorageV2ConversationRepository(target_dir)
    session = v2_repo.get("legacy_conv_B")
    assert session is not None, "Empty conversation must be preserved"
    assert len(session.messages) == 0
    v2_repo.close()


# ── C-AT09: Digest match ───────────────────────────────────────────────

def test_c_at09_digest_match(legacy_fixture):
    """C-AT09: normalized canonical digest matches 100%."""
    source_dir = tempfile.mkdtemp(prefix="r2c_")
    source_path = Path(source_dir) / "conversations.json"
    source_path.write_text(json.dumps(legacy_fixture))
    target_dir = tempfile.mkdtemp(prefix="r2c_tgt_")

    result = migrate_legacy_conversations(source_path, target_dir)
    assert result["digest_match"] is True, "Normalized digest must match"
    assert result["rebuild_ok"] is True, "Rebuild digest must match"


# ── C-AT10: Rebuild after migration ────────────────────────────────────

def test_c_at10_rebuild_after_migration(legacy_fixture):
    """C-AT10: delete/rebuild catalog after migration remains exact."""
    source_dir = tempfile.mkdtemp(prefix="r2c_")
    source_path = Path(source_dir) / "conversations.json"
    source_path.write_text(json.dumps(legacy_fixture))
    target_dir = tempfile.mkdtemp(prefix="r2c_tgt_")

    migrate_legacy_conversations(source_path, target_dir)

    # Delete catalog and rebuild
    cat_path = Path(target_dir) / "catalog.sqlite"
    os.remove(cat_path)
    rebuilder = StorageV2ConversationRepository(target_dir)
    msgs = rebuilder.get_messages("legacy_conv_A")
    assert len(msgs) == 4
    rebuilder.close()


# ── C-AT12: Migration rejects on failure ────────────────────────────────

def test_c_at12_no_partial_success():
    """C-AT12: migration failure must not produce CUTOVER_READY."""
    source_dir = tempfile.mkdtemp(prefix="r2c_fail_")
    source_path = Path(source_dir) / "conversations.json"
    # Corrupt data
    source_path.write_text('{"not": "an array"}')
    target_dir = tempfile.mkdtemp(prefix="r2c_fail_tgt_")

    result = migrate_legacy_conversations(source_path, target_dir)
    assert result.get("status") != "CUTOVER_READY"


# ── PRODUCTION: 38-session migration ───────────────────────────────────

def test_production_38_session_migration():
    """C-AT-PROD: migrate actual 38 production sessions."""
    prod_path = Path(os.path.expanduser("~/julia_ai_assistant/data/conversations.json"))
    if not prod_path.exists():
        pytest.skip("Production conversations.json not available")

    import hashlib
    sha_before = hashlib.sha256(prod_path.read_bytes()).hexdigest()

    target_dir = tempfile.mkdtemp(prefix="r2c_prod_")
    result = migrate_legacy_conversations(prod_path, target_dir)

    sha_after = hashlib.sha256(prod_path.read_bytes()).hexdigest()

    assert result["status"] == "CUTOVER_READY", \
        f"Production migration failed: {result.get('errors', [])}"
    assert result["source_unchanged"] is True
    assert result["digest_match"] is True
    assert result["rebuild_ok"] is True
    assert sha_before == sha_after, "Production source must not be modified"

    print(f"\n  Production migration: {result['source_count']} conversations, "
          f"{result['source_messages']} messages → CUTOVER_READY")
    for c in result["per_conversation"]:
        print(f"    {c['conversation_id']}: {c['message_count']} msgs → {c['verify']}")
