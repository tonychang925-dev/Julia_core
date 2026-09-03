"""Trusted ReviewDecisionCandidate artifact authority.

Governance never upgrades a caller-constructed ``ReviewDecisionCandidate``.
An admissible artifact must associate all of the following by exact object
identity:

* one trusted candidate-creator binding;
* one raw-response observation produced from a trusted invocation;
* the complete semantic fingerprint of the candidate.

Production creator bindings start UNBOUND. Therefore the positive creation path
is intentionally unavailable in production and governance fails closed until a
canonical creator integration introduces its own source-truth-backed binding.
"""

from __future__ import annotations

import json as _json
import secrets
import time as _time
from dataclasses import dataclass, field
from typing import Any

from julia_core.review.contracts import ReviewDecisionCandidate
from julia_core.review.digest import compute_text_digest
from julia_core.review.source_binding import (
    CandidateCreatorBinding,
    _resolve_creator,
    is_trusted_candidate_creator,
)


_CANDIDATE_AUTHORITY_FIELDS = (
    "contract_version",
    "review_id",
    "candidate_id",
    "candidate_sha",
    "source",
    "verdict",
    "findings",
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
    return _json.dumps(
        authority,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


@dataclass(frozen=True, slots=True)
class _RawResponseObservation:
    """Core-owned observation identity for one trusted execution."""

    observation_id: str
    invocation_id: str
    raw_response_ref: str
    raw_response_digest: str
    raw_response: str


_RAW_OBSERVATIONS: dict[str, tuple[_RawResponseObservation, Any, str]] = {}


def _raw_observation_fingerprint(observation: _RawResponseObservation) -> str:
    data = {
        "observation_id": observation.observation_id,
        "invocation_id": observation.invocation_id,
        "raw_response_ref": observation.raw_response_ref,
        "raw_response_digest": observation.raw_response_digest,
        "raw_response": observation.raw_response,
    }
    return _json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def is_trusted_raw_observation(observation: Any) -> bool:
    """True only for the exact registered observation of a trusted invocation."""
    from julia_core.review.invocation import is_trusted_invocation

    if not isinstance(observation, _RawResponseObservation):
        return False
    entry = _RAW_OBSERVATIONS.get(observation.observation_id)
    if entry is None:
        return False
    reference, invocation, fingerprint = entry
    return (
        reference is observation
        and invocation.invocation_id == observation.invocation_id
        and is_trusted_invocation(invocation)
        and _raw_observation_fingerprint(observation) == fingerprint
    )


def observe_raw_response(invocation) -> _RawResponseObservation:
    """Create the Core-owned observation used by a bound creator.

    This observation is not candidate authority by itself. It only names the
    exact trusted raw response that a later creator binding must consume.
    """
    from julia_core.review.invocation import is_trusted_invocation

    if not is_trusted_invocation(invocation):
        raise ValueError("raw response observation requires a trusted invocation")
    result = invocation.execution.tool_result
    structured = result.structured_output if result is not None else None
    structured = structured or {}
    raw_response = structured.get("raw_response")
    if not isinstance(raw_response, str) or not raw_response:
        raise ValueError("trusted invocation contains no observable raw response")

    call_id = result.capability_call_id if result is not None else ""
    observation = _RawResponseObservation(
        observation_id=f"raw_obs_{secrets.token_urlsafe(16)}",
        invocation_id=invocation.invocation_id,
        raw_response_ref=f"tool_result:{call_id}:raw_response",
        raw_response_digest=compute_text_digest(raw_response),
        raw_response=raw_response,
    )
    _RAW_OBSERVATIONS[observation.observation_id] = (
        observation,
        invocation,
        _raw_observation_fingerprint(observation),
    )
    return observation


@dataclass(frozen=True, slots=True)
class SealedCandidate:
    """A candidate artifact bound to an exact creator and raw observation."""

    candidate_artifact_id: str
    candidate: ReviewDecisionCandidate
    fingerprint: str
    creator_binding_id: str
    raw_observation_id: str
    created_at: str = field(
        default_factory=lambda: _time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", _time.gmtime()
        )
    )


@dataclass(frozen=True, slots=True)
class _CandidateAuthority:
    sealed: SealedCandidate
    fingerprint: str
    creator_binding: CandidateCreatorBinding
    creator: Any
    raw_observation: _RawResponseObservation
    invocation: Any
    invocation_id: str


_TRUSTED_CANDIDATES: dict[str, _CandidateAuthority] = {}


def _seal_candidate_with_trusted_authorities(
    candidate: ReviewDecisionCandidate,
    *,
    creator_binding: CandidateCreatorBinding,
    creator: Any,
    raw_observation: _RawResponseObservation,
) -> SealedCandidate:
    """Seal one candidate through an exact creator and raw observation.

    This is deliberately not a generic public upgrade function. It requires an
    already trusted creator binding whose exact registered creator object is
    supplied, plus the exact trusted raw observation.
    """
    if not is_trusted_candidate_creator(creator_binding):
        raise ValueError("candidate creator binding is not trusted")
    try:
        registered_creator = _resolve_creator(creator_binding)
    except ValueError as exc:
        raise ValueError("candidate creator binding is not trusted") from exc
    if registered_creator is not creator:
        raise ValueError("candidate was not produced by the exact bound creator")
    if not is_trusted_raw_observation(raw_observation):
        raise ValueError("raw response observation is not trusted")

    errors = candidate.validate_minimum()
    if errors:
        raise ValueError(f"candidate invalid: {errors}")
    if candidate.raw_response_ref != raw_observation.raw_response_ref:
        raise ValueError("candidate raw_response_ref does not match observation")
    if candidate.raw_response_digest != raw_observation.raw_response_digest:
        raise ValueError("candidate raw_response_digest does not match observation")

    fingerprint = _candidate_fingerprint(candidate)
    sealed = SealedCandidate(
        candidate_artifact_id=f"cand_art_{secrets.token_urlsafe(16)}",
        candidate=candidate,
        fingerprint=fingerprint,
        creator_binding_id=creator_binding.binding_id,
        raw_observation_id=raw_observation.observation_id,
    )
    _TRUSTED_CANDIDATES[sealed.candidate_artifact_id] = _CandidateAuthority(
        sealed=sealed,
        fingerprint=fingerprint,
        creator_binding=creator_binding,
        creator=creator,
        raw_observation=raw_observation,
        invocation=_registered_invocation(raw_observation),
        invocation_id=raw_observation.invocation_id,
    )
    return sealed


def is_trusted_candidate(candidate: Any) -> bool:
    """Verify artifact ID, creator, raw observation, and all fingerprints."""
    if not isinstance(candidate, SealedCandidate):
        return False
    authority = _TRUSTED_CANDIDATES.get(candidate.candidate_artifact_id)
    if authority is None or authority.sealed is not candidate:
        return False
    if not is_trusted_candidate_creator(authority.creator_binding):
        return False
    if candidate.creator_binding_id != authority.creator_binding.binding_id:
        return False
    if not is_trusted_raw_observation(authority.raw_observation):
        return False
    if candidate.raw_observation_id != authority.raw_observation.observation_id:
        return False
    if authority.invocation_id != authority.raw_observation.invocation_id:
        return False

    recomputed = _candidate_fingerprint(candidate.candidate)
    return (
        candidate.fingerprint == authority.fingerprint
        and recomputed == authority.fingerprint
        and candidate.candidate.raw_response_ref
        == authority.raw_observation.raw_response_ref
        and candidate.candidate.raw_response_digest
        == authority.raw_observation.raw_response_digest
    )


def _candidate_authority(candidate: Any) -> _CandidateAuthority | None:
    """Return verified association state, or ``None`` if untrusted."""
    if not is_trusted_candidate(candidate):
        return None
    return _TRUSTED_CANDIDATES.get(candidate.candidate_artifact_id)


def _registered_invocation(observation: _RawResponseObservation) -> Any:
    entry = _RAW_OBSERVATIONS.get(observation.observation_id)
    if entry is None:
        raise ValueError("raw response observation is not trusted")
    return entry[1]


def candidate_fingerprint(candidate: ReviewDecisionCandidate) -> str:
    """Recompute the pure semantic fingerprint (not authority by itself)."""
    return _candidate_fingerprint(candidate)


__all__ = [
    "SealedCandidate",
    "candidate_fingerprint",
    "is_trusted_candidate",
    "is_trusted_raw_observation",
    "observe_raw_response",
]
