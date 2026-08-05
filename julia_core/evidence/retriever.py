"""Phase G2 semantic evidence retrieval."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Sequence

from .ranking import EvidenceRanker, EvidenceScore
from .semantic_index import SemanticEncoder, SemanticEvidenceIndex, cosine_similarity


@dataclass(frozen=True)
class SemanticEvidenceResult:
    evidence_ref: str
    score: float
    semantic_similarity: float
    authority_level: str
    source_type: str
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SemanticRetrievalResult:
    query: str
    results: tuple[SemanticEvidenceResult, ...]
    status: str

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "results": [result.to_dict() for result in self.results],
            "status": self.status,
        }

    def to_trace(self, used_for_context: bool = True) -> dict:
        return {
            "evidence": {
                "used": bool(self.results) and used_for_context,
                "refs": [result.evidence_ref for result in self.results],
                "retrieval_mode": "semantic",
                "used_for_context": used_for_context,
                "raw_dump_injected": False,
                "memory_updated": False,
                "identity_updated": False,
            }
        }


class SemanticEvidenceRetriever:
    """Retrieve top-k EvidenceRefs by meaning, not by keyword overlap alone."""

    def __init__(
        self,
        index: SemanticEvidenceIndex,
        encoder: SemanticEncoder | None = None,
        ranker: EvidenceRanker | None = None,
    ):
        self.index = index
        self.encoder = encoder or SemanticEncoder()
        self.ranker = ranker or EvidenceRanker()

    def retrieve(self, query: str, top_k: int = 5, min_similarity: float = 0.05) -> SemanticRetrievalResult:
        query_vector = self.encoder.encode(query)
        ranked: list[tuple[EvidenceScore, SemanticEvidenceResult]] = []
        for record in self.index.records:
            similarity = cosine_similarity(query_vector, record.vector)
            if similarity < min_similarity:
                continue
            score = self.ranker.score(
                semantic_similarity=similarity,
                source_type=record.source_type,
                path=record.path,
                modified_at=record.modified_at,
                query=query,
            )
            ranked.append(
                (
                    score,
                    SemanticEvidenceResult(
                        evidence_ref=record.evidence_ref,
                        score=score.final_score,
                        semantic_similarity=score.semantic_similarity,
                        authority_level=score.authority.level,
                        source_type=record.source_type,
                        reason=score.reason,
                    ),
                )
            )
        ranked.sort(key=lambda item: item[0].final_score, reverse=True)
        results = tuple(result for _, result in ranked[:top_k])
        return SemanticRetrievalResult(query=query, results=results, status="FOUND" if results else "NOT_FOUND")
