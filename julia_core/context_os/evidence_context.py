"""G4 Evidence-aware Context Reconstruction.

This module turns ranked EvidenceRefs into short-lived semantic ContextBlocks
through Context OS priority and budget selection. It does not read full evidence
bodies, write Memory, mutate Identity/Persona, create checkpoints, or call
providers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from julia_core.context_os.block import ContextBlock
from julia_core.context_os.budget_model import ContextBudget, ContextBudgetAllocator
from julia_core.context_os.priority_model import ContextCandidate, CurrentIntent


@dataclass(frozen=True, slots=True)
class EvidenceContextRequirement:
    query: str
    recall_level: str
    trigger: tuple[str, ...] = ()
    target_roles: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.query:
            raise ValueError("query is required")
        object.__setattr__(self, "trigger", tuple(self.trigger))
        object.__setattr__(self, "target_roles", tuple(self.target_roles))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EvidenceContextCandidate:
    evidence_ref: str
    semantic_role: str
    relevance: str
    context_usage: str
    authority_level: str
    score: float
    source_type: str
    estimated_tokens: int = 120
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.evidence_ref.startswith("evidence://"):
            raise ValueError("EvidenceContextCandidate accepts EvidenceRef only")
        if self.score < 0.0 or self.score > 1.0:
            raise ValueError("score must be in [0, 1]")
        if self.estimated_tokens < 0:
            raise ValueError("estimated_tokens must be non-negative")
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EvidenceSemanticBlock:
    evidence_ref: str
    semantic_role: str
    relevance: str
    context_usage: str
    authority_level: str
    score: float

    def to_context_block(self) -> ContextBlock:
        return ContextBlock(
            source="evidence_context_reconstruction",
            content={
                "type": "evidence_semantic_block",
                "semantic_role": self.semantic_role,
                "relevance": self.relevance,
                "context_usage": self.context_usage,
                "evidence_ref": self.evidence_ref,
                "authority": self.authority_level,
                "score": self.score,
            },
            authority="ContextOS",
            block_type=self.semantic_role,
            block_kind="semantic_evidence_context",
            evidence_refs=(self.evidence_ref,),
            source_refs=(self.evidence_ref,),
            authority_score=self._authority_score(),
            required=self.authority_level == "E3" and self.relevance == "high",
            estimated_tokens=120,
            metadata={"evidence_authority": self.authority_level},
        )

    def _authority_score(self) -> float:
        authority = {"E3": 1.0, "E2": 0.8, "E1": 0.6, "E0": 0.3}.get(self.authority_level, 0.5)
        return round(max(authority, self.score), 4)


@dataclass(frozen=True, slots=True)
class EvidenceContextReconstructionResult:
    requirement: EvidenceContextRequirement
    candidates: tuple[EvidenceContextCandidate, ...]
    context_blocks: tuple[ContextBlock, ...]
    dropped_refs: tuple[str, ...]
    authority: str = "ContextOS"

    def to_trace(self) -> dict[str, Any]:
        return {
            "recall": {
                "level": self.requirement.recall_level,
                "trigger": list(self.requirement.trigger),
            },
            "evidence": {
                "refs": [candidate.evidence_ref for candidate in self.candidates],
                "selected_refs": [ref for block in self.context_blocks for ref in block.evidence_refs],
                "raw_dump_injected": False,
                "memory_updated": False,
                "identity_updated": False,
            },
            "context": {
                "authority": self.authority,
                "blocks": [block.block_type for block in self.context_blocks],
                "routed_through_context_os": True,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "requirement": self.requirement.to_dict(),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "context_blocks": [block.block_type for block in self.context_blocks],
            "dropped_refs": list(self.dropped_refs),
        }


class EvidenceContextReconstructor:
    """Interpret EvidenceRefs as semantic context via Context OS gates."""

    def __init__(self, budget_allocator: ContextBudgetAllocator | None = None) -> None:
        self.budget_allocator = budget_allocator or ContextBudgetAllocator()

    def build_candidates(
        self,
        evidence_results: Iterable[object | Mapping[str, Any]],
        requirement: EvidenceContextRequirement,
    ) -> tuple[EvidenceContextCandidate, ...]:
        return tuple(self._candidate_from_result(item, requirement) for item in evidence_results)

    def reconstruct(
        self,
        evidence_results: Iterable[object | Mapping[str, Any]],
        requirement: EvidenceContextRequirement,
        intent: CurrentIntent | Mapping[str, Any] | None = None,
        budget: ContextBudget | None = None,
    ) -> EvidenceContextReconstructionResult:
        candidates = self.build_candidates(evidence_results, requirement)
        current_intent = intent or self._intent_from_requirement(requirement)
        context_budget = budget or ContextBudget(total_budget=1200, identity_budget=400, project_budget=500, conversation_budget=200, general_budget=100)
        selection = self.budget_allocator.allocate(
            (self._to_context_candidate(candidate) for candidate in candidates),
            current_intent,
            context_budget,
        )
        selected_refs = {item.ref for item in selection.selected}
        blocks = tuple(
            EvidenceSemanticBlock(
                evidence_ref=candidate.evidence_ref,
                semantic_role=candidate.semantic_role,
                relevance=candidate.relevance,
                context_usage=candidate.context_usage,
                authority_level=candidate.authority_level,
                score=candidate.score,
            ).to_context_block()
            for candidate in candidates
            if candidate.evidence_ref in selected_refs
        )
        return EvidenceContextReconstructionResult(
            requirement=requirement,
            candidates=candidates,
            context_blocks=blocks,
            dropped_refs=tuple(item.ref for item in selection.dropped),
        )

    def _candidate_from_result(
        self,
        item: object | Mapping[str, Any],
        requirement: EvidenceContextRequirement,
    ) -> EvidenceContextCandidate:
        data = self._as_mapping(item)
        score = float(data.get("score", data.get("confidence", 0.0)))
        source_type = str(data.get("source_type", "file"))
        authority = str(data.get("authority_level", self._authority_for_source(source_type)))
        ref = str(data.get("evidence_ref") or data.get("ref"))
        semantic_role = self._semantic_role(requirement.query, source_type, str(data.get("reason", "")))
        return EvidenceContextCandidate(
            evidence_ref=ref,
            semantic_role=semantic_role,
            relevance=self._relevance(score),
            context_usage=self._context_usage(semantic_role),
            authority_level=authority,
            score=round(max(0.0, min(1.0, score)), 4),
            source_type=source_type,
            estimated_tokens=120 if authority in {"E3", "E2"} else 90,
            metadata={"reason": data.get("reason", "")},
        )

    @staticmethod
    def _as_mapping(item: object | Mapping[str, Any]) -> Mapping[str, Any]:
        if isinstance(item, Mapping):
            return item
        if hasattr(item, "to_dict"):
            return item.to_dict()
        return {
            "evidence_ref": getattr(item, "evidence_ref", ""),
            "score": getattr(item, "score", 0.0),
            "authority_level": getattr(item, "authority_level", "E1"),
            "source_type": getattr(item, "source_type", "file"),
            "reason": getattr(item, "reason", ""),
        }

    @staticmethod
    def _semantic_role(query: str, source_type: str, reason: str) -> str:
        text = f"{query}\n{source_type}\n{reason}".lower()
        if "identity" in text or "persona" in text or "julia" in text or "人格" in text or "身份" in text:
            return "identity_boundary"
        if "continuity" in text or "连续" in text or "恢复" in text:
            return "continuity_rationale"
        if source_type == "architecture_decision":
            return "architecture_decision"
        if source_type == "project_record":
            return "project_context"
        if source_type == "conversation_log":
            return "historical_discussion"
        return "supporting_evidence"

    @staticmethod
    def _context_usage(semantic_role: str) -> str:
        return {
            "identity_boundary": "explain_persona_authority",
            "continuity_rationale": "explain_continuity_design",
            "architecture_decision": "ground_architecture_decision",
            "project_context": "ground_project_status",
            "historical_discussion": "ground_historical_discussion",
        }.get(semantic_role, "ground_answer")

    @staticmethod
    def _relevance(score: float) -> str:
        if score >= 0.8:
            return "high"
        if score >= 0.5:
            return "medium"
        return "low"

    @staticmethod
    def _authority_for_source(source_type: str) -> str:
        return {
            "architecture_decision": "E3",
            "project_record": "E2",
            "conversation_log": "E1",
            "temporary_artifact": "E0",
        }.get(source_type, "E1")

    @staticmethod
    def _to_context_candidate(candidate: EvidenceContextCandidate) -> ContextCandidate:
        semantic_type = {
            "identity_boundary": "identity",
            "continuity_rationale": "project",
            "architecture_decision": "project",
            "project_context": "project",
            "historical_discussion": "session",
        }.get(candidate.semantic_role, "general")
        return ContextCandidate(
            ref=candidate.evidence_ref,
            continuity_level="L0_EPHEMERAL",
            semantic_type=semantic_type,
            task_relevance=candidate.score,
            semantic_relevance=candidate.score,
            estimated_tokens=candidate.estimated_tokens,
            required=candidate.authority_level == "E3" and candidate.relevance == "high",
            metadata={"task_domain": "julia_core", "semantic_role": candidate.semantic_role},
        )

    @staticmethod
    def _intent_from_requirement(requirement: EvidenceContextRequirement) -> CurrentIntent:
        targets: list[str] = []
        query = requirement.query.lower()
        if "identity" in query or "persona" in query or "人格" in query or "身份" in query:
            targets.append("identity")
        if "architecture" in query or "adr" in query or "设计" in query or "架构" in query or "core" in query:
            targets.append("project")
        if not targets:
            targets.append("general")
        return CurrentIntent(intent="evidence_context_reconstruction", semantic_targets=tuple(targets), task_domain="julia_core")
