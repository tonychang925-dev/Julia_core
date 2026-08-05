"""Semantic evidence index for Phase G2.

The index is a search structure over EvidenceRefs. It stores deterministic local
embedding metadata and never promotes evidence into Memory, Persona, Continuity,
or Provider state.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from math import sqrt
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .local_retrieval import EvidenceCatalogEntry, EvidenceScanner, SUPPORTED_FILE_TYPES


CONCEPT_LEXICON: Mapping[str, tuple[str, ...]] = {
    "identity": ("identity", "persona", "self", "人格", "身份", "自我", "julia 是"),
    "prompt": ("prompt", "system prompt", "giant prompt", "提示词", "系统提示", "上下文提示"),
    "externalization": ("externalization", "externalize", "externalized", "依赖", "保存", "存", "放进", "写进"),
    "context_independence": ("context independence", "provider independent", "context independent", "不依赖", "独立", "provider migration"),
    "continuity": ("continuity", "compact", "recovery", "restore", "preserve", "survive", "连续", "恢复", "保真"),
    "memory": ("memory", "memory os", "memoryref", "记忆", "长期经验", "经验存储"),
    "evidence": ("evidence", "evidenceref", "trace", "grounding", "证据", "溯源", "引用"),
    "architecture": ("adr", "architecture", "decision", "contract", "design", "设计", "架构", "决策", "边界", "phase"),
    "project": ("project", "roadmap", "milestone", "status", "julia core", "core", "timeline", "history", "historical", "项目", "阶段", "完成", "历史", "时间线"),
    "noise": ("scratch", "tmp", "temporary", "draft note", "old draft", "old/", "临时", "草稿", "旧", "随手"),
}

CONCEPTS: tuple[str, ...] = tuple(CONCEPT_LEXICON.keys())


@dataclass(frozen=True)
class EvidenceEmbeddingRecord:
    """Metadata-only vector index record.

    It may store vector coordinates and source metadata, but it does not store
    the source body. The canonical payload remains in the original evidence
    source addressed by ``evidence_ref`` / ``path``.
    """

    evidence_ref: str
    embedding_id: str
    content_hash: str
    source_type: str
    path: str
    file_type: str
    vector: tuple[float, ...]
    modified_at: float

    def to_dict(self) -> dict:
        return asdict(self)


class SemanticEncoder:
    """Small deterministic concept encoder used for local G2 tests.

    Production can swap this with an embedding provider while preserving the
    EvidenceEmbeddingRecord boundary.
    """

    def encode(self, text: str) -> tuple[float, ...]:
        lowered = text.lower()
        weights: list[float] = []
        for concept in CONCEPTS:
            score = 0.0
            for phrase in CONCEPT_LEXICON[concept]:
                phrase_l = phrase.lower()
                if phrase_l in lowered:
                    score += 2.0 if " " in phrase_l or any(ord(ch) > 127 for ch in phrase_l) else 1.0
            weights.append(score)
        return self._normalize(tuple(weights))

    @staticmethod
    def _normalize(vector: Sequence[float]) -> tuple[float, ...]:
        norm = sqrt(sum(value * value for value in vector))
        if norm == 0:
            return tuple(0.0 for _ in vector)
        return tuple(round(value / norm, 8) for value in vector)


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return round(sum(a * b for a, b in zip(left, right)), 8)


class SemanticEvidenceIndex:
    """Build and hold metadata-only semantic records for evidence retrieval."""

    def __init__(self, records: Iterable[EvidenceEmbeddingRecord] = ()):  # noqa: D107
        self.records = tuple(records)

    @classmethod
    def build(
        cls,
        roots: Sequence[str],
        file_types: Iterable[str] = SUPPORTED_FILE_TYPES,
        encoder: SemanticEncoder | None = None,
    ) -> "SemanticEvidenceIndex":
        scanner = EvidenceScanner()
        catalog = scanner.scan(roots, file_types)
        return cls.from_catalog(catalog, encoder=encoder)

    @classmethod
    def from_catalog(
        cls,
        catalog: Sequence[EvidenceCatalogEntry],
        encoder: SemanticEncoder | None = None,
    ) -> "SemanticEvidenceIndex":
        selected_encoder = encoder or SemanticEncoder()
        records: list[EvidenceEmbeddingRecord] = []
        for entry in catalog:
            path = Path(entry.path)
            text = path.read_text(encoding="utf-8", errors="ignore")
            source_type = infer_source_type(path, text)
            vector = selected_encoder.encode(path.name + "\n" + source_type + "\n" + text)
            records.append(
                EvidenceEmbeddingRecord(
                    evidence_ref=entry.evidence_id,
                    embedding_id="vec-" + sha256(f"{entry.content_hash}:{source_type}".encode("utf-8")).hexdigest()[:16],
                    content_hash=entry.content_hash,
                    source_type=source_type,
                    path=str(path),
                    file_type=entry.file_type,
                    vector=vector,
                    modified_at=path.stat().st_mtime,
                )
            )
        return cls(records)

    def to_dict(self) -> dict:
        return {"records": [record.to_dict() for record in self.records]}


def infer_source_type(path: Path, text: str = "") -> str:
    name = path.name.lower()
    lowered = text.lower()
    path_text = path.as_posix().lower()
    if "temporary" in lowered or "scratch" in lowered or "old draft" in lowered or "/tmp/" in path_text or "/old/" in path_text:
        return "temporary_artifact"
    if name.startswith("adr-") or "architecture decision" in lowered or "# adr" in lowered:
        return "architecture_decision"
    if "phase_contract" in name or "test_case_spec" in name or "roadmap" in name:
        return "project_record"
    if path.suffix == ".jsonl" or "conversation" in path.as_posix().lower():
        return "conversation_log"
    if path.suffix in {".md", ".txt"}:
        return "project_record"
    return "file"
