"""Trusted CandidateShaSource binding (E6-E9).

A bare Python Protocol / duck-typed object is NOT provenance. The only way to
bind a candidate-SHA source is through ``bind_candidate_sha_source()``, a
Core-owned trusted creator that registers the binding by identity.

The governance service accepts ONLY a trusted binding; an arbitrary object
(FakeSource) cannot become production SHA authority. A custom ``__setattr__``
lock alone is insufficient because ``object.__setattr__`` can bypass it — the
authority lives in the identity registry here.

Concrete Git adapter remains NOT IMPLEMENTED; until a canonical repository
adapter is bound, the service stays safely UNBOUND and stale validation fails
closed.
"""

from __future__ import annotations

import secrets
import time as _time
from dataclasses import dataclass, field
from typing import Any

from julia_core.review.validation import CandidateShaSource


@dataclass(frozen=True, slots=True)
class CandidateShaSourceBinding:
    """A trusted binding of a candidate-SHA source.

    Created ONLY by bind_candidate_sha_source(). The ``binding_id`` is random;
    identity is enforced by the module registry.
    """

    binding_id: str
    created_at: str = field(default_factory=lambda: _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()))
    provenance: dict[str, Any] = field(default_factory=dict)

    def current_candidate_sha(self, *, review_id: str, candidate_id: str) -> str:
        from julia_core.review.source_binding import _resolve_adapter
        adapter = _resolve_adapter(self)
        return adapter.current_candidate_sha(review_id=review_id, candidate_id=candidate_id)


_TRUSTED_BINDINGS: dict[str, tuple[CandidateShaSourceBinding, Any]] = {}


def bind_candidate_sha_source(adapter: CandidateShaSource) -> CandidateShaSourceBinding:
    """TEST/INTEGRATION trusted creator: bind a source adapter once.

    NOT exported on the public production surface (round-5 §5). Production
    source authority stays UNBOUND -> stale validation fails closed. A later
    canonical repository adapter may add the trusted production binding without
    altering the semantic contract. The adapter object itself is stored in the
    registry; the returned binding carries only an opaque binding_id.
    """
    if not callable(getattr(adapter, "current_candidate_sha", None)):
        raise TypeError("candidate SHA source must provide current_candidate_sha()")
    binding = CandidateShaSourceBinding(binding_id=f"sha_src_{secrets.token_urlsafe(16)}")
    _TRUSTED_BINDINGS[binding.binding_id] = (binding, adapter)
    return binding


# ── Trusted candidate creator binding (§6) ───────────────────────────────────

@dataclass(frozen=True, slots=True)
class CandidateCreatorBinding:
    """Trusted binding of a raw-response -> ReviewDecisionCandidate creator.

    Created ONLY by bind_candidate_creator(). Without a trusted creator/parser,
    candidate admission FAILS CLOSED.
    """

    binding_id: str
    created_at: str = field(default_factory=lambda: _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()))
    provenance: dict[str, Any] = field(default_factory=dict)


_CREATOR_BINDINGS: dict[str, tuple[CandidateCreatorBinding, Any]] = {}


def bind_candidate_creator(creator: Any) -> CandidateCreatorBinding:
    """TEST/INTEGRATION trusted creator binding (round-5 §6).

    NOT exported on the public production surface. A future provider/parser
    integration supplies the implementation through this explicit trusted seam.
    """
    if not callable(getattr(creator, "create_candidate", None)):
        raise TypeError("candidate creator must provide create_candidate()")
    binding = CandidateCreatorBinding(binding_id=f"cand_creator_{secrets.token_urlsafe(16)}")
    _CREATOR_BINDINGS[binding.binding_id] = (binding, creator)
    return binding


def _resolve_creator(binding: CandidateCreatorBinding):
    entry = _CREATOR_BINDINGS.get(binding.binding_id)
    if entry is None:
        raise ValueError("candidate creator binding is not trusted")
    ref, creator = entry
    if ref is not binding:
        raise ValueError("candidate creator binding object is not the trusted one")
    return creator


def is_trusted_candidate_creator(binding: Any) -> bool:
    if not isinstance(binding, CandidateCreatorBinding):
        return False
    entry = _CREATOR_BINDINGS.get(binding.binding_id)
    if entry is None:
        return False
    return entry[0] is binding


def _resolve_adapter(binding: CandidateShaSourceBinding):
    entry = _TRUSTED_BINDINGS.get(binding.binding_id)
    if entry is None:
        raise ValueError("candidate SHA source binding is not trusted")
    ref, adapter = entry
    if ref is not binding:
        raise ValueError("candidate SHA source binding object is not the trusted one")
    return adapter


def is_trusted_source_binding(binding: Any) -> bool:
    """True only for an identity-registered source binding."""
    if not isinstance(binding, CandidateShaSourceBinding):
        return False
    entry = _TRUSTED_BINDINGS.get(binding.binding_id)
    if entry is None:
        return False
    return entry[0] is binding


__all__ = [
    "CandidateCreatorBinding",
    "CandidateShaSourceBinding",
    "bind_candidate_creator",
    "bind_candidate_sha_source",
    "is_trusted_candidate_creator",
    "is_trusted_source_binding",
]
