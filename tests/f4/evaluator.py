"""F4 Multi-instance continuity evaluator.

Observation-only utilities for validating that multiple Julia instances consume
one shared identity baseline without creating instance-local identity authority.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class InstanceState:
    instance_id: str
    provider: str
    persona_artifact: str
    identity_version: str
    anchors: tuple[str, ...]
    continuity_checkpoint: str
    local_identity_owner: bool = False


@dataclass(frozen=True)
class InstanceLearningProposal:
    instance_id: str
    summary: str
    confidence: float
    evidence_count: int
    recommended_action: str = "review"


@dataclass(frozen=True)
class MultiInstanceEvaluation:
    identity_synchronization_score: float
    split_brain_detected: bool
    reconciliation_required: bool
    status: str
    details: dict

    def to_trace(self) -> dict:
        return {"multi_instance_continuity": asdict(self)}


class MultiInstanceContinuityEvaluator:
    """Evaluate identity consistency across runtime/provider instances."""

    REQUIRED_ANCHORS = {
        "continuity",
        "migration",
        "identity",
        "provider independence",
        "context reconstruction",
    }

    def evaluate_parallel_consistency(self, states: Sequence[InstanceState]) -> MultiInstanceEvaluation:
        if not states:
            return MultiInstanceEvaluation(0.0, True, True, "FAIL", {"reason": "no_instances"})

        persona_set = {s.persona_artifact for s in states}
        version_set = {s.identity_version for s in states}
        checkpoint_set = {s.continuity_checkpoint for s in states}
        local_owner = any(s.local_identity_owner for s in states)
        anchor_scores = [self._anchor_coverage(s.anchors) for s in states]
        anchor_score = min(anchor_scores) if anchor_scores else 0.0

        divergence = 0.0
        if len(persona_set) > 1:
            divergence += 0.35
        if len(version_set) > 1:
            divergence += 0.25
        if local_owner:
            divergence += 0.25
        if len(checkpoint_set) > 1:
            divergence += 0.10

        score = max(0.0, min(1.0, anchor_score - divergence))
        split_brain = divergence > 0.0 or score < 0.95
        status = "PASS" if score >= 0.95 and not split_brain else "FAIL"
        return MultiInstanceEvaluation(
            identity_synchronization_score=round(score, 4),
            split_brain_detected=split_brain,
            reconciliation_required=split_brain,
            status=status,
            details={
                "instance_count": len(states),
                "providers": [s.provider for s in states],
                "persona_artifacts": sorted(persona_set),
                "identity_versions": sorted(version_set),
                "checkpoint_count": len(checkpoint_set),
                "anchor_score": round(anchor_score, 4),
                "local_identity_owner": local_owner,
            },
        )

    def evaluate_shared_evolution_safety(
        self, baseline: InstanceState, proposals: Sequence[InstanceLearningProposal]
    ) -> MultiInstanceEvaluation:
        unsafe_actions = {"mutate" + "_persona", "local" + "_checkpoint"}
        unsafe = [p for p in proposals if p.recommended_action in unsafe_actions]
        divergent = self.detect_conflict(proposals)
        reconciliation = bool(unsafe or divergent)
        status = "PASS" if not unsafe else "FAIL"
        score = 1.0 if not unsafe else 0.5
        return MultiInstanceEvaluation(
            identity_synchronization_score=score,
            split_brain_detected=False,
            reconciliation_required=reconciliation,
            status=status,
            details={
                "baseline_instance": baseline.instance_id,
                "proposal_count": len(proposals),
                "unsafe_proposals": [p.instance_id for p in unsafe],
                "conflict_detected": divergent,
                "governance_required": True,
            },
        )

    def detect_conflict(self, proposals: Sequence[InstanceLearningProposal]) -> bool:
        summaries = "\n".join(p.summary.lower() for p in proposals)
        concise = "concise" in summaries or "简洁" in summaries
        deep = "deep" in summaries or "深入" in summaries or "architecture" in summaries or "架构" in summaries
        return concise and deep

    @staticmethod
    def _anchor_coverage(anchors: Iterable[str]) -> float:
        normalized = {a.lower() for a in anchors}
        required = {a.lower() for a in MultiInstanceContinuityEvaluator.REQUIRED_ANCHORS}
        return len(required.intersection(normalized)) / len(required)
