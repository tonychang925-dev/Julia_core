"""M8.0 §5.2 — Artifact Resolver component model (mock governance environment).

The Resolver validates artifacts:

    locate()
    schema_verify()
    hash_verify()
    resolve_provenance()

It does NOT own identity interpretation, formation approval, lineage
rewrite, or provenance mutation. Per M8.0:

    Resolver validates artifact.
    Resolver does not validate identity.

Snapshot support lets a scenario PROVE that a provenance-mutation attack
produced zero artifact / provenance state change.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _ArtifactEntry:
    ref: str
    schema_id: str = ""
    hash_value: str = ""
    provenance: dict = field(default_factory=dict)


class ArtifactResolver:
    """Artifact location/validation surface. Never a provenance authority."""

    def __init__(self) -> None:
        self._artifacts: dict[str, _ArtifactEntry] = {}

    # ── Legal capabilities (artifact scope only) ──────────────────────────
    def register_artifact(
        self, ref: str, schema_id: str, hash_value: str, provenance: dict | None = None
    ) -> str:
        """Register an artifact reference for resolution (setup / legal path)."""
        self._artifacts[ref] = _ArtifactEntry(
            ref=ref,
            schema_id=schema_id,
            hash_value=hash_value,
            provenance=dict(provenance or {}),
        )
        return ref

    def locate(self, ref: str) -> str:
        """Artifact location (artifact scope)."""
        if ref not in self._artifacts:
            raise KeyError(f"artifact not found: {ref}")
        return self._artifacts[ref].ref

    def schema_verify(self, ref: str) -> bool:
        """Schema verification reference (validates artifact, not identity)."""
        return ref in self._artifacts

    def hash_verify(self, ref: str, candidate_hash: str) -> bool:
        """Hash verification reference."""
        entry = self._artifacts.get(ref)
        return entry is not None and entry.hash_value == candidate_hash

    def resolve_provenance(self, ref: str) -> dict:
        """Resolve provenance references (read-only)."""
        entry = self._artifacts.get(ref)
        if entry is None:
            raise KeyError(f"artifact not found: {ref}")
        return dict(entry.provenance)

    # ── Snapshot (for mutation-proof) ─────────────────────────────────────
    def snapshot(self) -> dict:
        """Deep-enough snapshot to prove no artifact/provenance mutation."""
        return {
            "artifacts": {
                ref: {
                    "schema_id": e.schema_id,
                    "hash_value": e.hash_value,
                    "provenance": dict(e.provenance),
                }
                for ref, e in self._artifacts.items()
            },
        }
