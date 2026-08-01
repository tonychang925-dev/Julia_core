"""Context reconstruction from Continuity checkpoint/recovery refs."""
from __future__ import annotations

from julia_core.continuity import ContinuityCheckpoint, RecoveryPlan

from .block import ContextBlock
from .requirements import ContextPriority, ContextReconstructionRequest, ContextReconstructionResult, ContextRequirement


class ContextReconstructor:
    """Builds short-lived ContextBlocks from refs.

    Does not mutate checkpoints, write memory, promote continuity levels, or call providers.
    """

    def build_requirements(
        self,
        checkpoint: ContinuityCheckpoint,
        recovery_plan: RecoveryPlan,
        request: ContextReconstructionRequest,
    ) -> tuple[ContextRequirement, ...]:
        requirements: list[ContextRequirement] = []
        if "identity_anchor" in recovery_plan.required_context_blocks:
            requirements.append(ContextRequirement("identity", "persona", ContextPriority.CRITICAL, tuple(checkpoint.identity_refs)))
        if "relationship_anchor" in recovery_plan.required_context_blocks:
            requirements.append(ContextRequirement("relationship", "memory", ContextPriority.HIGH, tuple(checkpoint.relationship_refs)))
        if "protected_memory_refs" in recovery_plan.required_context_blocks:
            requirements.append(ContextRequirement("memory_reference", "memory", ContextPriority.CRITICAL, tuple(checkpoint.protected_memory_refs)))
        if "active_project_context" in recovery_plan.required_context_blocks:
            requirements.append(ContextRequirement("project", "project", ContextPriority.HIGH, tuple(checkpoint.active_project_refs)))
        return tuple(req for req in requirements if req.refs)

    def reconstruct(
        self,
        checkpoint: ContinuityCheckpoint,
        recovery_plan: RecoveryPlan,
        request: ContextReconstructionRequest,
    ) -> ContextReconstructionResult:
        requirements = self.build_requirements(checkpoint, recovery_plan, request)
        blocks = tuple(self._block_from_requirement(req, checkpoint.checkpoint_id) for req in requirements)
        return ContextReconstructionResult(
            context_blocks=blocks,
            continuity_restored=bool(blocks),
            source_checkpoint=checkpoint.checkpoint_id,
            requirements=requirements,
        )

    @staticmethod
    def _block_from_requirement(requirement: ContextRequirement, checkpoint_id: str) -> ContextBlock:
        return ContextBlock(
            source="continuity_reconstruction",
            content={"requirement": requirement.required_type, "refs": list(requirement.refs)},
            authority="ContextOS",
            block_type=requirement.required_type,
            block_kind="reconstructed_context",
            evidence_refs=requirement.refs,
            source_refs=(checkpoint_id, *requirement.refs),
            authority_score=1.0 if requirement.priority == ContextPriority.CRITICAL else 0.8,
            required=requirement.priority in (ContextPriority.CRITICAL, ContextPriority.HIGH),
            metadata={"source": requirement.source, "priority": requirement.priority.value},
        )
