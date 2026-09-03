"""Pre-send trusted candidate admission authority.

This seam is intentionally distinct from ``CandidateShaSource``:

* candidate admission answers “what exact object may we send for review?”;
* CandidateShaSource answers “is that previously reviewed object still current?”.

Core owns record validation, binding trust, and the pre-send gate. The physical
repository resolver and admission history are composed by the trusted product
runtime; semantic request callers and providers cannot register authority.
"""

from __future__ import annotations

import json as _json
import secrets
import time as _time
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class CandidateAdmissionRecord:
    """Immutable authorization binding for one external review transmission."""

    review_id: str
    candidate_id: str
    repository: str
    candidate_sha: str

    def __post_init__(self) -> None:
        for name in ("review_id", "candidate_id", "repository", "candidate_sha"):
            value = str(getattr(self, name, ""))
            object.__setattr__(self, name, value)
            if not value.strip():
                raise ValueError(f"candidate admission field is empty: {name}")


class CandidateAdmissionSource(Protocol):
    """Trusted product-owned original-candidate admission source."""

    def candidate_admission(
        self,
        *,
        review_id: str,
        candidate_id: str,
    ) -> CandidateAdmissionRecord:
        """Return the immutable admission record for the exact review identity."""
        ...


@dataclass(frozen=True, slots=True)
class CandidateAdmissionSourceBinding:
    """Identity of one exact-object trusted admission composition."""

    binding_id: str
    created_at: str = field(
        default_factory=lambda: _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())
    )
    provenance: dict[str, Any] = field(default_factory=dict)


class CandidateAdmissionError(ValueError):
    """Raised when pre-send candidate admission authority is absent or invalid."""


def _binding_fingerprint(binding: CandidateAdmissionSourceBinding) -> str:
    authority = {
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


_ADMISSION_BINDINGS: dict[
    str,
    tuple[CandidateAdmissionSourceBinding, CandidateAdmissionSource, str],
] = {}


class CandidateAdmissionComposition:
    """Frozen, exact-object bridge from one trusted product source to Core.

    Construction is a product-boot composition act, not a semantic request
    operation. There is deliberately no registry-entry-point that can be called
    from provider payloads or ordinary request arguments.
    """

    __slots__ = ("_binding", "_source", "_frozen")

    def __init__(
        self,
        source: CandidateAdmissionSource,
        *,
        provenance: dict[str, Any] | None = None,
    ) -> None:
        if not callable(getattr(source, "candidate_admission", None)):
            raise TypeError("candidate admission source must implement candidate_admission()")
        binding = CandidateAdmissionSourceBinding(
            binding_id=f"cand_admission_{secrets.token_urlsafe(16)}",
            provenance=dict(provenance or {}),
        )
        object.__setattr__(self, "_binding", binding)
        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_frozen", True)
        _ADMISSION_BINDINGS[binding.binding_id] = (
            binding,
            source,
            _binding_fingerprint(binding),
        )

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_frozen", False):
            raise AttributeError(
                f"CandidateAdmissionComposition is frozen; cannot set {name!r}"
            )
        object.__setattr__(self, name, value)

    @property
    def binding(self) -> CandidateAdmissionSourceBinding:
        return self._binding


def is_trusted_candidate_admission_binding(binding: Any) -> bool:
    """True only for the exact identity-registered, unchanged binding."""
    if not isinstance(binding, CandidateAdmissionSourceBinding):
        return False
    entry = _ADMISSION_BINDINGS.get(binding.binding_id)
    if entry is None:
        return False
    return (
        entry[0] is binding
        and _binding_fingerprint(binding) == entry[2]
    )


def _resolve_admission_source(
    binding: CandidateAdmissionSourceBinding,
) -> CandidateAdmissionSource:
    if not is_trusted_candidate_admission_binding(binding):
        raise CandidateAdmissionError("candidate admission binding is not trusted")
    entry = _ADMISSION_BINDINGS[binding.binding_id]
    return entry[1]


def resolve_candidate_admission(
    binding: Any,
    *,
    review_id: str,
    candidate_id: str,
) -> CandidateAdmissionRecord:
    """Resolve and shape-check one immutable original-candidate admission."""
    source = _resolve_admission_source(binding)
    try:
        admission = source.candidate_admission(
            review_id=review_id,
            candidate_id=candidate_id,
        )
    except Exception as exc:
        raise CandidateAdmissionError(
            f"candidate admission lookup failed: {type(exc).__name__}"
        ) from exc
    if not isinstance(admission, CandidateAdmissionRecord):
        raise CandidateAdmissionError("candidate admission source returned invalid record")
    if admission.review_id != review_id or admission.candidate_id != candidate_id:
        raise CandidateAdmissionError("candidate admission lookup returned foreign identity")
    return admission


def assert_candidate_admission(
    binding: Any,
    *,
    review_id: str,
    candidate_id: str,
    repository: str,
    candidate_sha: str,
) -> CandidateAdmissionRecord:
    """Fail closed unless the bundle matches trusted pre-send admission truth."""
    admission = resolve_candidate_admission(
        binding,
        review_id=review_id,
        candidate_id=candidate_id,
    )
    expected = (review_id, candidate_id, repository, candidate_sha)
    supplied = (
        admission.review_id,
        admission.candidate_id,
        admission.repository,
        admission.candidate_sha,
    )
    if supplied != expected:
        raise CandidateAdmissionError(
            "ReviewBundle does not match trusted candidate admission: "
            f"admission={supplied!r}, bundle={expected!r}"
        )
    return admission


__all__ = [
    "CandidateAdmissionComposition",
    "CandidateAdmissionError",
    "CandidateAdmissionRecord",
    "CandidateAdmissionSource",
    "CandidateAdmissionSourceBinding",
    "assert_candidate_admission",
    "is_trusted_candidate_admission_binding",
    "resolve_candidate_admission",
]
