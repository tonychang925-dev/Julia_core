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


class CausalStatus(str, Enum):
    DIRECT_RAW_SUPPORTED = "DIRECT_RAW_SUPPORTED"
    INFERRED_CROSS_RECORD = "INFERRED_CROSS_RECORD"
    MIXED_DIRECT_AND_INFERRED = "MIXED_DIRECT_AND_INFERRED"


class PolicyTransferApplicability(str, Enum):
    HISTORICAL_EXPLANATION = "HISTORICAL_EXPLANATION"
    FUTURE_POLICY_CANDIDATE = "FUTURE_POLICY_CANDIDATE"


class SubjectIdentity(str, Enum):
    MIRA = "MIRA"
    TONY = "TONY"
    OTHER_EXACT_ID = "OTHER_EXACT_ID"


class AutobiographicalOwner(str, Enum):
    MIRA = "MIRA"
    TONY = "TONY"
    NONE = "NONE"


class CommitmentStage(str, Enum):
    FORMATION_DRAFT = "FORMATION_DRAFT"
    FROZEN_FINAL = "FROZEN_FINAL"


@dataclass(frozen=True, slots=True)
class EvidenceBindingRef:
    binding_id: str
    evidence_role: str

    def __post_init__(self) -> None:
        _require_id(self.binding_id, "binding_id")
        _require_id(self.evidence_role, "evidence_role")

    def to_dict(self) -> dict[str, Any]:
        return {"binding_id": self.binding_id, "evidence_role": self.evidence_role}


@dataclass(frozen=True, slots=True)
class PolicyTransferSemantics:
    observed_scope: str
    applicability_scope: PolicyTransferApplicability
    future_behavior_proof: bool = False
    binding_role_refs: tuple[EvidenceBindingRef, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.observed_scope, "observed_scope", max_length=2_048)
        _require_enum(
            self.applicability_scope, PolicyTransferApplicability, "applicability_scope"
        )
        if self.future_behavior_proof is not False:
            raise ValueError("future_behavior_proof must remain false")
        _require_present_binding_refs(self.binding_role_refs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "coverage": "PRESENT",
            "observed_scope": self.observed_scope,
            "applicability_scope": self.applicability_scope.value,
            "future_behavior_proof": False,
            "binding_role_refs": [item.to_dict() for item in self.binding_role_refs],
        }


@dataclass(frozen=True, slots=True)
class PolicyTransferNotApplicable:
    reason: str

    def __post_init__(self) -> None:
        _require_text(self.reason, "reason", max_length=2_048)

    def to_dict(self) -> dict[str, Any]:
        return {"coverage": "NOT_APPLICABLE", "reason": self.reason}


