"""Governed Julia Diary semantic domain.

AT-12 boundary: ReflectionTrigger is only an opportunity; NO_ENTRY is a valid
terminal reflection result and creates no canonical Diary artifact.
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
from .reflection_decision import ReflectionOpportunity, decide_trivial_reflection
from .repository_protocol import DiaryRepository

__all__ = [
    "AcceptedDiaryEntry",
    "DiaryCandidate",
    "DiaryProvenance",
    "DiaryRepository",
    "DiarySourceRef",
    "NoEntry",
    "NO_ENTRY",
    "ReflectionOpportunity",
    "ReflectionResult",
    "decide_trivial_reflection",
]
