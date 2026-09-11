"""ENG-09 C-05 MemoryExperience engineering candidate.

This bounded canonical seam stores governed lived/history semantics only. It
has no recall, context admission, continuity hydration, runtime, or provider
authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any
from urllib.parse import urlsplit


MAX_EXPERIENCE_TEXT_LENGTH = 4_000
MAX_ID_LENGTH = 256


class MemoryExperienceConflictError(ValueError):
    pass


class MemoryExperienceRefNotFoundError(LookupError):
    pass


class MemoryExperienceLifecycleError(ValueError):
    pass


class MemoryExperienceType(str, Enum):
    NARRATIVE = "NarrativeExperience"
    RELATIONSHIP = "RelationshipExperience"
    PREFERENCE = "PreferenceExperience"
    PROJECT_COMMITMENT = "ProjectCommitmentExperience"
    EPISODIC = "EpisodicExperience"


class MemoryExperienceStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    ADMITTED = "ADMITTED"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"


class CommitmentTransferSemantics(str, Enum):
    NOT_TRANSFERABLE = "NOT_TRANSFERABLE"
    EXPLICIT_REAUTHORIZATION_REQUIRED = "EXPLICIT_REAUTHORIZATION_REQUIRED"


@dataclass(frozen=True, slots=True)
class NarrativeExperienceContent:
    event: str
    meaning_at_time: str
    significance: str
    later_reinterpretation: str = ""
    source_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.event, "event")
        _require_text(self.meaning_at_time, "meaning_at_time")
        _require_text(self.significance, "significance")
        if type(self.later_reinterpretation) is not str:
            raise ValueError("later_reinterpretation must be an exact built-in string")
        if self.later_reinterpretation:
            _require_text(self.later_reinterpretation, "later_reinterpretation")
        object.__setattr__(self, "source_refs", tuple(self.source_refs))
        for source_ref in self.source_refs:
            _require_ref(source_ref)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"source_refs": list(self.source_refs)}


@dataclass(frozen=True, slots=True)
class RelationshipExperienceContent:
    relationship_id: str
    event: str
    interpretation: str
    occurred_at: str

    def __post_init__(self) -> None:
        _require_id(self.relationship_id, "relationship_id")
        _require_text(self.event, "event")
        _require_text(self.interpretation, "interpretation")
        _require_text(self.occurred_at, "occurred_at", max_length=128)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PreferenceExperienceContent:
    subject: str
    preference: str
    learned_from_event: str
    source_ref: str

    def __post_init__(self) -> None:
        _require_id(self.subject, "subject")
        _require_text(self.preference, "preference", max_length=512)
        _require_text(self.learned_from_event, "learned_from_event")
        _require_ref(self.source_ref)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ProjectCommitmentExperienceContent:
    subject: str
    counterparty: str
    scope: str
    commitment: str
    transfer_semantics: CommitmentTransferSemantics
    occurred_at: str

    def __post_init__(self) -> None:
        _require_id(self.subject, "subject")
        _require_id(self.counterparty, "counterparty")
        _require_text(self.scope, "scope")
        _require_text(self.commitment, "commitment")
        if type(self.transfer_semantics) is not CommitmentTransferSemantics:
            raise ValueError(
                "transfer_semantics must be an explicit commitment transfer enum"
            )
        _require_text(self.occurred_at, "occurred_at", max_length=128)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["transfer_semantics"] = self.transfer_semantics.value
        return data


@dataclass(frozen=True, slots=True)
class EpisodicExperienceContent:
    event: str
    occurred_at: str
    context: str
    source_ref: str

    def __post_init__(self) -> None:
        _require_text(self.event, "event")
        _require_text(self.occurred_at, "occurred_at", max_length=128)
        _require_text(self.context, "context")
        _require_ref(self.source_ref)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


MemoryExperienceContent = (
    NarrativeExperienceContent
    | RelationshipExperienceContent
    | PreferenceExperienceContent
    | ProjectCommitmentExperienceContent
    | EpisodicExperienceContent
)


@dataclass(frozen=True, slots=True)
class MemoryExperienceProvenance:
    source_type: str
    source_ref: str
    source_digest: str
    admission_metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        metadata = tuple(self.admission_metadata)
        _require_id(self.source_type, "source_type")
        _require_ref(self.source_ref)
        if len(self.source_digest) != 64 or any(
            char not in "0123456789abcdef" for char in self.source_digest
        ):
            raise ValueError("source_digest must be a lowercase SHA-256 hex digest")
        if not isinstance(self.admission_metadata, tuple):
            raise ValueError("admission_metadata must contain key/value string pairs")
        object.__setattr__(self, "admission_metadata", metadata)
        for item in metadata:
            if (
                type(item) is not tuple
                or len(item) != 2
                or type(item[0]) is not str
                or type(item[1]) is not str
            ):
                raise ValueError(
                    "admission_metadata must contain key/value string pairs"
                )
        metadata_keys = [key for key, _ in metadata]
        if len(metadata_keys) != len(set(metadata_keys)):
            raise ValueError("admission_metadata keys must be unique")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "source_digest": self.source_digest,
            "admission_metadata": dict(self.admission_metadata),
        }


@dataclass(frozen=True, slots=True)
class MemoryExperienceRef:
    experience_id: str
    version_id: str

    def __post_init__(self) -> None:
        _require_id(self.experience_id, "experience_id")
        _require_id(self.version_id, "version_id")

    @property
    def uri(self) -> str:
        return f"memory-experience://{self.experience_id}/{self.version_id}"

    def to_dict(self) -> dict[str, Any]:
        return {"experience_id": self.experience_id, "version_id": self.version_id}


@dataclass(frozen=True, slots=True)
class MemoryExperienceRecord:
    experience_id: str
    version_id: str
    experience_type: MemoryExperienceType
    content: MemoryExperienceContent
    provenance_refs: tuple[MemoryExperienceProvenance, ...]
    created_at: str
    predecessor_version_id: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.experience_id, "experience_id")
        _require_id(self.version_id, "version_id")
        if type(self.experience_type) is not MemoryExperienceType:
            raise ValueError("experience_type must be a canonical MemoryExperienceType")
        expected_type = _CONTENT_TYPE_BY_EXPERIENCE_TYPE[self.experience_type]
        if type(self.content) is not expected_type:
            raise ValueError(
                f"{self.experience_type.value} requires exact {expected_type.__name__}"
            )
        object.__setattr__(self, "provenance_refs", tuple(self.provenance_refs))
        if any(
            type(item) is not MemoryExperienceProvenance
            for item in self.provenance_refs
        ):
            raise ValueError(
                "provenance_refs elements must be MemoryExperienceProvenance"
            )
        if not self.provenance_refs:
            raise ValueError("MemoryExperienceRecord requires provenance")
        _require_text(self.created_at, "created_at", max_length=128)
        if self.predecessor_version_id is not None:
            _require_id(self.predecessor_version_id, "predecessor_version_id")

    @property
    def ref(self) -> MemoryExperienceRef:
        return MemoryExperienceRef(self.experience_id, self.version_id)

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.memory_experience.record.v1",
            "experience_id": self.experience_id,
            "version_id": self.version_id,
            "experience_type": self.experience_type.value,
            "content": self.content.to_dict(),
            "provenance_refs": [item.to_dict() for item in self.provenance_refs],
            "created_at": self.created_at,
            "predecessor_version_id": self.predecessor_version_id,
            "authority": {
                "standing_authorization": False,
                "current_consent": False,
                "mutates_identity": False,
                "runtime_authority": False,
            },
        }

    def canonical_serialization(self) -> str:
        return json.dumps(
            self.canonical_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def digest(self) -> str:
        return hashlib.sha256(
            self.canonical_serialization().encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class MemoryExperienceCandidate:
    record: MemoryExperienceRecord
    submitted_at: str

    def __post_init__(self) -> None:
        if type(self.record) is not MemoryExperienceRecord:
            raise TypeError(
                "MemoryExperienceCandidate requires an exact MemoryExperienceRecord"
            )
        _require_text(self.submitted_at, "submitted_at", max_length=128)


@dataclass(frozen=True, slots=True)
class MemoryExperienceAdmission:
    admission_id: str
    target: MemoryExperienceRef
    actor: str
    reason: str
    occurred_at: str

    def __post_init__(self) -> None:
        _require_id(self.admission_id, "admission_id")
        _require_id(self.actor, "actor")
        _require_text(self.reason, "reason")
        _require_text(self.occurred_at, "occurred_at", max_length=128)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["target"] = self.target.to_dict()
        return data


@dataclass(frozen=True, slots=True)
class GovernedMemoryExperience:
    record: MemoryExperienceRecord
    status: MemoryExperienceStatus
    governance_events: tuple[
        tuple[MemoryExperienceStatus, MemoryExperienceAdmission | None], ...
    ]

    @property
    def ref(self) -> MemoryExperienceRef:
        return self.record.ref

    def to_dict(self) -> dict[str, Any]:
        return {
            "record": self.record.canonical_payload(),
            "status": self.status.value,
            "governance_events": [
                {
                    "status": status.value,
                    "admission": admission.to_dict() if admission is not None else None,
                }
                for status, admission in self.governance_events
            ],
        }


_CONTENT_TYPE_BY_EXPERIENCE_TYPE = {
    MemoryExperienceType.NARRATIVE: NarrativeExperienceContent,
    MemoryExperienceType.RELATIONSHIP: RelationshipExperienceContent,
    MemoryExperienceType.PREFERENCE: PreferenceExperienceContent,
    MemoryExperienceType.PROJECT_COMMITMENT: ProjectCommitmentExperienceContent,
    MemoryExperienceType.EPISODIC: EpisodicExperienceContent,
}


def _require_id(value: str, field_name: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an exact built-in string")
    if not value or not value.strip() or len(value) > MAX_ID_LENGTH:
        raise ValueError(
            f"{field_name} is required and must be at most {MAX_ID_LENGTH} characters"
        )


def _require_text(
    value: str, field_name: str, *, max_length: int = MAX_EXPERIENCE_TEXT_LENGTH
) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an exact built-in string")
    if not value or not value.strip() or len(value) > max_length:
        raise ValueError(
            f"{field_name} is required and must be at most {max_length} characters"
        )


def _require_ref(value: str) -> None:
    if type(value) is not str:
        raise ValueError("experience source references must be exact built-in strings")
    if not value or len(value) > 2_048 or any(char.isspace() for char in value):
        raise ValueError("experience source references must be URI-shaped and bounded")
    parsed = urlsplit(value)
    scheme = parsed.scheme
    valid_scheme = (
        bool(scheme)
        and scheme[0].isalpha()
        and all(char.isascii() and (char.isalnum() or char in "+-.") for char in scheme)
    )
    if not valid_scheme or not parsed.netloc:
        raise ValueError("experience source references must be URI-shaped and bounded")


__all__ = [
    "CommitmentTransferSemantics",
    "EpisodicExperienceContent",
    "GovernedMemoryExperience",
    "MemoryExperienceAdmission",
    "MemoryExperienceCandidate",
    "MemoryExperienceContent",
    "MemoryExperienceProvenance",
    "MemoryExperienceRecord",
    "MemoryExperienceRef",
    "MemoryExperienceStatus",
    "MemoryExperienceType",
    "NarrativeExperienceContent",
    "PreferenceExperienceContent",
    "ProjectCommitmentExperienceContent",
    "RelationshipExperienceContent",
]
