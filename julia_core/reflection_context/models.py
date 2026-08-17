"""DIA-4 R1 — Core Reflection Context canonical contract.

A ReflectionContext is bounded ephemeral generation input for DIA-5. It is not
Diary, Memory, Context OS, persistence, model generation, interpretation, or a
new conversation truth authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Protocol, runtime_checkable

from julia_core.reflection_trigger import ReflectionOpportunity, TriggerSourceRef

CANONICAL_VERSION = "dia4-reflection-context-v1"
CONTEXT_DOMAIN_SEPARATOR = "julia_core.reflection_context.context.v1"
POLICY_DOMAIN_SEPARATOR = "julia_core.reflection_context.policy.v1"
FACT_DIGEST_FUNCTION = "sha256:canonical-payload:v1"
CONTEXT_DIGEST_ALGORITHM_REVISION = "dia4-context-digest-v1"
SELECTION_ALGORITHM_REVISION = "dia4-select-opportunity-source-refs-v1"
DEFAULT_FACT_PROJECTION_REVISION = "canonical-fact-projection-v1"


def _require_non_empty_str(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty str")


def _require_tuple(name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")


def _require_positive_int(name: str, value: object) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive int")


def _require_bytes(name: str, value: object) -> None:
    if type(value) is not bytes:
        raise ValueError(f"{name} must be bytes")


def _frame(value: str) -> bytes:
    _require_non_empty_str("canonical field", value)
    encoded = value.encode("utf-8")
    return str(len(encoded)).encode("ascii") + b":" + encoded + b"\n"


def _bytes_frame(value: bytes) -> bytes:
    _require_bytes("canonical bytes", value)
    return str(len(value)).encode("ascii") + b":" + value + b"\n"


def _field(name: str, value: str) -> bytes:
    return _frame(name) + _frame(value)


def _bytes_field(name: str, value: bytes) -> bytes:
    return _frame(name) + _bytes_frame(value)


def _digest_hex(canonical_bytes: bytes) -> str:
    return sha256(canonical_bytes).hexdigest()


class CanonicalFactType(Enum):
    CONVERSATION_EVENT = "conversation_event"
    TURN_BOUNDARY = "turn_boundary"
    EXPLICIT_REQUEST = "explicit_request"


def _require_fact_type(name: str, value: object) -> CanonicalFactType:
    if type(value) is CanonicalFactType:
        return value
    if type(value) is str:
        try:
            return CanonicalFactType(value)
        except ValueError as e:
            raise ValueError(f"{name} must be a frozen CanonicalFactType") from e
    raise ValueError(f"{name} must be CanonicalFactType")


def _ref_key(ref: TriggerSourceRef) -> str:
    return ref.canonical_key()


@dataclass(frozen=True)
class ContextBounds:
    max_facts: int
    max_payload_bytes: int
    max_fact_payload_bytes: int

    def __post_init__(self) -> None:
        _require_positive_int("ContextBounds.max_facts", self.max_facts)
        _require_positive_int("ContextBounds.max_payload_bytes", self.max_payload_bytes)
        _require_positive_int("ContextBounds.max_fact_payload_bytes", self.max_fact_payload_bytes)

    def canonical_bytes(self) -> bytes:
        return (
            _field("bounds.max_facts", str(self.max_facts))
            + _field("bounds.max_payload_bytes", str(self.max_payload_bytes))
            + _field("bounds.max_fact_payload_bytes", str(self.max_fact_payload_bytes))
        )


@dataclass(frozen=True)
class ContextAssemblyPolicy:
    revision: str
    bounds: ContextBounds
    selection_algorithm_revision: str = SELECTION_ALGORITHM_REVISION
    fact_projection_revision: str = DEFAULT_FACT_PROJECTION_REVISION
    context_digest_algorithm_revision: str = CONTEXT_DIGEST_ALGORITHM_REVISION
    schema_version: str = CANONICAL_VERSION

    def __post_init__(self) -> None:
        _require_non_empty_str("ContextAssemblyPolicy.revision", self.revision)
        if type(self.bounds) is not ContextBounds:
            raise ValueError("ContextAssemblyPolicy.bounds must be ContextBounds")
        _require_non_empty_str("ContextAssemblyPolicy.selection_algorithm_revision", self.selection_algorithm_revision)
        _require_non_empty_str("ContextAssemblyPolicy.fact_projection_revision", self.fact_projection_revision)
        _require_non_empty_str("ContextAssemblyPolicy.context_digest_algorithm_revision", self.context_digest_algorithm_revision)
        _require_non_empty_str("ContextAssemblyPolicy.schema_version", self.schema_version)
        if self.schema_version != CANONICAL_VERSION:
            raise ValueError("ContextAssemblyPolicy.schema_version must equal CANONICAL_VERSION")
        if self.selection_algorithm_revision != SELECTION_ALGORITHM_REVISION:
            raise ValueError("ContextAssemblyPolicy.selection_algorithm_revision is not implemented")
        if self.context_digest_algorithm_revision != CONTEXT_DIGEST_ALGORITHM_REVISION:
            raise ValueError("ContextAssemblyPolicy.context_digest_algorithm_revision is not implemented")

    def canonical_bytes(self) -> bytes:
        return (
            _field("policy.domain", POLICY_DOMAIN_SEPARATOR)
            + _field("policy.schema_version", self.schema_version)
            + _field("policy.revision", self.revision)
            + _field("policy.selection_algorithm_revision", self.selection_algorithm_revision)
            + _field("policy.fact_projection_revision", self.fact_projection_revision)
            + _field("policy.context_digest_algorithm_revision", self.context_digest_algorithm_revision)
            + _field("policy.bounds", self.bounds.canonical_bytes().decode("utf-8"))
        )

    def policy_fingerprint(self) -> str:
        return _digest_hex(self.canonical_bytes())


@dataclass(frozen=True)
class CanonicalFact:
    source_ref: TriggerSourceRef
    fact_type: CanonicalFactType
    source_schema_version: str
    projection_revision: str
    canonical_payload: bytes
    canonical_digest: str | None = None
    digest_function: str = FACT_DIGEST_FUNCTION
    reader_authority: str = "canonical-reader"

    def __post_init__(self) -> None:
        if type(self.source_ref) is not TriggerSourceRef:
            raise ValueError("CanonicalFact.source_ref must be TriggerSourceRef")
        object.__setattr__(self, "fact_type", _require_fact_type("CanonicalFact.fact_type", self.fact_type))
        for name in ("source_schema_version", "projection_revision", "digest_function", "reader_authority"):
            _require_non_empty_str(f"CanonicalFact.{name}", getattr(self, name))
        if self.digest_function != FACT_DIGEST_FUNCTION:
            raise ValueError("CanonicalFact.digest_function is frozen")
        _require_bytes("CanonicalFact.canonical_payload", self.canonical_payload)
        digest = sha256(self.canonical_payload).hexdigest()
        if self.canonical_digest is None:
            object.__setattr__(self, "canonical_digest", digest)
        elif self.canonical_digest != digest:
            raise ValueError("CanonicalFact.canonical_digest must equal SHA-256 payload digest")

    def semantic_provenance(self) -> "FactSemanticProvenance":
        return FactSemanticProvenance(
            self.source_ref,
            self.source_schema_version,
            self.projection_revision,
            self.digest_function,
            self.canonical_digest or "",
        )


@dataclass(frozen=True)
class FactSemanticProvenance:
    source_ref: TriggerSourceRef
    source_schema_version: str
    projection_revision: str
    digest_function: str
    canonical_digest: str

    def __post_init__(self) -> None:
        if type(self.source_ref) is not TriggerSourceRef:
            raise ValueError("FactSemanticProvenance.source_ref must be TriggerSourceRef")
        for name in ("source_schema_version", "projection_revision", "digest_function", "canonical_digest"):
            _require_non_empty_str(f"FactSemanticProvenance.{name}", getattr(self, name))

    def canonical_bytes(self) -> bytes:
        return (
            _field("semantic_provenance.source_ref", self.source_ref.canonical_bytes().decode("utf-8"))
            + _field("semantic_provenance.source_schema_version", self.source_schema_version)
            + _field("semantic_provenance.projection_revision", self.projection_revision)
            + _field("semantic_provenance.digest_function", self.digest_function)
            + _field("semantic_provenance.canonical_digest", self.canonical_digest)
        )


@dataclass(frozen=True)
class FactAuditMetadata:
    source_ref: TriggerSourceRef
    reader_authority: str
    adapter_label: str | None = None
    read_diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.source_ref) is not TriggerSourceRef:
            raise ValueError("FactAuditMetadata.source_ref must be TriggerSourceRef")
        _require_non_empty_str("FactAuditMetadata.reader_authority", self.reader_authority)
        if self.adapter_label is not None:
            _require_non_empty_str("FactAuditMetadata.adapter_label", self.adapter_label)
        _require_tuple("FactAuditMetadata.read_diagnostics", self.read_diagnostics)
        if not all(type(item) is str for item in self.read_diagnostics):
            raise ValueError("FactAuditMetadata.read_diagnostics must contain str only")


@dataclass(frozen=True)
class ContextFact:
    source_ref: TriggerSourceRef
    canonical_digest: str
    digest_function: str
    fact_type: CanonicalFactType
    source_schema_version: str
    projection_revision: str
    payload: bytes
    semantic_provenance: FactSemanticProvenance

    def __post_init__(self) -> None:
        if type(self.source_ref) is not TriggerSourceRef:
            raise ValueError("ContextFact.source_ref must be TriggerSourceRef")
        if type(self.semantic_provenance) is not FactSemanticProvenance:
            raise ValueError("ContextFact.semantic_provenance must be FactSemanticProvenance")
        object.__setattr__(self, "fact_type", _require_fact_type("ContextFact.fact_type", self.fact_type))
        for name in ("canonical_digest", "digest_function", "source_schema_version", "projection_revision"):
            _require_non_empty_str(f"ContextFact.{name}", getattr(self, name))
        if self.digest_function != FACT_DIGEST_FUNCTION:
            raise ValueError("ContextFact.digest_function is frozen")
        _require_bytes("ContextFact.payload", self.payload)
        if sha256(self.payload).hexdigest() != self.canonical_digest:
            raise ValueError("ContextFact.canonical_digest must equal payload digest")
        provenance = self.semantic_provenance
        if (
            provenance.source_ref != self.source_ref
            or provenance.source_schema_version != self.source_schema_version
            or provenance.projection_revision != self.projection_revision
            or provenance.digest_function != self.digest_function
            or provenance.canonical_digest != self.canonical_digest
        ):
            raise ValueError("ContextFact semantic provenance must match top-level fields")

    @classmethod
    def from_canonical_fact(cls, fact: CanonicalFact) -> "ContextFact":
        if type(fact) is not CanonicalFact:
            raise ValueError("fact must be CanonicalFact")
        return cls(
            source_ref=fact.source_ref,
            canonical_digest=fact.canonical_digest or "",
            digest_function=fact.digest_function,
            fact_type=fact.fact_type,
            source_schema_version=fact.source_schema_version,
            projection_revision=fact.projection_revision,
            payload=fact.canonical_payload,
            semantic_provenance=fact.semantic_provenance(),
        )

    def canonical_bytes(self) -> bytes:
        return (
            _field("context_fact.source_ref", self.source_ref.canonical_bytes().decode("utf-8"))
            + _field("context_fact.fact_type", self.fact_type.value)
            + _field("context_fact.source_schema_version", self.source_schema_version)
            + _field("context_fact.projection_revision", self.projection_revision)
            + _field("context_fact.digest_function", self.digest_function)
            + _field("context_fact.canonical_digest", self.canonical_digest)
            + _bytes_field("context_fact.payload", self.payload)
            + _field("context_fact.semantic_provenance", self.semantic_provenance.canonical_bytes().decode("utf-8"))
        )


@dataclass(frozen=True)
class ReflectionContext:
    opportunity_id: str
    opportunity_key_digest: str
    assembly_policy_revision: str
    assembly_policy_fingerprint: str
    facts: tuple[ContextFact, ...]
    bounds: ContextBounds
    context_digest: str | None = None
    schema_version: str = CANONICAL_VERSION

    def __post_init__(self) -> None:
        for name in ("opportunity_id", "opportunity_key_digest", "assembly_policy_revision", "assembly_policy_fingerprint", "schema_version"):
            _require_non_empty_str(f"ReflectionContext.{name}", getattr(self, name))
        if self.schema_version != CANONICAL_VERSION:
            raise ValueError("ReflectionContext.schema_version must equal CANONICAL_VERSION")
        _require_tuple("ReflectionContext.facts", self.facts)
        if not self.facts:
            raise ValueError("ReflectionContext.facts must be non-empty")
        if not all(type(fact) is ContextFact for fact in self.facts):
            raise ValueError("ReflectionContext.facts must contain ContextFact only")
        if type(self.bounds) is not ContextBounds:
            raise ValueError("ReflectionContext.bounds must be ContextBounds")
        if len(self.facts) > self.bounds.max_facts:
            raise ValueError("ReflectionContext.facts exceeds max_facts")
        total = sum(len(fact.payload) for fact in self.facts)
        if total > self.bounds.max_payload_bytes:
            raise ValueError("ReflectionContext payload exceeds max_payload_bytes")
        if any(len(fact.payload) > self.bounds.max_fact_payload_bytes for fact in self.facts):
            raise ValueError("ReflectionContext fact payload exceeds max_fact_payload_bytes")
        keys = [_ref_key(fact.source_ref) for fact in self.facts]
        if len(set(keys)) != len(keys):
            raise ValueError("ReflectionContext.facts must not contain duplicate source refs")
        digest = _digest_hex(self.semantic_canonical_bytes(include_digest=False))
        if self.context_digest is None:
            object.__setattr__(self, "context_digest", digest)
        elif self.context_digest != digest:
            raise ValueError("ReflectionContext.context_digest mismatch")

    def semantic_canonical_bytes(self, *, include_digest: bool = True) -> bytes:
        out = (
            _field("context.domain", CONTEXT_DOMAIN_SEPARATOR)
            + _field("context.schema_version", self.schema_version)
            + _field("context.opportunity_id", self.opportunity_id)
            + _field("context.opportunity_key_digest", self.opportunity_key_digest)
            + _field("context.assembly_policy_revision", self.assembly_policy_revision)
            + _field("context.assembly_policy_fingerprint", self.assembly_policy_fingerprint)
            + _field("context.bounds", self.bounds.canonical_bytes().decode("utf-8"))
        )
        for fact in self.facts:
            out += _field("context.fact", fact.canonical_bytes().decode("utf-8"))
        if include_digest:
            out += _field("context.digest", self.context_digest or "")
        return out


@dataclass(frozen=True)
class ReflectionContextAudit:
    opportunity_id: str
    context_digest: str
    fact_audit_metadata: tuple[FactAuditMetadata, ...]

    def __post_init__(self) -> None:
        _require_non_empty_str("ReflectionContextAudit.opportunity_id", self.opportunity_id)
        _require_non_empty_str("ReflectionContextAudit.context_digest", self.context_digest)
        _require_tuple("ReflectionContextAudit.fact_audit_metadata", self.fact_audit_metadata)
        if not all(type(item) is FactAuditMetadata for item in self.fact_audit_metadata):
            raise ValueError("ReflectionContextAudit.fact_audit_metadata must contain FactAuditMetadata only")


@dataclass(frozen=True)
class ReflectionOpportunityHandoff:
    opportunity: ReflectionOpportunity
    pending_record_digest: str
    handoff_provenance: str

    def __post_init__(self) -> None:
        if type(self.opportunity) is not ReflectionOpportunity:
            raise ValueError("ReflectionOpportunityHandoff.opportunity must be ReflectionOpportunity")
        _require_non_empty_str("ReflectionOpportunityHandoff.pending_record_digest", self.pending_record_digest)
        _require_non_empty_str("ReflectionOpportunityHandoff.handoff_provenance", self.handoff_provenance)


@runtime_checkable
class ReflectionOpportunityInputPort(Protocol):
    def next_handoff_opportunity(self) -> ReflectionOpportunityHandoff | None:
        ...


@runtime_checkable
class CanonicalFactReader(Protocol):
    def get_fact(self, ref: TriggerSourceRef) -> CanonicalFact | None:
        ...


@runtime_checkable
class ReflectionContextAssembler(Protocol):
    def assemble(self, handoff: ReflectionOpportunityHandoff, reader: CanonicalFactReader, policy: ContextAssemblyPolicy) -> ReflectionContext:
        ...


class DeterministicReflectionContextAssembler:
    """Core deterministic assembler: exact refs, exact facts, no interpretation."""

    def assemble(self, handoff: ReflectionOpportunityHandoff, reader: CanonicalFactReader, policy: ContextAssemblyPolicy) -> ReflectionContext:
        if type(handoff) is not ReflectionOpportunityHandoff:
            raise ValueError("production assembly requires ReflectionOpportunityHandoff provenance")
        if type(policy) is not ContextAssemblyPolicy:
            raise ValueError("policy must be ContextAssemblyPolicy")
        opportunity = handoff.opportunity
        refs = opportunity.source_refs
        if not refs:
            raise ValueError("ReflectionOpportunity.source_refs must be non-empty")
        keys = [_ref_key(ref) for ref in refs]
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate source refs fail closed")
        if len(refs) > policy.bounds.max_facts:
            raise ValueError("selected refs exceed max_facts")

        facts: list[ContextFact] = []
        for ref in refs:
            fact = reader.get_fact(ref)
            if type(fact) is not CanonicalFact:
                raise ValueError("missing canonical fact")
            if fact.source_ref != ref:
                raise ValueError("canonical fact source_ref mismatch")
            if fact.projection_revision != policy.fact_projection_revision:
                raise ValueError("canonical fact projection revision mismatch")
            if len(fact.canonical_payload) > policy.bounds.max_fact_payload_bytes:
                raise ValueError("canonical fact payload exceeds max_fact_payload_bytes")
            facts.append(ContextFact.from_canonical_fact(fact))

        total = sum(len(fact.payload) for fact in facts)
        if total > policy.bounds.max_payload_bytes:
            raise ValueError("context payload exceeds max_payload_bytes")
        return ReflectionContext(
            opportunity_id=opportunity.opportunity_id or opportunity.opportunity_key.opportunity_id(),
            opportunity_key_digest=sha256(opportunity.opportunity_key.canonical_bytes()).hexdigest(),
            assembly_policy_revision=policy.revision,
            assembly_policy_fingerprint=policy.policy_fingerprint(),
            facts=tuple(facts),
            bounds=policy.bounds,
        )
