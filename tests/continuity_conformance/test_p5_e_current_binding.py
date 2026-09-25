from pathlib import Path

from tests.continuity_conformance.evaluation_contract import DIMENSION_IDS
from tests.continuity_conformance.p5_e_current_binding import (
    EXPECTED_IDENTITY_PROJECTED_DIGEST, EXPECTED_IDENTITY_SOURCE_DIGEST,
    EXPECTED_PSB_DIGEST, build_current_contract,
)

REPOSITORY = Path(__file__).resolve().parents[2]
AUTHORITY_ROOT = Path('/Users/admin/.julia_mira_e2e/authority')
PSB_ROOT = Path('/Users/admin/.julia_mira_e2e/authority-runtime/persona-self-binding-store-v1')


def test_p5_e_binds_current_four_identity_eight_experience_psb_v2() -> None:
    contract = build_current_contract(
        repository=REPOSITORY, authority_root=AUTHORITY_ROOT, psb_store_root=PSB_ROOT
    )
    current = contract.admitted_input
    assert current['identity_count'] == 4
    assert current['memory_experience_count'] == 8
    assert len(current['refs']) == 12
    assert len(current['digests']) == 12
    assert current['psb_version'] == 'v2'
    assert current['psb_digest'] == EXPECTED_PSB_DIGEST
    assert current['identity_source_digest'] == EXPECTED_IDENTITY_SOURCE_DIGEST
    assert current['identity_projected_digest'] == EXPECTED_IDENTITY_PROJECTED_DIGEST
    assert current['relationship_binding_state'] == 'ABSENT'
    assert tuple(item['id'] for item in contract.dimensions) == DIMENSION_IDS
    assert all(value == 0 for value in contract.authority.values())


def test_p5_e_contains_c04_relationship_role_identity() -> None:
    contract = build_current_contract(
        repository=REPOSITORY, authority_root=AUTHORITY_ROOT, psb_store_root=PSB_ROOT
    )
    refs = contract.admitted_input['refs']
    assert any('mira-id-cand-004' in ref for ref in refs)
    assert not any('not-admitted' in ref for ref in refs)
