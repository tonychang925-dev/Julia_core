"""External Code Review semantic contracts.

Canonical source: Julia Core × ChatGPT Web — Code Review Bridge Architecture
v1.1.2 CANONICAL FROZEN 2026-08-28.

Julia Core owns the SEMANTIC capability contract: review identity, candidate
binding, ReviewBundle schema, ReviewDecisionCandidate schema, validation,
correlation, digest rules. It does NOT own browser session authority, DOM
selectors, ChatGPT URLs, extension nonces, or transport internals — those
belong to the provider / transport layer.

This module deliberately excludes persona, relationship, continuity restore,
self-model and private-memory material. Identity isolation is enforced.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ReviewVerdict(str, Enum):
    """Candidate review verdict space (raw, unadmitted)."""

    PASS = "PASS"
    REWORK = "REWORK"
    HOLD = "HOLD"
    UNPARSEABLE = "UNPARSEABLE"


class ReviewErrorCode(str, Enum):
    """Core-side semantic review error taxonomy.

    Transport-internal failures (DOM binding, tab closed, etc.) are reported by
    the provider as ProviderExecutionOutcome with exact error.code; the Core
    taxonomy below covers review correlation / contract / admission errors.
    """

    BUNDLE_SCHEMA_INVALID = "BUNDLE_SCHEMA_INVALID"
    IDENTITY_PROJECTION_FORBIDDEN = "IDENTITY_PROJECTION_FORBIDDEN"
    REPOSITORY_NOT_FOUND = "REPOSITORY_NOT_FOUND"
    GIT_STATE_INVALID = "GIT_STATE_INVALID"
    REVIEW_EMPTY_RESPONSE = "REVIEW_EMPTY_RESPONSE"
    STALE_REVIEW = "STALE_REVIEW"
    REVIEW_DECISION_REJECTED = "REVIEW_DECISION_REJECTED"
    REVIEW_ID_MISMATCH = "REVIEW_ID_MISMATCH"
    CANDIDATE_ID_MISMATCH = "CANDIDATE_ID_MISMATCH"
    CANDIDATE_SHA_MISMATCH = "CANDIDATE_SHA_MISMATCH"
    BUNDLE_DIGEST_MISMATCH = "BUNDLE_DIGEST_MISMATCH"
    REVIEW_FINDING_INVALID = "REVIEW_FINDING_INVALID"


class IdentityIsolationViolation(ValueError):
    """Raised when a review payload includes identity/continuity/private material.

    Phase-1 review is engineering-only. No Julia or Golden Mira identity
    material may be inserted merely to make Code Review work.
    """


_FORBIDDEN_IDENTITY_KEYS = {
    "persona",
    "persona_projection",
    "julia_persona",
    "golden_mira_persona",
    "relationship_projection",
    "relationship_memory",
    "continuity_restore",
    "continuity_checkpoint",
    "private_identity_memory",
    "private_diary",
    "self_model_projection",
    "formation_history",
}


def validate_identity_isolation(payload: dict[str, Any]) -> None:
    """Enforce Phase-1 identity isolation.

    Only DISABLED flags are allowed for identity-related keys. Any other
    identity/continuity/private-memory material is rejected.
    """
    def walk(value: Any, path: str = "") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                key_l = str(key).lower()
                next_path = f"{path}.{key}" if path else str(key)
                if key_l in _FORBIDDEN_IDENTITY_KEYS:
                    if child != "DISABLED" and not (
                        isinstance(child, dict) and all(v == "DISABLED" for v in child.values())
                    ):
                        raise IdentityIsolationViolation(next_path)
                walk(child, next_path)
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(payload)


@dataclass(frozen=True, slots=True)
class ReviewTransportTrace:
    """Opaque transport execution trace returned upward for audit only.

    This is an audit observation, NOT browser authority input. The provider may
    record transport-local truth (status transitions, timestamps, error codes)
    here; Core never reads browser/session primitives from it as authority.
    """

    source: str = "manual"
    status: str = "CREATED"
    sent_at: str = ""
    response_started_at: str = ""
    response_completed_at: str = ""
    error_code: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReviewFindingSeverity(str, Enum):
    """Canonical structured finding severity."""

    BLOCKER = "BLOCKER"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"


class ReviewEvidenceBindingKind(str, Enum):
    """Typed review evidence taxonomy.

    Representability does not imply admissibility. R3 admits only review-input
    and Core-owned raw-response references; repository facts and provider
    observations require a separately governed validator.
    """

    REVIEW_INPUT = "REVIEW_INPUT"
    REPOSITORY_FACT = "REPOSITORY_FACT"
    PROVIDER_OBSERVATION = "PROVIDER_OBSERVATION"
    RAW_RESPONSE = "RAW_RESPONSE"


ADMISSIBLE_REVIEW_EVIDENCE_BINDING_KINDS = frozenset(
    {
        ReviewEvidenceBindingKind.REVIEW_INPUT,
        ReviewEvidenceBindingKind.RAW_RESPONSE,
    }
)


def _finding_semantics(
    severity: ReviewFindingSeverity,
    observation: str,
    inference: str,
    causal_impact: str,
    evidence_bindings: tuple["ReviewEvidenceBinding", ...],
    confidence: float | None,
    required_change: str,
) -> dict[str, Any]:
    return {
        "severity": severity.value,
        "observation": observation,
        "inference": inference,
        "causal_impact": causal_impact,
        "evidence_bindings": [
            {"kind": binding.kind.value, "ref": binding.ref}
            for binding in evidence_bindings
        ],
        "confidence": confidence,
        "required_change": required_change,
    }


def _canonical_finding_semantics(finding: ReviewFindingCandidate) -> str:
    return json.dumps(
        _finding_semantics(
            finding.severity,
            finding.observation,
            finding.inference,
            finding.causal_impact,
            finding.evidence_bindings,
            finding.confidence,
            finding.required_change,
        ),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


@dataclass(frozen=True, slots=True)
class ReviewEvidenceBinding:
    """One typed reference to an allowed evidence authority."""

    kind: ReviewEvidenceBindingKind | str
    ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", ReviewEvidenceBindingKind(self.kind))
        object.__setattr__(self, "ref", str(self.ref))
        if not self.ref.strip():
            raise ValueError(
                f"{ReviewErrorCode.REVIEW_FINDING_INVALID.value}: evidence ref is empty"
            )
        if self.kind not in ADMISSIBLE_REVIEW_EVIDENCE_BINDING_KINDS:
            raise ValueError(
                f"{ReviewErrorCode.REVIEW_FINDING_INVALID.value}: "
                f"{self.kind.value} is schema-defined but not yet admissible"
            )

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind.value, "ref": self.ref}


@dataclass(frozen=True, slots=True)
class ReviewFindingCandidate:
    """One Core-normalized structured finding.

    ``finding_id`` is Core-owned and cannot be supplied by provider output.
    ``provider_finding_label`` is non-authoritative reviewer metadata.
    Confidence is reviewer semantics, never source or transport trust.
    """

    severity: ReviewFindingSeverity | str
    observation: str
    inference: str = ""
    causal_impact: str = ""
    evidence_bindings: tuple[ReviewEvidenceBinding, ...] = ()
    confidence: float | None = None
    required_change: str = ""
    provider_finding_label: str = ""
    finding_id: str = field(init=False, default="")

    def __post_init__(self) -> None:
        object.__setattr__(self, "severity", ReviewFindingSeverity(self.severity))
        object.__setattr__(self, "observation", str(self.observation))
        object.__setattr__(self, "inference", str(self.inference))
        object.__setattr__(self, "causal_impact", str(self.causal_impact))
        object.__setattr__(self, "required_change", str(self.required_change))
        object.__setattr__(self, "provider_finding_label", str(self.provider_finding_label))

        if not self.observation.strip():
            raise ValueError(
                f"{ReviewErrorCode.REVIEW_FINDING_INVALID.value}: observation is empty"
            )
        if not isinstance(self.evidence_bindings, (list, tuple)):
            raise ValueError(
                f"{ReviewErrorCode.REVIEW_FINDING_INVALID.value}: "
                "evidence_bindings must be a sequence"
            )
        normalized = tuple(
            value
            if isinstance(value, ReviewEvidenceBinding)
            else ReviewEvidenceBinding(**value)
            for value in self.evidence_bindings
        )
        object.__setattr__(self, "evidence_bindings", normalized)

        confidence = self.confidence
        if confidence is not None:
            if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
                raise ValueError(
                    f"{ReviewErrorCode.REVIEW_FINDING_INVALID.value}: confidence must be numeric"
                )
            confidence = float(confidence)
            if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
                raise ValueError(
                    f"{ReviewErrorCode.REVIEW_FINDING_INVALID.value}: "
                    "confidence must be finite and in [0, 1]"
                )
            if confidence == 0.0:
                confidence = 0.0
            object.__setattr__(self, "confidence", confidence)

        semantics = _finding_semantics(
            self.severity,
            self.observation,
            self.inference,
            self.causal_impact,
            self.evidence_bindings,
            self.confidence,
            self.required_change,
        )
        canonical = json.dumps(
            semantics,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        object.__setattr__(
            self,
            "finding_id",
            f"finding_{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "severity": self.severity.value,
            "observation": self.observation,
            "inference": self.inference,
            "causal_impact": self.causal_impact,
            "evidence_bindings": [
                binding.to_dict() for binding in self.evidence_bindings
            ],
            "confidence": self.confidence,
            "required_change": self.required_change,
            "provider_finding_label": self.provider_finding_label,
        }


@dataclass(frozen=True, slots=True)
class ReviewBundle:
    """One governed engineering review request (semantic contract).

    Minimum required fields per canonical architecture:
      review_id, candidate_id, candidate_sha, repository, objective,
      changed_files, review_mode, questions.
    """

    contract_version: str = "review_bundle.v1"
    review_id: str = ""
    task_id: str = ""
    candidate_id: str = ""
    candidate_sha: str = ""
    repository: str = ""
    branch: str = ""
    review_mode: str = "architecture_and_code"
    objective: str = ""
    acceptance_criteria: tuple[str, ...] = ()
    changed_files: tuple[str, ...] = ()
    diff_summary: str = ""
    diff_blocks: tuple[dict[str, Any], ...] = ()
    tests: tuple[str, ...] = ()
    known_risks: tuple[str, ...] = ()
    architecture_constraints: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    limits: dict[str, Any] = field(default_factory=lambda: {
        "max_response_chars": 12000,
        "allow_scope_expansion": False,
    })
    identity_projection: dict[str, str] = field(default_factory=lambda: {
        "persona_projection": "DISABLED",
        "relationship_projection": "DISABLED",
        "continuity_restore": "DISABLED",
        "private_identity_memory": "DISABLED",
        "self_model_projection": "DISABLED",
    })

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name in ("review_id", "candidate_id", "candidate_sha", "repository", "objective", "review_mode"):
            if not str(getattr(self, name, "")).strip():
                errors.append(f"missing:{name}")
        if not self.changed_files:
            errors.append("missing:changed_files")
        if not self.questions:
            errors.append("missing:questions")
        try:
            validate_identity_isolation(self.to_dict())
        except IdentityIsolationViolation as exc:
            errors.append(f"identity_isolation:{exc}")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReviewDecisionCandidate:
    """Raw candidate decision returned by the external reviewer.

    This is a CANDIDATE, not admitted truth. Julia Core validates it
    (correlation + binding) before any later governance admission.
    """

    contract_version: str = "review_decision_candidate.v1"
    review_id: str = ""
    candidate_id: str = ""
    candidate_sha: str = ""
    source: str = "external_review"
    verdict: ReviewVerdict | str = ReviewVerdict.UNPARSEABLE
    findings: tuple[ReviewFindingCandidate, ...] = ()
    blockers: tuple[str, ...] = ()
    high: tuple[str, ...] = ()
    medium: tuple[str, ...] = ()
    required_changes: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    raw_response_ref: str = ""
    raw_response_digest: str = ""
    captured_at: str = ""
    transport_trace: ReviewTransportTrace | dict[str, Any] = field(default_factory=ReviewTransportTrace)
    validation_state: str = "CANDIDATE"

    def __post_init__(self) -> None:
        if not isinstance(self.findings, (list, tuple)):
            raise ValueError(
                f"{ReviewErrorCode.REVIEW_FINDING_INVALID.value}: findings must be a sequence"
            )
        findings = tuple(
            finding
            if isinstance(finding, ReviewFindingCandidate)
            else ReviewFindingCandidate(**finding)
            for finding in self.findings
        )

        legacy_severity_values = (
            (self.blockers, "blockers"),
            (self.high, "high"),
            (self.medium, "medium"),
        )
        if findings:
            conflicting = [name for values, name in legacy_severity_values if values]
            if conflicting:
                raise ValueError(
                    f"{ReviewErrorCode.REVIEW_FINDING_INVALID.value}: "
                    f"structured findings conflict with legacy {', '.join(conflicting)}"
                )
            if self.required_changes:
                raise ValueError(
                    f"{ReviewErrorCode.REVIEW_FINDING_INVALID.value}: "
                    "required changes conflict between findings and candidate"
                )

        seen_semantics: set[str] = set()
        normalized_findings: list[ReviewFindingCandidate] = []
        for index, finding in enumerate(findings):
            semantics = _canonical_finding_semantics(finding)
            if semantics in seen_semantics:
                raise ValueError(
                    f"{ReviewErrorCode.REVIEW_FINDING_INVALID.value}: duplicate finding semantics"
                )
            seen_semantics.add(semantics)
            identity = json.dumps(
                {
                    "review_id": self.review_id,
                    "candidate_id": self.candidate_id,
                    "candidate_sha": self.candidate_sha,
                    "finding_index": index,
                    "semantics": json.loads(semantics),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            object.__setattr__(
                finding,
                "finding_id",
                f"finding_{hashlib.sha256(identity.encode('utf-8')).hexdigest()}",
            )
            normalized_findings.append(finding)

        object.__setattr__(self, "findings", tuple(normalized_findings))
        if findings:
            object.__setattr__(
                self,
                "blockers",
                tuple(
                    finding.observation
                    for finding in normalized_findings
                    if finding.severity is ReviewFindingSeverity.BLOCKER
                ),
            )
            object.__setattr__(
                self,
                "high",
                tuple(
                    finding.observation
                    for finding in normalized_findings
                    if finding.severity is ReviewFindingSeverity.HIGH
                ),
            )
            object.__setattr__(
                self,
                "medium",
                tuple(
                    finding.observation
                    for finding in normalized_findings
                    if finding.severity is ReviewFindingSeverity.MEDIUM
                ),
            )
            object.__setattr__(
                self,
                "required_changes",
                tuple(
                    finding.required_change
                    for finding in normalized_findings
                    if finding.required_change
                ),
            )

    def validate_minimum(self) -> list[str]:
        errors: list[str] = []
        for name in ("review_id", "candidate_id", "candidate_sha"):
            if not str(getattr(self, name, "")).strip():
                errors.append(f"missing:{name}")
        verdict = self.verdict.value if isinstance(self.verdict, ReviewVerdict) else str(self.verdict)
        if verdict not in {v.value for v in ReviewVerdict}:
            errors.append("unknown:verdict")
        return errors

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if isinstance(self.verdict, ReviewVerdict):
            data["verdict"] = self.verdict.value
        data["findings"] = [finding.to_dict() for finding in self.findings]
        if isinstance(self.transport_trace, ReviewTransportTrace):
            data["transport_trace"] = self.transport_trace.to_dict()
        return data


__all__ = [
    "ADMISSIBLE_REVIEW_EVIDENCE_BINDING_KINDS",
    "IdentityIsolationViolation",
    "ReviewBundle",
    "ReviewDecisionCandidate",
    "ReviewEvidenceBinding",
    "ReviewEvidenceBindingKind",
    "ReviewFindingCandidate",
    "ReviewFindingSeverity",
    "ReviewErrorCode",
    "ReviewTransportTrace",
    "ReviewVerdict",
    "validate_identity_isolation",
]
