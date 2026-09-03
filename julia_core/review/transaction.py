"""Review transaction binding, ledger, one-shot token, duplicate/retry control.

Canonical end-to-end binding:

    trusted outbound ReviewBundle snapshot (SealedReviewBundle)
        -> ReviewTransaction (immutable, ledger-owned)
        -> provider execution (one-shot token claim)
        -> captured raw response
        -> ReviewDecisionCandidate
        -> Julia validation
        -> ReviewGovernanceRecord

One-shot token (P0-A):

    mint -> atomic claim/consume at the guarded provider boundary
    -> first execution allowed
    -> same token second execution rejected BEFORE real provider
    -> an already-consumed bearer token is never reused

Exact retry MUST mint a NEW transaction/token (never reuse an executed token).

Ledger ownership (P1-E):

    transactions are ledger-minted only; handcrafted/copied transaction objects
    are NOT trusted. Governance verifies ledger ownership + exact execution.
"""

from __future__ import annotations

import secrets
import threading
import time as _time
from dataclasses import dataclass, field
from typing import Any

from julia_core.review.snapshot import (
    SealedReviewBundle,
    _snapshot_fingerprint,
    is_trusted_snapshot,
)


class ReviewDuplicateError(ValueError):
    """Raised when a review binding is submitted again without governed exact retry."""


class ReviewRetryUnsafeError(ValueError):
    """Raised when an exact retry is requested while prior side effect is UNKNOWN."""


class ReviewUntrustedSnapshotError(ValueError):
    """Raised when a snapshot was not created through the trusted sealing path."""


class ReviewUntrustedTransactionError(ValueError):
    """Raised when a transaction object is not owned by the exact ledger."""


class ReviewTokenConsumedError(ValueError):
    """Raised when an already-consumed bearer token is replayed."""


class ReviewOutcomeAlreadySealedError(ValueError):
    """Raised when a transaction outcome is sealed a second time (write-once)."""


def _binding_tuple(
    *,
    review_id: str,
    candidate_id: str,
    candidate_sha: str,
    bundle_digest: str,
) -> tuple[str, str, str, str]:
    return (review_id, candidate_id, candidate_sha, bundle_digest)


_TRANSACTION_AUTHORITY_FIELDS = (
    "transaction_id",
    "review_id",
    "candidate_id",
    "candidate_sha",
    "bundle_digest",
    "token",
)


