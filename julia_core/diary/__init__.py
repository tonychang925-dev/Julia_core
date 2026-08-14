"""Diary — semantic domain (Wave-3 / DIA-1 + DIA-2A).

DIA-1 freezes immutable semantic value types. DIA-2A adds the
application-agnostic DiaryRepository port (Core semantics only).
No filesystem, no persistence, no governance execution, no Memory/Context
/provider dependency.
"""
from .models import (
    AcceptedDiaryEntry,
    DiaryCandidate,
    DiaryProvenance,
    DiarySourceRef,
    NoEntry,
    NO_ENTRY,
    ReflectionResult,
)
from .repository_protocol import DiaryRepository

__all__ = [
    "DiarySourceRef",
    "DiaryProvenance",
    "DiaryCandidate",
    "AcceptedDiaryEntry",
    "NoEntry",
    "NO_ENTRY",
    "ReflectionResult",
    "DiaryRepository",
]
