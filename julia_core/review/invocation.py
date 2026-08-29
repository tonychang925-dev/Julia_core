"""Manual / explicit external code review invocation path.

Invocation is OPERATOR-TRIGGERED ONLY and REQUIRES the governed semantic
ingress:

    ReviewBundle
    -> validation
    -> immutable semantic snapshot (deep-sealed, owned digest)
    -> trusted transaction (token minted by Core ledger)
    -> CapabilityRequest (bound to the EXACT transaction snapshot)
    -> CapabilityManager
    -> guarded provider

§1 (Q1-Q4): the request payload derives ONLY from transaction.snapshot. The
GuardedReviewProvider re-derives the provider-facing payload from the trusted
snapshot after claiming the token, so caller-mutated request.arguments can never
become provider semantic truth.

§2 (I1-I4): submit_review registers a trusted ReviewInvocationResult binding
the exact transaction + exact CapabilityExecution identities. Governance rejects
handcrafted / copied / mismatched invocations.

§4 (X1-X2): the bearer token is burned under ALL exit paths (exception-safe
finally), so a failed delegation can never leave a reusable token.
"""

from __future__ import annotations

import json as _json
from dataclasses import dataclass
from typing import Any

from julia_core.capability.manager import CapabilityExecution, CapabilityManager
from julia_core.capability.models import CapabilityRequest
from julia_core.review.contracts import ReviewBundle
from julia_core.review.guard import REVIEW_SEMANTIC_ARG, REVIEW_TOKEN_ARG
from julia_core.review.snapshot import SealedReviewBundle, seal_review_bundle
from julia_core.review.transaction import ReviewTransaction, ReviewTransactionLedger

EXTERNAL_REVIEW_CAPABILITY = "engineering.code_review"
EXTERNAL_REVIEW_SCOPE = "engineering.review.external"

# Fields a Core-side request MUST NOT carry: browser/transport authority.
_FORBIDDEN_AUTHORITY_KEYS = {
    "tab_id",
    "tab_ref",
    "dom_selector",
    "conversation_url",
    "chatgpt_url",
    "extension_nonce",
    "browser_command",
    "browser_session_id",
    "browser_session_ref",
}


class BrowserAuthorityInRequestError(ValueError):
    """Raised when review request arguments attempt to carry browser authority."""


class ReviewIngressRequiredError(ValueError):
    """Raised when submit_review is called without a trusted ledger/token path."""


def _find_forbidden_authority_keys(value: Any) -> set[str]:
    found: set[str] = set()
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, child in current.items():
                if str(key) in _FORBIDDEN_AUTHORITY_KEYS:
                    found.add(str(key))
                stack.append(child)
        elif isinstance(current, (list, tuple, set)):
            stack.extend(current)
    return found


def build_review_request(
    transaction: ReviewTransaction,
    *,
    correlation_id: str = "",
    turn_id: str = "",
    generation_id: str = "",
) -> CapabilityRequest:
    """Project the EXACT transaction snapshot into a CapabilityRequest.

    §1 (Q1-Q4): the semantic payload derives ONLY from transaction.snapshot.
    There is NO separate snapshot parameter — a caller cannot bind Snapshot B to
    Transaction A. Browser authority fields fail closed (recursive).
    """
    payload = transaction.snapshot.to_payload()

    forbidden = sorted(_find_forbidden_authority_keys(payload))
    if forbidden:
        raise BrowserAuthorityInRequestError(
            f"browser authority fields are not allowed in Core review request: {forbidden}"
        )

    arguments: dict[str, Any] = dict(payload)
    arguments[REVIEW_TOKEN_ARG] = transaction.token
    arguments[REVIEW_SEMANTIC_ARG] = True

    request = CapabilityRequest(
        capability_id=EXTERNAL_REVIEW_CAPABILITY,
        arguments=arguments,
        requested_scope=EXTERNAL_REVIEW_SCOPE,
        idempotency_key=f"review:{transaction.transaction_id}",
        turn_id=turn_id,
        generation_id=generation_id,
        correlation_id=correlation_id,
        provenance={
            "ingress": "governed_review_semantic",
            "transaction_id": transaction.transaction_id,
            "snapshot_id": transaction.snapshot.snapshot_id,
            "source": "julia_core.review.invocation",
            # NOTE: provenance is descriptive only; it is NOT authority.
        },
    )
    return request


