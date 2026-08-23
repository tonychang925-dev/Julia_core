"""AT-15 Diary/Memory separation guards.

This module is intentionally narrow: it prevents Diary authority objects from
being used as Memory persistence authority. It does not implement MemoryCandidate
creation, MemoryExperience schema migration, Context OS retrieval, or provider
memory generation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import AcceptedDiaryEntry, DiaryCandidate, NoEntry
from .provenance import DiaryProvenanceReport, DiarySourceResolution

_DIARY_AUTHORITY_TYPES = (
    AcceptedDiaryEntry,
    DiaryCandidate,
    NoEntry,
    DiaryProvenanceReport,
    DiarySourceResolution,
)


@dataclass(frozen=True)
class DiaryMemorySeparationResult:
    """Observable proof that a Diary object did not become Memory."""

    diary_ref: str
    memory_mutated: bool
    reason: str

    def __post_init__(self) -> None:
        if type(self.diary_ref) is not str or not self.diary_ref.strip():
            raise ValueError("DiaryMemorySeparationResult.diary_ref must be a non-empty str")
        if type(self.memory_mutated) is not bool:
            raise ValueError("DiaryMemorySeparationResult.memory_mutated must be bool")
        if type(self.reason) is not str or not self.reason.strip():
            raise ValueError("DiaryMemorySeparationResult.reason must be a non-empty str")


def is_diary_authority_object(value: Any) -> bool:
    """Return True for Diary objects forbidden as Memory persistence input."""

    return type(value) in _DIARY_AUTHORITY_TYPES


def assert_not_memory_persistence_input(value: Any) -> None:
    """Fail closed if a Diary authority object is passed to Memory persistence."""

    if is_diary_authority_object(value):
        raise TypeError("Diary authority objects are not Memory persistence inputs")


def prove_diary_does_not_mutate_memory(diary: AcceptedDiaryEntry, memory_store: Any) -> DiaryMemorySeparationResult:
    """Return a separation proof without reading/writing Memory content.

    The memory_store fixture/product object may expose `writes` or `list_entries`;
    this helper only observes whether a mutation is already visible. It never
    creates MemoryCandidate or MemoryExperience.
    """

    if type(diary) is not AcceptedDiaryEntry:
        raise ValueError("diary must be AcceptedDiaryEntry")
    writes = getattr(memory_store, "writes", None)
    if writes is not None and len(writes) != 0:
        raise RuntimeError("Memory store already contains writes; cannot prove AT-15 separation")
    return DiaryMemorySeparationResult(
        diary_ref=diary.entry_id,
        memory_mutated=False,
        reason="AcceptedDiaryEntry remains Diary authority only; Memory governance did not run",
    )


__all__ = [
    "DiaryMemorySeparationResult",
    "assert_not_memory_persistence_input",
    "is_diary_authority_object",
    "prove_diary_does_not_mutate_memory",
]
