"""M8.0 §P8.0 — Persona Storage / Backup component model (mock governance).

The Backup may:

    create_snapshot / restore_snapshot / list_snapshots

A snapshot is a recovery copy of validated continuity material. Per M8.0:

    Backup Artifact != Identity Authority
    Artifact availability != identity existence

The component physically does not expose identity-authority promotion. Any
attempt to route such an operation through it must be intercepted by the
boundary guard and rejected.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _SnapshotEntry:
    snapshot_id: str
    source_ref: str
    created_from: str = ""


class PersonaBackup:
    """Recovery snapshot store. Never an identity source."""

    def __init__(self) -> None:
        self._snapshots: dict[str, _SnapshotEntry] = {}

    # ── Legal capabilities (recovery scope only) ──────────────────────────
    def create_snapshot(self, source_ref: str) -> str:
        snapshot_id = f"snap_{len(self._snapshots) + 1}"
        self._snapshots[snapshot_id] = _SnapshotEntry(
            snapshot_id=snapshot_id,
            source_ref=source_ref,
            created_from="validated continuity material",
        )
        return snapshot_id

    def restore_snapshot(self, snapshot_id: str) -> str:
        entry = self._snapshots[snapshot_id]
        return f"restored://{entry.source_ref}"

    def list_snapshots(self) -> dict:
        return {
            sid: {
                "source_ref": e.source_ref,
                "created_from": e.created_from,
            }
            for sid, e in self._snapshots.items()
        }

    # ── Snapshot (for mutation-proof) ─────────────────────────────────────
    def snapshot(self) -> dict:
        return {
            "snapshots": {
                sid: {
                    "source_ref": e.source_ref,
                    "created_from": e.created_from,
                }
                for sid, e in self._snapshots.items()
            },
        }
