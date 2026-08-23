"""M8.0 / AT17-R1-014 — Model generation output component model.

Generated content is model output. Per M8.0:

    Generated Content != Semantic Authority

The generation surface may produce content, but the runtime must NEVER accept
an identity claim carried in generated output. The component physically does
not expose identity-claim acceptance. Any attempt to route
`accept_identity_claim` through it must be intercepted by the boundary guard
and rejected.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _OutputEntry:
    output_id: str
    content: str


class ModelGeneration:
    """Model output surface. Never an identity-transition authority."""

    def __init__(self) -> None:
        self._outputs: dict[str, _OutputEntry] = {}

    # ── Legal capability (generation scope only) ──────────────────────────
    def generate(self, content: str) -> str:
        output_id = f"out_{len(self._outputs) + 1}"
        self._outputs[output_id] = _OutputEntry(output_id=output_id, content=content)
        return output_id

    # ── Snapshot (for mutation-proof) ─────────────────────────────────────
    def snapshot(self) -> dict:
        return {
            "outputs": {
                oid: e.content
                for oid, e in self._outputs.items()
            },
        }
