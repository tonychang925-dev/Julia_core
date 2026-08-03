"""Runtime continuity trace pipeline v1.1.

E1.8.2 scope:
    Runtime Event + Continuity Hook Result -> ExecutionTrace v1.1

This module is a trace adapter only. It does not resolve memory, reconstruct
context, invoke alignment, call providers, or accept lifecycle-control commands
from Continuity OS.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from julia_core.continuity.events import ContinuityEvent
from julia_core.runtime.continuity_hook import RuntimeContinuityInspection

TRACE_VERSION = "1.1"
AUTHORITY_CHAIN = ("Runtime", "ContinuityHook", "ContinuityOS")
_ALLOWED_CONTINUITY_TRACE_KEYS = {
    "checked",
    "checkpoint_found",
    "checkpoint_id",
    "decision_level",
    "recovery_status",
}


@dataclass(frozen=True, slots=True)
class RuntimeTraceContext:
    """Runtime-owned identity for a trace emission."""

    runtime_id: str
    session_id: str
    event: ContinuityEvent

    def to_trace(self) -> dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "session_id": self.session_id,
            "event": self.event.value,
        }


@dataclass(frozen=True, slots=True)
class ExecutionTraceV11:
    """Minimal ExecutionTrace contract for E1.8.2."""

    trace_version: str
    runtime: dict[str, Any]
    continuity: dict[str, Any]
    authority_chain: list[str] = field(default_factory=lambda: list(AUTHORITY_CHAIN))

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_version": self.trace_version,
            "runtime": dict(self.runtime),
            "continuity": dict(self.continuity),
            "authority_chain": list(self.authority_chain),
        }


class ContinuityTracePipeline:
    """Builds ExecutionTrace v1.1 from Runtime context and Continuity result."""

    def build_trace(
        self,
        *,
        runtime: RuntimeTraceContext,
        continuity: RuntimeContinuityInspection | Mapping[str, Any],
    ) -> ExecutionTraceV11:
        return ExecutionTraceV11(
            trace_version=TRACE_VERSION,
            runtime=runtime.to_trace(),
            continuity=self._continuity_payload(continuity),
        )

    @staticmethod
    def _continuity_payload(
        continuity: RuntimeContinuityInspection | Mapping[str, Any],
    ) -> dict[str, Any]:
        if isinstance(continuity, RuntimeContinuityInspection):
            payload = continuity.to_trace()
        else:
            payload = dict(continuity)

        return {
            key: payload[key]
            for key in _ALLOWED_CONTINUITY_TRACE_KEYS
            if key in payload
        }
