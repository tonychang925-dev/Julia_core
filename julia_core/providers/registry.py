"""Provider Registry — domain-independent infrastructure.

Registry is a LOOKUP TABLE. It is NOT a domain router.
It does not rank, compare, recommend, or select providers.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from julia_core.providers.interface import DomainProvider


# ── Exceptions ──

class ProviderNotFoundError(Exception):
    pass


class DuplicateProviderError(Exception):
    pass


# ── Identity ──

@dataclass(frozen=True, slots=True)
class ProviderIdentity:
    provider_id: str
    provider_name: str
    version: str
    domain: str
    capabilities: tuple[str, ...]


# ── State ──

class ProviderState(str, enum.Enum):
    REGISTERED = "registered"
    READY = "ready"
    ACTIVE = "active"
    DISABLED = "disabled"


# ── Record ──

@dataclass(slots=True)
class ProviderRecord:
    provider: DomainProvider
    identity: ProviderIdentity
    state: ProviderState = ProviderState.REGISTERED


# ── Registry ──

class ProviderRegistry:
    """Maps provider_id → ProviderRecord. Lookup only, no routing."""

    def __init__(self) -> None:
        self._records: dict[str, ProviderRecord] = {}

    # ── Registration ──

    def register(self, provider: DomainProvider) -> str:
        identity = provider.metadata()
        pid = identity.provider_id
        if pid in self._records:
            raise DuplicateProviderError(f"Provider '{pid}' already registered")
        self._records[pid] = ProviderRecord(provider=provider, identity=identity)
        return pid

    def activate(self, provider_id: str) -> None:
        record = self._records.get(provider_id)
        if record is None:
            return
        if record.state == ProviderState.DISABLED:
            return
        record.state = ProviderState.ACTIVE

    def disable(self, provider_id: str) -> None:
        record = self._records.get(provider_id)
        if record is None:
            return
        record.state = ProviderState.DISABLED

    # ── Lookup ──

    def get(self, provider_id: str) -> DomainProvider | None:
        record = self._records.get(provider_id)
        if record is None or record.state != ProviderState.ACTIVE:
            return None
        return record.provider

    def get_by_domain(self, domain: str) -> tuple[DomainProvider, ...]:
        return tuple(
            record.provider
            for record in self._records.values()
            if record.state == ProviderState.ACTIVE
            and record.identity.domain == domain
        )

    def list_active(self) -> tuple[str, ...]:
        return tuple(
            pid for pid, record in self._records.items()
            if record.state == ProviderState.ACTIVE
        )

    def list_capabilities(self) -> tuple[str, ...]:
        seen: set[str] = set()
        for record in self._records.values():
            if record.state == ProviderState.ACTIVE:
                seen.update(record.identity.capabilities)
        return tuple(sorted(seen))
