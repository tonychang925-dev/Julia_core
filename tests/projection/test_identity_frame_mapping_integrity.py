from __future__ import annotations

from collections.abc import Mapping

from julia_core.identity import IdentityRef, IdentityStatus
from julia_core.projection.contracts import IdentityFrame


class BackedMapping(Mapping):
    def __init__(self, backing):
        self._backing = backing

    def __getitem__(self, key):
        return self._backing[key]

    def __iter__(self):
        return iter(self._backing)

    def __len__(self):
        return len(self._backing)


def frame(mapping):
    return IdentityFrame(
        schema_version="1.0.0",
        policy_id="persona_projection.identity_only",
        policy_version="1.0.0",
        source_ref=IdentityRef("lineage-synthetic-frame", "v1"),
        source_digest="a" * 64,
        source_status=IdentityStatus.ADMITTED,
        identity_id="identity-synthetic-frame",
        predecessor_version_id=None,
        anchors=(mapping,),
        values=(),
        boundaries=(),
        relationship_role_anchors=(),
        provenance_refs=(mapping,),
    )


def test_all_mapping_implementations_are_detached_from_backing_state() -> None:
    backing = {"anchor_id": "anchor-core", "statement": "original"}
    projected = frame(BackedMapping(backing))
    original_digest = projected.digest()

    backing["statement"] = "mutated backing"
    backing["injected"] = "system_prompt"

    assert projected.anchors[0]["statement"] == "original"
    assert "injected" not in projected.anchors[0]
    assert projected.digest() == original_digest


def test_semantically_identical_mappings_remain_deterministic_and_detached() -> None:
    first_backing = {"case": "same"}
    second_backing = {"case": "same"}
    first = frame(BackedMapping(first_backing))
    second = frame(BackedMapping(second_backing))

    assert first.digest() == second.digest()
    outward = first.to_dict()
    outward["anchors"][0]["case"] = "mutated outward"
    assert first.anchors[0]["case"] == "same"
    assert first.digest() == second.digest()
