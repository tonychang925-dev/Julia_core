"""Reflection Trigger — Core semantic contract (DIA-3 R1.1 / Codex A)."""

from .models import (
    CANONICAL_VERSION,
    DOMAIN_SEPARATOR,
    EVIDENCE_DIGEST_FUNCTION,
    ActivityWindowAnchor,
    BoundedSchedulingState,
    CausalAnchor,
    EligibilityBoundary,
    EvidenceBasis,
    OpportunityKey,
    PendingOpportunity,
    QuietWindowAnchor,
    ReflectionOpportunity,
    SingleEventAnchor,
    TriggerKind,
    TriggerPolicy,
    TriggerReason,
    TriggerSourceRef,
)
from .repository_protocol import ReflectionTriggerStateRepository, TriggerIdentityConflict

__all__ = [
    "CANONICAL_VERSION",
    "DOMAIN_SEPARATOR",
    "EVIDENCE_DIGEST_FUNCTION",
    "TriggerKind",
    "TriggerSourceRef",
    "TriggerReason",
    "EvidenceBasis",
    "EligibilityBoundary",
    "SingleEventAnchor",
    "ActivityWindowAnchor",
    "QuietWindowAnchor",
    "CausalAnchor",
    "OpportunityKey",
    "ReflectionOpportunity",
    "TriggerPolicy",
    "PendingOpportunity",
    "BoundedSchedulingState",
    "ReflectionTriggerStateRepository",
    "TriggerIdentityConflict",
]
