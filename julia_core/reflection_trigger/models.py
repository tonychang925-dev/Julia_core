"""DIA-3 R1 — Core ReflectionTrigger semantic contract.

ReflectionTrigger is a candidate opportunity to reflect. It is not a Diary
entry, not accepted truth, not persistence, not Memory, and not Context.

Frozen R1 semantics:
  * SourceRef is trigger-owned, typed, and opaque; it does not depend on
    DiarySourceRef.
  * Identity is SHA-256 over versioned canonical serialization using explicit
    domain separation and length-framed UTF-8 fields.
  * triggered_at is audit-only. It is intentionally excluded from causal
    identity and exact-retry semantic equality.
  * evidence_basis uses canonical membership and canonical ordering under a
    frozen digest function.

Forbidden here: filesystem I/O, persistence implementation, governance,
provider/LLM, Memory/Context/Diary dependency. stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

CANONICAL_VERSION = "dia3-reflection-trigger-v1"
DOMAIN_SEPARATOR = "julia_core.reflection_trigger.identity.v1"
EVIDENCE_DIGEST_FUNCTION = "sha256:length-framed-utf8:v1"


def _require_non_empty_str(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty str")


def _require_tuple(name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")


def _frame(value: str) -> bytes:
    """Length-frame a UTF-8 string as `<byte-length>:<bytes>` plus newline."""
    _require_non_empty_str("canonical field", value)
    encoded = value.encode("utf-8")
    return str(len(encoded)).encode("ascii") + b":" + encoded + b"\n"


def _field(name: str, value: str) -> bytes:
    return _frame(name) + _frame(value)


def _digest_hex(canonical_bytes: bytes) -> str:
    return sha256(canonical_bytes).hexdigest()


@dataclass(frozen=True)
class TriggerSourceRef:
    """Trigger-owned typed opaque source reference.

    `ref_type` is a semantic namespace controlled by reflection-trigger code.
    `opaque_ref` is an uninterpreted stable reference inside that namespace.
    This is deliberately not DiarySourceRef and carries no physical path.
    """

    ref_type: str
    opaque_ref: str

    def __post_init__(self) -> None:
        _require_non_empty_str("TriggerSourceRef.ref_type", self.ref_type)
        _require_non_empty_str("TriggerSourceRef.opaque_ref", self.opaque_ref)

    def canonical_bytes(self) -> bytes:
        return (
            _field("ref.version", CANONICAL_VERSION)
            + _field("ref.type", self.ref_type)
            + _field("ref.opaque", self.opaque_ref)
        )

    def canonical_key(self) -> str:
        return _digest_hex(self.canonical_bytes())


@dataclass(frozen=True)
class EvidenceBasis:
    """Canonical evidence membership used to decide trigger identity.

    Input order is never trusted. `source_refs` are canonicalized by their
    length-framed byte representation and must form a set by canonical key.
    """

    source_refs: tuple[TriggerSourceRef, ...]
    digest_function: str = EVIDENCE_DIGEST_FUNCTION

    def __post_init__(self) -> None:
        _require_tuple("EvidenceBasis.source_refs", self.source_refs)
        if not self.source_refs:
            raise ValueError("EvidenceBasis.source_refs must be non-empty")
        if not all(type(ref) is TriggerSourceRef for ref in self.source_refs):
            raise ValueError("EvidenceBasis.source_refs must contain TriggerSourceRef only")
        _require_non_empty_str("EvidenceBasis.digest_function", self.digest_function)
        if self.digest_function != EVIDENCE_DIGEST_FUNCTION:
            raise ValueError("EvidenceBasis.digest_function is frozen")
        keys = [ref.canonical_key() for ref in self.source_refs]
        if len(set(keys)) != len(keys):
            raise ValueError("EvidenceBasis.source_refs must not contain duplicate canonical refs")

    @property
    def canonical_source_refs(self) -> tuple[TriggerSourceRef, ...]:
        return tuple(sorted(self.source_refs, key=lambda ref: ref.canonical_bytes()))

    def canonical_bytes(self) -> bytes:
        out = _field("evidence.version", CANONICAL_VERSION)
        out += _field("evidence.digest_function", self.digest_function)
        out += _field("evidence.count", str(len(self.source_refs)))
        for ref in self.canonical_source_refs:
            ref_bytes = ref.canonical_bytes().decode("utf-8")
            out += _field("evidence.ref", ref_bytes)
        return out

    def digest(self) -> str:
        return _digest_hex(self.canonical_bytes())


@dataclass(frozen=True)
class ReflectionTriggerSemanticPayload:
    """Causal payload for exact-retry equality and identity.

    `triggered_at` is intentionally absent; it is audit-only on state records.
    """

    trigger_kind: str
    source_ref: TriggerSourceRef
    evidence_basis: EvidenceBasis

    def __post_init__(self) -> None:
        _require_non_empty_str("ReflectionTriggerSemanticPayload.trigger_kind", self.trigger_kind)
        if type(self.source_ref) is not TriggerSourceRef:
            raise ValueError("ReflectionTriggerSemanticPayload.source_ref must be TriggerSourceRef")
        if type(self.evidence_basis) is not EvidenceBasis:
            raise ValueError("ReflectionTriggerSemanticPayload.evidence_basis must be EvidenceBasis")

    def canonical_bytes(self) -> bytes:
        return (
            _field("payload.domain", DOMAIN_SEPARATOR)
            + _field("payload.version", CANONICAL_VERSION)
            + _field("payload.trigger_kind", self.trigger_kind)
            + _field("payload.source_ref", self.source_ref.canonical_bytes().decode("utf-8"))
            + _field("payload.evidence_digest_function", self.evidence_basis.digest_function)
            + _field("payload.evidence_digest", self.evidence_basis.digest())
        )

    def identity(self) -> str:
        return _digest_hex(self.canonical_bytes())

    def semantic_equals(self, other: object) -> bool:
        return type(other) is ReflectionTriggerSemanticPayload and self.canonical_bytes() == other.canonical_bytes()


@dataclass(frozen=True)
class ReflectionTriggerState:
    """Pending reflection trigger state.

    `trigger_id` is derived from `semantic_payload.identity()`.
    `triggered_at` is audit-only and is not used by semantic equality.
    """

    trigger_id: str
    semantic_payload: ReflectionTriggerSemanticPayload
    triggered_at: str
    status: str = "pending"

    def __post_init__(self) -> None:
        _require_non_empty_str("ReflectionTriggerState.trigger_id", self.trigger_id)
        if type(self.semantic_payload) is not ReflectionTriggerSemanticPayload:
            raise ValueError("ReflectionTriggerState.semantic_payload must be ReflectionTriggerSemanticPayload")
        _require_non_empty_str("ReflectionTriggerState.triggered_at", self.triggered_at)
        _require_non_empty_str("ReflectionTriggerState.status", self.status)
        if self.status != "pending":
            raise ValueError("ReflectionTriggerState.status must be 'pending'")
        if self.trigger_id != self.semantic_payload.identity():
            raise ValueError("ReflectionTriggerState.trigger_id must equal semantic payload identity")

    @classmethod
    def pending(
        cls,
        semantic_payload: ReflectionTriggerSemanticPayload,
        *,
        triggered_at: str,
    ) -> "ReflectionTriggerState":
        return cls(
            trigger_id=semantic_payload.identity(),
            semantic_payload=semantic_payload,
            triggered_at=triggered_at,
        )

    def exact_retry_equals(self, other: object) -> bool:
        return (
            type(other) is ReflectionTriggerState
            and self.trigger_id == other.trigger_id
            and self.semantic_payload.semantic_equals(other.semantic_payload)
        )
