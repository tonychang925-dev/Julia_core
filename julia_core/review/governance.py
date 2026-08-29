"""Review governance / admission record.

Core-side audit record for a review transaction. This records the exact typed
execution truth (status, side-effect state, provider outcome) plus the
correlation result. It does NOT fabricate a verdict, does NOT promote a
transport failure to PASS, and does NOT own browser/transport authority.

Governance admission here is: the raw candidate either correlates to the
bound bundle (CANDIDATE admitted for later review) or is REJECTED with the
exact correlation errors. No semantic verdict authority is granted.
"""

from __future__ import annotations

import time as _time
from dataclasses import asdict, dataclass, field
from typing import Any

from julia_core.review.contracts import (
    ReviewBundle,
    ReviewDecisionCandidate,
    ReviewTransportTrace,
)
from julia_core.review.digest import compute_bundle_digest


@dataclass(frozen=True, slots=True)
class ReviewGovernanceRecord:
    """One immutable audit record for a review transaction."""

    record_id: str
    review_id: str
    candidate_id: str
    candidate_sha: str
    bundle_digest: str
    outcome_status: str
    side_effect_state: str
    admission: str          # "CANDIDATE_ADMITTED" | "REJECTED"
    rejection_reasons: tuple[str, ...] = ()
    source: str = "external_review"
    transport_trace: ReviewTransportTrace | dict[str, Any] = field(default_factory=ReviewTransportTrace)
    recorded_at: str = field(default_factory=lambda: _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()))
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if isinstance(self.transport_trace, ReviewTransportTrace):
            data["transport_trace"] = self.transport_trace.to_dict()
        return data


def build_governance_record(
    *,
    bundle: ReviewBundle,
    candidate: ReviewDecisionCandidate,
    outcome_status: str,
    side_effect_state: str,
    correlation_errors: list[str] | tuple[str, ...] = (),
    record_id: str | None = None,
    transport_trace: ReviewTransportTrace | dict[str, Any] | None = None,
    provenance: dict[str, Any] | None = None,
) -> ReviewGovernanceRecord:
    """Build the governance record from exact execution truth.

    Admission is CANDIDATE_ADMITTED only when correlation errors are empty AND
    outcome status is SUCCESS/PARTIAL. Anything else is REJECTED with reasons.
    This never turns an ERROR/TIMEOUT/UNAVAILABLE into a review.
    """
    admitted = (
        not correlation_errors
        and outcome_status in ("success", "partial")
    )
    trace = transport_trace if transport_trace is not None else candidate.transport_trace
    return ReviewGovernanceRecord(
        record_id=record_id or f"rvw_rec_{_time.time_ns()}",
        review_id=bundle.review_id,
        candidate_id=bundle.candidate_id,
        candidate_sha=bundle.candidate_sha,
        bundle_digest=compute_bundle_digest(bundle),
        outcome_status=outcome_status,
        side_effect_state=side_effect_state,
        admission="CANDIDATE_ADMITTED" if admitted else "REJECTED",
        rejection_reasons=tuple(correlation_errors),
        source="external_review",
        transport_trace=trace,
        provenance=dict(provenance or {}),
    )


__all__ = ["ReviewGovernanceRecord", "build_governance_record"]