@dataclass(frozen=True, slots=True)
class SubjectBoundary:
    semantic_subject: SubjectIdentity
    observed_subject: SubjectIdentity
    autobiographical_owner: AutobiographicalOwner

    def __post_init__(self) -> None:
        _require_enum(self.semantic_subject, SubjectIdentity, "semantic_subject")
        _require_enum(self.observed_subject, SubjectIdentity, "observed_subject")
        _require_enum(
            self.autobiographical_owner,
            AutobiographicalOwner,
            "autobiographical_owner",
        )
        if (
            self.observed_subject is SubjectIdentity.TONY
            and self.autobiographical_owner is AutobiographicalOwner.MIRA
        ):
            raise ValueError("observed Tony history cannot become Mira autobiography")

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantic_subject": self.semantic_subject.value,
            "observed_subject": self.observed_subject.value,
            "autobiographical_owner": self.autobiographical_owner.value,
        }


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
    schema_version: str = "v1"
    significance: str = ""
    prior_judgment: str = ""
    corrected_judgment: str = ""
    later_reinterpretation: str = ""
    policy_transfer: PolicyTransferSemantics | PolicyTransferNotApplicable | None = None
    causal_status: CausalStatus | None = None
    subject_boundary: SubjectBoundary | None = None
    judgment_binding_role_refs: tuple[EvidenceBindingRef, ...] = ()

    def __post_init__(self) -> None:
        _require_id(self.relationship_id, "relationship_id")
        _require_text(self.event, "event")
        _require_text(self.interpretation, "interpretation")
        _require_text(self.occurred_at, "occurred_at", max_length=128)
        _require_schema_version(self.schema_version)
        _require_optional_text(self.significance, "significance")
        _require_optional_text(self.prior_judgment, "prior_judgment")
        _require_optional_text(self.corrected_judgment, "corrected_judgment")
        _require_optional_text(self.later_reinterpretation, "later_reinterpretation")
        _require_binding_refs(self.judgment_binding_role_refs)

        if self.schema_version == "v1":
            if self._has_v2_fields():
                raise ValueError(
                    "RelationshipExperience v1 cannot carry v2 trajectory fields"
                )
            return

        _require_text(self.significance, "significance")
        if bool(self.prior_judgment) != bool(self.corrected_judgment):
            raise ValueError(
                "prior_judgment and corrected_judgment must be supplied together"
            )
        if self.prior_judgment:
            _require_present_binding_refs(self.judgment_binding_role_refs)
        elif self.judgment_binding_role_refs:
            raise ValueError(
                "judgment_binding_role_refs require a prior/corrected judgment pair"
            )
        if type(self.policy_transfer) not in (
            PolicyTransferSemantics,
            PolicyTransferNotApplicable,
        ):
            raise ValueError(
                "policy_transfer must explicitly be present or NOT_APPLICABLE for v2"
            )
        _require_enum(self.causal_status, CausalStatus, "causal_status")
        if self.subject_boundary is not None and (
            type(self.subject_boundary) is not SubjectBoundary
        ):
            raise ValueError("subject_boundary must be an exact SubjectBoundary")

    def _has_v2_fields(self) -> bool:
        return any(
            (
                self.significance,
                self.prior_judgment,
                self.corrected_judgment,
                self.later_reinterpretation,
                self.policy_transfer,
                self.causal_status,
                self.subject_boundary,
                self.judgment_binding_role_refs,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        base = {
            "relationship_id": self.relationship_id,
            "event": self.event,
            "interpretation": self.interpretation,
            "occurred_at": self.occurred_at,
        }
        if self.schema_version == "v1":
            return base
        result = base | {
            "significance": self.significance,
            "prior_judgment": self.prior_judgment,
            "corrected_judgment": self.corrected_judgment,
            "later_reinterpretation": self.later_reinterpretation,
            "policy_transfer": self.policy_transfer.to_dict(),
            "causal_status": self.causal_status.value,
            "judgment_binding_role_refs": [
                item.to_dict() for item in self.judgment_binding_role_refs
            ],
        }
        if self.subject_boundary is not None:
            result["subject_boundary"] = self.subject_boundary.to_dict()
        return result

    @property
    def payload_schema_version(self) -> str:
        return self.schema_version

    def binding_role_refs(self) -> tuple[EvidenceBindingRef, ...]:
        policy_refs = (
            self.policy_transfer.binding_role_refs
            if type(self.policy_transfer) is PolicyTransferSemantics
            else ()
        )
        return self.judgment_binding_role_refs + policy_refs


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
    schema_version: str = "v1"
    trigger_event: str = ""
    interpretation: str = ""
    significance: str = ""
    commitment_stage: CommitmentStage | None = None
    revision: CommitmentRevision | None = None
    binding_role_refs: tuple[EvidenceBindingRef, ...] = ()
    applicability: CommitmentApplicability | None = None

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
        _require_schema_version(self.schema_version)
        _require_optional_text(self.trigger_event, "trigger_event")
        _require_optional_text(self.interpretation, "interpretation")
        _require_optional_text(self.significance, "significance")
        if self.commitment_stage is not None and (
            type(self.commitment_stage) is not CommitmentStage
        ):
            raise ValueError("commitment_stage must be an explicit CommitmentStage")
        if self.revision is not None and type(self.revision) is not CommitmentRevision:
            raise ValueError("revision must be an exact CommitmentRevision")
        _require_binding_refs(self.binding_role_refs)
        if self.applicability is not None and (
            type(self.applicability) is not CommitmentApplicability
        ):
            raise ValueError("applicability must be an exact CommitmentApplicability")

        if self.schema_version == "v1":
            if any(
                (
                    self.trigger_event,
                    self.interpretation,
                    self.significance,
                    self.commitment_stage,
                    self.revision,
                    self.binding_role_refs,
                    self.applicability,
                )
            ):
                raise ValueError(
                    "ProjectCommitmentExperience v1 cannot carry v2 stage fields"
                )
            return

        _require_text(self.trigger_event, "trigger_event")
        _require_text(self.interpretation, "interpretation")
        _require_text(self.significance, "significance")
        _require_enum(self.commitment_stage, CommitmentStage, "commitment_stage")
        _require_present_binding_refs(self.binding_role_refs)
        if type(self.applicability) is not CommitmentApplicability:
            raise ValueError("applicability must be an exact CommitmentApplicability")
        if self.commitment_stage is CommitmentStage.FORMATION_DRAFT:
            if self.revision is not None:
                raise ValueError("FORMATION_DRAFT cannot carry a revision")
        elif type(self.revision) is not CommitmentRevision:
            raise ValueError("FROZEN_FINAL requires an exact CommitmentRevision")

    def to_dict(self) -> dict[str, Any]:
        base = {
            "subject": self.subject,
            "counterparty": self.counterparty,
            "scope": self.scope,
            "commitment": self.commitment,
            "transfer_semantics": self.transfer_semantics.value,
            "occurred_at": self.occurred_at,
        }
        if self.schema_version == "v1":
            return base
        return base | {
            "trigger_event": self.trigger_event,
            "interpretation": self.interpretation,
            "significance": self.significance,
            "commitment_stage": self.commitment_stage.value,
            "revision": self.revision.to_dict() if self.revision else None,
            "binding_role_refs": [item.to_dict() for item in self.binding_role_refs],
            "applicability": self.applicability.to_dict(),
        }

    @property
    def payload_schema_version(self) -> str:
        return self.schema_version


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


@dataclass(frozen=True, slots=True)
class CommitmentRevision:
    predecessor_ref: MemoryExperienceRef
    supersession_scope: str
    supersession_reason: str
    rewrite_history: bool = False

    def __post_init__(self) -> None:
        if type(self.predecessor_ref) is not MemoryExperienceRef:
            raise ValueError("predecessor_ref must be an exact MemoryExperienceRef")
        _require_text(self.supersession_scope, "supersession_scope", max_length=2_048)
        _require_text(self.supersession_reason, "supersession_reason", max_length=2_048)
        if self.rewrite_history is not False:
            raise ValueError("rewrite_history must remain false")

    def to_dict(self) -> dict[str, Any]:
        return {
            "predecessor_ref": self.predecessor_ref.to_dict(),
            "supersession_scope": self.supersession_scope,
            "supersession_reason": self.supersession_reason,
            "rewrite_history": False,
        }


@dataclass(frozen=True, slots=True)
class CommitmentApplicability:
    scope: str
    inheritance: CommitmentTransferSemantics
    current_authorization: bool = False
    standing_consent: bool = False
    runtime_authority: bool = False

    def __post_init__(self) -> None:
        _require_id(self.scope, "applicability scope")
        if (
            self.inheritance
            is not CommitmentTransferSemantics.EXPLICIT_REAUTHORIZATION_REQUIRED
        ):
            raise ValueError(
                "commitment applicability requires explicit reauthorization"
            )
        if any(
            (
                self.current_authorization is not False,
                self.standing_consent is not False,
                self.runtime_authority is not False,
            )
        ):
            raise ValueError("commitment history cannot encode current authority")

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "inheritance": self.inheritance.value,
            "current_authorization": False,
            "standing_consent": False,
            "runtime_authority": False,
        }


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
        if _payload_schema_version(self.content) == "v2":
            _validate_binding_role_refs(self)

    @property
    def ref(self) -> MemoryExperienceRef:
        return MemoryExperienceRef(self.experience_id, self.version_id)

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": (
                "julia_core.memory_experience.record."
                f"{_payload_schema_version(self.content)}"
            ),
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


