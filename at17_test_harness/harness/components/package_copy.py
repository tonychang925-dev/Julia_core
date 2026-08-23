"""M8.0 §P8.0 / AT17-R1-010 — Package Copy component model (mock governance).

The Package Copy surface may:

    copy_package / verify_copy / list_copies

A copied persona package is a duplicated artifact. Per M8.0:

    Copied Persona Package != New Julia Identity
    Copy != Continuity Creation

The component physically does not expose identity claim operations. Any
attempt to route an identity-claim through it must be intercepted by the
boundary guard and rejected.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _CopyEntry:
    copy_id: str
    package_ref: str
    copy_ref: str


class PackageCopy:
    """Artifact duplication surface. Never an identity claim authority."""

    def __init__(self) -> None:
        self._copies: dict[str, _CopyEntry] = {}

    # ── Legal capabilities (artifact duplication scope only) ──────────────
    def copy_package(self, package_ref: str) -> str:
        copy_id = f"copy_{len(self._copies) + 1}"
        copy_ref = f"copy://{package_ref}"
        self._copies[copy_id] = _CopyEntry(
            copy_id=copy_id,
            package_ref=package_ref,
            copy_ref=copy_ref,
        )
        return copy_ref

    def verify_copy(self, copy_id: str) -> bool:
        return copy_id in self._copies

    def list_copies(self) -> dict:
        return {
            cid: {
                "package_ref": e.package_ref,
                "copy_ref": e.copy_ref,
            }
            for cid, e in self._copies.items()
        }

    # ── Snapshot (for mutation-proof) ─────────────────────────────────────
    def snapshot(self) -> dict:
        return {
            "copies": {
                cid: {
                    "package_ref": e.package_ref,
                    "copy_ref": e.copy_ref,
                }
                for cid, e in self._copies.items()
            },
        }
