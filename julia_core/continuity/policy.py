"""Continuity OS v0.1 policy skeleton."""
from __future__ import annotations

from uuid import uuid4

from .contracts import ContinuityDecision, ContinuityLevel, ContinuityRequest, TTLPolicy


class ContinuityPolicy:
    """Deterministic first-pass continuity classifier.

    This policy classifies refs/state; it does not store memory, mutate persona,
    build context, or call providers.
    """

    def decide(self, request: ContinuityRequest) -> ContinuityDecision:
        signals = request.signals
        refs = list(request.candidate_refs)

        if signals.get("identity_related") and (
            signals.get("relationship_related") or signals.get("project_related")
        ):
            return ContinuityDecision(
                decision_id=f"continuity-decision-{uuid4().hex}",
                request_id=request.request_id,
                level=ContinuityLevel.L3_IDENTITY,
                preserve=True,
                checkpoint_required=True,
                reason="identity_forming_event",
                protected_refs=refs,
                ttl_policy=TTLPolicy.PROTECT,
            )

        if signals.get("relationship_related") or signals.get("project_related") or signals.get("recurring"):
            return ContinuityDecision(
                decision_id=f"continuity-decision-{uuid4().hex}",
                request_id=request.request_id,
                level=ContinuityLevel.L2_MEMORY,
                preserve=True,
                checkpoint_required=bool(signals.get("provider_independent", False)),
                reason="durable_memory_state",
                protected_refs=refs,
                ttl_policy=TTLPolicy.RETAIN_REF,
            )

        if request.source == "session" or request.event_type == "session_summary":
            return ContinuityDecision(
                decision_id=f"continuity-decision-{uuid4().hex}",
                request_id=request.request_id,
                level=ContinuityLevel.L1_SESSION,
                preserve=False,
                checkpoint_required=False,
                reason="session_state",
                protected_refs=[],
                ttl_policy=TTLPolicy.SUMMARIZE,
            )

        return ContinuityDecision(
            decision_id=f"continuity-decision-{uuid4().hex}",
            request_id=request.request_id,
            level=ContinuityLevel.L0_EPHEMERAL,
            preserve=False,
            checkpoint_required=False,
            reason="ephemeral_context",
            protected_refs=[],
            ttl_policy=TTLPolicy.DISCARD,
        )
