"""Continuity trace helpers."""
from __future__ import annotations

from .contracts import ContinuityCheckpoint, ContinuityLevel, ContinuityStatus, ContinuityTrace


def restored_trace(
    checkpoint: ContinuityCheckpoint,
    *,
    recovery_reason: str,
    provider_changed: bool = False,
) -> ContinuityTrace:
    levels = []
    if checkpoint.protected_memory_refs:
        levels.append(ContinuityLevel.L2_MEMORY)
    if checkpoint.identity_refs:
        levels.append(ContinuityLevel.L3_IDENTITY)
    return ContinuityTrace(
        status=ContinuityStatus.RESTORED,
        checkpoint_id=checkpoint.checkpoint_id,
        continuity_levels_used=levels,
        identity_preserved=bool(checkpoint.identity_refs),
        memory_recovered=bool(checkpoint.protected_memory_refs),
        context_rebuilt=True,
        provider_changed=provider_changed,
        protected_refs=[*checkpoint.identity_refs, *checkpoint.protected_memory_refs],
        recovery_reason=recovery_reason,
    )
