from __future__ import annotations

import asyncio
import json
from typing import Any

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
from julia_core.review.contracts import ReviewBundle
from julia_core.review.candidate_artifact import is_trusted_candidate
from julia_core.review.governance import ReviewGovernanceService
from julia_core.review.guard import install_review_guard
from julia_core.review.invocation import submit_review
from julia_core.review.parser import (
    ReviewMachineResponseParseError,
    get_core_review_parser_binding,
    parse_review_response,
)
from julia_core.review.registration import register_external_review_capability
from julia_core.review.source_binding import is_trusted_candidate_creator
from julia_core.review.transaction import ReviewTransactionLedger
from tests.review._testonly import (
    TestCandidateShaSource,
    register_test_candidate_sha_source,
    candidate_admission_binding_for,
)


class FixtureProvider:
    def __init__(self, raw_response: str):
        self.raw_response = raw_response

    async def health(self):
        return True, "ok"

    async def execute(self, request: CapabilityRequest):
        return ProviderExecutionOutcome(
            status=ToolResultStatus.SUCCESS,
            structured_output={"raw_response": self.raw_response},
            side_effect_state=SideEffectState.SUCCEEDED,
        )


class AllowPolicy(PermissionPolicy):
    def check(self, scope: str) -> AuthorizationDecision:
        return AuthorizationDecision(
            decision=AuthorizationStatus.ALLOW, scope=scope, reason="test allow"
        )


class CurrentShaSource(TestCandidateShaSource):
    def current_candidate_sha(self, *, review_id: str, candidate_id: str) -> str:
        return "sha_1"


class StaleShaSource(TestCandidateShaSource):
    def current_candidate_sha(self, *, review_id: str, candidate_id: str) -> str:
        return "sha_changed"


def _bundle() -> ReviewBundle:
    return ReviewBundle(
        review_id="rvw_parser",
        task_id="task_parser",
        candidate_id="cand_parser",
        candidate_sha="sha_1",
        repository="Julia_core",
        branch="feature/parser",
        objective="Validate parser trust",
        changed_files=("julia_core/review/parser.py",),
        questions=("Can provider output become trusted?",),
        evidence_refs=("evidence://changed",),
    )


def _invocation(raw_response: str):
    invocation, _ = _governed_invocation(raw_response)
    return invocation


def _governed_invocation(raw_response: str):
    ledger = ReviewTransactionLedger()
    registry = CapabilityRegistry()
    register_external_review_capability(registry, status=CapabilityStatus.AVAILABLE)
    providers = {}
    install_review_guard(
        providers,
        real_provider=FixtureProvider(raw_response),
        ledger=ledger,
    )
    manager = CapabilityManager(registry, AllowPolicy(), providers)
    invocation = asyncio.run(
        submit_review(
            manager,
            _bundle(),
            ledger,
            admission_source=candidate_admission_binding_for(_bundle()),
        )
    )
    return invocation, ledger


