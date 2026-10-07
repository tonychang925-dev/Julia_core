"""#243: conversation id integrity at the Core public ingress.

Strict ``conv_[0-9a-f]{32}`` for conversation ids; invalid ids are rejected with
INVALID_CONVERSATION_ID, well-formed unknown ids with CONVERSATION_NOT_FOUND, and
neither may create anything on disk or emit events.
"""
from __future__ import annotations

import os

import pytest

from julia_core.public.conversation import (
    CoreConversationConfig,
    CoreConversationIngress,
    CoreConversationRequest,
)

UNKNOWN_VALID = "conv_" + "0" * 32
INVALID_IDS = [
    "None", "null", "undefined", "conv_", "conv_" + "0" * 31, "conv_" + "0" * 33,
    "conv_" + "A" * 32, "CONV_" + "0" * 32, " conv_" + "0" * 32, "conv_" + "0" * 32 + "\n",
    "../x", "a/b", "/etc/x", "..", ".", "conv_" + "0" * 31 + "/", "", "conv_" + "g" * 32,
    "conv_" + "0" * 32 + "\x00",
]


class _Provider:
    def chat(self, messages, cognitive_mode=""):
        return "stub reply"


@pytest.fixture()
def ingress(tmp_path, monkeypatch):
    import julia_core.events.store as es

    monkeypatch.setattr(es, "_store", es.EventStore(storage_dir=str(tmp_path / "events")))
    return CoreConversationIngress(CoreConversationConfig(tmp_path / "data"), provider_factory=lambda: _Provider())


def _entries(root):
    return sorted(os.listdir(root))


def _req(cid, turn="t1"):
    return CoreConversationRequest(cid, turn, "text", "hello")


@pytest.mark.parametrize("bad", INVALID_IDS)
def test_process_rejects_invalid_ids_without_touching_disk(ingress, tmp_path, bad):
    before = _entries(tmp_path / "data")
    result = ingress.process(_req(bad))
    assert result.status == "failed" and result.error_code == "INVALID_CONVERSATION_ID"
    assert _entries(tmp_path / "data") == before


def test_process_unknown_but_valid_id_is_not_found_and_creates_nothing(ingress, tmp_path):
    before = _entries(tmp_path / "data")
    result = ingress.process(_req(UNKNOWN_VALID))
    assert result.status == "failed" and result.error_code == "CONVERSATION_NOT_FOUND"
    assert _entries(tmp_path / "data") == before
    assert not (tmp_path / "events").exists() or not any((tmp_path / "events").iterdir())


@pytest.mark.parametrize("bad", [b for b in INVALID_IDS if b])
def test_read_methods_reject_invalid_ids(ingress, tmp_path, bad):
    before = _entries(tmp_path / "data")
    with pytest.raises(ValueError):
        ingress.get_conversation(bad)
    with pytest.raises(ValueError):
        ingress.get_messages(bad)
    assert _entries(tmp_path / "data") == before


@pytest.mark.parametrize("bad", [None, 0, 1.5, [], {}, {"conversation_id": "x"}, b"conv_" + b"0" * 32])
def test_non_string_ids_are_rejected_not_converted(ingress, bad):
    assert ingress.process(_req(bad)).error_code == "INVALID_CONVERSATION_ID"
    with pytest.raises(ValueError):
        ingress.get_conversation(bad)


def test_read_of_unknown_valid_id_returns_none_or_empty_and_creates_nothing(ingress, tmp_path):
    before = _entries(tmp_path / "data")
    assert ingress.get_conversation(UNKNOWN_VALID) is None
    assert ingress.get_messages(UNKNOWN_VALID) == []
    assert _entries(tmp_path / "data") == before


@pytest.mark.parametrize("bad", [b for b in INVALID_IDS if b])
def test_create_with_supplied_invalid_id_is_rejected(ingress, tmp_path, bad):
    before = _entries(tmp_path / "data")
    with pytest.raises(ValueError):
        ingress.create_conversation(bad)
    assert _entries(tmp_path / "data") == before


def test_allocated_and_supplied_conforming_ids_still_work(ingress):
    cid = ingress.create_conversation(None)
    assert cid.startswith("conv_") and len(cid) == 37
    assert ingress.get_conversation(cid) is not None
    supplied = "conv_" + "a1" * 16
    assert ingress.create_conversation(supplied) == supplied
    assert ingress.create_conversation(supplied) == supplied  # idempotent
    result = ingress.process(_req(cid))
    assert result.status == "completed" and result.assistant_content == "stub reply"
    assert len(ingress.get_messages(cid)) == 2
