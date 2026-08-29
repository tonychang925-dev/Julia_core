"""Manual / explicit external code review invocation path.

Invocation is OPERATOR-TRIGGERED ONLY and REQUIRES the governed semantic
ingress:

    ReviewBundle
    -> validation
    -> immutable semantic snapshot (deep-sealed, owned digest)
    -> trusted transaction (token minted by Core ledger)
    -> CapabilityRequest (carries token)
    -> CapabilityManager
    -> guarded provider

A caller must NOT bypass this path by constructing a normal CapabilityRequest:
the guarded provider rejects any request without a valid transaction token.
Forgeable provenance strings ("manual": true) are NOT authority — only the
opaque ledger token is.
"""

from __future__ import annotations

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
    """Recursively find browser/session authority keys anywhere in the payload."""
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
    snapshot: SealedReviewBundle,
    transaction: ReviewTransaction,
    *,
    correlation_id: str = "",
    turn_id: str = "",
    generation_id: str = "",
) -> CapabilityRequest:
    """Project a SEALED snapshot into a canonical CapabilityRequest.

    Uses ONLY the immutable snapshot payload (deep-copied, owned digest) and the
    trusted transaction token. The caller's original ReviewBundle object is
    never referenced, so later mutation of the caller object cannot change the
    trusted request. Browser authority fields fail closed (recursive).
    """
    payload = snapshot.to_payload()

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
            "source": "julia_core.review.invocation",
            # NOTE: provenance is descriptive only; it is NOT authority.
        },
    )
    return request


@dataclass(frozen=True, slots=True)
class ReviewInvocationResult:
    """Typed result of one governed external review submission.

    Carries the exact CapabilityExecution plus the trusted transaction.
    Never flattens to a legacy string.
    """

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
    """
    snapshot = seal_review_bundle(bundle)
    transaction = ledger.mint(
        snapshot,
        allow_exact_retry=allow_exact_retry,
        provenance=provenance,
    )
    request = build_review_request(
        snapshot,
        transaction,
        correlation_id=correlation_id,
        turn_id=turn_id,
        generation_id=generation_id,
    )
    execution = await manager.execute_typed(request)
    # Record the real execution truth into the ledger BEFORE returning, so
    # duplicate/exact-retry control (F) sees the prior outcome.
    result = execution.tool_result
    outcome_status = (
        result.status.value if result is not None and hasattr(result.status, "value")
        else ("denied" if result is None else str(result.status))
    )
    side_effect_state = (
        result.side_effect_state.value if result is not None and hasattr(result.side_effect_state, "value")
        else ("none" if result is None else str(result.side_effect_state))
    )
    ledger.record_outcome(
        transaction,
        outcome_status=outcome_status,
        side_effect_state=side_effect_state,
    )
    return ReviewInvocationResult(execution=execution, transaction=transaction)


__all__ = [
    "BrowserAuthorityInRequestError",
    "EXTERNAL_REVIEW_CAPABILITY",
    "EXTERNAL_REVIEW_SCOPE",
    "ReviewIngressRequiredError",
    "ReviewInvocationResult",
    "build_review_request",
    "submit_review",
]
