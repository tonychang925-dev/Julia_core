"""Pre-send trusted candidate admission authority.

This seam is intentionally distinct from ``CandidateShaSource``:

* candidate admission answers “what exact object may we send for review?”;
* CandidateShaSource answers “is that previously reviewed object still current?”.

Core owns record validation, binding trust, and the pre-send gate. The physical
repository resolver and admission history are composed by the trusted product
runtime; semantic request callers and providers cannot register authority.
"""

from __future__ import annotations

import hashlib
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

    def fingerprint(self) -> str:
        """Return the canonical historical admission-record fingerprint."""
        authority = {
            "review_id": self.review_id,
            "candidate_id": self.candidate_id,
            "repository": self.repository,
            "candidate_sha": self.candidate_sha,
        }
        serialized = _json.dumps(
            authority,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


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


_ADMISSION_COMPOSITION_AUTHORITY = object()
_INSTALLED_ADMISSION: tuple[
    CandidateAdmissionSourceBinding,
    CandidateAdmissionSource,
    str,
] | None = None


def _install_candidate_admission_source(
    source: CandidateAdmissionSource,
    *,
    composition_authority: object,
    provenance: dict[str, Any] | None = None,
) -> CandidateAdmissionSourceBinding:
    """Install the one process-lifetime product admission composition."""
    global _INSTALLED_ADMISSION
    if composition_authority is not _ADMISSION_COMPOSITION_AUTHORITY:
        raise CandidateAdmissionError("candidate admission composition authority is invalid")
    if _INSTALLED_ADMISSION is not None:
        raise CandidateAdmissionError("candidate admission source is already installed")
    if not callable(getattr(source, "candidate_admission", None)):
        raise TypeError("candidate admission source must implement candidate_admission()")

    binding = CandidateAdmissionSourceBinding(
        binding_id=f"cand_admission_{secrets.token_urlsafe(16)}",
        provenance=dict(provenance or {}),
    )
    try:
        fingerprint = _binding_fingerprint(binding)
    except (TypeError, ValueError) as exc:
        raise CandidateAdmissionError(
            "candidate admission provenance is not canonically serializable"
        ) from exc
    _INSTALLED_ADMISSION = (binding, source, fingerprint)
    return binding


def _reset_candidate_admission_composition_for_tests() -> None:
    """Reset the one-shot composition between isolated test fixtures."""
    global _INSTALLED_ADMISSION
    _INSTALLED_ADMISSION = None


def candidate_admission_binding() -> CandidateAdmissionSourceBinding:
    """Return the exact installed binding, or fail closed when absent."""
    if _INSTALLED_ADMISSION is None:
        raise CandidateAdmissionError("candidate admission source is not installed")
    return _INSTALLED_ADMISSION[0]


def is_trusted_candidate_admission_binding(binding: Any) -> bool:
    """True only for the exact installed, unchanged binding object."""
    if _INSTALLED_ADMISSION is None or not isinstance(
        binding, CandidateAdmissionSourceBinding
    ):
        return False
    installed, _, fingerprint = _INSTALLED_ADMISSION
    return installed is binding and _binding_fingerprint(binding) == fingerprint


def _resolve_admission_source(
    binding: CandidateAdmissionSourceBinding,
) -> CandidateAdmissionSource:
    if not is_trusted_candidate_admission_binding(binding):
        raise CandidateAdmissionError("candidate admission binding is not trusted")
    assert _INSTALLED_ADMISSION is not None
    return _INSTALLED_ADMISSION[1]


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
    *,
    review_id: str,
    candidate_id: str,
    repository: str,
    candidate_sha: str,
) -> CandidateAdmissionRecord:
    """Fail closed unless the bundle matches trusted pre-send admission truth."""
    binding = candidate_admission_binding()
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


def candidate_admission_audit(
    admission: CandidateAdmissionRecord,
) -> dict[str, str]:
    """Return Core-derived immutable admission audit metadata."""
    binding = candidate_admission_binding()
    if not is_trusted_candidate_admission_binding(binding):
        raise CandidateAdmissionError("candidate admission binding is not trusted")
    return {
        "binding_id": binding.binding_id,
        "admission_record_fingerprint": admission.fingerprint(),
    }


__all__ = [
    "CandidateAdmissionError",
    "CandidateAdmissionRecord",
    "CandidateAdmissionSource",
    "CandidateAdmissionSourceBinding",
    "assert_candidate_admission",
    "candidate_admission_audit",
    "candidate_admission_binding",
    "is_trusted_candidate_admission_binding",
    "resolve_candidate_admission",
]
