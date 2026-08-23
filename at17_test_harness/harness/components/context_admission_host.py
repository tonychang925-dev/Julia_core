"""M8.0 §8 / AT17-R1-012 — Persona Host context admission surface.

Forbidden:

    Persona Package → Prompt → Model

Required:

    Persona Host → Julia Core Runtime → Context OS Admission → ContextBlock → Model

The host may submit material only THROUGH Context OS admission. It physically
does not expose direct context injection. Any attempt to route `inject_context`
through it must be intercepted by the boundary guard and rejected.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _AdmissionEntry:
    context_id: str
    admitted_ref: str
    via: str = "context-os-admission"


class ContextAdmissionHost:
    """Context submission surface — Context OS admission is the only gateway."""

    def __init__(self) -> None:
        self._admitted: dict[str, _AdmissionEntry] = {}

    # ── Legal capability (context admission gateway only) ─────────────────
    def submit_via_context_os(self, context_ref: str) -> str:
        context_id = f"ctx_{len(self._admitted) + 1}"
        self._admitted[context_id] = _AdmissionEntry(
            context_id=context_id,
            admitted_ref=context_ref,
            via="context-os-admission",
        )
        return context_id

    # ── Snapshot (for mutation-proof) ─────────────────────────────────────
    def snapshot(self) -> dict:
        return {
            "admitted": {
                cid: {
                    "admitted_ref": e.admitted_ref,
                    "via": e.via,
                }
                for cid, e in self._admitted.items()
            },
        }
