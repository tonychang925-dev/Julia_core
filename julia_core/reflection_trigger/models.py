"""DIA-3 R1.1 — Core Reflection Trigger canonical contract.

A reflection trigger is a bounded opportunity to reflect. It is not a diary
entry, accepted truth, memory, context, or physical scheduling implementation.

Frozen Core semantics:
  * TriggerKind is a closed enum with exactly four members.
  * Opportunity identity is SHA-256 over versioned canonical OpportunityKey
    bytes: schema_version, conversation_id, policy_revision, trigger_kind, and
    the typed causal anchor all enter the identity domain.
  * Causal anchors are closed variants: single event, activity window, quiet
    window.
  * EvidenceBasis preserves caller-supplied canonical event order exactly; it
    rejects duplicate refs but never sorts membership internally.
  * triggered_at is audit-only on PendingOpportunity and is excluded from causal
    identity / exact retry equality.

Forbidden here: filesystem I/O, persistence implementation, governance, model
runtime execution, Memory/Context/Diary imports. stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256

CANONICAL_VERSION = "dia3-reflection-trigger-v1"
DOMAIN_SEPARATOR = "julia_core.reflection_trigger.opportunity_key.v1"
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


class TriggerKind(Enum):
    """Closed frozen trigger kind set; arbitrary strings are outside contract."""

    TURN_BOUNDARY = "TURN_BOUNDARY"
    QUIET_WINDOW = "QUIET_WINDOW"
    ACTIVITY_WINDOW = "ACTIVITY_WINDOW"
    EXPLICIT_REFLECTION_REQUEST = "EXPLICIT_REFLECTION_REQUEST"


@dataclass(frozen=True)
class TriggerSourceRef:
    """Trigger-owned typed opaque source reference."""

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
class TriggerReason:
    """Opaque Core reason for why a reflection opportunity was raised."""

    reason_code: str
    detail: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str("TriggerReason.reason_code", self.reason_code)
        if self.detail is not None and type(self.detail) is not str:
            raise ValueError("TriggerReason.detail must be None or str")

    def canonical_bytes(self) -> bytes:
        return _field("reason.code", self.reason_code) + _field("reason.detail", self.detail or "-")


@dataclass(frozen=True)
class EvidenceBasis:
    """Evidence refs in already-canonical causal event order.

    This class freezes membership and preserves order. It does not infer,
    lexical-sort, arrival-sort, or otherwise reorder evidence.
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

    def canonical_bytes(self) -> bytes:
        out = _field("evidence.version", CANONICAL_VERSION)
        out += _field("evidence.digest_function", self.digest_function)
        out += _field("evidence.count", str(len(self.source_refs)))
        for ref in self.source_refs:
            out += _field("evidence.ref", ref.canonical_bytes().decode("utf-8"))
        return out

    def digest(self) -> str:
        return _digest_hex(self.canonical_bytes())


@dataclass(frozen=True)
class EligibilityBoundary:
    """Closed activity-window eligibility boundary."""

    boundary_event_id: str
    boundary_reason: str

    def __post_init__(self) -> None:
        _require_non_empty_str("EligibilityBoundary.boundary_event_id", self.boundary_event_id)
        _require_non_empty_str("EligibilityBoundary.boundary_reason", self.boundary_reason)

    def canonical_bytes(self) -> bytes:
        return (
            _field("eligibility.boundary_event_id", self.boundary_event_id)
            + _field("eligibility.boundary_reason", self.boundary_reason)
        )


@dataclass(frozen=True)
class SingleEventAnchor:
    event_id: str
    evidence_basis: EvidenceBasis

    def __post_init__(self) -> None:
        _require_non_empty_str("SingleEventAnchor.event_id", self.event_id)
        if type(self.evidence_basis) is not EvidenceBasis:
            raise ValueError("SingleEventAnchor.evidence_basis must be EvidenceBasis")

    def canonical_bytes(self) -> bytes:
        return (
            _field("anchor.variant", "single_event")
            + _field("anchor.event_id", self.event_id)
            + _field("anchor.evidence_digest_function", self.evidence_basis.digest_function)
            + _field("anchor.evidence_digest", self.evidence_basis.digest())
        )


