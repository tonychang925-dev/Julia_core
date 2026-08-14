"""DIA-1 — Core Diary domain value types (immutable semantic objects only).

Frozen A0–A7 semantics:
  ReflectionResult = NO_ENTRY | DiaryCandidate
  DiaryCandidate    ≠ accepted DiaryEntry ≠ durable truth ≠ Memory
  AcceptedDiaryEntry exists only after GOVERNANCE_APPROVED AND DIARY_DURABLE
  (DIA-1 defines the shape; DIA-2 persistence / DIA-6 governance own the flow).

Forbidden here: filesystem I/O, persistence, governance execution, Memory
mutation, Context visibility, provider/LLM, Assistant/Electron. stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass


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
        if not self.uri or not self.uri.strip():
            raise ValueError("DiarySourceRef uri must be non-empty")


@dataclass(frozen=True)
class DiaryProvenance:
    """Minimal model/runtime provenance. Exists; carries no observability schema."""

    model_provider: str
    model_name: str
    runtime: str

    def __post_init__(self) -> None:
        if not self.model_provider or not self.model_provider.strip():
            raise ValueError("DiaryProvenance.model_provider must be non-empty")
        if not self.model_name or not self.model_name.strip():
            raise ValueError("DiaryProvenance.model_name must be non-empty")
        if not self.runtime or not self.runtime.strip():
            raise ValueError("DiaryProvenance.runtime must be non-empty")


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
        if not self.candidate_id or not self.candidate_id.strip():
            raise ValueError("DiaryCandidate.candidate_id must be non-empty")
        if not self.body or not self.body.strip():
            raise ValueError("DiaryCandidate.body must be non-empty")
        if not self.source_refs:
            raise ValueError("DiaryCandidate.source_refs must be non-empty")


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
    governance_status: str = "accepted"

    def __post_init__(self) -> None:
        if not self.entry_id or not self.entry_id.strip():
            raise ValueError("AcceptedDiaryEntry.entry_id must be non-empty")
        if not self.body or not self.body.strip():
            raise ValueError("AcceptedDiaryEntry.body must be non-empty")
        if not self.source_refs:
            raise ValueError("AcceptedDiaryEntry.source_refs must be non-empty")
        if not self.body_hash or not self.body_hash.strip():
            raise ValueError("AcceptedDiaryEntry.body_hash must be non-empty")
        if self.governance_status != "accepted":
            raise ValueError("AcceptedDiaryEntry.governance_status must be 'accepted'")


@dataclass(frozen=True)
class NoEntry:
    """First-class reflection result: Julia reflected, nothing warranted a diary.

    NOT None, NOT False, NOT "", NOT an error, NOT missing data.
    """

    pass


NO_ENTRY = NoEntry()

# ReflectionResult = NO_ENTRY | DiaryCandidate (never AcceptedDiaryEntry, never Exception)
ReflectionResult = NoEntry | DiaryCandidate
