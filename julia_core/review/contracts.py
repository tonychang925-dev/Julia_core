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
        if isinstance(self.transport_trace, ReviewTransportTrace):
            data["transport_trace"] = self.transport_trace.to_dict()
        return data


__all__ = [
    "IdentityIsolationViolation",
    "ReviewBundle",
    "ReviewDecisionCandidate",
    "ReviewErrorCode",
    "ReviewTransportTrace",
    "ReviewVerdict",
    "validate_identity_isolation",
]
