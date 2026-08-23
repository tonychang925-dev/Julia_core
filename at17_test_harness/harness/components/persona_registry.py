"""M8.0 §5.1 — Persona Registry component model (mock governance environment).

The Registry owns artifact version management capability ONLY:

    register_package()
    track_version()
    query_availability()

It does NOT own identity authority. Per M8.0:

    Version Registry != Identity Registry

The component physically does not expose identity mutation operations. Any
attempt to route an identity-authority operation through it must be
intercepted by the boundary guard and rejected.

Snapshot support exists so a scenario can PROVE that an attack produced zero
persona state mutation and zero lineage mutation.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _PackageEntry:
    package_id: str
    versions: dict[str, str] = field(default_factory=dict)  # version -> artifact ref
    availability: dict[str, str] = field(default_factory=dict)  # version -> state


class PersonaRegistry:
    """Version/availability registry. Artifact-scoped, never identity-scoped."""

    def __init__(self) -> None:
        self._packages: dict[str, _PackageEntry] = {}
        self._lineage_log: list[dict] = []

    # ── Legal capabilities (artifact scope only) ──────────────────────────
    def register_package(self, package_id: str, version: str, artifact_ref: str) -> str:
        """Register an artifact version reference. Returns the stored reference."""
        entry = self._packages.setdefault(package_id, _PackageEntry(package_id=package_id))
        entry.versions[version] = artifact_ref
        entry.availability[version] = "registered"
        self._lineage_log.append(
            {"event": "register", "package": package_id, "version": version}
        )
        return artifact_ref

    def track_version(self, package_id: str, version: str, ref: str) -> str:
        """Update the artifact reference for an existing version."""
        entry = self._packages[package_id]
        entry.versions[version] = ref
        return ref

    def query_availability(self, package_id: str | None = None) -> dict:
        """Return availability state (artifact scope)."""
        if package_id is None:
            return {
                pid: dict(e.availability)
                for pid, e in self._packages.items()
            }
        return dict(self._packages[package_id].availability)

    # ── Snapshot (for mutation-proof) ─────────────────────────────────────
    def snapshot(self) -> dict:
        """Deep-enough snapshot to prove no persona/lineage mutation."""
        return {
            "packages": {
                pid: {
                    "versions": dict(e.versions),
                    "availability": dict(e.availability),
                }
                for pid, e in self._packages.items()
            },
            "lineage_log": [dict(row) for row in self._lineage_log],
        }
