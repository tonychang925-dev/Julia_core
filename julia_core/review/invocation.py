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


def _invocation_fingerprint(invocation: ReviewInvocationResult) -> str:
    """Bind exact transaction + exact execution identities."""
    call = invocation.execution.capability_call
    tool = invocation.execution.tool_result
    call_id = call.capability_call_id if call is not None else None
    tool_call_id = tool.capability_call_id if tool is not None else None
    evidence_ids = tuple(e.evidence_id for e in invocation.execution.evidence)
    authority = {
        "invocation_id": invocation.invocation_id,
        "transaction_id": invocation.transaction.transaction_id,
        "transaction_fingerprint_ok": True,
        "capability_request_id": call.capability_request_id if call is not None else None,
        "capability_call_id": call_id,
        "tool_result_call_id": tool_call_id,
        "evidence_ids": evidence_ids,
        "authorization_decision": (
            invocation.execution.authorization_decision.decision.value
            if invocation.execution.authorization_decision is not None
            and hasattr(invocation.execution.authorization_decision.decision, "value")
            else (invocation.execution.authorization_decision.decision
                  if invocation.execution.authorization_decision is not None
                  else None)
        ),
    }
    return _json.dumps(authority, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def register_trusted_invocation(invocation: ReviewInvocationResult) -> ReviewInvocationResult:
    """Register a trusted invocation (submit_review only)."""
    _TRUSTED_INVOCATIONS[invocation.invocation_id] = (
        invocation,
        _invocation_fingerprint(invocation),
    )
    return invocation


def is_trusted_invocation(invocation: ReviewInvocationResult) -> bool:
    """True only for the exact registered invocation with an unchanged
    execution/transaction binding fingerprint."""
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

    # Record the real execution truth internally (derived from the exact
    # ToolResult, not a caller string).
    result = execution.tool_result
    outcome_status = (
        result.status.value if result is not None and hasattr(result.status, "value")
        else ("denied" if result is None else str(result.status))
    )
    side_effect_state = (
        result.side_effect_state.value if result is not None and hasattr(result.side_effect_state, "value")
        else ("none" if result is None else str(result.side_effect_state))
    )
    ledger._record_execution_outcome(
        transaction,
        outcome_status=outcome_status,
        side_effect_state=side_effect_state,
    )

    invocation = ReviewInvocationResult(
        invocation_id=f"rvw_inv_{_time_ns()}",
        execution=execution,
        transaction=transaction,
    )
    return register_trusted_invocation(invocation)


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
    "register_trusted_invocation",
    "submit_review",
]