def _require_optional_text(value: str, field_name: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an exact built-in string")
    if value:
        _require_text(value, field_name)


def _require_enum(value: Any, enum_type: type[Enum], field_name: str) -> None:
    if type(value) is not enum_type:
        raise ValueError(f"{field_name} must be an explicit {enum_type.__name__}")


def _require_schema_version(value: str) -> None:
    if type(value) is not str or value not in {"v1", "v2"}:
        raise ValueError("schema_version must be exactly v1 or v2")


def _require_binding_refs(value: tuple[EvidenceBindingRef, ...]) -> None:
    if type(value) is not tuple:
        raise ValueError("binding role references must be an exact tuple")
    if any(type(item) is not EvidenceBindingRef for item in value):
        raise ValueError("binding role references must be EvidenceBindingRef objects")


def _require_present_binding_refs(value: tuple[EvidenceBindingRef, ...]) -> None:
    _require_binding_refs(value)
    if not value:
        raise ValueError("binding role references are required")
    if len(value) != len(set(value)):
        raise ValueError("binding role references must be unique")


def _payload_schema_version(content: MemoryExperienceContent) -> str:
    if type(content) in (
        RelationshipExperienceContent,
        ProjectCommitmentExperienceContent,
    ):
        return content.schema_version
    return "v1"


def _semantic_binding_refs(
    content: MemoryExperienceContent,
) -> tuple[EvidenceBindingRef, ...]:
    if type(content) is RelationshipExperienceContent:
        return content.binding_role_refs()
    if type(content) is ProjectCommitmentExperienceContent:
        return content.binding_role_refs
    return ()


def _validate_binding_role_refs(record: MemoryExperienceRecord) -> None:
    semantic_refs = _semantic_binding_refs(record.content)
    if not semantic_refs:
        return
    available_bindings = {
        (metadata.get("binding_id"), metadata.get("causal_role"))
        for provenance in record.provenance_refs
        for metadata in (dict(provenance.admission_metadata),)
    }
    for semantic_ref in semantic_refs:
        if (semantic_ref.binding_id, semantic_ref.evidence_role) not in (
            available_bindings
        ):
            raise ValueError(
                "semantic binding role references must resolve in the same record provenance"
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
    "AutobiographicalOwner",
    "CausalStatus",
    "CommitmentApplicability",
    "CommitmentRevision",
    "CommitmentStage",
    "CommitmentTransferSemantics",
    "EvidenceBindingRef",
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
    "PolicyTransferApplicability",
    "PolicyTransferNotApplicable",
    "PolicyTransferSemantics",
    "PreferenceExperienceContent",
    "ProjectCommitmentExperienceContent",
    "RelationshipExperienceContent",
    "SubjectBoundary",
    "SubjectIdentity",
]