# ── Trusted invocation registry (§2, I1-I4) ──────────────────────────────────

_TRUSTED_INVOCATIONS: dict[str, tuple[Any, str]] = {}


@dataclass(frozen=True, slots=True)
class ReviewInvocationResult:
    """Typed result of one governed external review submission.

    Trusted-creator semantics: only submit_review() may produce and register an
    invocation. Governance verifies is_trusted_invocation() before admission, so
    a handcrafted / copied / mismatched (execution=A, transaction=B) invocation
    is rejected even when A and B are individually genuine.
    """

    invocation_id: str
    execution: CapabilityExecution
    transaction: ReviewTransaction

    @property
    def tool_result(self):
        return self.execution.tool_result

    @property
    def outcome_status(self) -> str:
        result = self.execution.tool_result
        if result is None:
            return "denied"
        return result.status.value if hasattr(result.status, "value") else str(result.status)

    @property
    def side_effect_state(self) -> str:
        result = self.execution.tool_result
        if result is None:
            return "none"
        return result.side_effect_state.value if hasattr(result.side_effect_state, "value") else str(result.side_effect_state)


def _seal_plain(value: Any) -> Any:
    """Normalize a value for canonical fingerprinting (no aliases)."""
    if isinstance(value, dict):
        return {k: _seal_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_seal_plain(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "value"):  # enum
        return value.value
    return str(value)


def _invocation_fingerprint(invocation: ReviewInvocationResult) -> str:
    """Bind the FULL authority-bearing execution truth (round-5 §2).

    Covers: authorization decision state, CapabilityCall identity/status/
    provider/correlation, ToolResult call id + status + side_effect_state +
    canonical structured_output + error, evidence ids + content/provenance, and
    the exact transaction full integrity. Nested-dict mutation or
    object.__setattr__ after creation invalidates the fingerprint.
    """
    execution = invocation.execution
    decision = execution.authorization_decision
    call = execution.capability_call
    tool = execution.tool_result

    authority = {
        "invocation_id": invocation.invocation_id,
        "transaction_id": invocation.transaction.transaction_id,
        "transaction_fingerprint": _transaction_fingerprint_of(invocation.transaction),
        "authorization_decision": _seal_plain(
            {
                "decision": getattr(decision.decision, "value", decision.decision) if decision is not None else None,
                "scope": decision.scope if decision is not None else None,
                "reason": decision.reason if decision is not None else None,
                "policy_ref": decision.policy_ref if decision is not None else None,
            }
        ),
        "capability_call": _seal_plain(
            {
                "capability_call_id": call.capability_call_id if call is not None else None,
                "capability_request_id": call.capability_request_id if call is not None else None,
                "status": getattr(call.status, "value", call.status) if call is not None else None,
                "provider": call.provider if call is not None else None,
                "correlation_id": call.correlation_id if call is not None else None,
            }
        ),
        "tool_result": _seal_plain(
            {
                "capability_call_id": tool.capability_call_id if tool is not None else None,
                "status": getattr(tool.status, "value", tool.status) if tool is not None else None,
                "side_effect_state": getattr(tool.side_effect_state, "value", tool.side_effect_state) if tool is not None else None,
                "structured_output": tool.structured_output if tool is not None else None,
                "error": tool.error if tool is not None else None,
                "provider": tool.provider if tool is not None else None,
                "schema_version": tool.schema_version if tool is not None else None,
            }
        ),
        "evidence": [
            _seal_plain({
                "evidence_id": e.evidence_id,
                "source_type": getattr(e.source_type, "value", e.source_type),
                "source_ref": e.source_ref,
                "observed_at": e.observed_at,
                "content_ref": e.content_ref,
                "provenance": e.provenance,
                "integrity_metadata": e.integrity_metadata,
                "freshness": e.freshness,
                "confidence": e.confidence,
                "correlation_id": e.correlation_id,
            })
            for e in execution.evidence
        ],
    }
    return _json.dumps(authority, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _transaction_fingerprint_of(transaction: ReviewTransaction) -> str:
    from julia_core.review.transaction import _transaction_fingerprint
    return _transaction_fingerprint(transaction)


def _register_trusted_invocation(
    invocation: ReviewInvocationResult,
    authority: Any,
) -> ReviewInvocationResult:
    """INTERNAL trusted registration — requires the opaque lifecycle authority
    minted by the controlled submit_review path (round-6 §A).

    Underscore naming is NOT authority: a fake caller calling this helper with a
    genuine transaction + fabricated execution is rejected because it cannot
    produce a valid un-consumed lifecycle authority for that exact
    transaction+execution pair.
    """
    from julia_core.review.lifecycle import authorize_registration
    from julia_core.review.transaction import _transaction_fingerprint
    from julia_core.review.lifecycle import _execution_fingerprint_of

    if not authorize_registration(
        authority,
        transaction_id=invocation.transaction.transaction_id,
        execution_fingerprint=_execution_fingerprint_of(invocation.execution),
    ):
        raise ReviewIngressRequiredError(
            "invocation registration requires the opaque lifecycle authority "
            "minted by submit_review; handcrafted registration rejected"
        )
    _TRUSTED_INVOCATIONS[invocation.invocation_id] = (
        invocation,
        _invocation_fingerprint(invocation),
    )
    return invocation


def is_trusted_invocation(invocation: ReviewInvocationResult) -> bool:
    """True only for the exact registered invocation with an unchanged
    full execution/transaction binding fingerprint."""
    entry = _TRUSTED_INVOCATIONS.get(invocation.invocation_id)
    if entry is None:
        return False
    ref, fingerprint = entry
    if ref is not invocation:
        return False
    return _invocation_fingerprint(invocation) == fingerprint


async def submit_review(
    manager: CapabilityManager,
    bundle: ReviewBundle,
    ledger: ReviewTransactionLedger,
    *,
    allow_exact_retry: bool = False,
    correlation_id: str = "",
    turn_id: str = "",
    generation_id: str = "",
    provenance: dict[str, Any] | None = None,
) -> ReviewInvocationResult:
    """Execute one governed review through the canonical CapabilityManager.

    The guarded provider must be installed under ``external_review``; otherwise
    the manager resolves no provider and returns typed UNAVAILABLE (fail-closed).

    Token lifecycle (X1-X2): the token is burned in a finally-equivalent path so
    it is unusable after this call no matter what happens (including unexpected
    manager/provider exceptions).
    """
    snapshot = seal_review_bundle(bundle)
    transaction = ledger.mint(
        snapshot,
        allow_exact_retry=allow_exact_retry,
        provenance=provenance,
    )
    request = build_review_request(
        transaction,
        correlation_id=correlation_id,
        turn_id=turn_id,
        generation_id=generation_id,
    )

    try:
        execution = await manager.execute_typed(request)
    finally:
        # Exception-safe burn: even if the manager/provider raised mid-way, the
        # bearer token must never remain reusable.
        ledger.burn_token(transaction.token)

    # Build the trusted invocation (binds execution + transaction), mint the
    # opaque lifecycle authority (round-6 §A), then seal retry truth write-once
    # and register the invocation — both gates require the same authority.
    invocation = ReviewInvocationResult(
        invocation_id=f"rvw_inv_{_time_ns()}",
        execution=execution,
        transaction=transaction,
    )
    from julia_core.review.lifecycle import (
        _execution_fingerprint_of,
        mint_lifecycle_authority,
    )
    authority = mint_lifecycle_authority(
        transaction_id=transaction.transaction_id,
        execution_fingerprint=_execution_fingerprint_of(execution),
    )
    ledger._seal_execution_outcome(
        transaction=transaction,
        invocation=invocation,
        authority=authority,
    )
    return _register_trusted_invocation(invocation, authority)


import time as _time_ns_mod


def _time_ns() -> str:
    return str(_time_ns_mod.time_ns())


__all__ = [
    "BrowserAuthorityInRequestError",
    "EXTERNAL_REVIEW_CAPABILITY",
    "EXTERNAL_REVIEW_SCOPE",
    "ReviewIngressRequiredError",
    "ReviewInvocationResult",
    "build_review_request",
    "is_trusted_invocation",
    "submit_review",
]
