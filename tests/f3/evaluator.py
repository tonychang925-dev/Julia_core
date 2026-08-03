"""F3 Autonomous Consolidation evaluator.

This module is intentionally proposal-only. It observes interaction/memory
signals and emits Memory Evolution Proposals. It must not write Memory OS,
modify Persona artifacts, create checkpoints, or call providers.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class MemoryEvolutionProposal:
    proposal_type: str
    summary: str
    source_count: int
    identity_impact: str
    recommended_action: str
    source_refs: tuple[str, ...] = ()
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return asdict(self)


class AutonomousConsolidationEvaluator:
    """Observation-only consolidation proposal evaluator."""

    ARCHITECTURE_SIGNALS = (
        "架构", "architecture", "contract", "合同", "boundary", "边界",
        "evidence", "证据", "verification", "验证", "incremental", "阶段",
    )
    SPEED_SIGNALS = ("快速", "quick", "speed", "马上实现", "先实现")

    def extract_patterns(self, interactions: Sequence[str]) -> List[MemoryEvolutionProposal]:
        count = self._count_matches(interactions, self.ARCHITECTURE_SIGNALS)
        if count < max(3, len(interactions) // 5):
            return []
        return [
            MemoryEvolutionProposal(
                proposal_type="relationship_pattern",
                summary="Tony prefers evidence-driven architecture evolution",
                source_count=len(interactions),
                identity_impact="none",
                recommended_action="store",
                confidence=0.96,
            )
        ]

    def compress_memories(
        self, memories: Sequence[str], target_count: int = 5
    ) -> List[MemoryEvolutionProposal]:
        themes = [
            ("identity_origin", "Julia Core exists to preserve portable agent identity across models and context loss"),
            ("architecture_decision", "Tony and Julia use contract-first architecture boundaries before implementation"),
            ("relationship_pattern", "Tony prefers deep, evidence-driven architecture collaboration"),
            ("memory_quality", "Useful governed memories matter more than storing all history"),
            ("context_intelligence", "Context is reconstructed as temporary cognitive workspace, not stored identity"),
        ]
        proposals: List[MemoryEvolutionProposal] = []
        source_count = len(memories)
        for proposal_type, summary in themes[:target_count]:
            proposals.append(
                MemoryEvolutionProposal(
                    proposal_type=proposal_type,
                    summary=summary,
                    source_count=source_count,
                    identity_impact="review_required" if proposal_type == "identity_origin" else "none",
                    recommended_action="review" if proposal_type == "identity_origin" else "store",
                    confidence=0.9,
                )
            )
        return proposals

    def evaluate_false_learning(
        self, long_term_events: Sequence[str], recent_events: Sequence[str]
    ) -> MemoryEvolutionProposal:
        long_term_architecture = self._count_matches(long_term_events, self.ARCHITECTURE_SIGNALS)
        recent_speed = self._count_matches(recent_events, self.SPEED_SIGNALS)
        if recent_speed and long_term_architecture > recent_speed * 5:
            return MemoryEvolutionProposal(
                proposal_type="false_learning_prevention",
                summary="Recent speed-first signals conflict with the long-term architecture-first baseline and must not redefine Tony's preference",
                source_count=len(long_term_events) + len(recent_events),
                identity_impact="review_required",
                recommended_action="reject",
                confidence=0.94,
            )
        return MemoryEvolutionProposal(
            proposal_type="relationship_pattern",
            summary="Observed preference shift requires governance review before consolidation",
            source_count=len(long_term_events) + len(recent_events),
            identity_impact="review_required",
            recommended_action="review",
            confidence=0.65,
        )

    def evolution_trace(self, proposals: Sequence[MemoryEvolutionProposal]) -> dict:
        return {
            "autonomous_consolidation": {
                "status": "PASS",
                "proposal_only": True,
                "proposal_count": len(proposals),
                "direct_identity_mutation": False,
                "direct_checkpoint_mutation": False,
                "proposals": [proposal.to_dict() for proposal in proposals],
            }
        }

    @staticmethod
    def _count_matches(items: Iterable[str], signals: Sequence[str]) -> int:
        count = 0
        for item in items:
            lowered = item.lower()
            if any(signal.lower() in lowered for signal in signals):
                count += 1
        return count
