from __future__ import annotations

import pytest

from dataclasses import replace

from tests.context_admission.production_fixtures import canonical_identity_frame

from julia_core.identity import IdentityRef
from julia_core.projection.contracts import IdentityFrame, IdentityFrameSet


def frame(lineage_id: str) -> IdentityFrame:
    return replace(canonical_identity_frame(), source_ref=IdentityRef(lineage_id, "v1"))


def test_identity_frame_set_accepts_one_and_three_ordered_frames() -> None:
    single = IdentityFrameSet(schema_version="1.0.0", frames=(frame("one"),))
    ordered = (frame("one"), frame("two"), frame("three"))
    multiple = IdentityFrameSet(schema_version="1.0.0", frames=ordered)

    assert single.ordered_source_refs() == (IdentityRef("one", "v1"),)
    assert multiple.frames == ordered
    assert multiple.ordered_source_refs() == tuple(item.source_ref for item in ordered)
    assert multiple.ordered_frame_digests() == tuple(item.digest() for item in ordered)


def test_identity_frame_set_rejects_invalid_carriers() -> None:
    with pytest.raises(ValueError, match="at least one"):
        IdentityFrameSet(schema_version="1.0.0", frames=())
    with pytest.raises(TypeError, match="exact tuple"):
        IdentityFrameSet(schema_version="1.0.0", frames=[frame("one")])
    with pytest.raises(TypeError, match="exact IdentityFrame"):
        IdentityFrameSet(schema_version="1.0.0", frames=(object(),))
    with pytest.raises(ValueError, match="unique"):
        IdentityFrameSet(schema_version="1.0.0", frames=(frame("one"), frame("one")))


def test_identity_frame_set_order_is_digest_significant() -> None:
    first = IdentityFrameSet(
        schema_version="1.0.0", frames=(frame("one"), frame("two"))
    )
    reordered = IdentityFrameSet(
        schema_version="1.0.0", frames=(frame("two"), frame("one"))
    )

    assert first.digest() != reordered.digest()
    assert first.ordered_frame_digests() != reordered.ordered_frame_digests()


def test_identity_frame_set_deterministic_serialization_and_digest() -> None:
    value = IdentityFrameSet(schema_version="1.0.0", frames=(frame("one"),))

    assert value.canonical_serialization() == value.canonical_serialization()
    assert (
        value.digest()
        == IdentityFrameSet(schema_version="1.0.0", frames=(frame("one"),)).digest()
    )
    assert value.to_dict()["schema"] == "julia_core.projection.identity_frame_set.v1"
