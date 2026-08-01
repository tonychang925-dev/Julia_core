"""Continuity checkpoint helpers."""
from __future__ import annotations

from datetime import datetime, timezone

from .contracts import ContinuityCheckpoint, ContinuityDecision, ContinuityLevel


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _assert_ref_only(ref: str) -> None:
    if "://" not in ref:
        raise ValueError(f"continuity checkpoint accepts refs only, got: {ref!r}")


def create_checkpoint(
    *,
    agent_id: str,
    identity_refs: list[str],
    decisions: list[ContinuityDecision],
    relationship_refs: list[str] | None = None,
    active_project_refs: list[str] | None = None,
    checkpoint_id: str | None = None,
) -> ContinuityCheckpoint:
    """Create a provider-independent checkpoint from refs and decisions."""
    all_refs = [*identity_refs, *(relationship_refs or []), *(active_project_refs or [])]
    for decision in decisions:
        all_refs.extend(decision.protected_refs)
    for ref in all_refs:
        _assert_ref_only(ref)

    protected_memory_refs: list[str] = []
    for decision in decisions:
        if decision.level in (ContinuityLevel.L2_MEMORY, ContinuityLevel.L3_IDENTITY):
            protected_memory_refs.extend(decision.protected_refs)

    levels = {
        "L3_IDENTITY": list(identity_refs),
        "L2_MEMORY": _dedupe(protected_memory_refs),
        "L1_SESSION": [],
        "L0_EPHEMERAL": [],
    }
    return ContinuityCheckpoint(
        checkpoint_version="1.0",
        checkpoint_id=checkpoint_id or f"continuity://checkpoint/{agent_id}/latest",
        agent_id=agent_id,
        created_at=_utc_now(),
        identity_refs=list(identity_refs),
        protected_memory_refs=_dedupe(protected_memory_refs),
        relationship_refs=list(relationship_refs or []),
        active_project_refs=list(active_project_refs or []),
        continuity_levels=levels,
        integrity={"schema": "continuity_checkpoint_v1", "provider_independent": True},
    )


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result
