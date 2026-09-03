"""Trusted process composition for the current-candidate SHA source.

Core owns the binding and admission authority. The physical repository/current
mapping source is composed once by trusted product boot; semantic requests and
providers cannot install or replace it. The installer and its exact authority
object are intentionally private and absent from the public review API.
"""

from __future__ import annotations

import secrets
import time
from typing import Any

from julia_core.review.source_binding import (
    CandidateShaSourceBinding,
    _TRUSTED_BINDINGS,
    _binding_fingerprint,
)


class CandidateShaSourceCompositionError(ValueError):
    """Raised when trusted current-source composition is absent or invalid."""


_CURRENT_SOURCE_COMPOSITION_AUTHORITY = object()
_INSTALLED_CURRENT_SOURCE: tuple[
    CandidateShaSourceBinding,
    Any,
    str,
] | None = None


def _install_current_candidate_sha_source(
    source: Any,
    *,
    composition_authority: object,
    provenance: dict[str, Any] | None = None,
) -> CandidateShaSourceBinding:
    """Install the one process-lifetime current-candidate source composition."""
    global _INSTALLED_CURRENT_SOURCE
    if composition_authority is not _CURRENT_SOURCE_COMPOSITION_AUTHORITY:
        raise CandidateShaSourceCompositionError(
            "current candidate source composition authority is invalid"
        )
    if _INSTALLED_CURRENT_SOURCE is not None:
        installed_binding, installed_source, _ = _INSTALLED_CURRENT_SOURCE
        if installed_source is source:
            return installed_binding
        raise CandidateShaSourceCompositionError(
            "current candidate source is already installed"
        )
    if not callable(getattr(source, "current_candidate_sha", None)):
        raise TypeError(
            "current candidate source must implement current_candidate_sha()"
        )

    binding = CandidateShaSourceBinding(
        binding_id=f"current_sha_{secrets.token_urlsafe(16)}",
        provenance=dict(provenance or {}),
    )
    try:
        fingerprint = _binding_fingerprint(binding)
    except (TypeError, ValueError) as exc:
        raise CandidateShaSourceCompositionError(
            "current candidate source provenance is not canonically serializable"
        ) from exc
    _TRUSTED_BINDINGS[binding.binding_id] = (binding, source, fingerprint)
    _INSTALLED_CURRENT_SOURCE = (binding, source, fingerprint)
    return binding


def _reset_current_candidate_sha_source_composition_for_tests() -> None:
    """Reset the one-shot current-source composition between test fixtures."""
    global _INSTALLED_CURRENT_SOURCE
    if _INSTALLED_CURRENT_SOURCE is not None:
        _TRUSTED_BINDINGS.pop(_INSTALLED_CURRENT_SOURCE[0].binding_id, None)
    _INSTALLED_CURRENT_SOURCE = None


def current_candidate_sha_source_binding() -> CandidateShaSourceBinding:
    """Return the exact installed binding, or fail closed when absent."""
    if _INSTALLED_CURRENT_SOURCE is None:
        raise CandidateShaSourceCompositionError(
            "current candidate SHA source is not installed"
        )
    return _INSTALLED_CURRENT_SOURCE[0]


def has_current_candidate_sha_source() -> bool:
    """True only when the exact installed binding remains unchanged."""
    if _INSTALLED_CURRENT_SOURCE is None:
        return False
    binding, _, fingerprint = _INSTALLED_CURRENT_SOURCE
    entry = _TRUSTED_BINDINGS.get(binding.binding_id)
    return (
        entry is not None
        and entry[0] is binding
        and _binding_fingerprint(binding) == fingerprint == entry[2]
    )


__all__ = [
    "CandidateShaSourceCompositionError",
    "current_candidate_sha_source_binding",
    "has_current_candidate_sha_source",
]
