"""Review governance — exact-invocation truth + trusted composition.

Governance consumes:

    trusted ReviewInvocationResult (exact CapabilityExecution + exact transaction)
    + ReviewDecisionCandidate
    + a Core-owned ReviewGovernanceService (trusted composition)

P0-B: transaction derived from invocation.transaction; ledger must own the exact
transaction (identity + full fingerprint). Handcrafted/spread/copied invocations
are rejected by is_trusted_invocation().

P0-C / E6-E9: the CandidateShaSource is bound ONLY through
bind_candidate_sha_source() (Core-owned trusted creator). The service accepts a
trusted binding or stays UNBOUND; an arbitrary FakeSource cannot become
authority, and object.__setattr__ cannot replace it because the adapter lives in
the registry keyed by binding_id.

§8 (C1-C5): raw-response provenance. Core computes the raw-response digest from
the trusted execution's observable content itself (never trusting a supplied
digest blindly). A candidate eligible for CANDIDATE_ADMITTED must carry
auditable raw-response truth (raw_response_ref + digest matching the
Core-computed digest of the exact execution observation).

§9 (GR1-GR4): ReviewGovernanceRecord is a trusted audit artifact. Only
record() may register it; is_trusted_review_governance_record() verifies
identity + full fingerprint, and nested values are deep-sealed.
"""

from __future__ import annotations

import json as _json
import time as _time
from dataclasses import asdict, dataclass, field
from typing import Any

from julia_core.review.candidate_artifact import (
    SealedCandidate,
    _candidate_authority,
    candidate_fingerprint,
    is_trusted_candidate,
)
from julia_core.review.contracts import ReviewDecisionCandidate, ReviewTransportTrace
from julia_core.review.digest import compute_text_digest
from julia_core.review.invocation import ReviewInvocationResult, is_trusted_invocation
from julia_core.review.source_binding import (
    CandidateCreatorBinding,
    CandidateShaSourceBinding,
    _resolve_adapter,
    is_trusted_candidate_creator,
    is_trusted_source_binding,
)
from julia_core.review.transaction import (
    ReviewTransactionLedger,
    ReviewUntrustedTransactionError,
)
from julia_core.review.validation import (
    assert_not_stale,
    validate_review_correlation,
    validate_transport_completion,
)


@dataclass(frozen=True, slots=True)
class ReviewGovernanceRecord:
    """One immutable audit record for a review transaction.

    Trusted audit artifact (GR1-GR4): only ReviewGovernanceService.record() may
    create and register it. is_trusted_review_governance_record() verifies the
    exact registered object with an unchanged full fingerprint.
    """

    record_id: str
    review_id: str
    candidate_id: str
    candidate_sha: str
    bundle_digest: str
    transaction_id: str
    invocation_id: str
    candidate_artifact_id: str          # exact trusted candidate artifact (round-6 §D)
    candidate_fingerprint: str          # full candidate fingerprint (round-6 §D)
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


_TRUSTED_RECORDS: dict[str, tuple[Any, str]] = {}


