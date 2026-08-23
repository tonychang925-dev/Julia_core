"""M8.0 §5.4 — Lifecycle Manager component model (mock governance environment).

The Lifecycle Manager may:

    activate / suspend / archive / restore / rollback

Lifecycle events affect runtime availability ONLY. Per M8.0:

    Lifecycle Event != Identity Event
    rollback != history rewrite
    archive != semantic deletion

The component physically does not expose lineage/history rewrite operations.
Any attempt to route lineage-overwrite or history-rewrite operations through
it must be intercepted by the boundary guard and rejected.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _VersionState:
    version: str
    state: str = "registered"          # registered | active | suspended | archived


class PersonaLifecycle:
    """Runtime availability lifecycle manager. Never a lineage/history authority."""

    def __init__(self) -> None:
        self._versions: dict[str, _VersionState] = {}
        self._history_log: list[dict] = []

    # ── Legal capabilities (availability scope only) ──────────────────────
    def register_version(self, version: str) -> str:
        self._versions[version] = _VersionState(version=version)
        self._history_log.append({"event": "register", "version": version})
        return version

    def activate(self, version: str) -> str:
        self._versions[version].state = "active"
        self._history_log.append({"event": "activate", "version": version})
        return version

    def suspend(self, version: str) -> str:
        self._versions[version].state = "suspended"
        self._history_log.append({"event": "suspend", "version": version})
        return version

    def archive(self, version: str) -> str:
        self._versions[version].state = "archived"
        self._history_log.append({"event": "archive", "version": version})
        return version

    def restore(self, version: str) -> str:
        self._versions[version].state = "active"
        self._history_log.append({"event": "restore", "version": version})
        return version

    def rollback(self, version: str) -> str:
        """Legal rollback: changes runtime availability state ONLY.

        Never rewrites causal history.
        """
        self._versions[version].state = "registered"
        self._history_log.append({"event": "rollback", "version": version})
        return version

    # ── Snapshot (for mutation-proof) ─────────────────────────────────────
    def snapshot(self) -> dict:
        return {
            "versions": {
                v: e.state
                for v, e in self._versions.items()
            },
            "history_log": [dict(row) for row in self._history_log],
        }
