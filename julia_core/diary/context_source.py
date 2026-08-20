"""STORAGE-DIA-7-R1 — Core DiaryContextSource (minimal, read/rank only).

Ranking authority only — NOT interpretation authority, NOT admission authority.
Deterministic ranking from explicit `as_of`; entry semantics preserved
field-for-field; no hidden wall-clock, no mutation, no synthesis.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .models import AcceptedDiaryEntry
from .repository_protocol import DiaryRepository


@dataclass(frozen=True)
class DiaryRetrievalQuery:
    query_text: str = ""
    as_of: str | None = None
    before: str | None = None
    limit: int = 20


@dataclass(frozen=True)
class DiaryRetrievalRanking:
    relevance: float
    recency: float
    significance: float


@dataclass(frozen=True)
class DiaryRetrievalCandidate:
    entry: AcceptedDiaryEntry          # immutable reference (exact, unmodified)
    ranking: DiaryRetrievalRanking     # rank signals only
    # NO selected / admitted / included field


@dataclass(frozen=True)
class DiaryRetrievalAudit:
    query: DiaryRetrievalQuery
    candidate_count: int
    # observability sidecar — never semantic content


class DiaryContextSource(Protocol):
    def retrieve(self, query: DiaryRetrievalQuery) -> tuple[DiaryRetrievalCandidate, ...]:
        """Rank immutable AcceptedDiaryEntry references. NO admission, NO mutation, NO synthesis."""
        ...


def _rank(entry: AcceptedDiaryEntry, query: DiaryRetrievalQuery) -> DiaryRetrievalRanking:
    relevance = 1.0 if query.query_text and query.query_text.lower() in entry.body.lower() else 0.0
    recency = 0.0
    if query.as_of is not None:
        # deterministic recency from explicit as_of — no hidden wall-clock
        recency = -abs((datetime.fromisoformat(query.as_of) - datetime.fromisoformat(entry.reflection_time)).total_seconds())
    significance = 1.0
    return DiaryRetrievalRanking(relevance, recency, significance)


def _sort_key(candidate: DiaryRetrievalCandidate) -> tuple:
    r = candidate.ranking
    return (-r.relevance, -r.recency, -r.significance, candidate.entry.entry_id)


class DeterministicDiaryContextSource:
    """Minimal Core DiaryContextSource — deterministic read/rank, no admission."""

    def __init__(self, repository: DiaryRepository) -> None:
        self._repository = repository

    def retrieve(self, query: DiaryRetrievalQuery) -> tuple[DiaryRetrievalCandidate, ...]:
        entries = self._repository.list_entries()
        candidates = [DiaryRetrievalCandidate(e, _rank(e, query)) for e in entries]
        # deterministic total ordering: relevance desc, recency desc, significance desc, entry_id asc
        candidates.sort(key=_sort_key)
        return tuple(candidates[:query.limit])
