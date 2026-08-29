"""Trusted ReviewDecisionCandidate artifact (round-6 §C).

A candidate must not be admitted merely because a subset of identity fields
match. The trusted creator binds the COMPLETE canonical candidate state and
registers a full fingerprint. Mutation / copy / reconstruction after creation
invalidates trust, so a caller cannot alter blockers/high/medium/
required_changes/notes while retaining an admitted PASS.
"""

from __future__ import annotations

import json as _json
import secrets
import time as _time
from dataclasses import dataclass, field
from typing import Any

from julia_core.review.contracts import ReviewDecisionCandidate


_CANDIDATE_AUTHORITY_FIELDS = (
    "contract_version",
    "review_id",
    "candidate_id",
    "candidate_sha",
    "source",
    "verdict",
    "blockers",
    "high",
    "medium",
    "required_changes",
    "notes",
    "raw_response_ref",
    "raw_response_digest",
    "captured_at",
    "transport_trace",
    "validation_state",
)


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if hasattr(value, "value"):
        return value.value
    return value


def _candidate_fingerprint(candidate: ReviewDecisionCandidate) -> str:
    data = candidate.to_dict()
    authority = {name: _plain(data.get(name)) for name in _CANDIDATE_AUTHORITY_FIELDS}
    return _json.dumps(authority, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class SealedCandidate:
    """A trusted full ReviewDecisionCandidate artifact.

    Created ONLY through seal_candidate() (the trusted creator path). Owns its
    full-authority fingerprint; mutation/copy/reconstruction invalidates trust.
    """

    candidate_artifact_id: str
    candidate: ReviewDecisionCandidate
    fingerprint: str
    created_at: str = field(default_factory=lambda: _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()))


_TRUSTED_CANDIDATES: dict[str, tuple[Any, str]] = {}


def seal_candidate(candidate: ReviewDecisionCandidate) -> SealedCandidate:
    """Trusted creator path: seal a full candidate and register it.

    Rejects candidates missing required binding fields (fail closed before any
    authority is created).
    """
    errors = candidate.validate_minimum()
    if errors:
        from julia_core.review.contracts import ReviewErrorCode
        raise ValueError(
            f"{ReviewErrorCode.REVIEW_DECISION_REJECTED.value}: candidate invalid: {errors}"
        )
    sealed = SealedCandidate(
        candidate_artifact_id=f"cand_art_{secrets.token_urlsafe(16)}",
        candidate=candidate,
        fingerprint=_candidate_fingerprint(candidate),
    )
    _TRUSTED_CANDIDATES[sealed.candidate_artifact_id] = (sealed, sealed.fingerprint)
    return sealed


def is_trusted_candidate(candidate: SealedCandidate) -> bool:
    """True only for the exact registered artifact with an unchanged full
    fingerprint (mutation via object.__setattr__ invalidates it)."""
    entry = _TRUSTED_CANDIDATES.get(candidate.candidate_artifact_id)
    if entry is None:
        return False
    ref, fingerprint = entry
    if ref is not candidate:
        return False
    return _candidate_fingerprint(candidate.candidate) == fingerprint


def candidate_fingerprint(candidate: ReviewDecisionCandidate) -> str:
    return _candidate_fingerprint(candidate)


__all__ = [
    "SealedCandidate",
    "candidate_fingerprint",
    "is_trusted_candidate",
    "seal_candidate",
]
