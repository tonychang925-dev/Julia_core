"""Trusted CandidateShaSource / CandidateCreator binding registries (round-6 §B).

PRODUCTION state: no canonical Git CandidateShaSource and no canonical review
parser/creator exist. Therefore:

    production CandidateShaSource   = UNBOUND
    production CandidateCreator     = UNBOUND

and governance FAILS CLOSED when unbound. There is NO production binder here —
arbitrary duck-typed adapters cannot be registered. Test-only bindings live in
julia_core.review._test_only and are NOT part of the production review surface.

Future canonical repository/parser adapters may add their own trusted
composition without changing the Core semantic contract.
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

    Identity is enforced by the module registry; the binding carries only an
    opaque binding_id. Created only through the test/integration seam.
    """

    binding_id: str
    created_at: str = field(default_factory=lambda: _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()))
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CandidateCreatorBinding:
    """Trusted binding of a raw-response -> ReviewDecisionCandidate creator.

    Identity enforced by the module registry. Without a trusted creator,
    candidate admission FAILS CLOSED.
    """

    binding_id: str
    created_at: str = field(default_factory=lambda: _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()))
    provenance: dict[str, Any] = field(default_factory=dict)


_TRUSTED_BINDINGS: dict[str, tuple[CandidateShaSourceBinding, Any]] = {}
_CREATOR_BINDINGS: dict[str, tuple[CandidateCreatorBinding, Any]] = {}


def _register_source_binding(binding: CandidateShaSourceBinding, adapter: Any) -> None:
    _TRUSTED_BINDINGS[binding.binding_id] = (binding, adapter)


def _register_creator_binding(binding: CandidateCreatorBinding, creator: Any) -> None:
    _CREATOR_BINDINGS[binding.binding_id] = (binding, creator)


def _make_source_binding() -> CandidateShaSourceBinding:
    return CandidateShaSourceBinding(binding_id=f"sha_src_{secrets.token_urlsafe(16)}")


def _make_creator_binding() -> CandidateCreatorBinding:
    return CandidateCreatorBinding(binding_id=f"cand_creator_{secrets.token_urlsafe(16)}")


def _resolve_adapter(binding: CandidateShaSourceBinding):
    entry = _TRUSTED_BINDINGS.get(binding.binding_id)
    if entry is None:
        raise ValueError("candidate SHA source binding is not trusted")
    ref, adapter = entry
    if ref is not binding:
        raise ValueError("candidate SHA source binding object is not the trusted one")
    return adapter


def _resolve_creator(binding: CandidateCreatorBinding):
    entry = _CREATOR_BINDINGS.get(binding.binding_id)
    if entry is None:
        raise ValueError("candidate creator binding is not trusted")
    ref, creator = entry
    if ref is not binding:
        raise ValueError("candidate creator binding object is not the trusted one")
    return creator


def is_trusted_source_binding(binding: Any) -> bool:
    """True only for an identity-registered source binding."""
    if not isinstance(binding, CandidateShaSourceBinding):
        return False
    entry = _TRUSTED_BINDINGS.get(binding.binding_id)
    if entry is None:
        return False
    return entry[0] is binding


def is_trusted_candidate_creator(binding: Any) -> bool:
    if not isinstance(binding, CandidateCreatorBinding):
        return False
    entry = _CREATOR_BINDINGS.get(binding.binding_id)
    if entry is None:
        return False
    return entry[0] is binding


__all__ = [
    "CandidateCreatorBinding",
    "CandidateShaSourceBinding",
    "_make_creator_binding",
    "_make_source_binding",
    "_register_creator_binding",
    "_register_source_binding",
    "_resolve_adapter",
    "_resolve_creator",
    "is_trusted_candidate_creator",
    "is_trusted_source_binding",
]
