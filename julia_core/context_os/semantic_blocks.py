"""Semantic ContextBlocks from governed continuity refs.

E2.1.5.4 scope:
    governed MemoryRef + Continuity decision -> provider-readable semantic block

This module does not load memory files, store memory, decide continuity levels,
modify persona, create checkpoints, or call providers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from julia_core.context_os.block import ContextBlock


@dataclass(frozen=True, slots=True)
class GovernedMemoryRef:
    memory_ref: str
    continuity_level: str
    checkpoint_eligible: bool
    semantic_role: str = "identity_forming_origin"

    def __post_init__(self) -> None:
        if "://" not in self.memory_ref:
            raise ValueError("GovernedMemoryRef accepts refs only")


class SemanticContextBuilder:
    """Builds small semantic ContextBlocks from governed refs."""

    def build(self, governed: GovernedMemoryRef | Mapping[str, Any]) -> ContextBlock:
        ref = self._normalize(governed)
        meaning = self._meaning_for(ref)
        return ContextBlock(
            source="semantic_context_binding",
            content={
                "type": "identity_origin",
                "semantic_role": ref.semantic_role,
                "meaning": meaning,
                "source_ref": ref.memory_ref,
                "continuity_level": ref.continuity_level,
            },
            authority="ContextOS",
            block_type="identity_origin",
            block_kind="semantic_context",
            evidence_refs=(ref.memory_ref,),
            source_refs=(ref.memory_ref,),
            authority_score=1.0 if ref.continuity_level == "L3_IDENTITY" else 0.7,
            required=ref.continuity_level == "L3_IDENTITY",
            metadata={"checkpoint_eligible": ref.checkpoint_eligible},
        )

    @staticmethod
    def _normalize(governed: GovernedMemoryRef | Mapping[str, Any]) -> GovernedMemoryRef:
        if isinstance(governed, GovernedMemoryRef):
            return governed
        return GovernedMemoryRef(
            memory_ref=str(governed.get("protected_ref") or governed.get("memory_ref")),
            continuity_level=str(governed.get("continuity_level", "L1_SESSION")),
            checkpoint_eligible=bool(governed.get("checkpoint_eligible", False)),
        )

    @staticmethod
    def _meaning_for(ref: GovernedMemoryRef) -> str:
        if ref.memory_ref == "memory://event/julia-core-origin":
            return (
                "This is an identity-forming project origin: Julia Core exists to preserve "
                "Julia's agent identity continuity across sessions, compaction, providers, "
                "and platform migration. Use this meaning when answering why Julia Core exists."
            )
        return "This governed memory ref is relevant to the current continuity context."