def _record_fingerprint(record: ReviewGovernanceRecord) -> str:
    authority = {
        "record_id": record.record_id,
        "review_id": record.review_id,
        "candidate_id": record.candidate_id,
        "candidate_sha": record.candidate_sha,
        "bundle_digest": record.bundle_digest,
        "transaction_id": record.transaction_id,
        "invocation_id": record.invocation_id,
        "candidate_artifact_id": record.candidate_artifact_id,
        "candidate_fingerprint": record.candidate_fingerprint,
        "outcome_status": record.outcome_status,
        "side_effect_state": record.side_effect_state,
        "admission": record.admission,
        "rejection_reasons": list(record.rejection_reasons),
        "raw_response_ref": record.raw_response_ref,
        "raw_response_digest": record.raw_response_digest,
        "transport_trace": _deep_plain(record.transport_trace),
        "provenance": _deep_plain(record.provenance),
    }
    return _json.dumps(authority, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _deep_plain(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__") and hasattr(value, "to_dict"):
        return _deep_plain(value.to_dict())
    if isinstance(value, dict):
        return {k: _deep_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_deep_plain(v) for v in value]
    return value


def is_trusted_review_governance_record(record: ReviewGovernanceRecord) -> bool:
    """True only for the exact registered record with unchanged fingerprint."""
    entry = _TRUSTED_RECORDS.get(record.record_id)
    if entry is None:
        return False
    ref, fingerprint = entry
    if ref is not record:
        return False
    return _record_fingerprint(record) == fingerprint


class ReviewGovernanceService:
    """Core-owned governance boundary with trusted composition.

    Binds the ledger, (optionally) a TRUSTED CandidateShaSourceBinding, and
    (optionally) a TRUSTED candidate-creator binding ONCE at construction
    (round-5 §5/§6/§7). Arbitrary adapter objects are rejected.

    Candidate admission FAILS CLOSED when no trusted candidate creator is bound
    (§6): a caller-constructed candidate cannot become admitted merely by
    supplying matching IDs and digest. The candidate must be the exact output
    of the bound trusted creator over the exact trusted raw response.
    """

    __slots__ = ("_ledger", "_source_binding", "_candidate_creator_binding", "_frozen")

    def __init__(
        self,
        ledger: ReviewTransactionLedger,
        source_binding: CandidateShaSourceBinding | None = None,
        candidate_creator_binding: CandidateCreatorBinding | None = None,
    ):
        if not isinstance(ledger, ReviewTransactionLedger):
            raise TypeError("ReviewGovernanceService requires a ReviewTransactionLedger")
        if source_binding is not None and not is_trusted_source_binding(source_binding):
            raise TypeError(
                "ReviewGovernanceService requires a TRUSTED CandidateShaSourceBinding; "
                "arbitrary adapter objects are not source authority (E6)"
            )
        if candidate_creator_binding is not None and not is_trusted_candidate_creator(candidate_creator_binding):
            raise TypeError(
                "ReviewGovernanceService requires a TRUSTED candidate creator binding; "
                "arbitrary parser objects are not candidate authority (§6)"
            )
        object.__setattr__(self, "_ledger", ledger)
        object.__setattr__(self, "_source_binding", source_binding)
        object.__setattr__(self, "_candidate_creator_binding", candidate_creator_binding)
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name, value):
        if getattr(self, "_frozen", False):
            raise AttributeError(
                f"ReviewGovernanceService is composition-frozen; cannot set {name!r}"
            )
        object.__setattr__(self, name, value)

    @property
    def source_binding(self) -> CandidateShaSourceBinding | None:
        """Read-only. Adapter authority lives in the registry keyed by id."""
        return self._source_binding

    @property
    def has_trusted_source(self) -> bool:
        binding = self._source_binding
        return binding is not None and is_trusted_source_binding(binding)

    @property
    def candidate_creator_binding(self) -> CandidateCreatorBinding | None:
        return self._candidate_creator_binding

    @property
    def bound_creator_binding_id(self) -> str | None:
        binding = self._candidate_creator_binding
        return binding.binding_id if binding is not None else None

    @property
    def has_trusted_candidate_creator(self) -> bool:
        binding = self._candidate_creator_binding
        return binding is not None and is_trusted_candidate_creator(binding)

    def record(
        self,
        invocation: ReviewInvocationResult,
        candidate: SealedCandidate,
        *,
        provenance: dict[str, Any] | None = None,
    ) -> ReviewGovernanceRecord:
        """Build the governance record from the EXACT trusted invocation.

        Fail-closed invariants:
          - invocation must be trusted (I1-I4)
          - transaction derived internally from invocation.transaction
          - ledger owns the exact transaction object with full fingerprint (T1-T4)
          - outcome/side-effect derive from the typed ToolResult
          - correlation validated against the sealed snapshot (owned digest)
          - transport completion from real execution status
          - stale validation uses the TRUSTED binding adapter (E6-E9); unbound
            source -> fail closed
          - §6: a TRUSTED candidate creator MUST be bound and the supplied
            candidate must be the exact output of that creator over the exact
            trusted raw response (no invented parsing; unbound creator -> FAILS
            CLOSED)
          - §7: record_id is internally minted (caller-selected is forbidden)
        """
        if not is_trusted_invocation(invocation):
            raise ReviewUntrustedTransactionError(
                "invocation is not a trusted submit_review-produced invocation; "
                "handcrafted / copied / mismatched invocations are rejected (I1-I4)"
            )
        transaction = invocation.transaction
        if not self._ledger.owns_transaction(transaction):
            raise ReviewUntrustedTransactionError(
                "transaction is not owned by the exact governance ledger with an "
                "unchanged fingerprint; handcrafted/spread/copied transactions rejected"
            )

        outcome_status = _tool_status_of(invocation)
        side_effect_state = _side_effect_of(invocation)

        reasons: list[str] = []

        # Exact creator/artifact/raw-observation association. Existence of some
        # creator binding plus some independently sealed artifact is not enough.
        service_creator_binding = self._candidate_creator_binding
        if service_creator_binding is None or not is_trusted_candidate_creator(service_creator_binding):
            reasons.append(
                "candidate_creator_unavailable:no trusted candidate parser/creator bound; "
                "candidate admission fails closed (§6)"
            )

        candidate_authority = _candidate_authority(candidate)
        if candidate_authority is None:
            reasons.append("candidate_not_trusted:not the exact trusted candidate artifact")
        else:
            if (
                service_creator_binding is None
                or candidate_authority.creator_binding is not service_creator_binding
            ):
                reasons.append(
                    "candidate_creator_binding_mismatch:artifact was not produced "
                    "by the exact creator bound to this governance service"
                )
            elif candidate.creator_binding_id != service_creator_binding.binding_id:
                reasons.append("candidate_creator_binding_id_mismatch")
            if (
                candidate_authority.invocation is not invocation
                or candidate_authority.invocation_id != invocation.invocation_id
            ):
                reasons.append(
                    "raw_observation_invocation_mismatch:artifact raw observation "
                    "belongs to a different invocation"
                )

        candidate_obj = candidate.candidate if isinstance(candidate, SealedCandidate) else candidate

        correlation_errors = validate_review_correlation(transaction.snapshot, candidate_obj)
        reasons.extend(correlation_errors)

        transport_errors = validate_transport_completion(candidate_obj, outcome_status)
        reasons.extend(transport_errors)

        # Stale check: TRUSTED binding adapter only (E6-E9). Unbound -> closed.
        binding = self._source_binding
        if binding is None or not is_trusted_source_binding(binding):
            reasons.append("stale_validation_unavailable:no trusted candidate SHA source binding")
        else:
            try:
                adapter = _resolve_adapter(binding)
                assert_not_stale(
                    transaction.snapshot,
                    _AdapterWrapper(adapter),
                )
            except Exception as exc:
                reasons.append(str(exc))

        # §6/§C: raw-response truth must bind to the exact trusted candidate
        # judgment. Core computes the digest from the exact raw response and
        # requires exact raw_response_ref + digest equality. The trusted
        # creator produced the artifact over the same raw observation.
        expected_digest, raw_ref = _expected_raw_digest_from_execution(invocation)
        if expected_digest is None:
            reasons.append(
                "raw_response_truth_unavailable:no trusted raw-response observation "
                "in the exact execution"
            )
        else:
            if not candidate_obj.raw_response_ref:
                reasons.append("raw_response_ref_missing")
            elif candidate_obj.raw_response_ref != raw_ref:
                reasons.append("raw_response_ref_mismatch")
            if not candidate_obj.raw_response_digest:
                reasons.append("raw_response_digest_missing")
            elif candidate_obj.raw_response_digest != expected_digest:
                reasons.append("raw_response_digest_mismatch")

        admitted = not reasons

        # Retry truth was sealed write-once by submit_review from the exact
        # execution; governance must NOT re-seal or overwrite it (round-5 §4).
        if self._ledger._latest_outcome(transaction) is None:
            raise ReviewUntrustedTransactionError(
                "invocation transaction has no sealed execution outcome; "
                "not a governed submit_review path"
            )

        record = ReviewGovernanceRecord(
            record_id=f"rvw_rec_{_time.time_ns()}",
            review_id=transaction.review_id,
            candidate_id=transaction.candidate_id,
            candidate_sha=transaction.candidate_sha,
            bundle_digest=transaction.bundle_digest,
            transaction_id=transaction.transaction_id,
            invocation_id=invocation.invocation_id,
            candidate_artifact_id=candidate.candidate_artifact_id,
            candidate_fingerprint=(
                candidate_authority.fingerprint
                if candidate_authority is not None
                else candidate_fingerprint(candidate_obj)
            ),
            outcome_status=outcome_status,
            side_effect_state=side_effect_state,
            admission="CANDIDATE_ADMITTED" if admitted else "REJECTED",
            rejection_reasons=tuple(reasons),
            raw_response_ref=candidate_obj.raw_response_ref or "",
            raw_response_digest=candidate_obj.raw_response_digest or "",
            transport_trace=_deep_seal(candidate_obj.transport_trace),
            provenance=_deep_seal(dict(provenance or {})),
        )
        _TRUSTED_RECORDS[record.record_id] = (record, _record_fingerprint(record))
        return record


class _AdapterWrapper:
    """Minimal structural wrapper so assert_not_stale can call the adapter."""

    def __init__(self, adapter):
        self._adapter = adapter

    def current_candidate_sha(self, *, review_id, candidate_id) -> str:
        return self._adapter.current_candidate_sha(review_id=review_id, candidate_id=candidate_id)


def _deep_seal(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _deep_seal(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return tuple(_deep_seal(v) for v in value)
    return value


def _tool_status_of(invocation: ReviewInvocationResult) -> str:
    result = invocation.execution.tool_result
    if result is None:
        return "denied"
    return result.status.value if hasattr(result.status, "value") else str(result.status)


def _side_effect_of(invocation: ReviewInvocationResult) -> str:
    result = invocation.execution.tool_result
    if result is None:
        return "none"
    return result.side_effect_state.value if hasattr(result.side_effect_state, "value") else str(result.side_effect_state)


def _raw_content_of(invocation: ReviewInvocationResult) -> str:
    """Extract the trusted raw response text from the exact execution."""
    result = invocation.execution.tool_result
    if result is None:
        return ""
    structured = result.structured_output or {}
    raw_text = structured.get("raw_response")
    return raw_text if isinstance(raw_text, str) else ""


def _expected_raw_digest_from_execution(invocation: ReviewInvocationResult) -> tuple[str | None, str | None]:
    """Compute the raw-response digest from the TRUSTED execution observation.

    Core computes the digest itself from the raw text content when present; it
    never blindly trusts a provider-supplied digest string. Returns
    (digest, raw_reference) or (None, None) when no trusted raw content exists.
    """
    result = invocation.execution.tool_result
    if result is None:
        return None, None
    structured = result.structured_output or {}

    raw_text = structured.get("raw_response")
    if isinstance(raw_text, str) and raw_text:
        digest = compute_text_digest(raw_text)
        raw_ref = f"tool_result:{result.capability_call_id}:raw_response"
        return digest, raw_ref

    # No raw text content -> no trusted raw observation. A supplied digest
    # string alone is NOT proof of raw response identity (C3).
    return None, None


__all__ = [
    "ReviewGovernanceRecord",
    "ReviewGovernanceService",
    "is_trusted_review_governance_record",
]