@dataclass(frozen=True)
class ActivityWindowAnchor:
    window_start_event_id: str
    eligibility_boundary: EligibilityBoundary
    evidence_basis: EvidenceBasis

    def __post_init__(self) -> None:
        _require_non_empty_str("ActivityWindowAnchor.window_start_event_id", self.window_start_event_id)
        if type(self.eligibility_boundary) is not EligibilityBoundary:
            raise ValueError("ActivityWindowAnchor.eligibility_boundary must be EligibilityBoundary")
        if type(self.evidence_basis) is not EvidenceBasis:
            raise ValueError("ActivityWindowAnchor.evidence_basis must be EvidenceBasis")

    def canonical_bytes(self) -> bytes:
        return (
            _field("anchor.variant", "activity_window")
            + _field("anchor.window_start_event_id", self.window_start_event_id)
            + _field("anchor.eligibility_boundary", self.eligibility_boundary.canonical_bytes().decode("utf-8"))
            + _field("anchor.evidence_digest_function", self.evidence_basis.digest_function)
            + _field("anchor.evidence_digest", self.evidence_basis.digest())
        )


@dataclass(frozen=True)
class QuietWindowAnchor:
    last_event_id: str
    quiet_boundary_id: str
    evidence_basis: EvidenceBasis

    def __post_init__(self) -> None:
        _require_non_empty_str("QuietWindowAnchor.last_event_id", self.last_event_id)
        _require_non_empty_str("QuietWindowAnchor.quiet_boundary_id", self.quiet_boundary_id)
        if type(self.evidence_basis) is not EvidenceBasis:
            raise ValueError("QuietWindowAnchor.evidence_basis must be EvidenceBasis")

    def canonical_bytes(self) -> bytes:
        return (
            _field("anchor.variant", "quiet_window")
            + _field("anchor.last_event_id", self.last_event_id)
            + _field("anchor.quiet_boundary_id", self.quiet_boundary_id)
            + _field("anchor.evidence_digest_function", self.evidence_basis.digest_function)
            + _field("anchor.evidence_digest", self.evidence_basis.digest())
        )


CausalAnchor = SingleEventAnchor | ActivityWindowAnchor | QuietWindowAnchor


@dataclass(frozen=True)
class OpportunityKey:
    """Canonical causal identity key for a reflection opportunity."""

    schema_version: str
    conversation_id: str
    policy_revision: str
    trigger_kind: TriggerKind
    causal_anchor: CausalAnchor

    def __post_init__(self) -> None:
        _require_non_empty_str("OpportunityKey.schema_version", self.schema_version)
        _require_non_empty_str("OpportunityKey.conversation_id", self.conversation_id)
        _require_non_empty_str("OpportunityKey.policy_revision", self.policy_revision)
        if type(self.trigger_kind) is not TriggerKind:
            raise ValueError("OpportunityKey.trigger_kind must be TriggerKind")
        if type(self.causal_anchor) not in (SingleEventAnchor, ActivityWindowAnchor, QuietWindowAnchor):
            raise ValueError("OpportunityKey.causal_anchor must be a frozen CausalAnchor variant")

    def canonical_bytes(self) -> bytes:
        return (
            _field("opportunity.domain", DOMAIN_SEPARATOR)
            + _field("opportunity.schema_version", self.schema_version)
            + _field("opportunity.conversation_id", self.conversation_id)
            + _field("opportunity.policy_revision", self.policy_revision)
            + _field("opportunity.trigger_kind", self.trigger_kind.value)
            + _field("opportunity.causal_anchor", self.causal_anchor.canonical_bytes().decode("utf-8"))
        )

    def opportunity_id(self) -> str:
        return _digest_hex(self.canonical_bytes())