def _observable_machine_response() -> str:
    invocation = _invocation("placeholder")
    snapshot = invocation.transaction.snapshot
    payload = {
        "review_id": snapshot.review_id,
        "candidate_id": snapshot.candidate_id,
        "candidate_sha": snapshot.candidate_sha,
        "bundle_digest": snapshot.digest,
        "verdict": "REWORK",
        "findings": [
            {
                "severity": "BLOCKER",
                "observation": "Authorization is bypassed",
                "inference": "The provider executes before policy admission",
                "causal_impact": "An unauthorized caller can invoke the capability",
                "evidence_bindings": [
                    {"kind": "REVIEW_INPUT", "ref": "evidence://changed"},
                ],
                "confidence": 0.9,
                "required_change": "Admit only after authorization",
                "provider_finding_label": "provider-local-label",
            }
        ],
        "notes": ["Machine review is structured"],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _parse(response: str):
    return parse_review_response(_invocation(response))


def test_parser_binding_is_core_owned_and_trusted():
    binding = get_core_review_parser_binding()
    assert binding.binding_id == "core_review_machine_parser_v1"
    assert is_trusted_candidate_creator(binding)


def test_parser_produces_trusted_sealed_candidate_from_exact_invocation():
    sealed = _parse(_observable_machine_response())
    assert is_trusted_candidate(sealed)
    candidate = sealed.candidate
    assert candidate.review_id == "rvw_parser"
    assert candidate.candidate_id == "cand_parser"
    assert candidate.candidate_sha == "sha_1"
    assert candidate.verdict.value == "REWORK"
    assert candidate.blockers == ("Authorization is bypassed",)
    assert candidate.required_changes == ("Admit only after authorization",)
    assert candidate.validation_state == "CANDIDATE"
    assert candidate.findings[0].finding_id.startswith("finding_")
    assert candidate.findings[0].provider_finding_label == "provider-local-label"
    assert candidate.transport_trace.status == "CAPTURED"


def test_parser_derives_raw_response_and_transport_truth_from_core():
    invocation = _invocation(_observable_machine_response())
    sealed = parse_review_response(invocation)
    tool_result = invocation.execution.tool_result
    expected_ref = f"tool_result:{tool_result.capability_call_id}:raw_response"
    assert sealed.candidate.raw_response_ref == expected_ref
    assert sealed.candidate.raw_response_digest != ""
    assert sealed.candidate.transport_trace.details["provider"] == "external_review"


@pytest.mark.parametrize(
    "overrides",
    [
        {"review_id": "rvw_foreign"},
        {"candidate_id": "cand_foreign"},
        {"candidate_sha": "sha_foreign"},
        {"bundle_digest": "forged_digest"},
    ],
)
def test_parser_rejects_foreign_review_or_bundle_binding(overrides):
    raw = _observable_machine_response()
    payload = json.loads(raw)
    payload.update(overrides)
    with pytest.raises(ReviewMachineResponseParseError, match="identity/bundle binding"):
        _parse(json.dumps(payload))


def test_parser_rejects_unknown_verdict():
    raw = _observable_machine_response()
    payload = json.loads(raw)
    payload["verdict"] = "SUPER_PASS"
    with pytest.raises(ReviewMachineResponseParseError, match="unknown verdict"):
        _parse(json.dumps(payload))


@pytest.mark.parametrize(
    "raw",
    [
        "   ",
        "{",
        '{"verdict":}',
        "null",
        "[]",
        '{"review_id":"rvw_parser","review_id":"rvw_parser"}',
    ],
)
def test_parser_rejects_empty_malformed_truncated_or_duplicate_json(raw):
    with pytest.raises(
        ReviewMachineResponseParseError,
        match="empty|strict JSON|JSON object",
    ):
        _parse(raw)


def test_empty_response_fails_at_observation_boundary():
    with pytest.raises(ValueError, match="no observable raw response"):
        parse_review_response(_invocation(""))


def test_parser_rejects_missing_required_field():
    raw = _observable_machine_response()
    payload = json.loads(raw)
    del payload["verdict"]
    with pytest.raises(ReviewMachineResponseParseError, match="missing or invalid field: verdict"):
        _parse(json.dumps(payload))


def test_parser_rejects_semantic_truncation():
    with pytest.raises(ReviewMachineResponseParseError):
        _parse('{"verdict":"PASS"}')


def test_parser_rejects_unsupported_required_semantic_and_provider_authority_fields():
    raw = _observable_machine_response()
    payload = json.loads(raw)
    payload["review_result_v1"] = {"forbidden": True}
    payload["raw_response_ref"] = "provider://raw"
    payload["raw_response_digest"] = "0" * 64
    payload["transport_trace"] = {"status": "CAPTURED"}
    payload["validation_state"] = "TRUSTED"
    with pytest.raises(ReviewMachineResponseParseError, match="unknown machine review fields"):
        _parse(json.dumps(payload))


def test_parser_rejects_provider_minted_finding_id():
    raw = _observable_machine_response()
    payload = json.loads(raw)
    payload["findings"][0]["finding_id"] = "provider://finding"
    with pytest.raises(ReviewMachineResponseParseError, match="finding_id"):
        _parse(json.dumps(payload))


@pytest.mark.parametrize("kind", ["REPOSITORY_FACT", "PROVIDER_OBSERVATION"])
def test_parser_rejects_unvalidated_evidence_kinds(kind):
    raw = _observable_machine_response()
    payload = json.loads(raw)
    payload["findings"][0]["evidence_bindings"] = [{"kind": kind, "ref": "anything"}]
    with pytest.raises(ReviewMachineResponseParseError, match="not yet admissible"):
        _parse(json.dumps(payload))


def test_parser_rejects_foreign_review_input_reference():
    raw = _observable_machine_response()
    payload = json.loads(raw)
    payload["findings"][0]["evidence_bindings"] = [
        {"kind": "REVIEW_INPUT", "ref": "evidence://foreign"}
    ]
    with pytest.raises(ReviewMachineResponseParseError, match="foreign REVIEW_INPUT"):
        _parse(json.dumps(payload))


def test_parser_rejects_foreign_raw_response_reference():
    raw = _observable_machine_response()
    payload = json.loads(raw)
    payload["findings"][0]["evidence_bindings"] = [
        {"kind": "RAW_RESPONSE", "ref": "tool_result:foreign:raw_response"}
    ]
    with pytest.raises(ReviewMachineResponseParseError, match="foreign RAW_RESPONSE"):
        _parse(json.dumps(payload))


def test_parser_rejects_invalid_and_boolean_confidence():
    raw = _observable_machine_response()
    payload = json.loads(raw)
    payload["findings"][0]["confidence"] = float("nan")
    with pytest.raises(ReviewMachineResponseParseError, match="confidence|strict JSON"):
        _parse(json.dumps(payload, allow_nan=True))

    payload["findings"][0]["confidence"] = True
    with pytest.raises(ReviewMachineResponseParseError, match="confidence"):
        _parse(json.dumps(payload))


def test_parser_rejects_required_change_dual_source():
    raw = _observable_machine_response()
    payload = json.loads(raw)
    payload["required_changes"] = ["Independent top-level change"]
    with pytest.raises(ReviewMachineResponseParseError, match="unknown machine review fields|required changes conflict"):
        _parse(json.dumps(payload))


def test_parser_rejects_mutated_invocation_or_transaction():
    invocation = _invocation(_observable_machine_response())
    object.__setattr__(invocation.transaction, "token", "mutated")
    with pytest.raises(ReviewMachineResponseParseError, match="invocation is not trusted"):
        parse_review_response(invocation)


def test_governance_rejects_foreign_invocation_for_parser_artifact():
    first = _invocation(_observable_machine_response())
    second, ledger = _governed_invocation(_observable_machine_response())
    sealed = parse_review_response(first)
    source_binding = register_test_candidate_sha_source(CurrentShaSource())
    service = ReviewGovernanceService(
        ledger,
        source_binding,
        get_core_review_parser_binding(),
    )
    record = service.record(second, sealed)
    assert record.admission == "REJECTED"
    assert any("raw_observation_invocation_mismatch" in reason for reason in record.rejection_reasons)


def test_governance_admits_parser_candidate_with_trusted_sha_source():
    invocation, ledger = _governed_invocation(_observable_machine_response())
    sealed = parse_review_response(invocation)
    source_binding = register_test_candidate_sha_source(CurrentShaSource())
    service = ReviewGovernanceService(
        ledger,
        source_binding,
        get_core_review_parser_binding(),
    )
    record = service.record(invocation, sealed)
    assert record.admission == "CANDIDATE_ADMITTED"
    assert record.rejection_reasons == ()


def test_governance_rejects_stale_candidate_with_trusted_sha_source():
    invocation, ledger = _governed_invocation(_observable_machine_response())
    sealed = parse_review_response(invocation)
    source_binding = register_test_candidate_sha_source(StaleShaSource())
    service = ReviewGovernanceService(
        ledger,
        source_binding,
        get_core_review_parser_binding(),
    )
    record = service.record(invocation, sealed)
    assert record.admission == "REJECTED"
    assert any("STALE_REVIEW" in reason for reason in record.rejection_reasons)


def test_mutated_candidate_artifact_is_no_longer_trusted():
    sealed = _parse(_observable_machine_response())
    object.__setattr__(sealed.candidate, "verdict", "PASS")
    assert is_trusted_candidate(sealed) is False
