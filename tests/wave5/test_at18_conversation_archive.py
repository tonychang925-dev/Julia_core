"""AT-18 — Archive (v1.0 plan definition, conversation level).

Archived conversation:
- disappears from default list
- remains canonical (transcript intact)
- remains retrievable
- state persists across restart
- restore returns it to the default list
"""

from __future__ import annotations

from pathlib import Path

import pytest

from julia_core.conversation_state.legacy_json_repository import LegacyJsonConversationRepository
from julia_core.runtime.conversation_runtime import ConversationRuntime


def _runtime(repo_path: Path) -> ConversationRuntime:
    return ConversationRuntime(repository=LegacyJsonConversationRepository(str(repo_path)))


def _mock_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    return f"ack:{modality}:{text}"


@pytest.fixture()
def repo_path(tmp_path):
    return tmp_path / "conversations.json"


def _setup(rt, n=2):
    cid = rt.create_conversation().conversation_id
    for i in range(n):
        rt.process_turn(
            conversation_id=cid, turn_id=f"t{i}", modality="text",
            input=f"msg-{i}", cognitive_fn=_mock_cognitive,
        )
    return cid


def test_at18_archive_hides_from_default_list(repo_path):
    rt = _runtime(repo_path)
    cid = _setup(rt)
    assert cid in [c.conversation_id for c in rt.list_conversations()]

    rt.archive_conversation(cid)
    assert cid not in [c.conversation_id for c in rt.list_conversations()]
    assert cid in [c.conversation_id for c in rt.get_archived_conversations()]


def test_at18_archive_keeps_canonical(repo_path):
    rt = _runtime(repo_path)
    cid = _setup(rt)
    rt.archive_conversation(cid)
    # Canonical transcript intact and retrievable.
    detail = rt.get_conversation(cid)
    assert detail is not None
    assert len(rt.get_canonical_history(cid)) == 4  # 2 turns × (user+assistant)


def test_at18_archive_persists_across_restart(repo_path):
    rt = _runtime(repo_path)
    cid = _setup(rt)
    rt.archive_conversation(cid)
    # Restart: new runtime over same file.
    rt2 = _runtime(repo_path)
    assert cid not in [c.conversation_id for c in rt2.list_conversations()]
    assert rt2.get_conversation(cid) is not None  # canonical remains
    assert cid in [c.conversation_id for c in rt2.get_archived_conversations()]


def test_at18_restore_returns_to_default_list(repo_path):
    rt = _runtime(repo_path)
    cid = _setup(rt)
    rt.archive_conversation(cid)
    assert rt.restore_archived(cid) is True
    assert cid in [c.conversation_id for c in rt.list_conversations()]
    assert cid not in [c.conversation_id for c in rt.get_archived_conversations()]


def test_at18_archive_not_deletion(repo_path):
    """archive != deletion: canonical data must survive."""
    rt = _runtime(repo_path)
    cid = _setup(rt)
    rt.archive_conversation(cid)
    rt2 = _runtime(repo_path)
    detail = rt2.get_conversation(cid)
    assert detail is not None
    users = [m["content"] for m in rt2.get_canonical_history(cid) if m["role"] == "user"]
    assert users == ["msg-0", "msg-1"]
