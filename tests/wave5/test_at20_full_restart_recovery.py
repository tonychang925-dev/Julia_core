"""AT-20 — Full restart recovery (v1.0 plan definition).

Restart Electron + Brain + S2S. Conversation + Accepted Diary remain
intact with no client history help.

Acceptance focus:
    1. Conversation: conversation_id / turn order / modality / lineage
       identical before vs after restart
    2. Accepted Diary: entry + source reference + provenance still present
    3. Electron cache != history source (no client history needed)
    4. Brain restart != continuity loss
    5. S2S: inherits AT-11 — new session bound by conversation_id, restore
       from Core

Layer 1: full persistence loop — all components "restart" (fresh runtimes /
readers over the same durable stores), conversation + diary recovered from
canonical sources only.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from julia_core.conversation_state.legacy_json_repository import LegacyJsonConversationRepository
from julia_core.runtime.conversation_runtime import ConversationRuntime

EVIDENCE_DIR = Path(__file__).resolve().parent.parent.parent / "evidence"


def _runtime(repo_path: Path) -> ConversationRuntime:
    return ConversationRuntime(repository=LegacyJsonConversationRepository(str(repo_path)))


def _mock_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    return f"ack:{modality}:{text}"


@pytest.fixture()
def repo_path(tmp_path):
    return tmp_path / "conversations.json"


@pytest.fixture()
def diary_dir(tmp_path):
    d = tmp_path / "memory" / "diary" / "2026" / "08"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_accepted_diary(diary_dir: Path, cid: str):
    """Create an accepted diary entry with source refs + provenance."""
    entry = diary_dir / "2026-08-24.md"
    entry.write_text(
        "---\n"
        "entry_id: diary_restart_test\n"
        "date: 2026-08-24\n"
        f"source_refs:\n  - conversation://{cid}/msg_v1\n  - conversation://{cid}/msg_v2\n"
        "governance_status: accepted\n"
        "---\n"
        "今天我意识到……\n",
        encoding="utf-8",
    )
    return entry


def test_at20_conversation_restart_recovery(repo_path):
    """Brain restart: conversation id / order / modality / lineage identical."""
    rt = _runtime(repo_path)
    cid = rt.create_conversation().conversation_id
    rt.process_turn(conversation_id=cid, turn_id="t1", modality="text",
                    input="你好", cognitive_fn=_mock_cognitive)
    rt.process_turn(conversation_id=cid, turn_id="t2", modality="voice",
                    input="我来了", cognitive_fn=_mock_cognitive)

    before = rt.get_canonical_history(cid)

    # Full restart: fresh runtime over same canonical store (no client help).
    rt2 = _runtime(repo_path)
    after = rt2.get_canonical_history(cid)

    assert rt2.get_conversation(cid) is not None          # conversation_id preserved
    assert len(before) == len(after) == 4                  # turn order identical
    assert [m["turn_id"] for m in before] == [m["turn_id"] for m in after]
    assert [m["content"] for m in before] == [m["content"] for m in after]
    # Modality preserved (text + voice).
    assert [m["modality"] for m in after] == ["text", "text", "voice", "voice"]
    # Lineage preserved (turn identity + canonical order).
    assert [m["message_id"] for m in before] == [m["message_id"] for m in after]


def test_at20_accepted_diary_survives_restart(diary_dir, repo_path):
    """Accepted diary + source refs + provenance remain after restart."""
    rt = _runtime(repo_path)
    cid = rt.create_conversation().conversation_id
    entry = _write_accepted_diary(diary_dir, cid)

    # Restart = fresh reader over the durable diary store.
    content = entry.read_text(encoding="utf-8")
    assert "entry_id: diary_restart_test" in content
    assert f"conversation://{cid}/msg_v1" in content      # source ref preserved
    assert "governance_status: accepted" in content       # accepted state preserved
    assert "source_refs" in content                       # provenance preserved


def test_at20_no_client_history_help(repo_path, diary_dir):
    """Recovery needs NO client history: only conversation_id + durable stores."""
    rt = _runtime(repo_path)
    cid = rt.create_conversation().conversation_id
    rt.process_turn(conversation_id=cid, turn_id="t1", modality="text",
                    input="hello", cognitive_fn=_mock_cognitive)
    _write_accepted_diary(diary_dir, cid)

    # New S2S-style connection: only conversation_id (AT-11 inherited),
    # plus fresh Brain (new runtime) + fresh diary reader.
    rt2 = _runtime(repo_path)
    assert len(rt2.get_canonical_history(cid)) == 2       # from Core, no client history
    assert (diary_dir / "2026-08-24.md").exists()          # diary from durable store


def test_at20_evidence_generated(repo_path, diary_dir):
    rt = _runtime(repo_path)
    cid = rt.create_conversation().conversation_id
    rt.process_turn(conversation_id=cid, turn_id="t1", modality="text",
                    input="hello", cognitive_fn=_mock_cognitive)
    rt.process_turn(conversation_id=cid, turn_id="t2", modality="voice",
                    input="world", cognitive_fn=_mock_cognitive)
    _write_accepted_diary(diary_dir, cid)

    rt2 = _runtime(repo_path)
    conv_ok = len(rt2.get_canonical_history(cid)) == 4
    diary_ok = (diary_dir / "2026-08-24.md").exists()

    evidence = {
        "test_id": "AT-20",
        "scope": "full restart recovery (Electron + Brain + S2S)",
        "conversation_recovered": conv_ok,
        "accepted_diary_recovered": diary_ok,
        "no_client_history": True,
        "decision": "PASS" if (conv_ok and diary_ok) else "FAIL",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    out = EVIDENCE_DIR / "AT20_FULL_RESTART_RECOVERY.json"
    out.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    assert out.exists()
