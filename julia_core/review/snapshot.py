"""Deep-sealed immutable ReviewBundle snapshot.

``frozen=True`` on ReviewBundle alone is insufficient because nested dict/list
payloads (diff_blocks, limits, identity_projection, ...) remain caller-mutable
aliases. Before any authority/digest creation we deep-copy the payload into a
canonical immutable snapshot and own the digest.

Required invariant:

    validate
    -> seal
    -> digest / request creation
    -> original caller object mutates
    -> trusted snapshot remains byte/semantic identical

Browser/session authority inserted into a caller-owned object AFTER validation
must never appear in the trusted snapshot / request.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from julia_core.review.contracts import ReviewBundle, validate_identity_isolation
from julia_core.review.digest import compute_text_digest


def _deep_freeze(value: Any) -> Any:
    """Recursively convert a value into an immutable tree.

    dict -> MappingProxyType-like frozen mapping
    list/tuple -> tuple
    set/frozenset -> frozenset
    primitives pass through.
    """
    if isinstance(value, dict):
        return _FrozenMapping({k: _deep_freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_deep_freeze(v) for v in value)
    return value


class _FrozenMapping(Mapping):
    """Hashable-by-content immutable mapping (canonical snapshot only)."""

    __slots__ = ("_data", "_hash")

    def __init__(self, data: dict[str, Any]):
        self._data = data
        self._hash = None

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return f"FrozenMapping({self._data!r})"

    def __eq__(self, other):
        if isinstance(other, _FrozenMapping):
            return self._data == other._data
        if isinstance(other, dict):
            return self._data == other
        return NotImplemented

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(sorted(self._data.items())))
        return self._hash

    def to_plain(self) -> dict[str, Any]:
        return _deep_unfreeze(self._data)


def _deep_unfreeze(value: Any) -> Any:
    if isinstance(value, _FrozenMapping):
        return {k: _deep_unfreeze(v) for k, v in value._data.items()}
    if isinstance(value, dict):
        return {k: _deep_unfreeze(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return tuple(_deep_unfreeze(v) for v in value)
    if isinstance(value, frozenset):
        return frozenset(_deep_unfreeze(v) for v in value)
    return value


@dataclass(frozen=True, slots=True)
class SealedReviewBundle:
    """Canonical immutable review payload snapshot.

    Owns its digest. ``to_payload()`` returns a FRESH deep copy every time so
    no caller can hold a mutable alias into the snapshot.
    """

    review_id: str
    task_id: str
    candidate_id: str
    candidate_sha: str
    repository: str
    branch: str
    review_mode: str
    objective: str
    payload: _FrozenMapping
    digest: str
    contract_version: str = "review_bundle.v1"

    def to_payload(self) -> dict[str, Any]:
        """Return a fresh deep copy of the immutable payload."""
        return _deep_unfreeze(self.payload)


def seal_review_bundle(bundle: ReviewBundle) -> SealedReviewBundle:
    """Deep-copy a ReviewBundle into an immutable snapshot and compute digest.

    Raises ValueError on schema/identity-isolation failure (fail closed BEFORE
    any digest / request authority is created).
    """
    errors = bundle.validate()
    if errors:
        from julia_core.review.contracts import ReviewErrorCode
        raise ValueError(f"{ReviewErrorCode.BUNDLE_SCHEMA_INVALID.value}: {'; '.join(errors)}")

    payload = _deep_freeze(bundle.to_dict())
    # Re-run identity isolation over the frozen tree (authority check).
    validate_identity_isolation(payload.to_plain())

    digest = compute_text_digest(_canonical_snapshot_serialization(payload.to_plain()))

    return SealedReviewBundle(
        review_id=bundle.review_id,
        task_id=bundle.task_id,
        candidate_id=bundle.candidate_id,
        candidate_sha=bundle.candidate_sha,
        repository=bundle.repository,
        branch=bundle.branch,
        review_mode=bundle.review_mode,
        objective=bundle.objective,
        payload=payload,
        digest=digest,
        contract_version=bundle.contract_version,
    )


def _canonical_snapshot_serialization(payload: dict[str, Any]) -> str:
    import json
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def snapshot_digest(snapshot: SealedReviewBundle) -> str:
    """Digest belongs to the immutable snapshot, not a caller object."""
    return snapshot.digest


__all__ = ["SealedReviewBundle", "seal_review_bundle", "snapshot_digest"]
