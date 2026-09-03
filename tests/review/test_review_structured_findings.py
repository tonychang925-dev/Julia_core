from __future__ import annotations

import copy
import json

import pytest

from julia_core.review.candidate_artifact import candidate_fingerprint
from julia_core.review.contracts import (
    ADMISSIBLE_REVIEW_EVIDENCE_BINDING_KINDS,
    ReviewDecisionCandidate,
    ReviewEvidenceBinding,
    ReviewEvidenceBindingKind,
    ReviewFindingCandidate,
    ReviewFindingSeverity,
)


def _candidate(**overrides):
    values = dict(
        review_id="rvw_1",
        candidate_id="cand_1",
        candidate_sha="sha_1",
        findings=(
            ReviewFindingCandidate(
                severity="BLOCKER",
                observation="Unsafe mutation",
                inference="Concurrent request can mutate provider payload",
                causal_impact="Authorization may be bypassed",
                evidence_bindings=(
                    ReviewEvidenceBinding(
                        kind=ReviewEvidenceBindingKind.REVIEW_INPUT,
                        ref="evidence://changed-file",
                    ),
                    ReviewEvidenceBinding(
                        kind=ReviewEvidenceBindingKind.RAW_RESPONSE,
                        ref="tool_result:call-1:raw_response",
                    ),
                ),
                confidence=0.91,
                required_change="Deep-copy provider-visible arguments",
                provider_finding_label="F1",
            ),
        ),
        notes=("Structured review follows the accepted contract",),
    )
    values.update(overrides)
    return ReviewDecisionCandidate(**values)


def test_structured_findings_are_canonical_and_project_legacy_severity():
    candidate = _candidate()
    assert candidate.findings[0].severity is ReviewFindingSeverity.BLOCKER
    assert candidate.blockers == ("Unsafe mutation",)
    assert candidate.high == ()
    assert candidate.medium == ()
    assert candidate.required_changes == (
        "Deep-copy provider-visible arguments",
    )


def test_multiple_severity_findings_project_without_dual_authority():
    findings = (
        ReviewFindingCandidate(severity="MEDIUM", observation="Naming is unclear"),
        ReviewFindingCandidate(severity="HIGH", observation="Timeout loses state"),
        ReviewFindingCandidate(severity="BLOCKER", observation="Auth occurs after execution"),
    )
    candidate = _candidate(findings=findings)
    assert candidate.medium == ("Naming is unclear",)
    assert candidate.high == ("Timeout loses state",)
    assert candidate.blockers == ("Auth occurs after execution",)


def test_observation_only_and_optional_semantics_are_representable():
    finding = ReviewFindingCandidate(severity="HIGH", observation="Exact behavior unclear")
    assert finding.inference == ""
    assert finding.causal_impact == ""
    assert finding.evidence_bindings == ()
    assert finding.confidence is None
    assert finding.required_change == ""


def test_structured_findings_reject_legacy_severity_dual_source():
    with pytest.raises(ValueError, match="structured findings conflict"):
        _candidate(blockers=("Legacy blocker",))


def test_structured_required_change_rejects_top_level_dual_source():
    with pytest.raises(ValueError, match="required changes conflict"):
        _candidate(required_changes=("Independent top-level change",))


def test_legacy_required_changes_remain_compatible_without_findings():
    candidate = ReviewDecisionCandidate(
        review_id="rvw_1",
        candidate_id="cand_1",
        candidate_sha="sha_1",
        required_changes=("Fix legacy path",),
    )
    assert candidate.findings == ()
    assert candidate.required_changes == ("Fix legacy path",)


def test_provider_cannot_supply_canonical_finding_identity():
    with pytest.raises(TypeError):
        ReviewFindingCandidate(
            finding_id="provider-id",
            severity="HIGH",
            observation="Provider identity",
        )


def test_canonical_identity_binds_review_and_candidate_identity():
    first = _candidate()
    second = _candidate(candidate_sha="sha_2")
    assert first.findings[0].finding_id != second.findings[0].finding_id


def test_duplicate_provider_labels_do_not_control_identity_or_override_findings():
    candidate = _candidate(
        findings=(
            ReviewFindingCandidate(
                severity="HIGH", observation="First finding", provider_finding_label="same"
            ),
            ReviewFindingCandidate(
                severity="MEDIUM", observation="Second finding", provider_finding_label="same"
            ),
        )
    )
    assert candidate.findings[0].finding_id != candidate.findings[1].finding_id
    assert candidate.high == ("First finding",)
    assert candidate.medium == ("Second finding",)


