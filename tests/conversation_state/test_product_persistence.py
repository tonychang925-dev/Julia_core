"""A2-R1: canonical structured-product persistence on ConversationMessage.

Covers serialization round-trip, optional product on ordinary messages,
historical product-less reads, repository durability, and stable digest.
"""
import hashlib
import json
import os
import tempfile

from julia_core.runtime.conversation_runtime import ConversationRuntime
from julia_core.conversation_state.legacy_json_repository import (
    LegacyJsonConversationRepository,
)

PRODUCT = {
    "contract_version": "research.brief.v1",
    "brief_id": "br_test_1",
    "headline": "Token 出海 主题市场变化",
    "event_title": "Token出海",
    "trace": {"judgment_id": "j_test_1", "market_event_id": 215257},
}

HISTORICAL_SESSION = {
    "id": "conv-hist",
    "title": "Hist",
    "created_at": "2026-09-06T22:00:00+08:00",
    "state": "completed",
    "messages": [
        {"message_id": "m1", "role": "user", "content": "hi",
         "status": "completed", "turn_id": "t1", "modality": "text",
         "source": "text", "created_at": "2026-09-06T22:00:01+08:00"},
        {"message_id": "m2", "role": "assistant", "content": "plain reply",
         "status": "completed", "turn_id": "t1", "modality": "text",
         "source": "text", "created_at": "2026-09-06T22:00:02+08:00"},
    ],
}


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def _new_runtime():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "conversations.json")
    json.dump([HISTORICAL_SESSION], open(p, "w"))
    repo = LegacyJsonConversationRepository(p)
    return ConversationRuntime(repository=repo), p, repo


def _sha(value):
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def test_historical_productless_message_reads():
    rt, _, _ = _new_runtime()
    hist = rt.get_canonical_history("conv-hist")
    assert len(hist) == 2
    assert "product" not in hist[0]
    assert hist[1]["content"] == "plain reply"
    assert "product" not in hist[1]


def test_ordinary_message_has_no_product():
    rt, _, repo = _new_runtime()
    repo.create_with_id("conv-new", "New")
    repo.add_message("conv-new", role="user", content="hello",
                     turn_id="t1", modality="text")
    repo.add_message("conv-new", role="assistant", content="world",
                     turn_id="t1", modality="text")
    am = [m for m in rt.get_canonical_history("conv-new")
          if m["role"] == "assistant"][0]
    assert "product" not in am


def test_research_message_persists_product():
    rt, p, repo = _new_runtime()
    repo.create_with_id("conv-new", "New")
    repo.add_message("conv-new", role="assistant", content="brief text",
                     turn_id="t2", modality="text", product=PRODUCT)
    m = [x for x in rt.get_canonical_history("conv-new")
         if x["turn_id"] == "t2"][0]
    assert m.get("product") == PRODUCT


def test_product_survives_disk_roundtrip():
    rt, p, repo = _new_runtime()
    repo.create_with_id("conv-new", "New")
    repo.add_message("conv-new", role="assistant", content="brief text",
                     turn_id="t2", modality="text", product=PRODUCT)
    rt2 = ConversationRuntime(repository=LegacyJsonConversationRepository(p))
    m = [x for x in rt2.get_canonical_history("conv-new")
         if x["turn_id"] == "t2"][0]
    assert m.get("product") == PRODUCT


def test_product_digest_stable():
    rt, p, repo = _new_runtime()
    repo.create_with_id("conv-new", "New")
    repo.add_message("conv-new", role="assistant", content="brief text",
                     turn_id="t2", modality="text", product=PRODUCT)
    rt2 = ConversationRuntime(repository=LegacyJsonConversationRepository(p))
    m = [x for x in rt2.get_canonical_history("conv-new")
         if x["turn_id"] == "t2"][0]
    assert _sha(PRODUCT) == _sha(m["product"])


def test_duplicate_read_no_duplicate_product():
    rt, _, repo = _new_runtime()
    repo.create_with_id("conv-new", "New")
    repo.add_message("conv-new", role="assistant", content="brief text",
                     turn_id="t2", modality="text", product=PRODUCT)
    # repeated read-back must not mint extra product copies
    rt.get_canonical_history("conv-new")
    rt.get_canonical_history("conv-new")
    products = [m.get("product") for m in rt.get_canonical_history("conv-new")
                if m.get("product") is not None]
    assert len(products) == 1
