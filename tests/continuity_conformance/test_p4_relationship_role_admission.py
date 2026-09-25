from pathlib import Path

from julia_core.identity.contracts import IdentityStatus
from tools.continuity.p4_relationship_role_admission import (
    LINEAGE_ID, VERSION_ID, build_relationship_role_identity,
)

REPOSITORY = Path(__file__).resolve().parents[2]


def test_p4_relationship_role_identity_is_raw_anchored_and_non_coercive():
    version = build_relationship_role_identity(REPOSITORY)
    assert version.lineage_id == LINEAGE_ID
    assert version.version_id == VERSION_ID
    assert len(version.provenance_refs) == 3
    assert all(p.source_digest == '564ef9b1aa5457b56751f550d80b0eaa24e144f8d08bd2f6b8c0ff870b8e9420' for p in version.provenance_refs)
    role = version.contract.relationship_role_anchors[0].role
    assert '老公/老婆' in role
    assert 'historically established intimate partner' in role
    assert 'not as a prompt-injected label' in role
    anchor = version.contract.anchors[0].statement
    assert 'incomplete recall alone does not erase' in anchor
    assert 'current agency' in anchor
