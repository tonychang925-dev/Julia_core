"""AT-19 — Hard-delete guard (v1.0 plan definition, conversation level).

A conversation referenced by Diary / Memory / Continuity cannot be
hard-deleted without governed resolution.

- register_reference simulates governed references.
- delete_conversation returns False when referenced (guarded).
- force=True is the explicit governed override.
- Unreferenced conversations delete normally.
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


def _setup(rt):
    cid = rt.create_conversation().conversation_id
    rt.process_turn(
        conversation_id=cid, turn_id="t0", modality="text",
        input="hello", cognitive_fn=_mock_cognitive,
    )
    return cid


def test_at19_referenced_conversation_cannot_hard_delete(repo_path):
    rt = _runtime(repo_path)
    cid = _setup(rt)
    rt.register_reference(cid, "diary://entry/xxx")

    assert rt.delete_conversation(cid) is False  # guarded
    assert rt.get_conversation(cid) is not None  # canonical intact


def test_at19_multiple_references_all_guard(repo_path):
    rt = _runtime(repo_path)
    cid = _setup(rt)
    rt.register_reference(cid, "memory://experience/1")
    rt.register_reference(cid, "continuity://checkpoint/2")

    assert rt.delete_conversation(cid) is False
    assert rt.get_references(cid) == [
        "continuity://checkpoint/2", "memory://experience/1",
    ]


def test_at19_unreferenced_conversation_deletes(repo_path):
    rt = _runtime(repo_path)
    cid = _setup(rt)
    assert rt.delete_conversation(cid) is True
    assert rt.get_conversation(cid) is None


def test_at19_force_is_governed_override(repo_path):
    rt = _runtime(repo_path)
    cid = _setup(rt)
    rt.register_reference(cid, "diary://entry/xxx")
    # force = explicit governed resolution
    assert rt.delete_conversation(cid, force=True) is True
    assert rt.get_conversation(cid) is None
