"""DIA-6 R1 — Core Context Evolution canonical contract.

Context evolution is lineage expansion over immutable DIA-4 ReflectionContext
identities. It is not in-place context mutation, persistence, generation,
Diary, Memory, or transport state.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Protocol, runtime_checkable

from julia_core.reflection_context import CANONICAL_VERSION as CONTEXT_VERSION
from julia_core.reflection_context import ReflectionContext
from julia_core.reflection_trigger import TriggerSourceRef

CANONICAL_VERSION = "dia6-context-evolution-v1"
LINEAGE_DOMAIN_SEPARATOR = "julia_core.context_evolution.lineage_edge.v1"
OPERATION_DOMAIN_SEPARATOR = "julia_core.context_evolution.operation.v1"
POLICY_DOMAIN_SEPARATOR = "julia_core.context_evolution.policy.v1"
LINEAGE_DIGEST_ALGORITHM_REVISION = "dia6-lineage-digest-v1"
PARENT_VERIFICATION_REVISION = "dia6-parent-verification-v1"
CHILD_VALIDATION_REVISION = "dia6-child-validation-v1"


def _require_non_empty_str(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty str")


def _require_tuple(name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")


def _require_positive_int(name: str, value: object) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive int")


def _require_sha256_hex(name: str, value: object) -> None:
    _require_non_empty_str(name, value)
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{name} must be a 64-character lowercase SHA-256 hex digest")


def _frame(value: str) -> bytes:
    _require_non_empty_str("canonical field", value)
    encoded = value.encode("utf-8")
    return str(len(encoded)).encode("ascii") + b":" + encoded + b"\n"


def _field(name: str, value: str) -> bytes:
    return _frame(name) + _frame(value)


def _digest_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def _reject_duplicate_refs(name: str, refs: tuple[TriggerSourceRef, ...]) -> None:
    keys = [ref.canonical_key() for ref in refs]
    if len(set(keys)) != len(keys):
        raise ValueError(f"{name} must not contain duplicate canonical refs")


class ContextEvolutionKind(Enum):
    FACT_APPEND = "fact_append"
    FACT_CORRECTION = "fact_correction"
    CONTEXT_SPLIT = "context_split"
    CONTEXT_MERGE = "context_merge"
    CONTEXT_DEPRECATION = "context_deprecation"


def _require_evolution_kind(name: str, value: object) -> ContextEvolutionKind:
    if type(value) is ContextEvolutionKind:
        return value
    if type(value) is str:
        try:
            return ContextEvolutionKind(value)
        except ValueError as e:
            raise ValueError(f"{name} must be a frozen ContextEvolutionKind") from e
    raise ValueError(f"{name} must be ContextEvolutionKind")


@dataclass(frozen=True)
class ContextLineageNode:
    context_digest: str
    context_version: str
    assembly_policy_revision: str
    assembly_policy_fingerprint: str
    context_semantic_bytes_sha256: str

    def __post_init__(self) -> None:
        _require_sha256_hex("ContextLineageNode.context_digest", self.context_digest)
        _require_non_empty_str("ContextLineageNode.context_version", self.context_version)
        if self.context_version != CONTEXT_VERSION:
            raise ValueError("ContextLineageNode.context_version is not supported")
        _require_non_empty_str("ContextLineageNode.assembly_policy_revision", self.assembly_policy_revision)
        _require_sha256_hex("ContextLineageNode.assembly_policy_fingerprint", self.assembly_policy_fingerprint)
        _require_sha256_hex("ContextLineageNode.context_semantic_bytes_sha256", self.context_semantic_bytes_sha256)

    @classmethod
    def from_context(cls, context: ReflectionContext) -> "ContextLineageNode":
        if type(context) is not ReflectionContext:
            raise ValueError("context must be exact ReflectionContext")
        return cls(
            context_digest=context.context_digest or "",
            context_version=context.schema_version,
            assembly_policy_revision=context.assembly_policy_revision,
            assembly_policy_fingerprint=context.assembly_policy_fingerprint,
            context_semantic_bytes_sha256=_digest_hex(context.semantic_canonical_bytes()),
        )

    def canonical_bytes(self) -> bytes:
        return (
            _field("node.context_digest", self.context_digest)
            + _field("node.context_version", self.context_version)
            + _field("node.assembly_policy_revision", self.assembly_policy_revision)
            + _field("node.assembly_policy_fingerprint", self.assembly_policy_fingerprint)
            + _field("node.context_semantic_bytes_sha256", self.context_semantic_bytes_sha256)
        )


@dataclass(frozen=True)
class EvolutionAuthority:
    authority_id: str
    authority_kind: str
    protocol_version: str

    def __post_init__(self) -> None:
        _require_non_empty_str("EvolutionAuthority.authority_id", self.authority_id)
        _require_non_empty_str("EvolutionAuthority.authority_kind", self.authority_kind)
        _require_non_empty_str("EvolutionAuthority.protocol_version", self.protocol_version)

    def canonical_bytes(self) -> bytes:
        return (
            _field("authority.id", self.authority_id)
            + _field("authority.kind", self.authority_kind)
            + _field("authority.protocol_version", self.protocol_version)
        )


@dataclass(frozen=True)
class ContextEvolutionPolicy:
    revision: str
    allowed_kinds: tuple[ContextEvolutionKind, ...]
    max_reason_refs: int
    parent_verification_revision: str = PARENT_VERIFICATION_REVISION
    child_validation_revision: str = CHILD_VALIDATION_REVISION
    lineage_digest_algorithm_revision: str = LINEAGE_DIGEST_ALGORITHM_REVISION
    schema_version: str = CANONICAL_VERSION

    def __post_init__(self) -> None:
        _require_non_empty_str("ContextEvolutionPolicy.revision", self.revision)
        _require_tuple("ContextEvolutionPolicy.allowed_kinds", self.allowed_kinds)
        if not self.allowed_kinds:
            raise ValueError("ContextEvolutionPolicy.allowed_kinds must be non-empty")
        normalized = tuple(_require_evolution_kind("ContextEvolutionPolicy.allowed_kinds", item) for item in self.allowed_kinds)
        object.__setattr__(self, "allowed_kinds", normalized)
        if len(set(kind.value for kind in normalized)) != len(normalized):
            raise ValueError("ContextEvolutionPolicy.allowed_kinds must not contain duplicates")
        _require_positive_int("ContextEvolutionPolicy.max_reason_refs", self.max_reason_refs)
        for name in ("parent_verification_revision", "child_validation_revision", "lineage_digest_algorithm_revision", "schema_version"):
            _require_non_empty_str(f"ContextEvolutionPolicy.{name}", getattr(self, name))
        if self.schema_version != CANONICAL_VERSION:
            raise ValueError("ContextEvolutionPolicy.schema_version is frozen")
        if self.parent_verification_revision != PARENT_VERIFICATION_REVISION:
            raise ValueError("ContextEvolutionPolicy.parent_verification_revision is not implemented")
        if self.child_validation_revision != CHILD_VALIDATION_REVISION:
            raise ValueError("ContextEvolutionPolicy.child_validation_revision is not implemented")
        if self.lineage_digest_algorithm_revision != LINEAGE_DIGEST_ALGORITHM_REVISION:
            raise ValueError("ContextEvolutionPolicy.lineage_digest_algorithm_revision is not implemented")

    def canonical_bytes(self) -> bytes:
        out = (
            _field("policy.domain", POLICY_DOMAIN_SEPARATOR)
            + _field("policy.schema_version", self.schema_version)
            + _field("policy.revision", self.revision)
            + _field("policy.parent_verification_revision", self.parent_verification_revision)
            + _field("policy.child_validation_revision", self.child_validation_revision)
            + _field("policy.lineage_digest_algorithm_revision", self.lineage_digest_algorithm_revision)
            + _field("policy.max_reason_refs", str(self.max_reason_refs))
            + _field("policy.allowed_kind_count", str(len(self.allowed_kinds)))
        )
        for kind in self.allowed_kinds:
            out += _field("policy.allowed_kind", kind.value)
        return out

    def policy_fingerprint(self) -> str:
        return _digest_hex(self.canonical_bytes())


@dataclass(frozen=True)
class ContextEvolutionOperation:
    operation_id: str
    operation_kind: ContextEvolutionKind
    parent_context: ContextLineageNode
    child_context: ContextLineageNode
    evolution_policy_revision: str
    evolution_policy_fingerprint: str
    authority: EvolutionAuthority
    reason_refs: tuple[TriggerSourceRef, ...]
    schema_version: str = CANONICAL_VERSION

    def __post_init__(self) -> None:
        _require_non_empty_str("ContextEvolutionOperation.operation_id", self.operation_id)
        object.__setattr__(self, "operation_kind", _require_evolution_kind("ContextEvolutionOperation.operation_kind", self.operation_kind))
        if type(self.parent_context) is not ContextLineageNode:
            raise ValueError("ContextEvolutionOperation.parent_context must be ContextLineageNode")
        if type(self.child_context) is not ContextLineageNode:
            raise ValueError("ContextEvolutionOperation.child_context must be ContextLineageNode")
        if self.parent_context.context_digest == self.child_context.context_digest:
            if self.parent_context.context_semantic_bytes_sha256 != self.child_context.context_semantic_bytes_sha256:
                raise ValueError("same context digest with different semantic bytes hash is corruption")
            raise ValueError("ContextEvolutionOperation requires distinct parent and child context identities")
        _require_non_empty_str("ContextEvolutionOperation.evolution_policy_revision", self.evolution_policy_revision)
        _require_sha256_hex("ContextEvolutionOperation.evolution_policy_fingerprint", self.evolution_policy_fingerprint)
        if type(self.authority) is not EvolutionAuthority:
            raise ValueError("ContextEvolutionOperation.authority must be EvolutionAuthority")
        _require_tuple("ContextEvolutionOperation.reason_refs", self.reason_refs)
        if not self.reason_refs:
            raise ValueError("ContextEvolutionOperation.reason_refs must be non-empty")
        if not all(type(ref) is TriggerSourceRef for ref in self.reason_refs):
            raise ValueError("ContextEvolutionOperation.reason_refs must contain TriggerSourceRef only")
        _reject_duplicate_refs("ContextEvolutionOperation.reason_refs", self.reason_refs)
        _require_non_empty_str("ContextEvolutionOperation.schema_version", self.schema_version)
        if self.schema_version != CANONICAL_VERSION:
            raise ValueError("ContextEvolutionOperation.schema_version is frozen")

    def validate_against_policy(self, policy: ContextEvolutionPolicy) -> None:
        if type(policy) is not ContextEvolutionPolicy:
            raise ValueError("policy must be ContextEvolutionPolicy")
        if self.evolution_policy_revision != policy.revision:
            raise ValueError("evolution policy revision mismatch")
        if self.evolution_policy_fingerprint != policy.policy_fingerprint():
            raise ValueError("evolution policy fingerprint mismatch")
        if self.operation_kind not in policy.allowed_kinds:
            raise ValueError("evolution kind not allowed by policy")
        if len(self.reason_refs) > policy.max_reason_refs:
            raise ValueError("reason refs exceed policy bound")
        if self.operation_kind in (ContextEvolutionKind.CONTEXT_MERGE, ContextEvolutionKind.CONTEXT_SPLIT):
            raise ValueError("merge/split require explicit multi-node lineage implementation")

    def canonical_bytes(self) -> bytes:
        out = (
            _field("operation.domain", OPERATION_DOMAIN_SEPARATOR)
            + _field("operation.schema_version", self.schema_version)
            + _field("operation.id", self.operation_id)
            + _field("operation.kind", self.operation_kind.value)
            + _field("operation.parent", self.parent_context.canonical_bytes().decode("utf-8"))
            + _field("operation.child", self.child_context.canonical_bytes().decode("utf-8"))
            + _field("operation.policy_revision", self.evolution_policy_revision)
            + _field("operation.policy_fingerprint", self.evolution_policy_fingerprint)
            + _field("operation.authority", self.authority.canonical_bytes().decode("utf-8"))
            + _field("operation.reason_ref_count", str(len(self.reason_refs)))
        )
        for ref in self.reason_refs:
            out += _field("operation.reason_ref", ref.canonical_bytes().decode("utf-8"))
        return out


@dataclass(frozen=True)
class ContextLineageEdge:
    parent_context_digest: str
    child_context_digest: str
    operation_id: str
    operation_kind: ContextEvolutionKind
    evolution_policy_revision: str
    evolution_policy_fingerprint: str
    edge_id: str | None = None
    lineage_digest: str | None = None
    schema_version: str = CANONICAL_VERSION

    def __post_init__(self) -> None:
        _require_sha256_hex("ContextLineageEdge.parent_context_digest", self.parent_context_digest)
        _require_sha256_hex("ContextLineageEdge.child_context_digest", self.child_context_digest)
        if self.parent_context_digest == self.child_context_digest:
            raise ValueError("ContextLineageEdge parent and child must differ")
        _require_non_empty_str("ContextLineageEdge.operation_id", self.operation_id)
        object.__setattr__(self, "operation_kind", _require_evolution_kind("ContextLineageEdge.operation_kind", self.operation_kind))
        _require_non_empty_str("ContextLineageEdge.evolution_policy_revision", self.evolution_policy_revision)
        _require_sha256_hex("ContextLineageEdge.evolution_policy_fingerprint", self.evolution_policy_fingerprint)
        _require_non_empty_str("ContextLineageEdge.schema_version", self.schema_version)
        if self.schema_version != CANONICAL_VERSION:
            raise ValueError("ContextLineageEdge.schema_version is frozen")
        digest = _digest_hex(self.semantic_canonical_bytes())
        if self.edge_id is None:
            object.__setattr__(self, "edge_id", digest)
        elif self.edge_id != digest:
            raise ValueError("ContextLineageEdge.edge_id must equal lineage digest")
        if self.lineage_digest is None:
            object.__setattr__(self, "lineage_digest", digest)
        elif self.lineage_digest != digest:
            raise ValueError("ContextLineageEdge.lineage_digest mismatch")

    @classmethod
    def from_operation(cls, operation: ContextEvolutionOperation, policy: ContextEvolutionPolicy) -> "ContextLineageEdge":
        if type(operation) is not ContextEvolutionOperation:
            raise ValueError("operation must be ContextEvolutionOperation")
        operation.validate_against_policy(policy)
        return cls(
            parent_context_digest=operation.parent_context.context_digest,
            child_context_digest=operation.child_context.context_digest,
            operation_id=operation.operation_id,
            operation_kind=operation.operation_kind,
            evolution_policy_revision=operation.evolution_policy_revision,
            evolution_policy_fingerprint=operation.evolution_policy_fingerprint,
        )

    def semantic_canonical_bytes(self) -> bytes:
        return (
            _field("lineage.domain", LINEAGE_DOMAIN_SEPARATOR)
            + _field("lineage.schema_version", self.schema_version)
            + _field("lineage.parent_context_digest", self.parent_context_digest)
            + _field("lineage.child_context_digest", self.child_context_digest)
            + _field("lineage.operation_id", self.operation_id)
            + _field("lineage.operation_kind", self.operation_kind.value)
            + _field("lineage.policy_revision", self.evolution_policy_revision)
            + _field("lineage.policy_fingerprint", self.evolution_policy_fingerprint)
        )


@dataclass(frozen=True)
class ContextEvolutionAudit:
    operation_id: str
    lineage_digest: str
    diagnostics: tuple[str, ...]
    created_at: str

    def __post_init__(self) -> None:
        _require_non_empty_str("ContextEvolutionAudit.operation_id", self.operation_id)
        _require_sha256_hex("ContextEvolutionAudit.lineage_digest", self.lineage_digest)
        _require_tuple("ContextEvolutionAudit.diagnostics", self.diagnostics)
        if not all(type(item) is str for item in self.diagnostics):
            raise ValueError("ContextEvolutionAudit.diagnostics must contain str only")
        _require_non_empty_str("ContextEvolutionAudit.created_at", self.created_at)


@runtime_checkable
class ContextEvolutionValidator(Protocol):
    def validate(self, operation: ContextEvolutionOperation, policy: ContextEvolutionPolicy) -> ContextLineageEdge:
        ...


class StrictContextEvolutionValidator:
    def validate(self, operation: ContextEvolutionOperation, policy: ContextEvolutionPolicy) -> ContextLineageEdge:
        if type(operation) is not ContextEvolutionOperation:
            raise ValueError("operation must be exact ContextEvolutionOperation")
        if type(policy) is not ContextEvolutionPolicy:
            raise ValueError("policy must be exact ContextEvolutionPolicy")
        return ContextLineageEdge.from_operation(operation, policy)
