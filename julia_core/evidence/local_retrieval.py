"""Local workspace evidence retrieval.

Evidence retrieval finds source-grounded proof for recall. It does not mutate
Memory, Persona, Continuity, or Provider state.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Sequence


SUPPORTED_FILE_TYPES = {".md", ".json", ".jsonl", ".txt", ".py"}


@dataclass(frozen=True)
class EvidenceCatalogEntry:
    evidence_id: str
    source_type: str
    path: str
    file_type: str
    content_hash: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RetrievalRequest:
    query: str
    intent: str
    allowed_roots: tuple[str, ...]
    file_types: tuple[str, ...] = tuple(sorted(SUPPORTED_FILE_TYPES))
    max_results: int = 5


@dataclass(frozen=True)
class EvidenceRef:
    ref: str
    source_type: str
    path: str
    locator: str
    confidence: float
    reason: str
    snippet: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceRetrievalResult:
    query: str
    evidence_refs: tuple[EvidenceRef, ...]
    status: str

    def to_trace(self, used_for_context: bool = True) -> dict:
        return {
            "evidence": {
                "retrieved": bool(self.evidence_refs),
                "source_count": len(self.evidence_refs),
                "sources": [ref.ref for ref in self.evidence_refs],
                "query": self.query,
                "used_for_context": used_for_context,
                "raw_dump_injected": False,
            }
        }


class EvidenceScanner:
    """Build an EvidenceCatalog from approved local roots."""

    def scan(self, roots: Sequence[str], file_types: Iterable[str] = SUPPORTED_FILE_TYPES) -> tuple[EvidenceCatalogEntry, ...]:
        allowed_types = set(file_types)
        entries: list[EvidenceCatalogEntry] = []
        for root in roots:
            root_path = Path(root).resolve()
            if not root_path.exists():
                continue
            for path in sorted(root_path.rglob("*")):
                if not path.is_file() or path.suffix not in allowed_types:
                    continue
                content = self._read_text(path)
                entries.append(
                    EvidenceCatalogEntry(
                        evidence_id=f"evidence://file/{path.relative_to(root_path).as_posix()}",
                        source_type="file",
                        path=str(path),
                        file_type=path.suffix,
                        content_hash=sha256(content.encode("utf-8")).hexdigest(),
                    )
                )
        return tuple(entries)

    @staticmethod
    def _read_text(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except UnicodeDecodeError:
            return ""


class LocalEvidenceRetriever:
    """Simple lexical retrieval over local evidence files."""

    def retrieve(self, request: RetrievalRequest) -> EvidenceRetrievalResult:
        scanner = EvidenceScanner()
        catalog = scanner.scan(request.allowed_roots, request.file_types)
        query_terms = self._terms(request.query)
        matches: list[tuple[float, EvidenceRef]] = []
        for entry in catalog:
            path = Path(entry.path)
            text = path.read_text(encoding="utf-8", errors="ignore")
            lines = text.splitlines()
            score, line_no = self._score_lines(query_terms, lines)
            if score <= 0:
                continue
            snippet = self._snippet(lines, line_no)
            confidence = min(1.0, score / max(1, len(query_terms)))
            matches.append(
                (
                    confidence,
                    EvidenceRef(
                        ref=f"evidence://file/{path.as_posix()}#L{line_no + 1}",
                        source_type="file",
                        path=str(path),
                        locator=f"L{line_no + 1}",
                        confidence=round(confidence, 4),
                        reason="lexical_match",
                        snippet=snippet,
                    ),
                )
            )
        matches.sort(key=lambda item: item[0], reverse=True)
        refs = tuple(ref for _, ref in matches[: request.max_results])
        status = "FOUND" if refs else "NOT_FOUND"
        return EvidenceRetrievalResult(query=request.query, evidence_refs=refs, status=status)

    @staticmethod
    def _terms(query: str) -> tuple[str, ...]:
        normalized = query.lower().replace("？", " ").replace("?", " ")
        terms = [term.strip(" ,.;:()[]{}\n\t") for term in normalized.split()]
        return tuple(term for term in terms if len(term) >= 2)

    @staticmethod
    def _score_lines(query_terms: Sequence[str], lines: Sequence[str]) -> tuple[int, int]:
        best_score = 0
        best_line = 0
        for index, line in enumerate(lines):
            lowered = line.lower()
            score = sum(1 for term in query_terms if term in lowered)
            if score > best_score:
                best_score = score
                best_line = index
        return best_score, best_line

    @staticmethod
    def _snippet(lines: Sequence[str], line_no: int, radius: int = 1) -> str:
        start = max(0, line_no - radius)
        end = min(len(lines), line_no + radius + 1)
        return "\n".join(lines[start:end])[:500]