def test_duplicate_finding_semantics_fail_closed():
    with pytest.raises(ValueError, match="duplicate finding semantics"):
        _candidate(
            findings=(
                ReviewFindingCandidate(severity="HIGH", observation="Same"),
                ReviewFindingCandidate(severity="HIGH", observation="Same"),
            )
        )


@pytest.mark.parametrize("kind", ["REPOSITORY_FACT", "PROVIDER_OBSERVATION"])
def test_unvalidated_evidence_kinds_are_not_admissible(kind):
    with pytest.raises(ValueError, match="not yet admissible"):
        ReviewEvidenceBinding(kind=kind, ref="anything")
    assert ReviewEvidenceBindingKind(kind) not in ADMISSIBLE_REVIEW_EVIDENCE_BINDING_KINDS


@pytest.mark.parametrize("confidence", [float("nan"), float("inf"), -float("inf"), -0.1, 1.1])
def test_invalid_confidence_fails_closed(confidence):
    with pytest.raises(ValueError, match="confidence"):
        ReviewFindingCandidate(
            severity="HIGH", observation="Confidence", confidence=confidence
        )


def test_confidence_is_finite_closed_interval_and_canonical():
    integral = _candidate(
        findings=(ReviewFindingCandidate(severity="HIGH", observation="x", confidence=1),)
    )
    floating = _candidate(
        findings=(ReviewFindingCandidate(severity="HIGH", observation="x", confidence=1.0),)
    )
    negative_zero = _candidate(
        findings=(ReviewFindingCandidate(severity="HIGH", observation="x", confidence=-0.0),)
    )
    zero = _candidate(
        findings=(ReviewFindingCandidate(severity="HIGH", observation="x", confidence=0),)
    )
    assert integral.findings[0].confidence == 1.0
    assert candidate_fingerprint(integral) == candidate_fingerprint(floating)
    assert str(negative_zero.findings[0].confidence) == "0.0"
    assert candidate_fingerprint(negative_zero) == candidate_fingerprint(zero)


def test_invalid_severity_and_unknown_finding_fields_fail_closed():
    with pytest.raises(ValueError):
        ReviewFindingCandidate(severity="CRITICAL", observation="x")
    with pytest.raises(TypeError):
        ReviewFindingCandidate(severity="HIGH", observation="x", evidence="ambiguous")


def test_unicode_and_canonical_serialization_are_lossless():
    candidate = _candidate(
        findings=(
            ReviewFindingCandidate(
                severity="MEDIUM",
                observation="中文审查观察 α",
                inference="推断",
                causal_impact="影响",
                required_change="修正",
            ),
        )
    )
    data = candidate.to_dict()
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    decoded = json.loads(encoded)
    assert decoded["findings"][0]["observation"] == "中文审查观察 α"
    assert decoded["findings"][0]["inference"] == "推断"
    assert decoded["findings"][0]["causal_impact"] == "影响"
    assert decoded["findings"][0]["required_change"] == "修正"


def test_structured_findings_are_immutable_and_not_aliased():
    candidate = _candidate()
    data = candidate.to_dict()
    data["findings"][0]["observation"] = "MUTATED"
    data["findings"][0]["evidence_bindings"][0]["ref"] = "foreign://ref"
    assert candidate.findings[0].observation == "Unsafe mutation"
    assert candidate.findings[0].evidence_bindings[0].ref == "evidence://changed-file"
    with pytest.raises(Exception):
        candidate.findings[0].observation = "MUTATED"


def test_deep_copy_cannot_change_authority_semantics():
    candidate = _candidate()
    duplicate = copy.deepcopy(candidate)
    assert duplicate == candidate
    assert duplicate.findings[0].finding_id == candidate.findings[0].finding_id
    with pytest.raises(Exception):
        duplicate.findings[0].severity = "HIGH"


def test_provider_confidence_is_semantic_not_trust():
    candidate = _candidate()
    assert candidate.validation_state == "CANDIDATE"
    assert candidate.findings[0].confidence == 0.91


def test_provider_evidence_reference_cannot_mint_repository_fact():
    with pytest.raises(ValueError, match="REPOSITORY_FACT"):
        ReviewFindingCandidate(
            severity="HIGH",
            observation="x",
            evidence_bindings=(
                ReviewEvidenceBinding(kind="REPOSITORY_FACT", ref="repo://fact"),
            ),
        )
