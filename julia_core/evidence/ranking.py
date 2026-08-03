"""Evidence authority and ranking for semantic retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from time import time


AUTHORITY_LEVELS: dict[str, tuple[str, float]] = {
    "architecture_decision": ("E3", 0.30),
    "project_record": ("E2", 0.20),
    "conversation_log": ("E1", 0.10),
    "temporary_artifact": ("E0", 0.00),
    "file": ("E1", 0.08),
}


@dataclass(frozen=True)
class EvidenceAuthority:
    level: str
    source_type: str
    weight: float


@dataclass(frozen=True)
class EvidenceScore:
    final_score: float
    semantic_similarity: float
    authority: EvidenceAuthority
    temporal_relevance: float
    project_relevance: float
    noise_penalty: float
    reason: str


class EvidenceRanker:
    """Combine semantic similarity with source authority and relevance signals."""

    def score(
        self,
        *,
        semantic_similarity: float,
        source_type: str,
        path: str,
        modified_at: float,
        query: str,
    ) -> EvidenceScore:
        authority = self.authority_for(source_type)
        temporal = self._temporal_relevance(modified_at)
        project = self._project_relevance(path, query)
        noise = self._noise_penalty(source_type, path)
        final = semantic_similarity + authority.weight + temporal + project - noise
        return EvidenceScore(
            final_score=round(max(0.0, min(1.0, final)), 4),
            semantic_similarity=round(semantic_similarity, 4),
            authority=authority,
            temporal_relevance=round(temporal, 4),
            project_relevance=round(project, 4),
            noise_penalty=round(noise, 4),
            reason=self._reason(semantic_similarity, authority, project, noise),
        )

    @staticmethod
    def authority_for(source_type: str) -> EvidenceAuthority:
        level, weight = AUTHORITY_LEVELS.get(source_type, AUTHORITY_LEVELS["file"])
        return EvidenceAuthority(level=level, source_type=source_type, weight=weight)

    @staticmethod
    def _temporal_relevance(modified_at: float) -> float:
        age_days = max(0.0, (time() - modified_at) / 86400.0)
        if age_days <= 30:
            return 0.05
        if age_days <= 365:
            return 0.025
        return 0.0

    @staticmethod
    def _project_relevance(path: str, query: str) -> float:
        lowered = (path + "\n" + query).lower()
        score = 0.0
        if "julia" in lowered:
            score += 0.03
        if "core" in lowered:
            score += 0.02
        if "docs/project_control" in lowered or "adr" in lowered:
            score += 0.03
        return min(0.08, score)

    @staticmethod
    def _noise_penalty(source_type: str, path: str) -> float:
        lowered = path.lower()
        penalty = 0.0
        if source_type == "temporary_artifact":
            penalty += 0.20
        if "/tmp/" in lowered or "/old/" in lowered or "scratch" in lowered or "draft" in lowered:
            penalty += 0.10
        return min(0.30, penalty)

    @staticmethod
    def _reason(semantic_similarity: float, authority: EvidenceAuthority, project: float, noise: float) -> str:
        parts = ["semantic_match"] if semantic_similarity > 0 else ["weak_semantic_match"]
        parts.append(f"authority_{authority.level}")
        if project > 0:
            parts.append("project_relevant")
        if noise > 0:
            parts.append("noise_penalized")
        return "+".join(parts)
