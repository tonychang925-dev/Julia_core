"""#243: StorageV2 read paths never create directories; ids can never escape the base dir."""
from __future__ import annotations

import os

import pytest

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository

CID = "conv_" + "1" * 32
UNKNOWN = "conv_" + "2" * 32
STRUCTURAL_BAD = ["../x", "a/b", "/etc/x", "..", ".", "", "x\x00y", "a" * 129, "a b", "../../escape"]


def _snapshot(root):
    return sorted(os.path.relpath(os.path.join(d, n), root) for d, ds, fs in os.walk(root) for n in ds + fs
                  if not n.startswith("catalog.sqlite"))


@pytest.fixture()
def repo(tmp_path):
    r = StorageV2ConversationRepository(tmp_path / "base")
    r.create_with_id(CID, "t")
    r.add_message(CID, "user", "hi", turn_id="t1")
    yield r
    r.close()


READS = {
    "get": lambda r, i: r.get(i),
    "get_messages": lambda r, i: r.get_messages(i, limit=10),
    "find_turn": lambda r, i: r.find_turn(i, "t1"),
    "update_title": lambda r, i: r.update_title(i, "x"),
    "delete": lambda r, i: r.delete(i),
}


@pytest.mark.parametrize("method", sorted(READS))
@pytest.mark.parametrize("ident", ["None", "null", UNKNOWN, "plain-name"])
def test_read_methods_do_not_create_directories(repo, tmp_path, ident, method):
    # each method on its own: a later call (e.g. delete) must not be able to mask an earlier mkdir
    before = _snapshot(tmp_path / "base")
    READS[method](repo, ident)
    assert _snapshot(tmp_path / "base") == before


def test_unknown_id_after_known_one_leaves_known_conversation_intact(repo, tmp_path):
    repo.find_turn("None", "t1")
    assert [m.content for m in repo.get(CID).messages] == ["hi"]
    assert not (tmp_path / "base" / "None").exists()


@pytest.mark.parametrize("bad", STRUCTURAL_BAD)
def test_traversal_and_malformed_ids_are_rejected_without_side_effects(repo, tmp_path, bad):
    before_all = sorted(os.listdir(tmp_path))
    before = _snapshot(tmp_path / "base")
    for call in (
        lambda: repo.create_with_id(bad),
        lambda: repo.update_title(bad, "x"),
        lambda: repo.delete(bad),
        lambda: repo.find_turn(bad, "t1"),
    ):
        with pytest.raises(ValueError):
            call()
    assert sorted(os.listdir(tmp_path)) == before_all          # nothing created next to base
    assert _snapshot(tmp_path / "base") == before


def test_symlink_escape_is_rejected(repo, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    os.symlink(outside, tmp_path / "base" / "evil-link")
    with pytest.raises(ValueError):
        repo.create_with_id("evil-link")
    assert os.listdir(outside) == []


def test_reconcile_does_not_adopt_directories_with_unsafe_names(tmp_path):
    base = tmp_path / "base"
    r = StorageV2ConversationRepository(base)
    r.close()
    bad = base / "weird name"
    bad.mkdir()
    (bad / "meta.json").write_text('{"conversation_id": "weird name", "title": "x", "state": "active"}')
    r2 = StorageV2ConversationRepository(base)
    assert r2.get("weird name") is None
    r2.close()


def test_writes_still_create_the_directory_and_survive_reopen(tmp_path):
    r = StorageV2ConversationRepository(tmp_path / "base")
    r.create_with_id(CID, "t")
    r.add_message(CID, "user", "hi", turn_id="t1")
    r.close()
    r2 = StorageV2ConversationRepository(tmp_path / "base")
    assert (tmp_path / "base" / CID / "meta.json").exists()
    assert [m.content for m in r2.get(CID).messages] == ["hi"]
    r2.close()
