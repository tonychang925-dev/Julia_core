"""Review governance — derives from EXACT execution truth.

Governance consumes:

    ReviewInvocationResult (exact CapabilityExecution)
    + trusted ReviewTransaction (sealed snapshot / binding)
    + ReviewDecisionCandidate
    + canonical current-candidate truth (CandidateShaSource)

and internally derives outcome status, side-effect state, correlation PASS,
transport completion, stale status, and raw-response digest binding.

A caller CANNOT self-report SUCCESS / correlation PASS / side-effect state /
stale / transport completion. Governance admission is:
    candidate admitted FOR GOVERNANCE CONSIDERATION
NOT final PASS authority.
"""

from __future__ import annotations

import time as _time
from dataclasses import asdict, dataclass, field
from typing import Any

from julia_core.review.contracts import (
    ReviewDecisionCandidate,
    ReviewTransportTrace,
)
from julia_core.review.invocation import ReviewInvocationResult
from julia_core.review.snapshot import SealedReviewBundle
from julia_core.review.transaction import ReviewTransaction, ReviewTransactionLedger
from julia_core.review.validation import (
    CandidateShaSource,
    CandidateShaSourceUnavailable,
    assert_transport_completed,
    raw_response_digest_matches,
    validate_review_correlation,
    validate_transport_completion,
)


@dataclass(frozen=True, slots=True)
class ReviewGovernanceRecord:
    """One immutable audit record for a review transaction."""

    record_id: str
    review_id: str
    candidate_id: str
    candidate_sha: str
    bundle_digest: str
    transaction_id: str
    outcome_status: str
    side_effect_state: str
    admission: str          # "CANDIDATE_ADMITTED" | "REJECTED"
    rejection_reasons: tuple[str, ...] = ()
    raw_response_ref: str = ""
    raw_response_digest: str = ""
    transport_trace: ReviewTransportTrace | dict[str, Any] = field(default_factory=ReviewTransportTrace)
    recorded_at: str = field(default_factory=lambda: _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()))
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if isinstance(self.transport_trace, ReviewTransportTrace):
            data["transport_trace"] = self.transport_trace.to_dict()
        return data


def _tool_status_of(invocation: ReviewInvocationResult) -> str:
    """Exact outcome status from the typed execution, never a caller string."""
    result = invocation.execution.tool_result
    if result is None:
        return "denied"
    return result.status.value if hasattr(result.status, "value") else str(result.status)


def _side_effect_of(invocation: ReviewInvocationResult) -> str:
    result = invocation.execution.tool_result
    if result is None:
        return "none"
    return result.side_effect_state.value if hasattr(result.side_effect_state, "value") else str(result.side_effect_state)


def _candidate_expected_raw_digest(invocation: ReviewInvocationResult) -> str | None:
    """Derive the expected raw-response digest from the real provider output."""
    result = invocation.execution.tool_result
    if result is None:
        return None
    structured = result.structured_output or {}
    digest = structured.get("raw_response_digest")
    return digest if isinstance(digest, str) and digest else None


def build_governance_record(
    *,
    invocation: ReviewInvocationResult,
    transaction: ReviewTransaction,
    candidate: ReviewDecisionCandidate,
    ledger: ReviewTransactionLedger,
    candidate_sha_source: CandidateShaSource | None,
    record_id: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> ReviewGovernanceRecord:
    """Build the governance record from exact execution truth only.

    Fail-closed invariants:
      - outcome status / side effect derive from the typed ToolResult
      - correlation validated against the sealed snapshot (owned digest)
      - transport completion validated against the real execution status
      - stale validation requires a canonical CandidateShaSource (fail closed
        otherwise — no caller-supplied current SHA)
      - raw response digest must bind to the trusted execution observation
    """
    outcome_status = _tool_status_of(invocation)
    side_effect_state = _side_effect_of(invocation)

    reasons: list[str] = []

    correlation_errors = validate_review_correlation(transaction.snapshot, candidate)
    reasons.extend(correlation_errors)

    transport_errors = validate_transport_completion(candidate, outcome_status)
    reasons.extend(transport_errors)

    # Stale check: canonical source required. If absent -> fail closed.
    if not reasons:
        try:
            assert_not_stale_candidate(transaction.snapshot, candidate_sha_source)
        except CandidateShaSourceUnavailable as exc:
            reasons.append(f"stale_validation_unavailable:{exc}")
        except Exception as exc:
            reasons.append(str(exc))

    # Raw response auditability: parsed PASS without auditable raw truth is not
    # an admitted candidate.
    expected_digest = _candidate_expected_raw_digest(invocation)
    if not raw_response_digest_matches(candidate, expected_digest):
        reasons.append("raw_response_digest_unbound")

    admitted = not reasons

    # Record the real outcome truth in the ledger for duplicate/retry control.
    ledger.record_outcome(
        transaction,
        outcome_status=outcome_status,
        side_effect_state=side_effect_state,
    )

    trace = candidate.transport_trace
    return ReviewGovernanceRecord(
        record_id=record_id or f"rvw_rec_{_time.time_ns()}",
        review_id=transaction.review_id,
        candidate_id=transaction.candidate_id,
        candidate_sha=transaction.candidate_sha,
        bundle_digest=transaction.bundle_digest,
        transaction_id=transaction.transaction_id,
        outcome_status=outcome_status,
        side_effect_state=side_effect_state,
        admission="CANDIDATE_ADMITTED" if admitted else "REJECTED",
        rejection_reasons=tuple(reasons),
        raw_response_ref=candidate.raw_response_ref or "",
        raw_response_digest=candidate.raw_response_digest or "",
        transport_trace=trace,
        provenance=dict(provenance or {}),
    )


def assert_not_stale_candidate(
    snapshot: SealedReviewBundle,
    source: CandidateShaSource | None,
) -> None:
    from julia_core.review.validation import assert_not_stale
    assert_not_stale(snapshot, source)


__all__ = ["ReviewGovernanceRecord", "build_governance_record"]
