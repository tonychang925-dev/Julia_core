"""AT-13 minimal governed significant-event Diary path.

This module is intentionally narrow. It does not generate diary prose, call an
LLM/provider, redesign persistence, create MemoryExperience objects, or validate
broken sources (AT-14). It only provides the positive authority boundary for a
meaningful grounded event:

GroundedSignificantEvent -> DiaryCandidate -> GovernanceAccepted ->
AcceptedDiaryEntry -> DIARY_DURABLE.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .models import AcceptedDiaryEntry, DiaryCandidate, DiaryProvenance, DiarySourceRef
from .repository_protocol import DiaryRepository

_CANONICAL_SOURCE_PREFIXES = (
    "conversation://",
    "memory://experience/",
    "migration://",
)
_SUMMARY_MARKERS = (
    "summary:",
    "transcript summary",
    "conversation summary",
    "user said",
    "assistant said",
    "tony said",
    "the conversation",
    "本次对话总结",
    "对话总结",
    "用户说",
    "助手说",
    "tony说",
)
_FIRST_PERSON_MARKERS = (
    "我",
    "I ",
    "I'",
    "I'm",
    "my ",
    "me ",
)


def _require_non_empty_str(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty str")


def _require_tuple(name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")


def _is_canonical_source_ref(ref: DiarySourceRef) -> bool:
    return any(ref.uri.startswith(prefix) for prefix in _CANONICAL_SOURCE_PREFIXES)


def validate_canonical_source_refs(source_refs: tuple[DiarySourceRef, ...]) -> None:
    """AT-13 source authority namespace guard.

    This confirms refs are anchored to canonical source namespaces. It does not
    dereference or prove the target exists; broken/missing source detection is
    reserved for AT-14.
    """

    _require_tuple("source_refs", source_refs)
    if not source_refs:
        raise ValueError("source_refs must be non-empty")
    for ref in source_refs:
        if type(ref) is not DiarySourceRef:
            raise ValueError("source_refs must contain DiarySourceRef only")
        if not _is_canonical_source_ref(ref):
            raise ValueError("source_refs must use canonical source namespaces")


def validate_first_person_reflection_body(body: str) -> None:
    """Reject transcript summaries and require minimal first-person reflection."""

    _require_non_empty_str("body", body)
    normalized = " ".join(body.strip().split()).lower()
    if any(marker in normalized for marker in _SUMMARY_MARKERS):
        raise ValueError("Diary body must be first-person reflection, not transcript summary")
    if not any(marker in body for marker in _FIRST_PERSON_MARKERS):
        raise ValueError("Diary body must contain first-person reflection markers")


@dataclass(frozen=True)
class GroundedSignificantEvent:
    """A meaningful event input, not Diary authority."""

    event_id: str
    reflection_time: str
    source_refs: tuple[DiarySourceRef, ...]
    reflective_body: str
    provenance: DiaryProvenance
    title: str | None = None
    themes: tuple[str, ...] = ()
    relationship_significance: str | None = None
    project_significance: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str("GroundedSignificantEvent.event_id", self.event_id)
        _require_non_empty_str("GroundedSignificantEvent.reflection_time", self.reflection_time)
        if type(self.provenance) is not DiaryProvenance:
            raise ValueError("GroundedSignificantEvent.provenance must be DiaryProvenance")
        if self.title is not None and type(self.title) is not str:
            raise ValueError("GroundedSignificantEvent.title must be None or str")
        _require_tuple("GroundedSignificantEvent.themes", self.themes)
        if not all(type(theme) is str for theme in self.themes):
            raise ValueError("GroundedSignificantEvent.themes must contain str only")
        if self.relationship_significance is not None and type(self.relationship_significance) is not str:
            raise ValueError("GroundedSignificantEvent.relationship_significance must be None or str")
        if self.project_significance is not None and type(self.project_significance) is not str:
            raise ValueError("GroundedSignificantEvent.project_significance must be None or str")
        validate_canonical_source_refs(self.source_refs)
        validate_first_person_reflection_body(self.reflective_body)


@dataclass(frozen=True)
class DiaryGovernanceAcceptance:
    """Explicit acceptance proof for AT-13 promotion."""

    governance_id: str
    accepted_at: str
    accepted_by: str
    reason: str

    def __post_init__(self) -> None:
        _require_non_empty_str("DiaryGovernanceAcceptance.governance_id", self.governance_id)
        _require_non_empty_str("DiaryGovernanceAcceptance.accepted_at", self.accepted_at)
        _require_non_empty_str("DiaryGovernanceAcceptance.accepted_by", self.accepted_by)
        _require_non_empty_str("DiaryGovernanceAcceptance.reason", self.reason)


@dataclass(frozen=True)
class DiaryDurableCommit:
    """Observable DIARY_DURABLE result."""

    entry_id: str
    durable: bool

    def __post_init__(self) -> None:
        _require_non_empty_str("DiaryDurableCommit.entry_id", self.entry_id)
        if type(self.durable) is not bool:
            raise ValueError("DiaryDurableCommit.durable must be bool")


def create_diary_candidate(event: GroundedSignificantEvent) -> DiaryCandidate:
    """Create a review candidate from a grounded event; not canonical history."""

    if type(event) is not GroundedSignificantEvent:
        raise ValueError("event must be GroundedSignificantEvent")
    return DiaryCandidate(
        candidate_id=f"cand_{event.event_id}",
        reflection_time=event.reflection_time,
        source_refs=event.source_refs,
        body=event.reflective_body,
        provenance=event.provenance,
        title=event.title,
        themes=event.themes,
        relationship_significance=event.relationship_significance,
        project_significance=event.project_significance,
    )


def promote_candidate_to_accepted_entry(
    candidate: DiaryCandidate,
    acceptance: DiaryGovernanceAcceptance,
) -> AcceptedDiaryEntry:
    """Promote a candidate only through explicit governance acceptance."""

    if type(candidate) is not DiaryCandidate:
        raise ValueError("candidate must be DiaryCandidate")
    if type(acceptance) is not DiaryGovernanceAcceptance:
        raise ValueError("acceptance must be DiaryGovernanceAcceptance")
    validate_canonical_source_refs(candidate.source_refs)
    validate_first_person_reflection_body(candidate.body)
    body_hash = sha256(candidate.body.encode("utf-8")).hexdigest()
    stable_seed = f"{candidate.candidate_id}:{acceptance.governance_id}:{body_hash}"
    entry_hash = sha256(stable_seed.encode("utf-8")).hexdigest()[:24]
    return AcceptedDiaryEntry(
        entry_id=f"diary_{entry_hash}",
        created_at=acceptance.accepted_at,
        reflection_time=candidate.reflection_time,
        source_refs=candidate.source_refs,
        body=candidate.body,
        body_hash=body_hash,
        provenance=candidate.provenance,
        title=candidate.title,
        themes=candidate.themes,
        relationship_significance=candidate.relationship_significance,
        project_significance=candidate.project_significance,
        governance_status="accepted",
    )


def commit_accepted_entry_durable(
    entry: AcceptedDiaryEntry,
    repository: DiaryRepository,
) -> DiaryDurableCommit:
    """Cross the DIARY_DURABLE boundary via repository append and visibility."""

    if type(entry) is not AcceptedDiaryEntry:
        raise ValueError("entry must be AcceptedDiaryEntry")
    if repository is None:
        raise ValueError("repository is required")
    repository.append_accepted(entry)
    observed = repository.get(entry.entry_id)
    if observed != entry:
        raise RuntimeError("DIARY_DURABLE was not established")
    return DiaryDurableCommit(entry_id=entry.entry_id, durable=True)


__all__ = [
    "DiaryDurableCommit",
    "DiaryGovernanceAcceptance",
    "GroundedSignificantEvent",
    "commit_accepted_entry_durable",
    "create_diary_candidate",
    "promote_candidate_to_accepted_entry",
    "validate_canonical_source_refs",
    "validate_first_person_reflection_body",
]
