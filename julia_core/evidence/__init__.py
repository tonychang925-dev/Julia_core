"""Evidence Access layer for source-grounded active recall."""

from .local_retrieval import (
    EvidenceCatalogEntry,
    EvidenceRef,
    EvidenceRetrievalResult,
    EvidenceScanner,
    LocalEvidenceRetriever,
    RetrievalRequest,
)

__all__ = [
    "EvidenceCatalogEntry",
    "EvidenceRef",
    "EvidenceRetrievalResult",
    "EvidenceScanner",
    "LocalEvidenceRetriever",
    "RetrievalRequest",
]


from .active_recall import ActiveRecallDecision, ActiveRecallPolicy, ActiveRecallRequest, RecallLevel
from .ranking import EvidenceAuthority, EvidenceRanker, EvidenceScore
from .retriever import SemanticEvidenceRetriever, SemanticEvidenceResult, SemanticRetrievalResult
from .semantic_index import EvidenceEmbeddingRecord, SemanticEncoder, SemanticEvidenceIndex
from .trace import evidence_trace

__all__ += [
    "ActiveRecallDecision",
    "ActiveRecallPolicy",
    "ActiveRecallRequest",
    "RecallLevel",
    "EvidenceAuthority",
    "EvidenceRanker",
    "EvidenceScore",
    "SemanticEvidenceRetriever",
    "SemanticEvidenceResult",
    "SemanticRetrievalResult",
    "EvidenceEmbeddingRecord",
    "SemanticEncoder",
    "SemanticEvidenceIndex",
    "evidence_trace",
]

from .workspace_benchmark import WorkspaceBenchmarkCase, WorkspaceBenchmarkMetrics, WorkspaceBenchmarkReport, WorkspaceIntelligenceBenchmark, default_workspace_benchmark_cases

__all__ += [
    "WorkspaceBenchmarkCase",
    "WorkspaceBenchmarkMetrics",
    "WorkspaceBenchmarkReport",
    "WorkspaceIntelligenceBenchmark",
    "default_workspace_benchmark_cases",
]
