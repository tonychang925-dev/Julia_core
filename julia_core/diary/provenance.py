"""AT-14 minimal Diary provenance resolution boundary.

This module validates source reference lifecycle state for accepted Diary entries.
It does not dereference real storage, copy transcript/source content, mutate Diary
entries, create MemoryExperience objects, or feed Context OS/model visibility.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Union

from .models import AcceptedDiaryEntry, DiarySourceRef

_CANONICAL_SOURCE_PREFIXES = (
    "conversation://",
    "memory://experience/",
    "migration://",
)


class SourceRefState(str, Enum):
    """Explicit lifecycle state for a Diary source reference."""

    RESOLVED = "RESOLVED"
    ARCHIVED = "ARCHIVED"
    TOMBSTONED = "TOMBSTONED"
    PURGED = "PURGED"
    MISSING = "MISSING"
    INVALID = "INVALID"


def _require_non_empty_str(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty str")


def _require_tuple(name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")


def classify_source_namespace(source_ref: DiarySourceRef) -> str:
    """Return source namespace or INVALID for non-authority refs."""

    if type(source_ref) is not DiarySourceRef:
        raise ValueError("source_ref must be DiarySourceRef")
    for prefix in _CANONICAL_SOURCE_PREFIXES:
        if source_ref.uri.startswith(prefix):
            return prefix[:-3]
    return "INVALID"


@dataclass(frozen=True)
class DiarySourceResolution:
    """Per-ref provenance result. Contains lifecycle only, never source content."""

    source_ref: DiarySourceRef
    state: SourceRefState
    namespace: str
    detail: str = ""

    def __post_init__(self) -> None:
        if type(self.source_ref) is not DiarySourceRef:
            raise ValueError("DiarySourceResolution.source_ref must be DiarySourceRef")
        if type(self.state) is not SourceRefState:
            raise ValueError("DiarySourceResolution.state must be SourceRefState")
        _require_non_empty_str("DiarySourceResolution.namespace", self.namespace)
        if type(self.detail) is not str:
            raise ValueError("DiarySourceResolution.detail must be str")


class DiarySourceResolver(Protocol):
    """Fixture/product port for resolving a Diary source ref lifecycle."""

    def resolve(self, source_ref: DiarySourceRef) -> Union[SourceRefState, DiarySourceResolution]:
        """Resolve a source ref to explicit lifecycle state; never return None."""
        ...


@dataclass(frozen=True)
class DiaryProvenanceReport:
    """Derived provenance report for an AcceptedDiaryEntry."""

    entry_id: str
    resolutions: tuple[DiarySourceResolution, ...]

    def __post_init__(self) -> None:
        _require_non_empty_str("DiaryProvenanceReport.entry_id", self.entry_id)
        _require_tuple("DiaryProvenanceReport.resolutions", self.resolutions)
        if not self.resolutions:
            raise ValueError("DiaryProvenanceReport.resolutions must be non-empty")
        if not all(type(item) is DiarySourceResolution for item in self.resolutions):
            raise ValueError("DiaryProvenanceReport.resolutions must contain DiarySourceResolution only")
        uris = [item.source_ref.uri for item in self.resolutions]
        if len(uris) != len(set(uris)):
            raise ValueError("DiaryProvenanceReport.resolutions must not duplicate source refs")

    @property
    def has_missing_or_invalid(self) -> bool:
        return any(item.state in (SourceRefState.MISSING, SourceRefState.INVALID) for item in self.resolutions)


def _normalize_resolution(
    source_ref: DiarySourceRef,
    result: Union[SourceRefState, DiarySourceResolution],
) -> DiarySourceResolution:
    namespace = classify_source_namespace(source_ref)
    if type(result) is SourceRefState:
        return DiarySourceResolution(source_ref=source_ref, state=result, namespace=namespace)
    if type(result) is DiarySourceResolution:
        if result.source_ref != source_ref:
            raise ValueError("resolver returned resolution for a different source_ref")
        return result
    raise ValueError("resolver must return SourceRefState or DiarySourceResolution")


def validate_diary_provenance(
    entry: AcceptedDiaryEntry,
    resolver: DiarySourceResolver,
) -> DiaryProvenanceReport:
    """Resolve every accepted Diary source ref exactly once.

    Invalid namespaces are reported as INVALID without asking the resolver.
    Resolver errors/None are not converted to provenance truth.
    """

    if type(entry) is not AcceptedDiaryEntry:
        raise ValueError("entry must be AcceptedDiaryEntry")
    if resolver is None:
        raise ValueError("resolver is required")

    resolutions: list[DiarySourceResolution] = []
    for source_ref in entry.source_refs:
        namespace = classify_source_namespace(source_ref)
        if namespace == "INVALID":
            resolutions.append(
                DiarySourceResolution(
                    source_ref=source_ref,
                    state=SourceRefState.INVALID,
                    namespace="INVALID",
                    detail="non-canonical source namespace",
                )
            )
            continue
        result = resolver.resolve(source_ref)
        resolution = _normalize_resolution(source_ref, result)
        resolutions.append(resolution)

    report = DiaryProvenanceReport(entry_id=entry.entry_id, resolutions=tuple(resolutions))
    expected_refs = tuple(ref.uri for ref in entry.source_refs)
    reported_refs = tuple(item.source_ref.uri for item in report.resolutions)
    if reported_refs != expected_refs:
        raise RuntimeError("Diary provenance report must cover every source_ref exactly once and in order")
    return report


__all__ = [
    "DiaryProvenanceReport",
    "DiarySourceResolution",
    "DiarySourceResolver",
    "SourceRefState",
    "classify_source_namespace",
    "validate_diary_provenance",
]
