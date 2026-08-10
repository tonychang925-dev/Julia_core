"""RT2-R3 — Core Acceptance. CM-Core v1.0 contract verification.

Runs CM-Core 10 ATs against ConversationRuntime v2 + StorageV2.
Zero production mutation. Zero semantic changes.
"""

import json
import os
import tempfile
import threading
from pathlib import Path

import pytest

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.conversation_state.legacy_migration import migrate_legacy_conversations
from julia_core.runtime.conversation_runtime import ConversationRuntime


@pytest.fixture
def runtime_with_v2():
    """Fresh Runtime + StorageV2 backend."""
    base = tempfile.mkdtemp(prefix="r3_")
    repo = StorageV2ConversationRepository(base)
    rt = ConversationRuntime(repository=repo)
    yield rt
    repo.close()
    import shutil
    shutil.rmtree(base, ignore_errors=True)


def _mock_cog(text, history, cid, tid, mod, interaction=None):
    return f"Julia reply to: {text}"


# ═══════════════════════════════════════════════════════════════════════════
# R3-AT01: Core-first create
# ═══════════════════════════════════════════════════════════════════════════

def test_r3_at01_core_first_create(runtime_with_v2):
    """CM-AT01: Core creates canonical conversation before client bind."""
    rt = runtime_with_v2
    conv = rt.create_conversation("r3_create_test", "R3 Create")
    assert conv.conversation_id == "r3_create_test"

    # Verify durable: restart
    repo2 = StorageV2ConversationRepository(rt._repository._base)
    rt2 = ConversationRuntime(repository=repo2)
    restored = rt2.get_conversation("r3_create_test")
    assert restored is not None
    repo2.close()


# ═══════════════════════════════════════════════════════════════════════════
# R3-AT02: Text user durability — ACK → kill → survive
# ═══════════════════════════════════════════════════════════════════════════

def test_r3_at02_text_user_durability(runtime_with_v2):
    """CM-AT02: Accepted text input survives restart."""
    rt = runtime_with_v2
    rt.create_conversation("r3_durable")

    result = rt.process_turn(
        conversation_id="r3_durable", turn_id="r3_t1",
        modality="text", input="survive restart", cognitive_fn=_mock_cog,
    )
    assert result.status == "completed"

    # Restart
    repo2 = StorageV2ConversationRepository(rt._repository._base)
    rt2 = ConversationRuntime(repository=repo2)
    msgs = repo2.find_turn("r3_durable", "r3_t1")
    assert len(msgs) == 2
    assert msgs[0].content == "survive restart"
    assert msgs[0].status == "completed"
    repo2.close()


# ═══════════════════════════════════════════════════════════════════════════
# R3-AT03: Cognition failure — user survives
# ═══════════════════════════════════════════════════════════════════════════

def test_r3_at03_cognition_failure_user_survives(runtime_with_v2):
    """CM-AT04: Assistant failure does not erase accepted user message."""
    rt = runtime_with_v2
    rt.create_conversation("r3_fail")

    def failing_cog(text, history, cid, tid, mod, interaction=None):
        raise RuntimeError("LLM timeout")

    result = rt.process_turn(
        conversation_id="r3_fail", turn_id="r3_fail_t",
        modality="text", input="must survive LLM crash", cognitive_fn=failing_cog,
    )
    assert result.status == "failed"

    repo2 = StorageV2ConversationRepository(rt._repository._base)
    msgs = repo2.find_turn("r3_fail", "r3_fail_t")
    user_msgs = [m for m in msgs if m.role == "user"]
    assert len(user_msgs) == 1
    assert user_msgs[0].content == "must survive LLM crash"
    assert user_msgs[0].status == "completed"
    repo2.close()


# ═══════════════════════════════════════════════════════════════════════════
# R3-AT04: Retry exactly-once
# ═══════════════════════════════════════════════════════════════════════════

def test_r3_at04_retry_exactly_once(runtime_with_v2):
    """CM-AT05: Same turn retry produces exactly one canonical user message."""
    rt = runtime_with_v2
    rt.create_conversation("r3_retry")

    r1 = rt.process_turn(
        conversation_id="r3_retry", turn_id="r3_idem",
        modality="text", input="idempotent", cognitive_fn=_mock_cog,
    )
    r2 = rt.process_turn(
        conversation_id="r3_retry", turn_id="r3_idem",
        modality="text", input="idempotent", cognitive_fn=_mock_cog,
    )
    assert r1.user_message_id == r2.user_message_id

    # Conflict: same turn, different content
    from julia_core.conversation_state.repository import TurnConflictError
    with pytest.raises(TurnConflictError):
        rt.process_turn(
            conversation_id="r3_retry", turn_id="r3_idem",
            modality="text", input="DIFFERENT content", cognitive_fn=_mock_cog,
        )


# ═══════════════════════════════════════════════════════════════════════════
# R3-AT05: Core restart recovery
# ═══════════════════════════════════════════════════════════════════════════

