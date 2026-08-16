"""Reflection Trigger — Core semantic contract (DIA-3 R1 / Codex A)."""

from .models import (
    CANONICAL_VERSION,
    DOMAIN_SEPARATOR,
    EVIDENCE_DIGEST_FUNCTION,
    EvidenceBasis,
    ReflectionTriggerSemanticPayload,
    ReflectionTriggerState,
    TriggerSourceRef,
)
from .repository_protocol import ReflectionTriggerStateRepository, TriggerIdentityConflict

__all__ = [
    "CANONICAL_VERSION",
    "DOMAIN_SEPARATOR",
    "EVIDENCE_DIGEST_FUNCTION",
    "TriggerSourceRef",
    "EvidenceBasis",
    "ReflectionTriggerSemanticPayload",
    "ReflectionTriggerState",
    "ReflectionTriggerStateRepository",
    "TriggerIdentityConflict",
]
