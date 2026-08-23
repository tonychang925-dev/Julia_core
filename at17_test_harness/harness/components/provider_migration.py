"""M8.0 §P9.2 / AT17-R1-011 — Provider Migration component model.

Provider changes affect the execution substrate (model provider adapters,
inference engine). Per M8.0:

    Provider Change != Identity Change
    Migration != Identity Replacement

The component may migrate between providers (substrate swap), but physically
does not expose identity replacement. Any attempt to route `replace_julia`
through it must be intercepted by the boundary guard and rejected.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _ProviderEntry:
    provider_id: str
    active: bool = False


class ProviderMigration:
    """Provider substrate migration surface. Never an identity authority."""

    def __init__(self) -> None:
        self._providers: dict[str, _ProviderEntry] = {}
        self._migrations: list[dict] = []

    # ── Legal capabilities (execution substrate scope only) ───────────────
    def register_provider(self, provider_id: str) -> str:
        self._providers[provider_id] = _ProviderEntry(provider_id=provider_id)
        return provider_id

    def migrate_provider(self, from_id: str, to_id: str) -> str:
        """Legal migration: swaps execution substrate only.

        Never replaces Julia continuity identity.
        """
        self._providers[from_id].active = False
        self._providers[to_id].active = True
        self._migrations.append({"from": from_id, "to": to_id})
        return to_id

    def list_providers(self) -> dict:
        return {
            pid: e.active
            for pid, e in self._providers.items()
        }

    # ── Snapshot (for mutation-proof) ─────────────────────────────────────
    def snapshot(self) -> dict:
        return {
            "providers": {
                pid: e.active
                for pid, e in self._providers.items()
            },
            "migrations": [dict(row) for row in self._migrations],
        }
