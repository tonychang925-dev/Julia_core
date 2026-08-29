"""Review transaction binding, ledger, and duplicate / exact-retry control.

Canonical end-to-end binding:

    trusted outbound ReviewBundle snapshot (SealedReviewBundle)
        -> ReviewTransaction (immutable)
        -> provider execution
        -> captured raw response
        -> ReviewDecisionCandidate
        -> Julia validation
        -> ReviewGovernanceRecord

Duplicate / exact-retry control:

    - a second ORDINARY submission of the same review binding must NOT execute
      the provider again silently
    - exact retry is allowed only when explicitly requested AND the prior
      submission's side_effect_state was provably NOT UNKNOWN
    - SideEffectState.UNKNOWN must NEVER auto retry
"""

from __future__ import annotations

import secrets
import time as _time
from dataclasses import dataclass, field
from typing import Any

from julia_core.review.snapshot import SealedReviewBundle


class ReviewDuplicateError(ValueError):
    """Raised when a review binding is submitted again without governed exact retry."""


class ReviewRetryUnsafeError(ValueError):
    """Raised when an exact retry is requested while prior side effect is UNKNOWN."""


def _binding_tuple(
    *,
    review_id: str,
    candidate_id: str,
    candidate_sha: str,
    bundle_digest: str,
) -> tuple[str, str, str, str]:
    return (review_id, candidate_id, candidate_sha, bundle_digest)


@dataclass(frozen=True, slots=True)
class ReviewTransaction:
    """One immutable governed review transaction.

    Created ONLY through ReviewTransactionLedger.mint() from a
    SealedReviewBundle snapshot. Carries an opaque token that the guarded
    provider requires — callers cannot mint a transaction by hand.
    """

    transaction_id: str
    snapshot: SealedReviewBundle
    token: str
    review_id: str
    candidate_id: str
    candidate_sha: str
    bundle_digest: str
    created_at: str = field(default_factory=lambda: _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()))
    provenance: dict[str, Any] = field(default_factory=dict)

    @property
    def binding(self) -> tuple[str, str, str, str]:
        return _binding_tuple(
            review_id=self.review_id,
            candidate_id=self.candidate_id,
            candidate_sha=self.candidate_sha,
            bundle_digest=self.bundle_digest,
        )


@dataclass(frozen=True, slots=True)
class _ExecutionOutcomeRecord:
    outcome_status: str
    side_effect_state: str
    completed_at: str = field(default_factory=lambda: _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()))


class ReviewTransactionLedger:
    """Core-owned trusted-creator ledger for review transactions.

    Only ``mint()`` creates transactions. ``token`` is opaque and generated
    with ``secrets``; callers cannot forge authority through provenance
    strings. The ledger owns duplicate detection and exact-retry policy.
    """

    def __init__(self):
        self._by_token: dict[str, ReviewTransaction] = {}
        self._by_binding: dict[tuple[str, str, str, str], list[ReviewTransaction]] = {}
        self._outcomes: dict[str, _ExecutionOutcomeRecord] = {}

    # ── mint / trusted creation ────────────────────────────────────────────

    def mint(
        self,
        snapshot: SealedReviewBundle,
        *,
        allow_exact_retry: bool = False,
        provenance: dict[str, Any] | None = None,
    ) -> ReviewTransaction:
        """Create ONE trusted transaction from a sealed snapshot.

        Duplicate control: an ordinary re-submission of the same binding is
        rejected. Exact retry is allowed only if explicitly requested AND no
        prior outcome has side_effect_state == UNKNOWN.
        """
        binding = _binding_tuple(
            review_id=snapshot.review_id,
            candidate_id=snapshot.candidate_id,
            candidate_sha=snapshot.candidate_sha,
            bundle_digest=snapshot.digest,
        )

        prior = self._by_binding.get(binding, ())
        if prior:
            latest_outcome = self._outcomes.get(prior[-1].transaction_id)
            if latest_outcome is not None and latest_outcome.side_effect_state == "unknown":
                raise ReviewRetryUnsafeError(
                    "prior submission side_effect_state is UNKNOWN; automatic or "
                    "ordinary retry is forbidden"
                )
            if not allow_exact_retry:
                raise ReviewDuplicateError(
                    f"review binding already submitted: review_id={binding[0]}, "
                    f"candidate_sha={binding[2]}, digest={binding[3]}"
                )

        transaction = ReviewTransaction(
            transaction_id=f"rvw_txn_{_time.time_ns()}",
            snapshot=snapshot,
            token=secrets.token_urlsafe(24),
            review_id=snapshot.review_id,
            candidate_id=snapshot.candidate_id,
            candidate_sha=snapshot.candidate_sha,
            bundle_digest=snapshot.digest,
            provenance=dict(provenance or {}),
        )
        self._by_token[transaction.token] = transaction
        self._by_binding.setdefault(binding, []).append(transaction)
        return transaction

    # ── verification (guarded provider uses this) ──────────────────────────

    def verify_token(self, token: str) -> ReviewTransaction | None:
        """Return the transaction for an opaque token, or None."""
        if not isinstance(token, str) or not token:
            return None
        return self._by_token.get(token)

    def get_by_binding(self, binding: tuple[str, str, str, str]) -> list[ReviewTransaction]:
        return list(self._by_binding.get(binding, ()))

    # ── outcome recording (governance uses this) ───────────────────────────

    def record_outcome(
        self,
        transaction: ReviewTransaction,
        *,
        outcome_status: str,
        side_effect_state: str,
    ) -> None:
        self._outcomes[transaction.transaction_id] = _ExecutionOutcomeRecord(
            outcome_status=outcome_status,
            side_effect_state=side_effect_state,
        )

    def latest_outcome(self, transaction: ReviewTransaction) -> dict[str, str] | None:
        record = self._outcomes.get(transaction.transaction_id)
        if record is None:
            return None
        return {
            "outcome_status": record.outcome_status,
            "side_effect_state": record.side_effect_state,
            "completed_at": record.completed_at,
        }


__all__ = [
    "ReviewDuplicateError",
    "ReviewRetryUnsafeError",
    "ReviewTransaction",
    "ReviewTransactionLedger",
]
