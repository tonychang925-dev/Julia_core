"""Core-side review correlation / identity rules.

These rules enforce the end-to-end binding:
  review_id + candidate_id + candidate_sha + bundle_digest

A returned review result must correlate to the exact outbound bundle. If the
candidate changes while review is in flight, the result is STALE_REVIEW and
must be rejected — no silent carry-over.
"""

from __future__ import annotations

from typing import Any

from julia_core.review.contracts import (
    ReviewBundle,
    ReviewDecisionCandidate,
    ReviewErrorCode,
    ReviewVerdict,
)
from julia_core.review.digest import compute_bundle_digest


class ReviewCorrelationError(ValueError):
    """Raised when a review result fails Core-side correlation/binding rules."""


def validate_review_correlation(
    bundle: ReviewBundle,
    candidate: ReviewDecisionCandidate,
    *,
    bundle_digest: str | None = None,
    max_response_chars: int = 12000,
) -> list[str]:
    """Return a list of correlation errors (empty = PASS).

    Checks:
      - candidate minimum fields (review_id / candidate_id / candidate_sha)
      - bundle schema validity
      - review_id match
      - candidate_id match
      - candidate_sha match
      - bundle_digest recompute match (when digest supplied)
      - response non-empty
      - verdict recognized
      - response within size limit
    """
    errors: list[str] = list(bundle.validate())
    errors.extend(candidate.validate_minimum())

    if not errors:
        if candidate.review_id != bundle.review_id:
            errors.append(f"{ReviewErrorCode.REVIEW_ID_MISMATCH.value}:candidate review_id != bundle review_id")
        if candidate.candidate_id != bundle.candidate_id:
            errors.append(f"{ReviewErrorCode.CANDIDATE_ID_MISMATCH.value}:candidate candidate_id != bundle candidate_id")
        if candidate.candidate_sha != bundle.candidate_sha:
            errors.append(f"{ReviewErrorCode.CANDIDATE_SHA_MISMATCH.value}:candidate candidate_sha != bundle candidate_sha")

        if bundle_digest is not None:
            recomputed = compute_bundle_digest(bundle)
            if recomputed != bundle_digest:
                errors.append(f"{ReviewErrorCode.BUNDLE_DIGEST_MISMATCH.value}:recomputed != supplied")

        if not _has_observable_content(candidate):
            errors.append(f"{ReviewErrorCode.REVIEW_EMPTY_RESPONSE.value}:no observable review content")

        if _response_size(candidate) > max_response_chars:
            errors.append(
                f"response_size_exceeded:> {max_response_chars} chars"
            )

    return errors


def assert_review_correlation(
    bundle: ReviewBundle,
    candidate: ReviewDecisionCandidate,
    *,
    bundle_digest: str | None = None,
    max_response_chars: int = 12000,
) -> None:
    """Raise ReviewCorrelationError on first failed correlation rule."""
    errors = validate_review_correlation(
        bundle, candidate,
        bundle_digest=bundle_digest,
        max_response_chars=max_response_chars,
    )
    if errors:
        raise ReviewCorrelationError("; ".join(errors))


def is_stale(bundle: ReviewBundle, current_candidate_sha: str) -> bool:
    """True when the bound candidate SHA no longer matches current truth."""
    return bundle.candidate_sha != current_candidate_sha


def assert_not_stale(bundle: ReviewBundle, current_candidate_sha: str) -> None:
    if is_stale(bundle, current_candidate_sha):
        raise ReviewCorrelationError(
            f"{ReviewErrorCode.STALE_REVIEW.value}:bound {bundle.candidate_sha} != current {current_candidate_sha}"
        )


def _has_observable_content(candidate: ReviewDecisionCandidate) -> bool:
    if candidate.verdict not in (ReviewVerdict.UNPARSEABLE, ReviewVerdict.UNPARSEABLE.value):
        return True
    return bool(
        candidate.blockers
        or candidate.high
        or candidate.medium
        or candidate.required_changes
        or candidate.notes
        or candidate.raw_response_ref
    )


def _response_size(candidate: ReviewDecisionCandidate) -> int:
    parts = [str(candidate.verdict.value if isinstance(candidate.verdict, ReviewVerdict) else candidate.verdict)]
    for name in ("blockers", "high", "medium", "required_changes", "notes"):
        parts.extend(str(x) for x in getattr(candidate, name, ()))
    parts.append(candidate.raw_response_ref or "")
    return sum(len(p) for p in parts)


__all__ = [
    "ReviewCorrelationError",
    "assert_not_stale",
    "assert_review_correlation",
    "is_stale",
    "validate_review_correlation",
]
