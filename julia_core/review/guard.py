"""Guarded provider boundary for engineering.code_review.

Makes governed semantic ingress MANDATORY. A generic / arbitrary
CapabilityRequest(capability_id="engineering.code_review") must NOT reach the
real external provider. Only requests carrying a valid opaque transaction token
(minted by ReviewTransactionLedger) may pass the guard.

This is a narrow review-specific boundary. CapabilityManager semantics are
frozen and untouched: the guard lives INSIDE the provider slot, so the Manager
resolves the definition -> guarded provider -> verifies the token -> delegates
to the real provider ONLY when the token resolves to a trusted transaction.
"""

from __future__ import annotations

from typing import Any

from julia_core.capability.models import (
    CapabilityProvider,
    CapabilityRequest,
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)
from julia_core.review.transaction import ReviewTransactionLedger

REVIEW_TOKEN_ARG = "review_transaction_token"
REVIEW_SEMANTIC_ARG = "review_semantic_ingress"


class ReviewIngressDenied(Exception):
    """Raised (or returned as UNAVAILABLE) when a request lacks trusted ingress.

    Never delegates to the real provider. Not a provider DENIED — it is a
    fail-closed Core ingress guard outcome.
    """


class GuardedReviewProvider:
    """Wraps the real external_review provider behind the trusted-ingress guard.

    health(): delegates to the real provider's health (health is not a send).
    execute(): requires a valid transaction token; otherwise returns a typed
    UNAVAILABLE outcome (no synthetic review, no fallback, no DENIED).
    """

    def __init__(
        self,
        real_provider: CapabilityProvider,
        ledger: ReviewTransactionLedger,
    ):
        self._real = real_provider
        self._ledger = ledger

    @property
    def real_provider(self) -> CapabilityProvider:
        return self._real

    async def health(self) -> tuple[bool, str]:
        return await self._real.health()

    async def execute(self, request: CapabilityRequest) -> dict[str, Any] | ProviderExecutionOutcome:
        token = request.arguments.get(REVIEW_TOKEN_ARG)
        # ATOMIC one-shot claim at the delegation boundary (P0-A): the token is
        # consumed here. A replayed/consumed/copied token yields None and the
        # real provider is never reached.
        if isinstance(token, str):
            transaction = self._ledger.claim_for_execution(token)
        else:
            transaction = None
        if transaction is None:
            return ProviderExecutionOutcome(
                status=ToolResultStatus.UNAVAILABLE,
                error={
                    "code": "governed_review_ingress_required",
                    "message": (
                        "engineering.code_review requires a governed review "
                        "transaction token; arbitrary or replayed ingress denied"
                    ),
                },
                side_effect_state=SideEffectState.NONE,
            )
        # Semantic ingress marker must also be present and non-forgeable by
        # provenance: only the trusted mint path sets it alongside the token.
        if request.arguments.get(REVIEW_SEMANTIC_ARG) is not True:
            return ProviderExecutionOutcome(
                status=ToolResultStatus.UNAVAILABLE,
                error={
                    "code": "governed_review_ingress_required",
                    "message": "review semantic ingress marker missing",
                },
                side_effect_state=SideEffectState.NONE,
            )
        return await self._real.execute(request)


def install_review_guard(
    providers: dict[str, CapabilityProvider],
    *,
    real_provider: CapabilityProvider,
    ledger: ReviewTransactionLedger,
) -> None:
    """Register the guarded provider under the external_review key.

    Callers (Julia-AI-Assistant or Core bridge) pass the real provider; the
    guard is installed by Core so arbitrary ingress can never reach it.
    """
    providers["external_review"] = GuardedReviewProvider(real_provider, ledger)


__all__ = [
    "GuardedReviewProvider",
    "ReviewIngressDenied",
    "REVIEW_SEMANTIC_ARG",
    "REVIEW_TOKEN_ARG",
    "install_review_guard",
]
