"""Review governance — exact-invocation truth + trusted composition.

Governance consumes:

    ReviewInvocationResult (exact CapabilityExecution + its exact transaction)
    + ReviewDecisionCandidate
    + a Core-owned ReviewGovernanceService (trusted composition)

P0-B: the transaction is DERIVED from invocation.transaction — there is no
separate caller-supplied transaction parameter. The ledger must own the exact
transaction (identity), and the invocation must be the ledger-minted one.

P0-C: the CandidateShaSource is bound ONCE at service composition time. Callers
cannot inject or replace it per governance call. No source bound -> stale
validation unavailable -> REJECT (fail closed).

A caller CANNOT self-report SUCCESS / correlation PASS / side-effect state /
stale / transport completion. Governance admission is:
    candidate admitted FOR GOVERNANCE CONSIDERATION
NOT final PASS authority.
"""

from __future__ import annotations

import time as _time
from dataclasses import asdict, dataclass, field
from typing import Any

from julia_core.review.contracts import ReviewDecisionCandidate, ReviewTransportTrace
from julia_core.review.invocation import ReviewInvocationResult
from julia_core.review.transaction import (
    ReviewTransaction,
    ReviewTransactionLedger,
    ReviewUntrustedTransactionError,
)
from julia_core.review.validation import (
    CandidateShaSource,
    CandidateShaSourceUnavailable,
    assert_not_stale,
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


class ReviewGovernanceService:
    """Core-owned governance boundary with trusted composition.

    Binds the ledger and the candidate-SHA source ONCE at construction (frozen
    slots — callers cannot replace them). ``record()`` derives the transaction
    from the exact invocation and rejects any invocation/transaction that is
    not ledger-minted and identical.
    """

    __slots__ = ("_ledger", "_candidate_sha_source", "_frozen")

    def __init__(
        self,
        ledger: ReviewTransactionLedger,
        candidate_sha_source: CandidateShaSource | None = None,
    ):
        if not isinstance(ledger, ReviewTransactionLedger):
            raise TypeError("ReviewGovernanceService requires a ReviewTransactionLedger")
        object.__setattr__(self, "_ledger", ledger)
        object.__setattr__(self, "_candidate_sha_source", candidate_sha_source)
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name, value):
        """Composition lock: after construction, source/ledger cannot be replaced."""
        if getattr(self, "_frozen", False):
            raise AttributeError(
                f"ReviewGovernanceService is composition-frozen; cannot set {name!r}"
            )
        object.__setattr__(self, name, value)

    @property
    def candidate_sha_source(self) -> CandidateShaSource | None:
        """Read-only: callers can never replace the bound source."""
        return self._candidate_sha_source

    def record(
        self,
        invocation: ReviewInvocationResult,
        candidate: ReviewDecisionCandidate,
        *,
        record_id: str | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> ReviewGovernanceRecord:
        """Build the governance record from the EXACT invocation transaction.

        Fail-closed invariants:
          - transaction derived internally from invocation.transaction
          - ledger owns the exact transaction object (P1-E)
          - outcome/side-effect derive from the typed ToolResult
          - correlation validated against the sealed snapshot (owned digest)
          - transport completion from real execution status
          - stale validation uses the composition-bound source (P0-C); absent
            source -> fail closed
          - raw response digest must bind to the trusted execution observation
        """
        transaction = invocation.transaction
        if not isinstance(transaction, ReviewTransaction):
            raise ReviewUntrustedTransactionError(
                "invocation transaction is not a ReviewTransaction"
            )
        if not self._ledger.owns_transaction(transaction):
            raise ReviewUntrustedTransactionError(
                "transaction is not owned by the exact governance ledger; "
                "handcrafted/spread/copied transactions are rejected"
            )

        outcome_status = _tool_status_of(invocation)
        side_effect_state = _side_effect_of(invocation)

        reasons: list[str] = []

        correlation_errors = validate_review_correlation(transaction.snapshot, candidate)
        reasons.extend(correlation_errors)

        transport_errors = validate_transport_completion(candidate, outcome_status)
        reasons.extend(transport_errors)

        # Stale check: composition-bound source ONLY. Absent -> fail closed.
        if not reasons:
            source = self._candidate_sha_source
            if source is None:
                reasons.append("stale_validation_unavailable:no trusted candidate SHA source")
            else:
                try:
                    assert_not_stale(transaction.snapshot, source)
                except CandidateShaSourceUnavailable as exc:
                    reasons.append(f"stale_validation_unavailable:{exc}")
                except Exception as exc:
                    reasons.append(str(exc))

        # Raw response auditability: parsed PASS without auditable raw truth is
        # not an admitted candidate.
        expected_digest = _candidate_expected_raw_digest(invocation)
        if not raw_response_digest_matches(candidate, expected_digest):
            reasons.append("raw_response_digest_unbound")

        admitted = not reasons

        # Record the real outcome truth for duplicate/retry control.
        self._ledger.record_outcome(
            transaction,
            outcome_status=outcome_status,
            side_effect_state=side_effect_state,
        )

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
            transport_trace=candidate.transport_trace,
            provenance=dict(provenance or {}),
        )


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


__all__ = ["ReviewGovernanceRecord", "ReviewGovernanceService"]
