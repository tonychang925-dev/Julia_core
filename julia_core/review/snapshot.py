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


# Trusted-creator registry: only seal_review_bundle() may register a snapshot.
# Identity-based (object reference) so handcrafted / reconstructed snapshots are
# NOT trusted even when field-for-field identical. The full sealed authority
# state is fingerprinted at creation and re-verified on every trust check, so
# object.__setattr__ mutations of ANY authority field invalidate trust.
_TRUSTED_SNAPSHOTS: dict[str, tuple[Any, str]] = {}  # snapshot_id -> (ref, full_fingerprint)


@dataclass(frozen=True, slots=True)
class SealedReviewBundle:
    """Canonical immutable review payload snapshot.

    Owns its digest. ``to_payload()`` returns a FRESH deep copy every time so
    no caller can hold a mutable alias into the snapshot.

    Trusted-creator semantics: a snapshot is TRUSTED only if it was produced by
    seal_review_bundle() and is identity-registered in the module registry.
    Handcrafted / copied / reconstructed snapshots are NOT trusted (P1-D).
    """

    snapshot_id: str
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


_SNAPSHOT_AUTHORITY_FIELDS = (
    "snapshot_id",
    "contract_version",
    "review_id",
    "task_id",
    "candidate_id",
    "candidate_sha",
    "repository",
    "branch",
    "review_mode",
    "objective",
    "digest",
)


def _snapshot_fingerprint(snapshot: SealedReviewBundle) -> str:
    """Canonical fingerprint of the full sealed authority state.

    Binds every top-level authority field + the canonical immutable payload, so
    mutation through object.__setattr__ of any authority field invalidates the
    fingerprint.
    """
    authority: dict[str, Any] = {}
    for name in _SNAPSHOT_AUTHORITY_FIELDS:
        authority[name] = getattr(snapshot, name)
    authority["payload"] = _deep_unfreeze(snapshot.payload)
    import json
    return compute_text_digest(
        json.dumps(authority, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def is_trusted_snapshot(snapshot: SealedReviewBundle) -> bool:
    """Return True only for the identity-registered snapshot with an
    unmodified full authority fingerprint."""
    entry = _TRUSTED_SNAPSHOTS.get(snapshot.snapshot_id)
    if entry is None:
        return False
    ref, sealed_fingerprint = entry
    if ref is not snapshot:
        return False
    return _snapshot_fingerprint(snapshot) == sealed_fingerprint


def seal_review_bundle(bundle: ReviewBundle) -> SealedReviewBundle:
    """Deep-copy a ReviewBundle into an immutable snapshot and compute digest.

    Raises ValueError on schema/identity-isolation failure (fail closed BEFORE
    any digest / request authority is created). Registers the snapshot in the
    trusted-creator registry (identity-based) so handcrafted snapshots are NOT
    trusted (P1-D).
    """
    import secrets

    errors = bundle.validate()
    if errors:
        from julia_core.review.contracts import ReviewErrorCode
        raise ValueError(f"{ReviewErrorCode.BUNDLE_SCHEMA_INVALID.value}: {'; '.join(errors)}")

    payload = _deep_freeze(bundle.to_dict())
    # Re-run identity isolation over the frozen tree (authority check).
    validate_identity_isolation(payload.to_plain())

    digest = compute_text_digest(_canonical_snapshot_serialization(payload.to_plain()))

    snapshot = SealedReviewBundle(
        snapshot_id=f"sealed_{secrets.token_urlsafe(16)}",
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
    _TRUSTED_SNAPSHOTS[snapshot.snapshot_id] = (snapshot, _snapshot_fingerprint(snapshot))
    return snapshot


def _canonical_snapshot_serialization(payload: dict[str, Any]) -> str:
    import json
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def snapshot_digest(snapshot: SealedReviewBundle) -> str:
    """Digest belongs to the immutable snapshot, not a caller object."""
    return snapshot.digest


__all__ = ["SealedReviewBundle", "is_trusted_snapshot", "seal_review_bundle", "snapshot_digest"]