def _transaction_fingerprint(transaction: "ReviewTransaction") -> str:
    """Canonical fingerprint of the transaction's full authority state.

    Binds transaction_id + token identity + review binding + the exact trusted
    snapshot identity (snapshot_id + snapshot digest), so swapping the snapshot
    or mutating any authority field invalidates the fingerprint (T1-T3).
    """
    import json
    authority = {
        name: getattr(transaction, name)
        for name in _TRANSACTION_AUTHORITY_FIELDS
    }
    authority["snapshot_id"] = transaction.snapshot.snapshot_id
    authority["snapshot_digest"] = transaction.snapshot.digest
    authority["candidate_admission"] = getattr(
        transaction,
        "candidate_admission",
        transaction.provenance.get("candidate_admission"),
    )
    return compute_digest(
        json.dumps(authority, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def compute_digest(text: str) -> str:
    from julia_core.review.digest import compute_text_digest
    return compute_text_digest(text)


@dataclass(frozen=True, slots=True)
class ReviewTransaction:
    """One immutable governed review transaction.

    Created ONLY through ReviewTransactionLedger.mint() from a TRUSTED
    SealedReviewBundle snapshot. Carries an opaque one-shot token. Handcrafted
    transaction objects are NOT trusted by the ledger.
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

    Only ``mint()`` creates transactions, and only from TRUSTED sealed
    snapshots. Tokens are one-shot: ``claim_for_execution()`` atomically
    consumes a token; a second claim returns None. Governance verifies
    transaction ownership through ``owns_transaction()`` which checks the full
    immutable authority fingerprint (T1-T4).

    Retry truth (O1-O5) is recorded internally from the exact execution by the
    invocation path; there is NO public caller-writable outcome API. Only the
    explicitly frozen safe set (NONE / FAILED) may permit an exact retry, and
    exact retry always mints a NEW token.
    """

    # Conservative set of prior side-effect states that PROVABLY did not leave
    # an ambiguous external send. UNKNOWN / SUCCEEDED / missing are not here.
    _RETRY_SAFE_SIDE_EFFECTS = frozenset({"none", "failed"})

    def __init__(self):
        self._lock = threading.Lock()
        self._by_token: dict[str, ReviewTransaction] = {}
        self._by_id: dict[str, tuple[ReviewTransaction, str]] = {}  # id -> (ref, fingerprint)
        self._consumed_tokens: set[str] = set()
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
        """Create ONE trusted transaction from a TRUSTED sealed snapshot.

        Rejects any snapshot not created through the trusted sealing path
        (P1-D). Duplicate control rejects an ordinary re-submission of the same
        binding; exact retry requires explicit request AND prior side effect
        known-safe (not UNKNOWN).
        """
        if not is_trusted_snapshot(snapshot):
            raise ReviewUntrustedSnapshotError(
                "snapshot was not created through the trusted seal_review_bundle() path"
            )

        binding = _binding_tuple(
            review_id=snapshot.review_id,
            candidate_id=snapshot.candidate_id,
            candidate_sha=snapshot.candidate_sha,
            bundle_digest=snapshot.digest,
        )

        with self._lock:
            prior = self._by_binding.get(binding, ())
            if prior:
                # Retry authority derives from the IMMUTABLE recorded outcome
                # (O1-O5). Missing / UNKNOWN / SUCCEEDED / non-safe all forbid.
                latest_outcome = self._outcomes.get(prior[-1].transaction_id)
                if latest_outcome is None:
                    raise ReviewRetryUnsafeError(
                        "prior submission outcome missing; retry forbidden"
                    )
                if latest_outcome.side_effect_state not in self._RETRY_SAFE_SIDE_EFFECTS:
                    raise ReviewRetryUnsafeError(
                        f"prior submission side_effect_state={latest_outcome.side_effect_state!r} "
                        "is not provably retry-safe; retry forbidden"
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
            self._by_id[transaction.transaction_id] = (transaction, _transaction_fingerprint(transaction))
            self._by_binding.setdefault(binding, []).append(transaction)
            return transaction

    # ── one-shot token claim (P0-A) ────────────────────────────────────────

    def claim_for_execution(self, token: str) -> ReviewTransaction | None:
        """Atomically claim/consume a token for provider execution.

        First claim returns the transaction ONLY when the exact ledger-owned
        transaction with an unchanged fingerprint AND its live trusted snapshot
        (is_trusted_snapshot == True) are all intact (round-5 §3). A lookalike
        snapshot with the same id/digest, or a genuine snapshot mutated after
        mint, makes the transaction unusable before provider delegation.

        Any later claim of the same token returns None (rejected BEFORE the
        real provider). Thread-safe.
        """
        with self._lock:
            if token in self._consumed_tokens:
                return None
            transaction = self._by_token.get(token)
            if transaction is None:
                return None
            if not self._integrity_ok(transaction):
                return None
            self._consumed_tokens.add(token)
            return transaction

    def burn_token(self, token: str) -> None:
        """Consume a token even if execution never reached the guard (e.g.
        authorization/health failure before a real send). Idempotent."""
        with self._lock:
            self._consumed_tokens.add(token)

    def token_consumed(self, token: str) -> bool:
        return token in self._consumed_tokens

    # ── ownership / verification (P1-E, T1-T4) ─────────────────────────────

    def _integrity_ok(self, transaction: ReviewTransaction) -> bool:
        """Full integrity: exact ledger-owned object + unchanged transaction
        fingerprint + exact original snapshot object + live trusted snapshot
        (round-5 §3). A handcrafted lookalike snapshot with the same id/digest
        cannot substitute; a genuine snapshot mutated after mint makes the
        transaction unusable."""
        entry = self._by_id.get(transaction.transaction_id)
        if entry is None:
            return False
        ref, fingerprint = entry
        if ref is not transaction:
            return False
        if _transaction_fingerprint(transaction) != fingerprint:
            return False
        if not is_trusted_snapshot(transaction.snapshot):
            return False
        return True

    def owns_transaction(self, transaction: ReviewTransaction) -> bool:
        """True only for the EXACT ledger-minted transaction object whose full
        authority fingerprint is unchanged AND whose snapshot is the live
        trusted snapshot object."""
        return self._integrity_ok(transaction)

    def verify_token(self, token: str) -> ReviewTransaction | None:
        """Return the transaction for a token WITHOUT consuming it.

        Used only for diagnostics; the guarded provider MUST use
        claim_for_execution() so a token is never replayable.
        """
        if not isinstance(token, str) or not token:
            return None
        return self._by_token.get(token)

    def get_by_binding(self, binding: tuple[str, str, str, str]) -> list[ReviewTransaction]:
        return list(self._by_binding.get(binding, ()))

    # ── outcome recording (write-once, internal only; O5, round-5 §4) ──────

    def _seal_execution_outcome(self, *, invocation) -> None:
        """WRITE-ONCE seal controlled by the exact registered invocation.

        The only controlled registration path is inlined in ``submit_review``.
        It creates opaque registry state keyed to the exact invocation object
        and its full execution/transaction fingerprint. There is no reusable
        module-level authority mint or registration helper.

        - never accepts caller-selected outcome_status / side_effect_state as
          authority
        - a second write / overwrite is rejected
        - UNKNOWN can never be rewritten into FAILED/NONE
        - missing outcome remains retry-forbidden (mint() enforces this)
        """
        from julia_core.review.invocation import is_trusted_invocation

        transaction = invocation.transaction
        if not is_trusted_invocation(invocation):
            raise ReviewUntrustedTransactionError(
                "outcome seal requires the exact invocation registered by the "
                "controlled submit_review lifecycle; handcrafted invocations rejected"
            )
        if not self.owns_transaction(transaction):
            raise ReviewUntrustedTransactionError(
                "cannot record outcome for a non-owned transaction"
            )
        result = invocation.execution.tool_result
        outcome_status = (
            result.status.value if result is not None and hasattr(result.status, "value")
            else ("denied" if result is None else str(result.status))
        )
        side_effect_state = (
            result.side_effect_state.value if result is not None and hasattr(result.side_effect_state, "value")
            else ("none" if result is None else str(result.side_effect_state))
        )
        with self._lock:
            if transaction.transaction_id in self._outcomes:
                raise ReviewOutcomeAlreadySealedError(
                    "transaction outcome is write-once; a second seal/overwrite is rejected"
                )
            self._outcomes[transaction.transaction_id] = _ExecutionOutcomeRecord(
                outcome_status=outcome_status,
                side_effect_state=side_effect_state,
            )

    def _latest_outcome(self, transaction: ReviewTransaction) -> dict[str, str] | None:
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
    "ReviewOutcomeAlreadySealedError",
    "ReviewRetryUnsafeError",
    "ReviewTokenConsumedError",
    "ReviewTransaction",
    "ReviewTransactionLedger",
    "ReviewUntrustedSnapshotError",
    "ReviewUntrustedTransactionError",
]
