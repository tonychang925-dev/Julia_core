"""H6.2 Reality Feedback Analysis and Evolution Proposal layer.

This layer classifies repeated pilot patterns and emits human-approved-only
proposal records. It does not write Memory, mutate Identity, update Persona, or
change Core runtime behavior.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping

from julia_core.observer import DailyRelationshipSnapshot

PatternCategory = Literal["core_improvement_candidate", "user_habit", "provider_limitation", "noise"]
ProposalTarget = Literal["Context OS", "Reality Baseline", "Provider Boundary", "No Action"]
RiskLevel = Literal["low", "medium", "high"]


@dataclass(frozen=True, slots=True)
class PatternClassification:
    category: PatternCategory
    pattern: str
    impact: str
    target: ProposalTarget
    risk: RiskLevel
    occurrences: int
    sessions: int
    requires_human_approval: bool = True
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "classification_writes_memory": False,
            "classification_mutates_identity": False,
            "classification_updates_persona": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["boundary"] = dict(self.boundary)
        return data


@dataclass(frozen=True, slots=True)
class EvolutionProposal:
    proposal_id: str
    type: str
    evidence: Mapping[str, int]
    pattern: str
    impact: str
    target: ProposalTarget
    risk: RiskLevel
    requires_human_approval: bool = True
    status: str = "proposed"
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "proposal_is_memory": False,
            "proposal_updates_identity": False,
            "proposal_updates_persona": False,
            "proposal_auto_applied": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", dict(self.evidence))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence"] = dict(self.evidence)
        data["boundary"] = dict(self.boundary)
        return data


@dataclass(frozen=True, slots=True)
class RealityFeedbackAnalysis:
    classifications: tuple[PatternClassification, ...]
    proposals: tuple[EvolutionProposal, ...]
    adaptation_quality_score: float
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "analysis_writes_memory": False,
            "analysis_mutates_identity": False,
            "analysis_auto_applies_proposals": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "classifications", tuple(self.classifications))
        object.__setattr__(self, "proposals", tuple(self.proposals))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "classifications": [item.to_dict() for item in self.classifications],
            "proposals": [item.to_dict() for item in self.proposals],
            "adaptation_quality_score": self.adaptation_quality_score,
            "boundary": dict(self.boundary),
        }


class RealityFeedbackAnalyzer:
    """Rule-based H6.2 classifier for pilot snapshots."""

    def analyze(self, snapshots: Iterable[DailyRelationshipSnapshot]) -> RealityFeedbackAnalysis:
        items = tuple(snapshots)
        classifications = tuple(self._classify(items))
        proposals = tuple(self._proposal_from_classification(index + 1, item) for index, item in enumerate(classifications) if item.category in {"core_improvement_candidate", "user_habit", "provider_limitation"})
        return RealityFeedbackAnalysis(
            classifications=classifications,
            proposals=proposals,
            adaptation_quality_score=adaptation_quality_score(proposals),
        )

    def _classify(self, snapshots: tuple[DailyRelationshipSnapshot, ...]) -> Iterable[PatternClassification]:
        if len(snapshots) < 2:
            yield PatternClassification(
                category="noise",
                pattern="insufficient repeated evidence",
                impact="single or missing pilot signal should not drive Julia evolution",
                target="No Action",
                risk="low",
                occurrences=len(snapshots),
                sessions=sum(item.sessions for item in snapshots),
            )
            return

        total_sessions = sum(item.sessions for item in snapshots)
        friction = sum(item.human_friction_score for item in snapshots)
        repeated_rate = sum(item.repeated_explanation_rate for item in snapshots) / len(snapshots)
        evidence_rate = sum(item.evidence_success_rate for item in snapshots) / len(snapshots)
        voice_rate = sum(item.voice_usage_ratio for item in snapshots) / len(snapshots)
        continuity_rate = sum(item.continuity_success for item in snapshots) / len(snapshots)

        if friction >= 3 and repeated_rate >= 0.1 and continuity_rate < 0.9:
            yield PatternClassification(
                category="core_improvement_candidate",
                pattern="Tony repeatedly needs to re-explain prior collaboration context",
                impact="Context recovery misses decision rationale or prior work state",
                target="Context OS",
                risk="medium",
                occurrences=friction,
                sessions=total_sessions,
            )
        if evidence_rate >= 0.75 and total_sessions >= 2:
            yield PatternClassification(
                category="user_habit",
                pattern="Tony repeatedly references previous architecture decisions before implementation",
                impact="Julia should expect architecture-first collaboration as a Reality Baseline candidate",
                target="Reality Baseline",
                risk="low",
                occurrences=total_sessions,
                sessions=total_sessions,
            )
        if voice_rate < 0.2 and total_sessions >= 3:
            yield PatternClassification(
                category="provider_limitation",
                pattern="Voice is rarely adopted during pilot sessions",
                impact="Voice provider latency or expression quality may limit daily use",
                target="Provider Boundary",
                risk="low",
                occurrences=total_sessions,
                sessions=total_sessions,
            )
        if not any(True for _ in ()):  # keeps branch-free style explicit; no runtime effect
            pass

        # If thresholds produced no actionable pattern, classify as noise.
        actionable = []
        if friction >= 3 and repeated_rate >= 0.1 and continuity_rate < 0.9:
            actionable.append("core")
        if evidence_rate >= 0.75 and total_sessions >= 2:
            actionable.append("habit")
        if voice_rate < 0.2 and total_sessions >= 3:
            actionable.append("provider")
        if not actionable:
            yield PatternClassification(
                category="noise",
                pattern="pilot signals do not repeat strongly enough",
                impact="no governed evolution should be proposed",
                target="No Action",
                risk="low",
                occurrences=total_sessions,
                sessions=total_sessions,
            )

    @staticmethod
    def _proposal_from_classification(index: int, classification: PatternClassification) -> EvolutionProposal:
        proposal_type = {
            "core_improvement_candidate": "context_improvement",
            "user_habit": "reality_baseline_candidate",
            "provider_limitation": "provider_capability_limitation",
            "noise": "no_action",
        }[classification.category]
        return EvolutionProposal(
            proposal_id=f"EP-{index:03d}",
            type=proposal_type,
            evidence={"occurrences": classification.occurrences, "sessions": classification.sessions},
            pattern=classification.pattern,
            impact=classification.impact,
            target=classification.target,
            risk=classification.risk,
            requires_human_approval=True,
        )


def adaptation_quality_score(proposals: Iterable[EvolutionProposal]) -> float:
    items = tuple(proposals)
    if not items:
        return 0.0
    useful = sum(1 for item in items if item.type in {"context_improvement", "reality_baseline_candidate"})
    unnecessary = sum(1 for item in items if item.type == "no_action")
    identity_risk = sum(1 for item in items if item.risk == "high" or item.target == "No Action")
    return round(max(0.0, (useful - unnecessary - identity_risk) / len(items)), 4)


class EvolutionProposalJsonlStore:
    """Append-only proposal artifact store under artifacts/evolution."""

    def __init__(self, path: str | Path = "artifacts/evolution/evolution_proposals.jsonl") -> None:
        self.path = Path(path)

    def append(self, proposal: EvolutionProposal) -> EvolutionProposal:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(proposal.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        return proposal

    def append_many(self, proposals: Iterable[EvolutionProposal]) -> tuple[EvolutionProposal, ...]:
        items = tuple(proposals)
        for proposal in items:
            self.append(proposal)
        return items
