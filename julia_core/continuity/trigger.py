"""Recovery trigger simulation for Continuity OS.

E1.8.3 scope:
    Runtime event + checkpoint availability -> recovery intent

This module does not load memory, rebuild context, switch providers, or invoke
Runtime lifecycle controls.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from julia_core.continuity.events import ContinuityEvent


@dataclass(frozen=True, slots=True)
class RecoveryTriggerInput:
    event: ContinuityEvent
    checkpoint_available: bool
    provider_changed: bool = False
    previous_provider: str | None = None
    current_provider: str | None = None


@dataclass(frozen=True, slots=True)
class RecoveryTriggerDecision:
    recovery_required: bool
    reason: str
    recovery_status: str
    continuity_state_changed: bool = False
    provider_changed: bool = False

    def to_trace(self) -> dict[str, Any]:
        return {
            "recovery_required": self.recovery_required,
            "reason": self.reason,
            "recovery_status": self.recovery_status,
            "continuity_state_changed": self.continuity_state_changed,
            "provider_changed": self.provider_changed,
        }


class RecoveryTrigger:
    """Evaluates recovery intent without executing recovery."""

    def evaluate(self, trigger: RecoveryTriggerInput) -> RecoveryTriggerDecision:
        if trigger.event == ContinuityEvent.SESSION_START and not trigger.checkpoint_available:
            return RecoveryTriggerDecision(
                recovery_required=False,
                reason="first_session_no_checkpoint",
                recovery_status="NOT_REQUIRED",
            )

        if trigger.event == ContinuityEvent.RUNTIME_RECOVERY and trigger.checkpoint_available:
            return RecoveryTriggerDecision(
                recovery_required=True,
                reason="checkpoint_available",
                recovery_status="RECOVERY_REQUIRED",
            )

        if trigger.event == ContinuityEvent.COMPACT_DETECTED and trigger.checkpoint_available:
            return RecoveryTriggerDecision(
                recovery_required=True,
                reason="compact_detected_checkpoint_available",
                recovery_status="RECOVERY_REQUIRED",
            )

        if trigger.event == ContinuityEvent.PROVIDER_SWITCH:
            return RecoveryTriggerDecision(
                recovery_required=trigger.checkpoint_available,
                reason="provider_switch_continuity_state_unchanged",
                recovery_status="RECOVERY_REQUIRED" if trigger.checkpoint_available else "NOT_REQUIRED",
                continuity_state_changed=False,
                provider_changed=trigger.provider_changed,
            )

        return RecoveryTriggerDecision(
            recovery_required=False,
            reason="no_recovery_condition",
            recovery_status="NOT_REQUIRED",
            provider_changed=trigger.provider_changed,
        )
