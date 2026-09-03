from __future__ import annotations

import asyncio
from dataclasses import replace

import pytest

from julia_core.capability.manager import CapabilityManager
from julia_core.capability.models import (
    CapabilityRequest,
    CapabilityStatus,
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)
from julia_core.capability.policy import (
    AuthorizationDecision,
    AuthorizationStatus,
    PermissionPolicy,
)
from julia_core.capability.registry import CapabilityRegistry
from julia_core.review.admission import (
    CandidateAdmissionComposition,
    CandidateAdmissionError,
    CandidateAdmissionRecord,
    is_trusted_candidate_admission_binding,
)
from julia_core.review.contracts import ReviewBundle
from julia_core.review.digest import compute_bundle_digest
from julia_core.review.guard import install_review_guard
from julia_core.review.invocation import submit_review
from julia_core.review.registration import register_external_review_capability
from julia_core.review.transaction import ReviewTransactionLedger


class AdmissionSource:
    def __init__(self, records):
        self.records = records
        self.lookup_count = 0

    def candidate_admission(self, *, review_id: str, candidate_id: str):
        self.lookup_count += 1
        try:
            return self.records[(review_id, candidate_id)]
        except KeyError as exc:
            raise RuntimeError("admission missing") from exc


class Provider:
    def __init__(self):
        self.execute_count = 0

    async def health(self):
        return True, "ready"

    async def execute(self, request: CapabilityRequest):
        self.execute_count += 1
        return ProviderExecutionOutcome(
            status=ToolResultStatus.SUCCESS,
            structured_output={"raw_response": "{}"},
            side_effect_state=SideEffectState.SUCCEEDED,
        )


class AllowPolicy(PermissionPolicy):
    def check(self, scope: str) -> AuthorizationDecision:
        return AuthorizationDecision(
            decision=AuthorizationStatus.ALLOW,
            scope=scope,
            reason="admission gate fixture",
        )


def _bundle(**overrides) -> ReviewBundle:
    values = dict(
        review_id="rvw_admission",
        task_id="task_admission",
        candidate_id="cand_admission",
        candidate_sha="3f57ab4c0f04ea2a39ca17298c1c1ee7a72c81",
        repository="tonychang925-dev/Julia_core",
        branch="feature/admission",
        objective="Prove pre-send authority",
        changed_files=("julia_core/review/admission.py",),
        questions=("Is admission before send?",),
    )
    values.update(overrides)
    return ReviewBundle(**values)


def _source(bundle: ReviewBundle | None = None):
    bundle = bundle or _bundle()
    return AdmissionSource(
        {
            (bundle.review_id, bundle.candidate_id): CandidateAdmissionRecord(
                review_id=bundle.review_id,
                candidate_id=bundle.candidate_id,
                repository=bundle.repository,
                candidate_sha=bundle.candidate_sha,
            )
        }
    )


def _binding(source=None):
    return CandidateAdmissionComposition(
        source or _source(),
        provenance={"composition": "test review ingress"},
    ).binding


def _manager(provider: Provider):
    ledger = ReviewTransactionLedger()
    registry = CapabilityRegistry()
    register_external_review_capability(registry, status=CapabilityStatus.AVAILABLE)
    providers = {}
    install_review_guard(providers, real_provider=provider, ledger=ledger)
    return CapabilityManager(registry, AllowPolicy(), providers), ledger


def _submit(bundle, binding, provider=None):
    manager, ledger = _manager(provider or Provider())
    return asyncio.run(
        submit_review(
            manager,
            bundle,
            ledger,
            admission_source=binding,
        )
    )


def test_admission_record_is_immutable_and_requires_all_authority_fields():
    record = CandidateAdmissionRecord(
        review_id="rvw_1",
        candidate_id="cand_1",
        repository="repo",
        candidate_sha="a" * 40,
    )
    assert record.candidate_sha == "a" * 40
    with pytest.raises(ValueError, match="review_id"):
        CandidateAdmissionRecord("", "cand", "repo", "a" * 40)
    with pytest.raises(Exception):
        record.candidate_sha = "b" * 40


