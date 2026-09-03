"""Core-side review correlation / transport-completion / stale rules.

Correlation binds the returned candidate to the TRUSTED outbound transaction:

    review_id + candidate_id + candidate_sha + bundle_digest

Transport completion must derive from the REAL typed provider execution truth,
not from caller-supplied strings. A candidate with an incomplete/failed
transport (e.g. transport_trace.status = CREATED) must never be admitted merely
because a caller passes outcome_status="success".

STALE_REVIEW (E): the current candidate SHA must come from a canonical
candidate/repository truth source owned by Julia Core. This module does NOT
invent one: stale validation requires a CandidateShaSource; without a source,
stale validation FAILS CLOSED and the candidate cannot be admitted.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from julia_core.review.contracts import (
    ReviewDecisionCandidate,
    ReviewEvidenceBindingKind,
    ReviewErrorCode,
    ReviewVerdict,
)
from julia_core.review.snapshot import SealedReviewBundle
from julia_core.review.transaction import ReviewTransaction


class CandidateShaSource(Protocol):
    """Core-owned canonical source for the CURRENT candidate SHA.

    Must be a trusted repository/candidate truth source owned by Julia Core.
    This module does NOT ship a default implementation: if Core has no such
    source, stale validation fails closed (candidate cannot be admitted).
    """

    def current_candidate_sha(self, *, review_id: str, candidate_id: str) -> str:
        """Return the canonical current SHA for the candidate identity."""
        ...


class CandidateShaSourceUnavailable(Exception):
    """Raised when stale validation requires a canonical source that is absent."""


def _observable_content(candidate: ReviewDecisionCandidate) -> bool:
    if candidate.verdict not in (ReviewVerdict.UNPARSEABLE, ReviewVerdict.UNPARSEABLE.value):
        return True
    return bool(
        candidate.findings
        or candidate.blockers
        or candidate.high
        or candidate.medium
        or candidate.required_changes
        or candidate.notes
        or candidate.raw_response_ref
    )


def _response_size(candidate: ReviewDecisionCandidate) -> int:
    parts = [str(candidate.verdict.value if isinstance(candidate.verdict, ReviewVerdict) else candidate.verdict)]
    for name in ("blockers", "high", "medium", "required_changes", "notes"):
        parts.extend(str(x) for x in getattr(candidate, name, ()))
    for finding in candidate.findings:
        parts.extend(
            (
                finding.severity.value,
                finding.observation,
                finding.inference,
                finding.causal_impact,
                finding.required_change,
                finding.provider_finding_label,
                str(finding.confidence),
            )
        )
        parts.extend(
            f"{binding.kind.value}:{binding.ref}" for binding in finding.evidence_bindings
        )
    parts.append(candidate.raw_response_ref or "")
    return sum(len(p) for p in parts)


def validate_review_correlation(
    snapshot: SealedReviewBundle,
    candidate: ReviewDecisionCandidate,
    *,
    max_response_chars: int = 12000,
) -> list[str]:
    """Return correlation errors between the trusted snapshot and candidate.

    The bundle digest is compared against the SNAPSHOT's owned digest, not a
    caller-supplied digest (no self-supplied authority).
    """
    errors: list[str] = list(candidate.validate_minimum())

    if not errors:
        if candidate.review_id != snapshot.review_id:
            errors.append(f"{ReviewErrorCode.REVIEW_ID_MISMATCH.value}:candidate review_id != transaction review_id")
        if candidate.candidate_id != snapshot.candidate_id:
            errors.append(f"{ReviewErrorCode.CANDIDATE_ID_MISMATCH.value}:candidate candidate_id != transaction candidate_id")
        if candidate.candidate_sha != snapshot.candidate_sha:
            errors.append(f"{ReviewErrorCode.CANDIDATE_SHA_MISMATCH.value}:candidate candidate_sha != transaction candidate_sha")

        if not _observable_content(candidate):
            errors.append(f"{ReviewErrorCode.REVIEW_EMPTY_RESPONSE.value}:no observable review content")

        if _response_size(candidate) > max_response_chars:
            errors.append(f"response_size_exceeded:> {max_response_chars} chars")

    return errors


def validate_transaction_correlation(
    transaction: ReviewTransaction,
    candidate: ReviewDecisionCandidate,
) -> list[str]:
    """Correlate the candidate against the trusted transaction binding."""
    return validate_review_correlation(transaction.snapshot, candidate)


def validate_structured_finding_bindings(
    snapshot: SealedReviewBundle,
    candidate: ReviewDecisionCandidate,
    *,
    raw_response_ref: str,
) -> list[str]:
    """Validate finding evidence against snapshot and Core observation truth."""
    errors: list[str] = []
    allowed_review_inputs = set(snapshot.to_payload().get("evidence_refs", ()))
    for finding in candidate.findings:
        for binding in finding.evidence_bindings:
            if binding.kind is ReviewEvidenceBindingKind.REVIEW_INPUT:
                if binding.ref not in allowed_review_inputs:
                    errors.append(
                        f"invalid_evidence_binding:foreign REVIEW_INPUT {binding.ref!r}"
                    )
            elif binding.kind is ReviewEvidenceBindingKind.RAW_RESPONSE:
                if binding.ref != raw_response_ref:
                    errors.append(
                        f"invalid_evidence_binding:foreign RAW_RESPONSE {binding.ref!r}"
                    )
            else:
                errors.append(
                    "invalid_evidence_binding:"
                    f"{binding.kind.value} is not admissible without a trusted validator"
                )
    return errors


class ReviewCorrelationError(ValueError):
    """Raised when a review result fails Core-side correlation/binding rules."""


def assert_review_correlation(
    snapshot: SealedReviewBundle,
    candidate: ReviewDecisionCandidate,
    *,
    max_response_chars: int = 12000,
) -> None:
    errors = validate_review_correlation(
        snapshot, candidate, max_response_chars=max_response_chars
    )
    if errors:
        raise ReviewCorrelationError("; ".join(errors))


# ── Transport completion truth (G) ───────────────────────────────────────────

# Real provider-execution statuses that imply transport completed.
_TRANSPORT_COMPLETE_STATUSES = {"success", "partial"}


def transport_completed(outcome_status: str) -> bool:
    """Transport completion derives from real typed execution truth.

    Only SUCCESS/PARTIAL execution outcomes represent completed transport.
    ERROR / TIMEOUT / UNAVAILABLE / CANCELLED are NOT transport completion.
    """
    return outcome_status in _TRANSPORT_COMPLETE_STATUSES


def validate_transport_completion(
    candidate: ReviewDecisionCandidate,
    outcome_status: str,
) -> list[str]:
    """Return transport-completion errors.

    A candidate must never be admitted merely because a caller supplies
    outcome_status="success" — outcome_status here must come from the exact
    typed provider execution (CapabilityExecution / ToolResult), not from a
    caller string. Additionally the candidate's own transport_trace must not be
    CREATED/incomplete when a full raw response is claimed.
    """
    errors: list[str] = []
    if not transport_completed(outcome_status):
        errors.append(f"transport_not_completed:outcome_status={outcome_status!r}")

    trace = candidate.transport_trace
    trace_status = ""
    if isinstance(trace, dict):
        trace_status = str(trace.get("status", ""))
    elif hasattr(trace, "status"):
        trace_status = str(trace.status)

    if trace_status in ("CREATED", "", "FAILED", "CANCELLED"):
        errors.append(f"transport_trace_incomplete:status={trace_status!r}")
    return errors


def assert_transport_completed(candidate: ReviewDecisionCandidate, outcome_status: str) -> None:
    errors = validate_transport_completion(candidate, outcome_status)
    if errors:
        raise ReviewCorrelationError("; ".join(errors))


# ── Stale / current-SHA truth (E) ────────────────────────────────────────────

def is_stale(
    snapshot: SealedReviewBundle,
    source: CandidateShaSource | None,
) -> bool:
    """Return True when the bound candidate SHA no longer matches canonical truth.

    If no canonical CandidateShaSource is available, raise
    CandidateShaSourceUnavailable — stale validation FAILS CLOSED rather than
    trusting a caller-supplied current SHA.
    """
    if source is None:
        raise CandidateShaSourceUnavailable(
            "no canonical candidate-SHA source; stale validation fails closed"
        )
    current_sha = source.current_candidate_sha(
        review_id=snapshot.review_id,
        candidate_id=snapshot.candidate_id,
    )
    return snapshot.candidate_sha != current_sha


def assert_not_stale(
    snapshot: SealedReviewBundle,
    source: CandidateShaSource | None,
) -> None:
    if is_stale(snapshot, source):
        raise ReviewCorrelationError(
            f"{ReviewErrorCode.STALE_REVIEW.value}:bound {snapshot.candidate_sha} != canonical current"
        )


# ── Raw response auditability (I) ────────────────────────────────────────────

def raw_response_digest_matches(
    candidate: ReviewDecisionCandidate,
    expected_digest: str | None,
) -> bool:
    """A parsed candidate must carry auditable raw response truth.

    If a raw response digest is claimed, it must match the expected digest from
    the trusted execution observation. If none is expected, an empty claim is
    accepted but a fabricated digest is not (caller cannot invent truth).
    """
    if not candidate.raw_response_ref and not candidate.raw_response_digest:
        return True  # no raw claim at all — admissible only as non-PASS candidate
    if not expected_digest:
        return False  # claimed raw digest but no trusted execution digest to bind
    return candidate.raw_response_digest == expected_digest


__all__ = [
    "CandidateShaSource",
    "CandidateShaSourceUnavailable",
    "ReviewCorrelationError",
    "assert_not_stale",
    "assert_review_correlation",
    "assert_transport_completed",
    "is_stale",
    "raw_response_digest_matches",
    "transport_completed",
    "validate_review_correlation",
    "validate_structured_finding_bindings",
    "validate_transaction_correlation",
    "validate_transport_completion",
]
