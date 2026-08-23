"""AT-16 Diary retrieval through Context OS only.

This module admits governed Diary entries into short-lived Context OS projection
objects. It does not mutate Diary, write Memory, update Identity/Persona, rewrite
Conversation history, optimize ranking/search, or generate provider responses.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Protocol

from julia_core.context_os.block import ContextBlock
from julia_core.context_os.request import ContextRequest

from .models import AcceptedDiaryEntry
from .provenance import DiaryProvenanceReport, DiarySourceResolver, SourceRefState, validate_diary_provenance

_BODY_VISIBLE_STATES = frozenset({SourceRefState.RESOLVED, SourceRefState.ARCHIVED})
_CONTEXT_ADMISSIBLE_STATES = frozenset(
    {
        SourceRefState.RESOLVED,
        SourceRefState.ARCHIVED,
        SourceRefState.TOMBSTONED,
        SourceRefState.PURGED,
    }
)


class DiaryReadRepository(Protocol):
    """Read-only Diary repository port for Context OS retrieval."""

    def list_entries(self, *, before=None, after=None, limit=None) -> list[AcceptedDiaryEntry]:
        ...


@dataclass(frozen=True)
class DiaryContextAdmission:
    """Context admission result; projection only, never Diary/Memory authority."""

    entry: AcceptedDiaryEntry
    provenance_report: DiaryProvenanceReport
    admitted: bool
    reason: str
    body_visible: bool

    def __post_init__(self) -> None:
        if type(self.entry) is not AcceptedDiaryEntry:
            raise ValueError("DiaryContextAdmission.entry must be AcceptedDiaryEntry")
        if type(self.provenance_report) is not DiaryProvenanceReport:
            raise ValueError("DiaryContextAdmission.provenance_report must be DiaryProvenanceReport")
        if type(self.admitted) is not bool:
            raise ValueError("DiaryContextAdmission.admitted must be bool")
        if type(self.body_visible) is not bool:
            raise ValueError("DiaryContextAdmission.body_visible must be bool")
        if type(self.reason) is not str or not self.reason:
            raise ValueError("DiaryContextAdmission.reason must be a non-empty str")


@dataclass(frozen=True)
class DiaryContextCandidate:
    """Short-lived Context OS input candidate, not Diary/Memory/Identity authority."""

    admission: DiaryContextAdmission

    def __post_init__(self) -> None:
        if type(self.admission) is not DiaryContextAdmission:
            raise ValueError("DiaryContextCandidate.admission must be DiaryContextAdmission")
        if not self.admission.admitted:
            raise ValueError("rejected Diary admission cannot become a DiaryContextCandidate")

    @property
    def entry_id(self) -> str:
        return self.admission.entry.entry_id


@dataclass(frozen=True)
class DiaryContextAssemblyTrace:
    """Trace proving source → provenance → admission → ContextBlock assembly."""

    entry_id: str
    source_refs: tuple[str, ...]
    source_states: tuple[str, ...]
    admitted: bool
    body_visible: bool
    routed_through_context_os: bool = True
    mutated_diary: bool = False
    mutated_memory: bool = False
    mutated_identity: bool = False
    mutated_conversation: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "entry_id": self.entry_id,
            "source_refs": list(self.source_refs),
            "source_states": list(self.source_states),
            "admitted": self.admitted,
            "body_visible": self.body_visible,
            "routed_through_context_os": self.routed_through_context_os,
            "mutated_diary": self.mutated_diary,
            "mutated_memory": self.mutated_memory,
            "mutated_identity": self.mutated_identity,
            "mutated_conversation": self.mutated_conversation,
        }


def admit_diary_for_context(entry: AcceptedDiaryEntry, resolver: DiarySourceResolver) -> DiaryContextAdmission:
    """Validate provenance before allowing Diary into Context OS projection."""

    if type(entry) is not AcceptedDiaryEntry:
        raise ValueError("entry must be AcceptedDiaryEntry")
    report = validate_diary_provenance(entry, resolver)
    states = tuple(resolution.state for resolution in report.resolutions)
    if any(state in (SourceRefState.MISSING, SourceRefState.INVALID) for state in states):
        return DiaryContextAdmission(
            entry=entry,
            provenance_report=report,
            admitted=False,
            reason="missing-or-invalid-source",
            body_visible=False,
        )
    if not all(state in _CONTEXT_ADMISSIBLE_STATES for state in states):
        return DiaryContextAdmission(
            entry=entry,
            provenance_report=report,
            admitted=False,
            reason="source-state-not-context-admissible",
            body_visible=False,
        )
    body_visible = all(state in _BODY_VISIBLE_STATES for state in states)
    return DiaryContextAdmission(
        entry=entry,
        provenance_report=report,
        admitted=True,
        reason="context-os-admitted",
        body_visible=body_visible,
    )


def build_diary_context_block(candidate: DiaryContextCandidate) -> ContextBlock:
    """Convert an admitted Diary candidate into a short-lived ContextBlock."""

    if type(candidate) is not DiaryContextCandidate:
        raise ValueError("candidate must be DiaryContextCandidate")
    admission = candidate.admission
    entry = admission.entry
    source_refs = tuple(ref.uri for ref in entry.source_refs)
    source_states = tuple(resolution.state.value for resolution in admission.provenance_report.resolutions)
    content: dict[str, object] = {
        "type": "diary_context_projection",
        "entry_id": entry.entry_id,
        "title": entry.title or "",
        "themes": list(entry.themes),
        "body": entry.body if admission.body_visible else "",
        "body_visible": admission.body_visible,
        "source_states": list(source_states),
        "boundary": "Diary retrieval is Context OS projection, not Diary/Memory/Identity authority.",
    }
    return ContextBlock(
        source="diary_context_os_provider",
        content=content,
        authority="ContextOS",
        block_type="diary_retrieval",
        block_kind="diary_context_projection",
        domain="diary",
        evidence_refs=(f"diary://entry/{entry.entry_id}",),
        source_refs=source_refs,
        authority_score=0.8 if admission.body_visible else 0.4,
        required=False,
        estimated_tokens=max(80, len(entry.body) // 4) if admission.body_visible else 80,
        metadata={
            "entry_id": entry.entry_id,
            "admission_reason": admission.reason,
            "routed_through_context_os": True,
            "projection_only": True,
            "mutates_diary": False,
            "mutates_memory": False,
            "mutates_identity": False,
            "mutates_conversation": False,
        },
    )


def trace_diary_context_block(block: ContextBlock) -> DiaryContextAssemblyTrace:
    """Return AT-16 trace for an assembled Diary ContextBlock."""

    if type(block) is not ContextBlock:
        raise ValueError("block must be ContextBlock")
    if block.domain != "diary" or block.block_kind != "diary_context_projection":
        raise ValueError("block is not a Diary Context OS projection")
    content = block.content if isinstance(block.content, Mapping) else {}
    entry_id = str(block.metadata.get("entry_id") or content.get("entry_id") or "")
    source_states = tuple(str(item) for item in content.get("source_states", ())) if isinstance(content, Mapping) else ()
    return DiaryContextAssemblyTrace(
        entry_id=entry_id,
        source_refs=tuple(block.source_refs),
        source_states=source_states,
        admitted=True,
        body_visible=bool(content.get("body_visible", False)) if isinstance(content, Mapping) else False,
        routed_through_context_os=bool(block.metadata.get("routed_through_context_os", False)),
        mutated_diary=bool(block.metadata.get("mutates_diary", True)),
        mutated_memory=bool(block.metadata.get("mutates_memory", True)),
        mutated_identity=bool(block.metadata.get("mutates_identity", True)),
        mutated_conversation=bool(block.metadata.get("mutates_conversation", True)),
    )


class DiaryContextProvider:
    """Context OS domain provider for governed Diary retrieval."""

    domain = "diary"

    def __init__(self, repository: DiaryReadRepository, resolver: DiarySourceResolver) -> None:
        self.repository = repository
        self.resolver = resolver
        self.last_admissions: tuple[DiaryContextAdmission, ...] = ()
        self.last_trace: tuple[DiaryContextAssemblyTrace, ...] = ()

    def provide(self, request: ContextRequest) -> tuple[ContextBlock, ...]:
        if type(request) is not ContextRequest:
            raise ValueError("request must be ContextRequest")
        limit = int(request.constraints.get("diary_limit", 3))
        entries = tuple(self.repository.list_entries(limit=limit))
        admissions = tuple(admit_diary_for_context(entry, self.resolver) for entry in entries)
        blocks = tuple(
            build_diary_context_block(DiaryContextCandidate(admission))
            for admission in admissions
            if admission.admitted
        )
        self.last_admissions = admissions
        self.last_trace = tuple(trace_diary_context_block(block) for block in blocks)
        return blocks


def assert_not_diary_context_authority_object(value: object) -> None:
    """Guard reverse promotion from Context OS projection to canonical authority."""

    if type(value) in (DiaryContextAdmission, DiaryContextCandidate, DiaryContextAssemblyTrace, ContextBlock):
        raise TypeError("Diary Context OS projection objects are not Diary, Memory, Identity, or Conversation authority")


__all__ = [
    "DiaryContextAdmission",
    "DiaryContextAssemblyTrace",
    "DiaryContextCandidate",
    "DiaryContextProvider",
    "DiaryReadRepository",
    "admit_diary_for_context",
    "assert_not_diary_context_authority_object",
    "build_diary_context_block",
    "trace_diary_context_block",
]