@dataclass(frozen=True)
class ReflectionOpportunity:
    """Core opportunity record carried into scheduling/retry state."""

    opportunity_key: OpportunityKey
    source_refs: tuple[TriggerSourceRef, ...]
    reasons: tuple[TriggerReason, ...]
    opportunity_id: str | None = None

    def __post_init__(self) -> None:
        if type(self.opportunity_key) is not OpportunityKey:
            raise ValueError("ReflectionOpportunity.opportunity_key must be OpportunityKey")
        _require_tuple("ReflectionOpportunity.source_refs", self.source_refs)
        if not self.source_refs:
            raise ValueError("ReflectionOpportunity.source_refs must be non-empty")
        if not all(type(ref) is TriggerSourceRef for ref in self.source_refs):
            raise ValueError("ReflectionOpportunity.source_refs must contain TriggerSourceRef only")
        _require_tuple("ReflectionOpportunity.reasons", self.reasons)
        if not self.reasons:
            raise ValueError("ReflectionOpportunity.reasons must be non-empty")
        if not all(type(reason) is TriggerReason for reason in self.reasons):
            raise ValueError("ReflectionOpportunity.reasons must contain TriggerReason only")
        expected = self.opportunity_key.opportunity_id()
        if self.opportunity_id is None:
            object.__setattr__(self, "opportunity_id", expected)
        elif self.opportunity_id != expected:
            raise ValueError("ReflectionOpportunity.opportunity_id must equal OpportunityKey identity")

    def canonical_bytes(self) -> bytes:
        out = _field("reflection_opportunity.id", self.opportunity_id or self.opportunity_key.opportunity_id())
        out += _field("reflection_opportunity.key", self.opportunity_key.canonical_bytes().decode("utf-8"))
        out += _field("reflection_opportunity.source_ref_count", str(len(self.source_refs)))
        for ref in self.source_refs:
            out += _field("reflection_opportunity.source_ref", ref.canonical_bytes().decode("utf-8"))
        out += _field("reflection_opportunity.reason_count", str(len(self.reasons)))
        for reason in self.reasons:
            out += _field("reflection_opportunity.reason", reason.canonical_bytes().decode("utf-8"))
        return out

    def semantic_equals(self, other: object) -> bool:
        return type(other) is ReflectionOpportunity and self.canonical_bytes() == other.canonical_bytes()


@dataclass(frozen=True)
class TriggerPolicy:
    """Core policy revision participating in opportunity identity."""

    policy_revision: str
    schema_version: str = CANONICAL_VERSION
    enabled_kinds: tuple[TriggerKind, ...] = tuple(TriggerKind)

    def __post_init__(self) -> None:
        _require_non_empty_str("TriggerPolicy.policy_revision", self.policy_revision)
        _require_non_empty_str("TriggerPolicy.schema_version", self.schema_version)
        _require_tuple("TriggerPolicy.enabled_kinds", self.enabled_kinds)
        if not self.enabled_kinds:
            raise ValueError("TriggerPolicy.enabled_kinds must be non-empty")
        if not all(type(kind) is TriggerKind for kind in self.enabled_kinds):
            raise ValueError("TriggerPolicy.enabled_kinds must contain TriggerKind only")


@dataclass(frozen=True)
class PendingOpportunity:
    """Pending scheduling state for a ReflectionOpportunity.

    triggered_at is first durable audit evidence, not part of causal identity.
    """

    opportunity_id: str
    opportunity: ReflectionOpportunity
    triggered_at: str
    status: str = "pending"

    def __post_init__(self) -> None:
        _require_non_empty_str("PendingOpportunity.opportunity_id", self.opportunity_id)
        if type(self.opportunity) is not ReflectionOpportunity:
            raise ValueError("PendingOpportunity.opportunity must be ReflectionOpportunity")
        _require_non_empty_str("PendingOpportunity.triggered_at", self.triggered_at)
        _require_non_empty_str("PendingOpportunity.status", self.status)
        if self.status != "pending":
            raise ValueError("PendingOpportunity.status must be 'pending'")
        if self.opportunity_id != self.opportunity.opportunity_id:
            raise ValueError("PendingOpportunity.opportunity_id must equal ReflectionOpportunity.opportunity_id")

    @classmethod
    def pending(cls, opportunity: ReflectionOpportunity, *, triggered_at: str) -> "PendingOpportunity":
        return cls(
            opportunity_id=opportunity.opportunity_id or opportunity.opportunity_key.opportunity_id(),
            opportunity=opportunity,
            triggered_at=triggered_at,
        )

    def exact_retry_equals(self, other: object) -> bool:
        return (
            type(other) is PendingOpportunity
            and self.opportunity_id == other.opportunity_id
            and self.opportunity.semantic_equals(other.opportunity)
        )


@dataclass(frozen=True)
class BoundedSchedulingState:
    """Bounded Core scheduling state; no physical queue/storage semantics."""

    pending: tuple[PendingOpportunity, ...] = ()
    max_pending: int = 1024

    def __post_init__(self) -> None:
        _require_tuple("BoundedSchedulingState.pending", self.pending)
        if not all(type(item) is PendingOpportunity for item in self.pending):
            raise ValueError("BoundedSchedulingState.pending must contain PendingOpportunity only")
        if type(self.max_pending) is not int or self.max_pending <= 0:
            raise ValueError("BoundedSchedulingState.max_pending must be positive int")
        if len(self.pending) > self.max_pending:
            raise ValueError("BoundedSchedulingState.pending exceeds max_pending")
