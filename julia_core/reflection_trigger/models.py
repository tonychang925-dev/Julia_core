"""DIA-3 R1.2 — Core Reflection Trigger canonical contract.

A reflection trigger is a bounded opportunity to reflect. It is not a diary
entry, accepted truth, memory, context, interpretation authority, or physical
scheduling implementation.

Frozen Core semantics:
  * TriggerKind is a closed enum with exactly four members.
  * TriggerReason is structural-only: kind + canonical evidence refs. It carries
    no arbitrary semantic text.
  * Opportunity identity is SHA-256 over versioned canonical OpportunityKey
    bytes: schema_version, conversation_id, policy_revision, trigger_kind, and
    the typed causal anchor all enter the identity domain.
  * Causal anchors are closed variants: single event, activity window, quiet
    window. Single and quiet anchors do not bind mutable evidence projections.
  * Activity-window closure includes start, frozen eligibility boundary, and
    ordered evidence basis.
  * EvidenceBasis preserves caller-supplied canonical event order exactly; it
    rejects duplicate refs but never sorts membership internally.
  * triggered_at is audit-only on PendingOpportunity and is excluded from causal
    identity / exact retry equality.

Forbidden here: filesystem I/O, persistence implementation, governance, model
runtime execution, Memory/Context/Diary imports. stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
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


def _require_non_negative_timedelta(name: str, value: object) -> None:
    if type(value) is not timedelta or value < timedelta(0):
        raise ValueError(f"{name} must be a non-negative timedelta")


def _require_positive_timedelta(name: str, value: object) -> None:
    if type(value) is not timedelta or value <= timedelta(0):
        raise ValueError(f"{name} must be a positive timedelta")


def _require_positive_int(name: str, value: object) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive int")


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


def _reject_duplicate_refs(name: str, refs: tuple[TriggerSourceRef, ...]) -> None:
    keys = [ref.canonical_key() for ref in refs]
    if len(set(keys)) != len(keys):
        raise ValueError(f"{name} must not contain duplicate canonical refs")


@dataclass(frozen=True)
class EvidenceBasis:
    """Evidence refs in already-canonical causal event order."""

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
        _reject_duplicate_refs("EvidenceBasis.source_refs", self.source_refs)

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
class TriggerReason:
    """Structural scheduling reason: closed kind + canonical facts only."""

    kind: TriggerKind
    evidence_refs: tuple[TriggerSourceRef, ...]

    def __post_init__(self) -> None:
        if type(self.kind) is not TriggerKind:
            raise ValueError("TriggerReason.kind must be TriggerKind")
        _require_tuple("TriggerReason.evidence_refs", self.evidence_refs)
        if not self.evidence_refs:
            raise ValueError("TriggerReason.evidence_refs must be non-empty")
        if not all(type(ref) is TriggerSourceRef for ref in self.evidence_refs):
            raise ValueError("TriggerReason.evidence_refs must contain TriggerSourceRef only")
        _reject_duplicate_refs("TriggerReason.evidence_refs", self.evidence_refs)

    def canonical_bytes(self) -> bytes:
        out = _field("reason.kind", self.kind.value)
        out += _field("reason.evidence_ref_count", str(len(self.evidence_refs)))
        for ref in self.evidence_refs:
            out += _field("reason.evidence_ref", ref.canonical_bytes().decode("utf-8"))
        return out


@dataclass(frozen=True)
class EventEligibilityBoundary:
    """Activity window closed by a canonical event id."""

    eligibility_event_id: str

    def __post_init__(self) -> None:
        _require_non_empty_str("EventEligibilityBoundary.eligibility_event_id", self.eligibility_event_id)

    def canonical_bytes(self) -> bytes:
        return (
            _field("eligibility.variant", "event")
            + _field("eligibility.event_id", self.eligibility_event_id)
        )


@dataclass(frozen=True)
class DeterministicTimerEligibilityBoundary:
    """Activity window closed by deterministic timer boundary identity.

    This is a deterministic boundary id, not an actual timer wake wall-clock.
    """

    deterministic_activity_boundary_id: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            "DeterministicTimerEligibilityBoundary.deterministic_activity_boundary_id",
            self.deterministic_activity_boundary_id,
        )

    def canonical_bytes(self) -> bytes:
        return (
            _field("eligibility.variant", "deterministic_timer")
            + _field("eligibility.deterministic_activity_boundary_id", self.deterministic_activity_boundary_id)
        )


EligibilityBoundary = EventEligibilityBoundary | DeterministicTimerEligibilityBoundary


@dataclass(frozen=True)
class SingleEventAnchor:
    event_id: str

    def __post_init__(self) -> None:
        _require_non_empty_str("SingleEventAnchor.event_id", self.event_id)

    def canonical_bytes(self) -> bytes:
        return _field("anchor.variant", "single_event") + _field("anchor.event_id", self.event_id)


@dataclass(frozen=True)
class ActivityWindowAnchor:
    window_start_event_id: str
    eligibility_boundary: EligibilityBoundary
    evidence_basis: EvidenceBasis

    def __post_init__(self) -> None:
        _require_non_empty_str("ActivityWindowAnchor.window_start_event_id", self.window_start_event_id)
        if type(self.eligibility_boundary) not in (EventEligibilityBoundary, DeterministicTimerEligibilityBoundary):
            raise ValueError("ActivityWindowAnchor.eligibility_boundary must be a frozen EligibilityBoundary variant")
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

    def __post_init__(self) -> None:
        _require_non_empty_str("QuietWindowAnchor.last_event_id", self.last_event_id)
        _require_non_empty_str("QuietWindowAnchor.quiet_boundary_id", self.quiet_boundary_id)

    def canonical_bytes(self) -> bytes:
        return (
            _field("anchor.variant", "quiet_window")
            + _field("anchor.last_event_id", self.last_event_id)
            + _field("anchor.quiet_boundary_id", self.quiet_boundary_id)
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
        if self.schema_version != CANONICAL_VERSION:
            raise ValueError("OpportunityKey.schema_version must equal CANONICAL_VERSION")
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
        _reject_duplicate_refs("ReflectionOpportunity.source_refs", self.source_refs)
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
    """Frozen temporal trigger policy knobs; quiet is duration of no events."""

    revision: str
    cooldown: timedelta
    window: timedelta
    quiet_threshold: timedelta
    schema_version: str = CANONICAL_VERSION

    def __post_init__(self) -> None:
        _require_non_empty_str("TriggerPolicy.revision", self.revision)
        _require_non_empty_str("TriggerPolicy.schema_version", self.schema_version)
        if self.schema_version != CANONICAL_VERSION:
            raise ValueError("TriggerPolicy.schema_version must equal CANONICAL_VERSION")
        _require_non_negative_timedelta("TriggerPolicy.cooldown", self.cooldown)
        _require_positive_timedelta("TriggerPolicy.window", self.window)
        _require_positive_timedelta("TriggerPolicy.quiet_threshold", self.quiet_threshold)


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
class SchedulingCursor:
    last_seen_event_id: str | None = None

    def __post_init__(self) -> None:
        if self.last_seen_event_id is not None:
            _require_non_empty_str("SchedulingCursor.last_seen_event_id", self.last_seen_event_id)

    def canonical_bytes(self) -> bytes:
        return _field("cursor.last_seen_event_id", self.last_seen_event_id or "-")


@dataclass(frozen=True)
class ActiveWindowState:
    window_start_event_id: str
    evidence_basis: EvidenceBasis

    def __post_init__(self) -> None:
        _require_non_empty_str("ActiveWindowState.window_start_event_id", self.window_start_event_id)
        if type(self.evidence_basis) is not EvidenceBasis:
            raise ValueError("ActiveWindowState.evidence_basis must be EvidenceBasis")


@dataclass(frozen=True)
class RecentDedupKey:
    opportunity_id: str

    def __post_init__(self) -> None:
        _require_non_empty_str("RecentDedupKey.opportunity_id", self.opportunity_id)


@dataclass(frozen=True)
class DeliveryTombstone:
    opportunity_id: str
    delivered_at: str

    def __post_init__(self) -> None:
        _require_non_empty_str("DeliveryTombstone.opportunity_id", self.opportunity_id)
        _require_non_empty_str("DeliveryTombstone.delivered_at", self.delivered_at)


@dataclass(frozen=True)
class BoundedSchedulingState:
    """Bounded Core scheduling state; no transcript body or storage semantics."""

    cursor: SchedulingCursor
    active_window: ActiveWindowState | None
    recent_dedup: tuple[RecentDedupKey, ...]
    pending: tuple[PendingOpportunity, ...]
    delivery_tombstones: tuple[DeliveryTombstone, ...]
    max_recent_dedup: int = 1024
    max_pending: int = 1024
    max_delivery_tombstones: int = 1024

    def __post_init__(self) -> None:
        if type(self.cursor) is not SchedulingCursor:
            raise ValueError("BoundedSchedulingState.cursor must be SchedulingCursor")
        if self.active_window is not None and type(self.active_window) is not ActiveWindowState:
            raise ValueError("BoundedSchedulingState.active_window must be None or ActiveWindowState")
        _require_tuple("BoundedSchedulingState.recent_dedup", self.recent_dedup)
        if not all(type(item) is RecentDedupKey for item in self.recent_dedup):
            raise ValueError("BoundedSchedulingState.recent_dedup must contain RecentDedupKey only")
        _require_tuple("BoundedSchedulingState.pending", self.pending)
        if not all(type(item) is PendingOpportunity for item in self.pending):
            raise ValueError("BoundedSchedulingState.pending must contain PendingOpportunity only")
        _require_tuple("BoundedSchedulingState.delivery_tombstones", self.delivery_tombstones)
        if not all(type(item) is DeliveryTombstone for item in self.delivery_tombstones):
            raise ValueError("BoundedSchedulingState.delivery_tombstones must contain DeliveryTombstone only")
        _require_positive_int("BoundedSchedulingState.max_recent_dedup", self.max_recent_dedup)
        _require_positive_int("BoundedSchedulingState.max_pending", self.max_pending)
        _require_positive_int("BoundedSchedulingState.max_delivery_tombstones", self.max_delivery_tombstones)
        if len(self.recent_dedup) > self.max_recent_dedup:
            raise ValueError("BoundedSchedulingState.recent_dedup exceeds max_recent_dedup")
        if len(self.pending) > self.max_pending:
            raise ValueError("BoundedSchedulingState.pending exceeds max_pending")
        if len(self.delivery_tombstones) > self.max_delivery_tombstones:
            raise ValueError("BoundedSchedulingState.delivery_tombstones exceeds max_delivery_tombstones")