def test_admission_composition_binding_is_exact_object_trusted():
    binding = _binding()
    assert is_trusted_candidate_admission_binding(binding)
    copied = replace(binding)
    assert copied.binding_id == binding.binding_id
    assert is_trusted_candidate_admission_binding(copied) is False


def test_admission_binding_mutation_fails_closed():
    binding = _binding()
    object.__setattr__(binding, "provenance", {"mutated": True})
    assert is_trusted_candidate_admission_binding(binding) is False
    with pytest.raises(CandidateAdmissionError, match="not trusted"):
        _submit(_bundle(), binding)


def test_admission_composition_is_non_rebindable():
    composition = CandidateAdmissionComposition(_source())
    with pytest.raises(AttributeError):
        composition._source = _source()


def test_missing_admission_source_fails_before_provider_dispatch():
    manager, _ledger = _manager(Provider())
    with pytest.raises(TypeError, match="admission_source"):
        asyncio.run(submit_review(manager, _bundle(), ReviewTransactionLedger()))


def test_unregistered_binding_lookalike_fails_before_provider_dispatch():
    provider = Provider()
    real = CandidateAdmissionComposition(_source()).binding
    lookalike = replace(real, provenance=dict(real.provenance))
    with pytest.raises(CandidateAdmissionError, match="not trusted"):
        _submit(_bundle(), lookalike, provider)
    assert provider.execute_count == 0


def test_lookup_failure_fails_before_provider_dispatch():
    source = AdmissionSource({})
    binding = _binding(source)
    provider = Provider()
    with pytest.raises(CandidateAdmissionError, match="lookup failed"):
        _submit(_bundle(), binding, provider)
    assert provider.execute_count == 0
    assert source.lookup_count == 1


@pytest.mark.parametrize(
    "overrides",
    [
        {"review_id": "rvw_foreign"},
        {"candidate_id": "cand_foreign"},
        {"repository": "foreign/repository"},
        {"candidate_sha": "f" * 40},
    ],
)
def test_forged_bundle_identity_fails_before_send(overrides):
    provider = Provider()
    with pytest.raises(CandidateAdmissionError, match="lookup failed|does not match trusted"):
        _submit(_bundle(**overrides), _binding(), provider)
    assert provider.execute_count == 0


def test_internally_consistent_forged_bundle_does_not_gain_authority():
    provider = Provider()
    manager, ledger = _manager(provider)
    forged = _bundle(
        review_id="rvw_forged",
        candidate_id="cand_forged",
        repository="foreign/repository",
        candidate_sha="f" * 40,
    )
    with pytest.raises(CandidateAdmissionError, match="lookup failed|does not match trusted"):
        asyncio.run(
            submit_review(
                manager,
                forged,
                ledger,
                admission_source=_binding(),
            )
        )
    assert provider.execute_count == 0
    binding = (
        forged.review_id,
        forged.candidate_id,
        forged.candidate_sha,
        compute_bundle_digest(forged),
    )
    assert ledger.get_by_binding(binding) == []


def test_provider_compatible_forged_sha_does_not_gain_authority():
    provider = Provider()
    admitted_sha = _bundle().candidate_sha
    forged = _bundle(candidate_id="cand_forged", candidate_sha=admitted_sha)
    with pytest.raises(CandidateAdmissionError, match="lookup failed|does not match trusted"):
        _submit(forged, _binding(), provider)
    assert provider.execute_count == 0


def test_valid_admission_reaches_provider_exactly_once_and_seals_snapshot():
    provider = Provider()
    invocation = _submit(_bundle(), _binding(), provider)
    assert provider.execute_count == 1
    assert invocation.transaction.snapshot.review_id == "rvw_admission"
    assert invocation.transaction.candidate_sha == _bundle().candidate_sha
