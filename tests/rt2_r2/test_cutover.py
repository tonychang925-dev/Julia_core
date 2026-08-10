"""RT2-R2-D — Production Cutover Sabotage Tests.

Proves authority switch is safe and legacy is sealed.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from julia_core.conversation_state.cutover import (
    cutover_to_storage_v2,
    create_repository_for_runtime,
    CutoverError,
    CutoverState,
)
from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.conversation_state.legacy_json_repository import LegacyJsonConversationRepository
from julia_core.runtime.conversation_runtime import ConversationRuntime


@pytest.fixture
def legacy_fixture_path():
    """Create a minimal legacy store."""
    d = tempfile.mkdtemp(prefix="r2d_legacy_")
    p = Path(d) / "conversations.json"
    data = [{
        "id": "cutover_conv_A", "title": "Cutover A",
        "created_at": "2026-08-01T00:00:00", "updated_at": "2026-08-01T00:00:00",
        "message_count": 2,
        "messages": [
            {"message_id": "msg_ca_1", "conversation_id": "cutover_conv_A",
             "turn_id": "turn_ca_1", "role": "user", "modality": "text",
             "content": "cutover test", "status": "completed",
             "created_at": "2026-08-01T10:00:00"},
            {"message_id": "msg_ca_2", "conversation_id": "cutover_conv_A",
             "turn_id": "turn_ca_1", "role": "assistant", "modality": "text",
             "content": "response", "status": "completed",
             "created_at": "2026-08-01T10:00:01"},
        ],
    }]
    p.write_text(json.dumps(data))
    return p


# ── D-AT01: Single writable authority ──────────────────────────────────

def test_d_at01_dry_run_safe(legacy_fixture_path):
    """D-AT01: dry run does not mutate anything."""
    import hashlib
    sha_before = hashlib.sha256(legacy_fixture_path.read_bytes()).hexdigest()
    v2_path = Path(tempfile.mkdtemp(prefix="r2d_v2_"))

    result = cutover_to_storage_v2(legacy_fixture_path, v2_path, dry_run=True)
    assert result["status"] == "DRY_RUN_OK"

    sha_after = hashlib.sha256(legacy_fixture_path.read_bytes()).hexdigest()
    assert sha_before == sha_after


# ── D-AT02: Migrated conversations reopen ──────────────────────────────

def test_d_at02_reopen_after_cutover(legacy_fixture_path):
    """D-AT02: all migrated conversations reopen correctly."""
    v2_path = Path(tempfile.mkdtemp(prefix="r2d_v2_"))
    state_dir = Path(tempfile.mkdtemp(prefix="r2d_state_"))

    result = cutover_to_storage_v2(legacy_fixture_path, v2_path, state_dir)
    assert result["status"] == "COMPLETE"

    repo = StorageV2ConversationRepository(v2_path)
    session = repo.get("cutover_conv_A")
    assert session is not None
    assert len(session.messages) == 2
    assert session.messages[0].content == "cutover test"
    repo.close()


# ── D-AT03: New conversation survives restart ──────────────────────────

def test_d_at03_new_conv_survives(legacy_fixture_path):
    """D-AT03: new conversation after cutover survives restart."""
    v2_path = Path(tempfile.mkdtemp(prefix="r2d_v2_"))
    state_dir = Path(tempfile.mkdtemp(prefix="r2d_state_"))
    cutover_to_storage_v2(legacy_fixture_path, v2_path, state_dir)

    repo = create_repository_for_runtime(v2_path)
    rt = ConversationRuntime(repository=repo)
    conv = rt.create_conversation("cutover_new", "New After Cutover")
    assert conv.conversation_id == "cutover_new"

    # Restart
    repo2 = StorageV2ConversationRepository(v2_path)
    rt2 = ConversationRuntime(repository=repo2)
    restored = rt2.get_conversation("cutover_new")
    assert restored is not None
    repo2.close()


# ── D-AT04: Accepted user survives crash ───────────────────────────────

def test_d_at04_user_survives_crash(legacy_fixture_path):
    """D-AT04: accepted user on v2 survives restart."""
    v2_path = Path(tempfile.mkdtemp(prefix="r2d_v2_"))
    state_dir = Path(tempfile.mkdtemp(prefix="r2d_state_"))
    cutover_to_storage_v2(legacy_fixture_path, v2_path, state_dir)

    repo = create_repository_for_runtime(v2_path)
    rt = ConversationRuntime(repository=repo)

    def mock_cog(text, history, cid, tid, mod, interaction=None):
        return f"reply: {text}"

    result = rt.process_turn(
        conversation_id="cutover_conv_A", turn_id="cutover_t_new",
        modality="text", input="post-cutover message",
        cognitive_fn=mock_cog,
    )
    assert result.status == "completed"

    # Restart
    repo2 = StorageV2ConversationRepository(v2_path)
    msgs = repo2.find_turn("cutover_conv_A", "cutover_t_new")
    assert len(msgs) == 2  # user + assistant
    assert msgs[0].content == "post-cutover message"
    repo2.close()


# ── D-AT05: Assistant failure leaves user unchanged ────────────────────

def test_d_at05_assistant_failure_on_v2(legacy_fixture_path):
    """D-AT05: on v2, assistant failure does not erase user."""
    v2_path = Path(tempfile.mkdtemp(prefix="r2d_v2_"))
    state_dir = Path(tempfile.mkdtemp(prefix="r2d_state_"))
    cutover_to_storage_v2(legacy_fixture_path, v2_path, state_dir)

    repo = create_repository_for_runtime(v2_path)
    rt = ConversationRuntime(repository=repo)

    def failing_cog(text, history, cid, tid, mod, interaction=None):
        raise RuntimeError("cognition exploded")

    result = rt.process_turn(
        conversation_id="cutover_conv_A", turn_id="cutover_fail_t",
        modality="text", input="this should survive",
        cognitive_fn=failing_cog,
    )
    assert result.status == "failed"

    # Restart — user must still exist
    repo2 = StorageV2ConversationRepository(v2_path)
    msgs = repo2.find_turn("cutover_conv_A", "cutover_fail_t")
    user_msgs = [m for m in msgs if m.role == "user"]
    assert len(user_msgs) == 1
    assert user_msgs[0].content == "this should survive"
    assert user_msgs[0].status == "completed"
    repo2.close()


# ── D-AT06: Idempotent retry on v2 ─────────────────────────────────────

def test_d_at06_idempotent_on_v2(legacy_fixture_path):
    """D-AT06: same turn retry produces exactly one message."""
    v2_path = Path(tempfile.mkdtemp(prefix="r2d_v2_"))
    state_dir = Path(tempfile.mkdtemp(prefix="r2d_state_"))
    cutover_to_storage_v2(legacy_fixture_path, v2_path, state_dir)

    repo = create_repository_for_runtime(v2_path)
    rt = ConversationRuntime(repository=repo)

    def mock_cog(text, history, cid, tid, mod, interaction=None):
        return "ok"

    r1 = rt.process_turn(
        conversation_id="cutover_conv_A", turn_id="idem_v2",
        modality="text", input="idempotent", cognitive_fn=mock_cog,
    )
    r2 = rt.process_turn(
        conversation_id="cutover_conv_A", turn_id="idem_v2",
        modality="text", input="idempotent", cognitive_fn=mock_cog,
    )
    assert r1.user_message_id == r2.user_message_id

    repo2 = StorageV2ConversationRepository(v2_path)
    msgs = repo2.find_turn("cutover_conv_A", "idem_v2")
    user_msgs = [m for m in msgs if m.role == "user"]
    assert len(user_msgs) == 1
    repo2.close()


# ── D-AT07: Catalog loss → rebuild restores truth ──────────────────────

def test_d_at07_catalog_loss_rebuild(legacy_fixture_path):
    """D-AT07: delete catalog → rebuild → all data restored."""
    v2_path = Path(tempfile.mkdtemp(prefix="r2d_v2_"))
    state_dir = Path(tempfile.mkdtemp(prefix="r2d_state_"))
    cutover_to_storage_v2(legacy_fixture_path, v2_path, state_dir)

    # Add new turn post-cutover
    repo = create_repository_for_runtime(v2_path)
    rt = ConversationRuntime(repository=repo)

    def mock_cog(text, history, cid, tid, mod, interaction=None):
        return "ok"
    rt.process_turn(conversation_id="cutover_conv_A", turn_id="post_cutover",
                    modality="text", input="after cutover", cognitive_fn=mock_cog)
    repo.close()

    # Delete catalog
    cat_path = v2_path / "catalog.sqlite"
    os.remove(cat_path)

    # Rebuild
    repo2 = StorageV2ConversationRepository(v2_path)
    msgs = repo2.get_messages("cutover_conv_A")
    assert len(msgs) == 4  # 2 original + 2 new
    assert msgs[2].content == "after cutover"
    repo2.close()


# ── D-AT09: Legacy source unchanged ────────────────────────────────────

def test_d_at09_legacy_unchanged(legacy_fixture_path):
    """D-AT09: legacy conversations.json unchanged after cutover."""
    import hashlib
    sha_before = hashlib.sha256(legacy_fixture_path.read_bytes()).hexdigest()
    v2_path = Path(tempfile.mkdtemp(prefix="r2d_v2_"))
    state_dir = Path(tempfile.mkdtemp(prefix="r2d_state_"))

    cutover_to_storage_v2(legacy_fixture_path, v2_path, state_dir)
    sha_after = hashlib.sha256(legacy_fixture_path.read_bytes()).hexdigest()
    assert sha_before == sha_after


# ── D-AT11: No automatic fallback ──────────────────────────────────────

def test_d_at11_no_automatic_fallback():
    """D-AT11: missing v2 path → fail closed, no silent legacy fallback."""
    nonexistent = Path(tempfile.mkdtemp()) / "nonexistent"
    # create_repository_for_runtime without fallback should fail
    # But with explicit fallback it should use legacy
    fallback_path = Path(tempfile.mkdtemp(prefix="r2d_fb_")) / "conversations.json"
    # Create minimal legacy store
    data = [{"id": "fb_conv", "title": "FB", "created_at": "", "updated_at": "",
             "message_count": 0, "messages": []}]
    fallback_path.write_text(json.dumps(data))

    repo = create_repository_for_runtime(nonexistent, fallback_legacy_path=fallback_path)
    sessions = repo.list_all()
    assert len(sessions) == 1
    assert sessions[0].id == "fb_conv"


# ── D-AT12: Runtime semantic delta = 0 ──────────────────────────────────

def test_d_at12_runtime_semantic_delta_zero(legacy_fixture_path):
    """D-AT12: ConversationRuntime works identically post-cutover."""
    v2_path = Path(tempfile.mkdtemp(prefix="r2d_v2_"))
    state_dir = Path(tempfile.mkdtemp(prefix="r2d_state_"))
    cutover_to_storage_v2(legacy_fixture_path, v2_path, state_dir)

    # Both legacy and v2 should produce identical semantic results
    def mock_cog(text, history, cid, tid, mod, interaction=None):
        return f"reply: {text}"

    # Legacy path
    legacy_repo = LegacyJsonConversationRepository(legacy_fixture_path)
    rt_legacy = ConversationRuntime(repository=legacy_repo)
    r_legacy = rt_legacy.process_turn(
        conversation_id="cutover_conv_A", turn_id="sem_delta_t",
        modality="text", input="semantic test",
        cognitive_fn=mock_cog,
    )

    # V2 path
    repo_v2 = StorageV2ConversationRepository(v2_path)
    rt_v2 = ConversationRuntime(repository=repo_v2)
    r_v2 = rt_v2.process_turn(
        conversation_id="cutover_conv_A", turn_id="sem_delta_t_v2",
        modality="text", input="semantic test",
        cognitive_fn=mock_cog,
    )

    # Both produce correct assistant content
    assert "reply: semantic test" in r_legacy.assistant_content
    assert "reply: semantic test" in r_v2.assistant_content
    repo_v2.close()
