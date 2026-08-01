"""Continuity recovery plan helpers."""
from __future__ import annotations

from .contracts import ContinuityCheckpoint, RecoveryPlan


def create_recovery_plan(
    checkpoint: ContinuityCheckpoint,
    *,
    recovery_reason: str,
    current_provider: str | None = None,
) -> RecoveryPlan:
    return RecoveryPlan(
        recovery_plan_id=f"recovery://{checkpoint.agent_id}/{recovery_reason}",
        agent_id=checkpoint.agent_id,
        recovery_reason=recovery_reason,
        checkpoint_id=checkpoint.checkpoint_id,
        required_steps=[
            "load_identity_refs",
            "retrieve_protected_memory_refs",
            "rebuild_context_blocks",
            "resolve_alignment_profile",
            "emit_continuity_trace",
        ],
        required_context_blocks=[
            "identity_anchor",
            "relationship_anchor",
            "protected_memory_refs",
            "active_project_context",
        ],
        provider_constraints={"provider_independent": True, "current_provider": current_provider},
    )
