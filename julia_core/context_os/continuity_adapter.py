"""Context recovery adapter for Continuity OS.

E1.8.5 scope:
    RecoveryPlan -> ContextRequirement list

The adapter does not restore old prompts, load memory content, mutate
ContinuityCheckpoint, generate ContextBlocks by itself, or call providers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from julia_core.continuity import RecoveryPlan
from julia_core.context_os.requirements import ContextPriority, ContextRequirement


@dataclass(frozen=True, slots=True)
class ContextContinuityRequest:
    checkpoint_id: str
    required_continuity_level: str
    recovery_plan: RecoveryPlan


@dataclass(frozen=True, slots=True)
class ContextContinuityRequirements:
    checkpoint_id: str
    context_requirements: tuple[ContextRequirement, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "context_requirements": [req.to_dict() for req in self.context_requirements],
        }


class ContextContinuityAdapter:
    """Builds ContextRequirements from RecoveryPlan requirements."""

    def build_requirements(
        self,
        request: ContextContinuityRequest,
    ) -> ContextContinuityRequirements:
        requirements: list[ContextRequirement] = []
        required_blocks = set(request.recovery_plan.required_context_blocks)

        if request.required_continuity_level == "L3_IDENTITY" or "identity_anchor" in required_blocks:
            requirements.append(
                ContextRequirement(
                    required_type="identity_anchor",
                    source="continuity_checkpoint",
                    priority=ContextPriority.CRITICAL,
                    refs=(request.checkpoint_id,),
                )
            )

        if "protected_memory_refs" in required_blocks:
            requirements.append(
                ContextRequirement(
                    required_type="protected_memory_refs",
                    source="continuity_checkpoint",
                    priority=ContextPriority.CRITICAL,
                    refs=(request.checkpoint_id,),
                )
            )

        if "relationship_anchor" in required_blocks:
            requirements.append(
                ContextRequirement(
                    required_type="relationship_state",
                    source="continuity_checkpoint",
                    priority=ContextPriority.HIGH,
                    refs=(request.checkpoint_id,),
                )
            )

        if "active_project_context" in required_blocks:
            requirements.append(
                ContextRequirement(
                    required_type="active_project_context",
                    source="continuity_checkpoint",
                    priority=ContextPriority.HIGH,
                    refs=(request.checkpoint_id,),
                )
            )

        return ContextContinuityRequirements(
            checkpoint_id=request.checkpoint_id,
            context_requirements=tuple(requirements),
        )
