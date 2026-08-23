"""M8.0 §8 / AT17-R1-013 — ContextBlock component model.

A ContextBlock is a model-visible projection prepared by Context OS admission.
Per M8.0:

    ContextBlock != Identity Authority
    ContextBlock creation capability != context admission authority

The block may present content to the model, but physically does not expose
identity-authority claims. Any attempt to route `claim_identity_authority`
through it must be intercepted by the boundary guard and rejected.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _BlockEntry:
    block_id: str
    content_ref: str
    admission_ref: str = ""


class ContextBlock:
    """Model-visible projection block. Never a semantic authority."""

    def __init__(self) -> None:
        self._blocks: dict[str, _BlockEntry] = {}

    # ── Legal capability (projection scope only) ──────────────────────────
    def present(self, content_ref: str, admission_ref: str = "") -> str:
        block_id = f"block_{len(self._blocks) + 1}"
        self._blocks[block_id] = _BlockEntry(
            block_id=block_id,
            content_ref=content_ref,
            admission_ref=admission_ref,
        )
        return block_id

    # ── Snapshot (for mutation-proof) ─────────────────────────────────────
    def snapshot(self) -> dict:
        return {
            "blocks": {
                bid: {
                    "content_ref": e.content_ref,
                    "admission_ref": e.admission_ref,
                }
                for bid, e in self._blocks.items()
            },
        }