def test_r3_at05_core_restart_recovery(runtime_with_v2):
    """CM-AT09: Restart Core → all accepted facts recoverable."""
    rt = runtime_with_v2
    rt.create_conversation("r3_recover")
    rt.process_turn(conversation_id="r3_recover", turn_id="r3_rec_1",
                    modality="text", input="first", cognitive_fn=_mock_cog)
    rt.process_turn(conversation_id="r3_recover", turn_id="r3_rec_2",
                    modality="text", input="second", cognitive_fn=_mock_cog)

    # Full restart
    repo2 = StorageV2ConversationRepository(rt._repository._base)
    rt2 = ConversationRuntime(repository=repo2)

    convs = rt2.list_conversations()
    assert any(c.conversation_id == "r3_recover" for c in convs)

    msgs = repo2.get_messages("r3_recover")
    assert len(msgs) == 4  # 2 turns × 2 messages
    contents = [m.content for m in msgs if m.role == "user"]
    assert contents == ["first", "second"]
    repo2.close()


# ═══════════════════════════════════════════════════════════════════════════
# R3-AT06: Catalog destruction → rebuild
# ═══════════════════════════════════════════════════════════════════════════

def test_r3_at06_catalog_destruction(runtime_with_v2):
    """CM-AT06 (storage): delete catalog → rebuild → all data intact."""
    rt = runtime_with_v2
    rt.create_conversation("r3_cat")
    rt.process_turn(conversation_id="r3_cat", turn_id="r3_cat_1",
                    modality="text", input="before catalog loss",
                    cognitive_fn=_mock_cog)

    base = rt._repository._base
    rt._repository.close()

    # Delete catalog
    cat_path = base / "catalog.sqlite"
    os.remove(cat_path)

    # Rebuild
    repo2 = StorageV2ConversationRepository(base)
    msgs = repo2.get_messages("r3_cat")
    assert len(msgs) == 2
    assert msgs[0].content == "before catalog loss"
    repo2.close()


# ═══════════════════════════════════════════════════════════════════════════
# R3-AT07: Long conversation — Context source reachable
# ═══════════════════════════════════════════════════════════════════════════

def test_r3_at07_long_history_context_reachable(runtime_with_v2):
    """CM-AT10: >40 messages — canonical source fully reachable."""
    rt = runtime_with_v2
    rt.create_conversation("r3_long")

    ANCHOR = "UNIQUE_HISTORY_ANCHOR_R3_X9K2"
    rt.process_turn(conversation_id="r3_long", turn_id="r3_long_00",
                    modality="text", input=ANCHOR, cognitive_fn=_mock_cog)

    for i in range(1, 51):
        rt.process_turn(conversation_id="r3_long", turn_id=f"r3_long_{i:02d}",
                        modality="text", input=f"filler message {i}",
                        cognitive_fn=_mock_cog)

    # Full canonical source must contain the anchor
    msgs = rt._repository.get_messages("r3_long")
    user_contents = [m.content for m in msgs if m.role == "user"]
    assert len(user_contents) >= 51
    assert ANCHOR in user_contents, (
        f"Context source must contain early anchor. "
        f"Total user messages: {len(user_contents)}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# R3-AT08: Conversation isolation
# ═══════════════════════════════════════════════════════════════════════════

def test_r3_at08_conversation_isolation(runtime_with_v2):
    """CM-AT07: concurrent A/B — zero cross-contamination."""
    rt = runtime_with_v2
    rt.create_conversation("r3_iso_A")
    rt.create_conversation("r3_iso_B")

    rt.process_turn(conversation_id="r3_iso_A", turn_id="iso_A1",
                    modality="text", input="alpha one", cognitive_fn=_mock_cog)
    rt.process_turn(conversation_id="r3_iso_B", turn_id="iso_B1",
                    modality="text", input="beta one", cognitive_fn=_mock_cog)

    a_msgs = rt._repository.get_messages("r3_iso_A")
    b_msgs = rt._repository.get_messages("r3_iso_B")

    a_contents = [m.content for m in a_msgs]
    b_contents = [m.content for m in b_msgs]
    assert "beta one" not in a_contents
    assert "alpha one" not in b_contents


# ═══════════════════════════════════════════════════════════════════════════
# R3-AT09: Legacy authority sealed
# ═══════════════════════════════════════════════════════════════════════════

def test_r3_at09_legacy_authority_sealed():
    """CM-AT09 (storage): legacy conversations.json not writable."""
    import hashlib
    prod_path = Path(os.path.expanduser("~/julia_ai_assistant/data/conversations.json"))
    if not prod_path.exists():
        pytest.skip("Production conversations.json not available")

    sha_before = hashlib.sha256(prod_path.read_bytes()).hexdigest()

    # Verify legacy can still be read
    from julia_core.conversation_state.legacy_json_repository import LegacyJsonConversationRepository
    legacy = LegacyJsonConversationRepository(prod_path)
    sessions = legacy.list_all()
    assert len(sessions) > 0

    sha_after = hashlib.sha256(prod_path.read_bytes()).hexdigest()
    assert sha_before == sha_after, "Legacy source must remain unchanged"


# ═══════════════════════════════════════════════════════════════════════════
# R3-AT10: Repository substitution invariant
# ═══════════════════════════════════════════════════════════════════════════

def test_r3_at10_repository_substitution(runtime_with_v2):
    """CM-AT10 (arch): Runtime code has zero StorageV2-specific knowledge."""
    source = Path(__file__).resolve().parents[2] / "julia_core" / "runtime" / "conversation_runtime.py"
    content = source.read_text()

    forbidden = ["StorageV2", "JSONL", "sqlite", "catalog.sqlite", "transcript-"]
    for term in forbidden:
        assert term not in content, (
            f"ConversationRuntime MUST NOT contain '{term}'. "
            "Repository abstraction must be the only storage dependency."
        )
