from __future__ import annotations

import pytest

from julia_core.identity import IdentityAnchor, IdentityRef


class SpoofString(str):
    pass


def test_identity_anchor_rejects_string_subclass_identifier() -> None:
    with pytest.raises(ValueError, match="anchor_id must be an exact built-in string"):
        IdentityAnchor(anchor_id=SpoofString("anchor-core"), statement="Synthetic anchor")


def test_identity_ref_rejects_string_subclass_identifier_before_key_construction() -> None:
    with pytest.raises(ValueError, match="lineage_id must be an exact built-in string"):
        IdentityRef(lineage_id=SpoofString("lineage-synthetic"), version_id="v1")
    with pytest.raises(ValueError, match="version_id must be an exact built-in string"):
        IdentityRef(lineage_id="lineage-synthetic", version_id=SpoofString("v1"))


def test_plain_built_in_identity_identifiers_remain_valid() -> None:
    ref = IdentityRef(lineage_id="lineage-synthetic", version_id="v1")

    assert type(ref.lineage_id) is str
    assert type(ref.version_id) is str
