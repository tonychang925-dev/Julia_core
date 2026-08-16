"""DIA-3 R1 — ReflectionTriggerStateRepository Port.

Core owns trigger semantics; applications own physical persistence. This port is
only the semantic surface for pending reflection trigger state and exposes no
storage implementation detail.

create_pending semantics:
  * absent id -> create and return pending state
  * same id + same semantic payload -> idempotent return of existing state
  * same id + different semantic payload -> fail closed with TriggerIdentityConflict
"""
from __future__ import annotations

from typing import Protocol

from .models import ReflectionTriggerState


class TriggerIdentityConflict(Exception):
    """Fail-closed signal for same trigger id with different semantic payload."""


class ReflectionTriggerStateRepository(Protocol):
    """Application-agnostic semantic port for pending ReflectionTrigger state."""

    def create_pending(self, state: ReflectionTriggerState) -> ReflectionTriggerState:
        """Create or idempotently return a pending trigger state.

        Normal return means the pending trigger state is durably known to the
        adapter. If an existing record has the same trigger id but a different
        semantic payload, the implementation MUST fail closed by raising
        TriggerIdentityConflict and MUST NOT overwrite the existing record.
        """
        ...
