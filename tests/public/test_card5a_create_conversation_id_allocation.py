"""CARD 5A: CoreConversationIngress.create_conversation restores Core-side id allocation.

CM-I04 / CM00-CONFLICT-004: a new conversation is created by Core (durable record
first), and the client receives the canonical id. The runtime's existing uuid
allocator (5ce95a1) is the only id source; the public entry adds no id generation.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import re
import threading
from types import SimpleNamespace

import pytest

from julia_core.public.conversation import (
    CoreConversationConfig,
    CoreConversationConfigurationError,
    CoreConversationIngress,
)

ALLOCATED_ID = re.compile(r"conv_[0-9a-f]{32}")


def _ingress(tmp_path, monkeypatch) -> tuple[CoreConversationIngress, object]:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr(
        "julia_core.providers.core_cognition.initialize_production_cognition",
        lambda: None,
    )
    monkeypatch.setattr(
        "julia_core.providers.core_cognition._get_cognition_provider",
        lambda _name: object(),
    )
    base = tmp_path / "conversations"
    ingress = CoreConversationIngress(CoreConversationConfig(base))
    assert ingress._composition_error is None
    return ingress, base


def _new_ingress_on(base) -> CoreConversationIngress:
    """Like the Assistant: one short-lived ingress (own sqlite connection) per request."""
    ingress = CoreConversationIngress(CoreConversationConfig(base))
    assert ingress._composition_error is None
    return ingress


def _meta(base, conversation_id: str) -> dict:
    return json.loads((base / conversation_id / "meta.json").read_text())


@pytest.mark.parametrize("empty", ["", None])
def test_empty_id_is_allocated_by_core_and_persisted_before_return(tmp_path, monkeypatch, empty):
    ingress, base = _ingress(tmp_path, monkeypatch)
    conversation_id = ingress.create_conversation(empty, "Allocated")
    assert ALLOCATED_ID.fullmatch(conversation_id)
    assert CoreConversationIngress._valid_identifier(conversation_id)
    # durable artifact exists on disk and through the public read seam
    assert _meta(base, conversation_id)["conversation_id"] == conversation_id
    assert _meta(base, conversation_id)["title"] == "Allocated"
    detail = ingress.get_conversation(conversation_id)
    assert detail is not None
    assert any(item.conversation_id == conversation_id for item in ingress.list_conversations())


def test_public_entry_delegates_to_runtime_allocator_without_own_generation(tmp_path, monkeypatch):
    ingress, _ = _ingress(tmp_path, monkeypatch)
    calls = []
    real = ingress._runtime.create_conversation

    def spy(conversation_id, title="New Conversation"):
        calls.append(conversation_id)
        return real(conversation_id, title)

    monkeypatch.setattr(ingress._runtime, "create_conversation", spy)
    allocated = ingress.create_conversation("", "spy")
    assert calls == [""]  # the runtime allocator receives the empty id and allocates
    assert ALLOCATED_ID.fullmatch(allocated)
    source = inspect.getsource(CoreConversationIngress.create_conversation)
    for forbidden in (r"\buuid\b", r"\btime\b", r"\bcounter\b", r"\brandom\b", r"id\(self\)"):
        assert not re.search(forbidden, source), f"public create_conversation must not generate ids ({forbidden})"


def test_invalid_id_from_allocator_fails_closed(tmp_path, monkeypatch):
    ingress, _ = _ingress(tmp_path, monkeypatch)
    monkeypatch.setattr(
        ingress._runtime,
        "create_conversation",
        lambda conversation_id, title="New Conversation": SimpleNamespace(conversation_id="../escape"),
    )
    with pytest.raises(ValueError):
        ingress.create_conversation("", "bad allocator")


def test_rapid_sequential_creates_are_unique_and_independent(tmp_path, monkeypatch):
    ingress, base = _ingress(tmp_path, monkeypatch)
    ids = [ingress.create_conversation("", f"seq-{i}") for i in range(200)]
    assert len(set(ids)) == 200
    for i, conversation_id in enumerate(ids):
        assert _meta(base, conversation_id)["title"] == f"seq-{i}"
    assert len([p for p in base.iterdir() if p.is_dir()]) == 200


def test_concurrent_threads_get_unique_ids_and_records_do_not_overwrite(tmp_path, monkeypatch):
    _, base = _ingress(tmp_path, monkeypatch)  # patches the cognition seam; base dir shared by all threads
    workers, per_worker = 24, 5
    barrier = threading.Barrier(workers)
    results: dict[tuple[int, int], str] = {}
    errors: list[BaseException] = []
    lock = threading.Lock()

    def work(worker: int) -> None:
        try:
            ingress = _new_ingress_on(base)  # sqlite connections are thread-bound: one ingress per thread
            barrier.wait(timeout=30)
            for n in range(per_worker):
                cid = ingress.create_conversation("", f"t{worker}-{n}")
                with lock:
                    results[(worker, n)] = cid
        except BaseException as exc:  # noqa: BLE001 - surfaced by the assertion below
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=work, args=(w,)) for w in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    assert not errors
    assert len(results) == workers * per_worker
    assert len(set(results.values())) == workers * per_worker  # no duplicate ids
    for (worker, n), cid in results.items():
        meta = _meta(base, cid)
        assert meta["conversation_id"] == cid
        assert meta["title"] == f"t{worker}-{n}"  # each record is its creator's, none overwritten
    assert len([p for p in base.iterdir() if p.is_dir()]) == workers * per_worker


def test_concurrent_coroutines_get_unique_ids_and_records_do_not_overwrite(tmp_path, monkeypatch):
    """Interleaved coroutines (one ingress each, all on the event-loop thread, like async handlers)."""
    _, base = _ingress(tmp_path, monkeypatch)
    ingresses = [_new_ingress_on(base) for _ in range(16)]  # built before any create is in flight

    async def worker(idx: int, ingress: CoreConversationIngress) -> list[tuple[str, str]]:
        out = []
        for n in range(4):
            title = f"co-{idx}-{n}"
            out.append((ingress.create_conversation("", title), title))
            await asyncio.sleep(0)  # let the other coroutines interleave between creates
        return out

    async def run():
        return await asyncio.gather(*[worker(i, ing) for i, ing in enumerate(ingresses)])

    created = [pair for batch in asyncio.run(run()) for pair in batch]
    assert len(created) == 64
    assert len({cid for cid, _ in created}) == 64
    for cid, title in created:
        assert _meta(base, cid)["title"] == title


@pytest.mark.parametrize(
    "bad",
    ["..", ".", "../x", "a/b", "a\\b", "/abs", " ", "  x", "x ", "-lead", ".lead", "x" * 129, "a\x00b", "a\nb"],
)
def test_invalid_explicit_ids_are_still_rejected(tmp_path, monkeypatch, bad):
    ingress, base = _ingress(tmp_path, monkeypatch)
    before = sorted(p.name for p in base.iterdir())
    with pytest.raises(ValueError):
        ingress.create_conversation(bad, "nope")
    assert sorted(p.name for p in base.iterdir()) == before  # nothing created, nothing escaped
    assert not (tmp_path / "x").exists()


# #243: an explicit id must now be a canonical conv_<32 hex> (free-form ids are rejected)
EXPLICIT_OK = "conv_" + "e" * 32


def test_explicit_valid_id_behaviour_is_unchanged(tmp_path, monkeypatch):
    ingress, base = _ingress(tmp_path, monkeypatch)
    assert ingress.create_conversation(EXPLICIT_OK, "Explicit") == EXPLICIT_OK
    assert _meta(base, EXPLICIT_OK)["title"] == "Explicit"
    # idempotent: same id returns the same conversation and does not duplicate it
    assert ingress.create_conversation(EXPLICIT_OK, "Other title") == EXPLICIT_OK
    assert len([p for p in base.iterdir() if p.is_dir()]) == 1
    assert _meta(base, EXPLICIT_OK)["title"] == "Explicit"


@pytest.mark.parametrize("conversation_id", ["", None, "explicit-1"])
def test_composition_error_still_raises_configuration_error(monkeypatch, conversation_id):
    monkeypatch.delenv("JULIA_CONVERSATION_DATA_DIR", raising=False)
    ingress = CoreConversationIngress(CoreConversationConfig(None))
    assert ingress._composition_error is not None
    with pytest.raises(CoreConversationConfigurationError):
        ingress.create_conversation(conversation_id, "x")
