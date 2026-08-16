"""DIA-3 R1.1 — ReflectionTriggerStateRepository Port.

Core owns trigger semantics; applications own physical persistence. This port is
only the semantic surface for pending reflection opportunities and exposes no
storage implementation detail.

create_pending semantics:
  * absent id -> create and return pending opportunity
  * same id + same canonical opportunity -> idempotent return of existing state
    and preserve the first durable audit timestamp
  * same id + different canonical opportunity -> fail closed with
    TriggerIdentityConflict
"""
from __future__ import annotations

from typing import Protocol

from .models import PendingOpportunity


class TriggerIdentityConflict(Exception):
    """Fail-closed signal for same opportunity id with different causal payload."""


class ReflectionTriggerStateRepository(Protocol):
    """Application-agnostic semantic port for pending ReflectionOpportunity state."""

    def create_pending(self, state: PendingOpportunity) -> PendingOpportunity:
        """Create or idempotently return a pending opportunity.

        Normal return means the pending opportunity is durably known to the
        adapter. If an existing record has the same opportunity id but a
        different canonical opportunity, the implementation MUST fail closed by
        raising TriggerIdentityConflict and MUST NOT overwrite the existing
        record.
        """
        ...
