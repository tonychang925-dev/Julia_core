"""DIA-1 — Core Diary domain value types (immutable semantic objects only).

Frozen A0–A7 semantics:
  ReflectionResult = NO_ENTRY | DiaryCandidate
  DiaryCandidate    ≠ accepted DiaryEntry ≠ durable truth ≠ Memory
  AcceptedDiaryEntry exists only after GOVERNANCE_APPROVED AND DIARY_DURABLE
  (DIA-1 defines the shape; DIA-2 persistence / DIA-6 governance own the flow).

Immutability is enforced at runtime, deep: collection fields MUST be tuples
of immutable primitives (never a mutable list, never a mutable list nested
inside a tuple); provenance/source-ref fields MUST be the value types.

Only representation/type is checked, never meaning ("is this theme reasonable?"
/ "does this supersedes target exist?" / "does this URI resolve?" are DIA-6 /
repository / source-resolution concerns).

Forbidden here: filesystem I/O, persistence, governance execution, Memory
mutation, Context visibility, provider/LLM, Assistant/Electron. stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Union


def _require_tuple(name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")


def _require_non_empty_str(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty str")


def _require_optional_str(name: str, value: object) -> None:
    if value is not None and type(value) is not str:
        raise ValueError(f"{name} must be None or str")


def _require_str_tuple(name: str, value: object) -> None:
    _require_tuple(name, value)
    if not all(type(item) is str for item in value):
        raise ValueError(f"{name} must be a tuple of str")


@dataclass(frozen=True)
class DiarySourceRef:
    """Semantic source reference (opaque URI), never a filesystem reference.

    Examples:
      conversation://conv_A/msg_123
      conversation://conv_A/turn_456
      memory://experience/...
      migration://claude_legacy/...
    """

    uri: str

    def __post_init__(self) -> None:
        _require_non_empty_str("DiarySourceRef.uri", self.uri)


@dataclass(frozen=True)
class DiaryProvenance:
    """Minimal model/runtime provenance. Exists; carries no observability schema."""

    model_provider: str
    model_name: str
    runtime: str

    def __post_init__(self) -> None:
        _require_non_empty_str("DiaryProvenance.model_provider", self.model_provider)
        _require_non_empty_str("DiaryProvenance.model_name", self.model_name)
        _require_non_empty_str("DiaryProvenance.runtime", self.runtime)


@dataclass(frozen=True)
class DiaryCandidate:
    """A Julia reflection warranting governance review.

    NOT accepted truth, NOT durable, NOT Memory.
    """

    candidate_id: str
    reflection_time: str
    source_refs: tuple[DiarySourceRef, ...]
    body: str
    provenance: DiaryProvenance
    title: str | None = None
    themes: tuple[str, ...] = ()
    relationship_significance: str | None = None
    project_significance: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str("DiaryCandidate.candidate_id", self.candidate_id)
        _require_non_empty_str("DiaryCandidate.reflection_time", self.reflection_time)
        _require_non_empty_str("DiaryCandidate.body", self.body)
        _require_optional_str("DiaryCandidate.title", self.title)
        _require_str_tuple("DiaryCandidate.themes", self.themes)
        _require_optional_str("DiaryCandidate.relationship_significance", self.relationship_significance)
        _require_optional_str("DiaryCandidate.project_significance", self.project_significance)
        if type(self.provenance) is not DiaryProvenance:
            raise ValueError("DiaryCandidate.provenance must be DiaryProvenance")
        _require_tuple("DiaryCandidate.source_refs", self.source_refs)
        if not self.source_refs:
            raise ValueError("DiaryCandidate.source_refs must be non-empty")
        if not all(type(ref) is DiarySourceRef for ref in self.source_refs):
            raise ValueError("DiaryCandidate.source_refs must contain DiarySourceRef only")


@dataclass(frozen=True)
class AcceptedDiaryEntry:
    """A governed, durable DiaryEntry (shape only; truth boundary is external).

    body_hash supports idempotent recovery (D0-02); it is caller-supplied here,
    not computed/verified in DIA-1.
    """

    entry_id: str
    created_at: str
    reflection_time: str
    source_refs: tuple[DiarySourceRef, ...]
    body: str
    body_hash: str
    provenance: DiaryProvenance
    title: str | None = None
    themes: tuple[str, ...] = ()
    relationship_significance: str | None = None
    project_significance: str | None = None
    supersedes: tuple[str, ...] = ()
    reinterprets: tuple[str, ...] = ()
    governance_status: str = "accepted"

    def __post_init__(self) -> None:
        _require_non_empty_str("AcceptedDiaryEntry.entry_id", self.entry_id)
        _require_non_empty_str("AcceptedDiaryEntry.created_at", self.created_at)
        _require_non_empty_str("AcceptedDiaryEntry.reflection_time", self.reflection_time)
        _require_non_empty_str("AcceptedDiaryEntry.body", self.body)
        _require_non_empty_str("AcceptedDiaryEntry.body_hash", self.body_hash)
        _require_optional_str("AcceptedDiaryEntry.title", self.title)
        _require_str_tuple("AcceptedDiaryEntry.themes", self.themes)
        _require_optional_str("AcceptedDiaryEntry.relationship_significance", self.relationship_significance)
        _require_optional_str("AcceptedDiaryEntry.project_significance", self.project_significance)
        _require_str_tuple("AcceptedDiaryEntry.supersedes", self.supersedes)
        _require_str_tuple("AcceptedDiaryEntry.reinterprets", self.reinterprets)
        _require_non_empty_str("AcceptedDiaryEntry.governance_status", self.governance_status)
        if self.governance_status != "accepted":
            raise ValueError("AcceptedDiaryEntry.governance_status must be 'accepted'")
        if type(self.provenance) is not DiaryProvenance:
            raise ValueError("AcceptedDiaryEntry.provenance must be DiaryProvenance")
        _require_tuple("AcceptedDiaryEntry.source_refs", self.source_refs)
        if not self.source_refs:
            raise ValueError("AcceptedDiaryEntry.source_refs must be non-empty")
        if not all(type(ref) is DiarySourceRef for ref in self.source_refs):
            raise ValueError("AcceptedDiaryEntry.source_refs must contain DiarySourceRef only")


@dataclass(frozen=True)
class NoEntry:
    """First-class reflection result: Julia reflected, nothing warranted a diary.

    NOT None, NOT False, NOT "", NOT an error, NOT missing data.
    """

    pass


NO_ENTRY = NoEntry()

# ReflectionResult = NO_ENTRY | DiaryCandidate (never AcceptedDiaryEntry, never Exception)
ReflectionResult = Union[NoEntry, DiaryCandidate]
