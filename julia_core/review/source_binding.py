"""Trusted CandidateShaSource / CandidateCreator binding registries (round-6 §B).

PRODUCTION state: no canonical Git CandidateShaSource exists, and the only
canonical review creator binding is the narrowly registered Core machine-review
parser. Therefore:

    production CandidateShaSource   = UNBOUND
    production CandidateCreator     = Core review parser binding only

and governance FAILS CLOSED when unbound. There is NO production binder,
factory, or arbitrary-adapter registrar here. Test-only bindings live outside
the installed production package under ``tests/``.

Future canonical repository adapters may add their own trusted composition
without changing the Core semantic contract. Additional parser/creator
adapters still have no generic public registrar.
"""

from __future__ import annotations

import json as _json
import time as _time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CandidateShaSourceBinding:
    """Identity of a candidate-SHA source binding.

    Production starts with no registered binding. The module registry enforces
    exact object identity; the public class constructor alone creates no trust.
    """

    binding_id: str
    created_at: str = field(default_factory=lambda: _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()))
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CandidateCreatorBinding:
    """Identity of a raw-response -> candidate creator binding.

    Production starts with no registered binding. The exact-object registry and
    creator/artifact association enforce trust; constructing or copying this
    dataclass creates no authority.
    """

    binding_id: str
    created_at: str = field(default_factory=lambda: _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()))
    provenance: dict[str, Any] = field(default_factory=dict)


_TRUSTED_BINDINGS: dict[str, tuple[CandidateShaSourceBinding, Any, str]] = {}
_CREATOR_BINDINGS: dict[str, tuple[CandidateCreatorBinding, Any, str]] = {}


def _binding_fingerprint(binding: CandidateShaSourceBinding | CandidateCreatorBinding) -> str:
    authority = {
        "type": type(binding).__name__,
        "binding_id": binding.binding_id,
        "created_at": binding.created_at,
        "provenance": binding.provenance,
    }
    return _json.dumps(
        authority,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _resolve_adapter(binding: CandidateShaSourceBinding):
    entry = _TRUSTED_BINDINGS.get(binding.binding_id)
    if entry is None:
        raise ValueError("candidate SHA source binding is not trusted")
    ref, adapter, fingerprint = entry
    if ref is not binding:
        raise ValueError("candidate SHA source binding object is not the trusted one")
    if _binding_fingerprint(binding) != fingerprint:
        raise ValueError("candidate SHA source binding has changed")
    return adapter


def _resolve_creator(binding: CandidateCreatorBinding):
    entry = _CREATOR_BINDINGS.get(binding.binding_id)
    if entry is None:
        raise ValueError("candidate creator binding is not trusted")
    ref, creator, fingerprint = entry
    if ref is not binding:
        raise ValueError("candidate creator binding object is not the trusted one")
    if _binding_fingerprint(binding) != fingerprint:
        raise ValueError("candidate creator binding has changed")
    return creator


def is_trusted_source_binding(binding: Any) -> bool:
    """True only for an identity-registered source binding."""
    if not isinstance(binding, CandidateShaSourceBinding):
        return False
    entry = _TRUSTED_BINDINGS.get(binding.binding_id)
    if entry is None:
        return False
    return entry[0] is binding and _binding_fingerprint(binding) == entry[2]


def is_trusted_candidate_creator(binding: Any) -> bool:
    if not isinstance(binding, CandidateCreatorBinding):
        return False
    entry = _CREATOR_BINDINGS.get(binding.binding_id)
    if entry is None:
        return False
    return entry[0] is binding and _binding_fingerprint(binding) == entry[2]


__all__ = [
    "CandidateCreatorBinding",
    "CandidateShaSourceBinding",
    "_resolve_adapter",
    "_resolve_creator",
    "_binding_fingerprint",
    "is_trusted_candidate_creator",
    "is_trusted_source_binding",
]
