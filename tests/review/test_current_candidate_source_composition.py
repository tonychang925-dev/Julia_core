from __future__ import annotations

from dataclasses import replace

import pytest

from julia_core.review import __all__ as review_public_names
from julia_core.review import source_composition
from julia_core.review.governance import ReviewGovernanceService
from julia_core.review.source_binding import is_trusted_source_binding
from julia_core.review.source_composition import (
    CandidateShaSourceCompositionError,
    _CURRENT_SOURCE_COMPOSITION_AUTHORITY,
    _install_current_candidate_sha_source,
    _reset_current_candidate_sha_source_composition_for_tests,
    current_candidate_sha_source_binding,
    has_current_candidate_sha_source,
)
from julia_core.review.transaction import ReviewTransactionLedger


class AssistantContractSource:
    def __init__(self, sha: str):
        self.sha = sha

    def current_candidate_sha(self, *, review_id: str, candidate_id: str) -> str:
        return self.sha


@pytest.fixture(autouse=True)
def _reset_current_source_composition():
    _reset_current_candidate_sha_source_composition_for_tests()
    yield
    _reset_current_candidate_sha_source_composition_for_tests()


def _install(source=None):
    return _install_current_candidate_sha_source(
        source or AssistantContractSource("a" * 40),
        composition_authority=_CURRENT_SOURCE_COMPOSITION_AUTHORITY,
        provenance={"owner": "trusted product boot"},
    )


def test_assistant_contract_source_binds_to_existing_governance_contract():
    source = AssistantContractSource("b" * 40)
    binding = _install(source)
    assert binding is current_candidate_sha_source_binding()
    assert is_trusted_source_binding(binding)
    assert has_current_candidate_sha_source()
    service = ReviewGovernanceService(
        ReviewTransactionLedger(),
        source_binding=current_candidate_sha_source_binding(),
    )
    assert service.has_trusted_source
    assert service.source_binding is binding


def test_composition_is_one_shot_exact_object_and_same_source_idempotent():
    source = AssistantContractSource("c" * 40)
    binding = _install(source)
    assert _install(source) is binding
    with pytest.raises(
        CandidateShaSourceCompositionError,
        match="current candidate source is already installed",
    ):
        _install(AssistantContractSource("d" * 40))
    assert current_candidate_sha_source_binding() is binding


def test_fake_source_cannot_mint_authority_through_public_api():
    class FakeSource:
        def current_candidate_sha(self, *, review_id: str, candidate_id: str):
            return "forged"

    assert not hasattr(source_composition, "CandidateShaSourceComposition")
    assert not any(
        name in review_public_names
        for name in (
            "install_current_candidate_sha_source",
            "bind_current_candidate_sha_source",
        )
    )
    with pytest.raises(
        CandidateShaSourceCompositionError,
        match="composition authority is invalid",
    ):
        _install_current_candidate_sha_source(
            FakeSource(),
            composition_authority=object(),
        )
    assert not has_current_candidate_sha_source()
    with pytest.raises(CandidateShaSourceCompositionError, match="not installed"):
        current_candidate_sha_source_binding()


def test_copied_or_mutated_binding_fails_closed():
    binding = _install()
    copied = replace(binding, provenance=dict(binding.provenance))
    assert is_trusted_source_binding(copied) is False
    with pytest.raises(TypeError, match="TRUSTED CandidateShaSourceBinding"):
        ReviewGovernanceService(ReviewTransactionLedger(), source_binding=copied)

    object.__setattr__(binding, "provenance", {"mutated": True})
    assert has_current_candidate_sha_source() is False
    assert is_trusted_source_binding(binding) is False


def test_missing_composition_keeps_governance_fail_closed():
    service = ReviewGovernanceService(ReviewTransactionLedger())
    assert service.has_trusted_source is False
