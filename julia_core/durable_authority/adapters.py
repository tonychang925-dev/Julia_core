"""Backend-neutral durable authority adapter contracts."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from julia_core.identity import IdentityRef
from julia_core.memory_experience import MemoryExperienceRef
from julia_core.runtime_canonical_binding import (
    RuntimeCanonicalAuthorityBindingRef,
)

from .contracts import AuthorityFamily, DurableAuthorityEnvelope


@runtime_checkable
class DurableAuthorityReader(Protocol):
    def read_exact(
        self,
        authority_family: AuthorityFamily,
        ref: IdentityRef | MemoryExperienceRef | RuntimeCanonicalAuthorityBindingRef,
    ) -> DurableAuthorityEnvelope:
        """Return one exact durable envelope or fail closed."""

    def list_exact_refs(self, authority_family: AuthorityFamily) -> tuple[str, ...]:
        """Return persisted exact ref URIs for restoration mechanics only."""


@runtime_checkable
class DurableAuthorityWriter(Protocol):
    def write_exact(self, envelope: DurableAuthorityEnvelope) -> None:
        """Persist one immutable envelope or fail closed."""


__all__ = [
    "DurableAuthorityReader",
    "DurableAuthorityWriter",
]
