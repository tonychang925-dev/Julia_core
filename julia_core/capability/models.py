"""Capability Operating Layer primitives.

This module now exposes the frozen C-08/C-12 vocabulary while preserving the
legacy M0/M1 call surface used by current runtime code.

Canonical objects:
  CapabilityRequest -> CapabilityCall -> ToolResult + Evidence

Compatibility objects:
  CapabilityResult and CapabilityEvidence remain temporary legacy wrappers for
  existing manager/provider tests. They are not the canonical ToolResult or
  Evidence contract.
"""

from __future__ import annotations

import time as _time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol


# ── Capability Status ───────────────────────────────────────────────────────

class CapabilityStatus(str, Enum):
    """Lifecycle state of a registered capability.

    REGISTERED → AVAILABLE → DEGRADED → DISABLED
    """
    REGISTERED = "registered"    # Defined but not yet validated
    AVAILABLE   = "available"    # Provider healthy, ready for use
    DEGRADED    = "degraded"     # Provider unhealthy but may recover
    DISABLED    = "disabled"     # Explicitly turned off


# ── Capability Layer ────────────────────────────────────────────────────────

class CapabilityLayer(str, Enum):
    """What kind of capability this is — determines how it interacts with Context OS."""
    PERCEPTION    = "perception"     # voice, vision
    KNOWLEDGE     = "knowledge"      # files, search
    MEMORY        = "memory"         # diary, long-term
    WORLD         = "world"          # weather, time, web
    INTELLIGENCE  = "intelligence"   # market, news, analysis (ADR-026)
    ACTION        = "action"         # write, execute


# ── Capability Definition ───────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class CapabilityDefinition:
    """A capability Julia can invoke — registered in CapabilityRegistry.

    This is WHAT Julia can do, not HOW. The provider/adapter handle HOW.
    """
    name: str                     # "market.snapshot.read", "system.time.read"
    description: str              # Human-readable: "Read today's market overview"
    layer: CapabilityLayer        # INTELLIGENCE, WORLD, PERCEPTION, etc.
    provider: str                 # "ai_theme_app_mcp", "local", "mock_time"
    permission_scope: str         # "market.observe", "system.read"
    input_schema: dict[str, str] = field(default_factory=dict)  # param → description
    adapter: str | None = None    # "mcp" | "http" | None for local handler
    status: CapabilityStatus = CapabilityStatus.REGISTERED
    schema_version: str = "1.0"


# ── Canonical C-08 Request / Call / Result ──────────────────────────────────

@dataclass(frozen=True, slots=True, init=False)
class CapabilityRequest:
    """Canonical C-08 request from Julia cognition to invoke a capability.

    Canonical fields follow C-08 exactly. Legacy callers may still construct
    this object as CapabilityRequest("file.read", {...}) and may read
    request.capability_name / request.request_id as compatibility aliases.
    These aliases are properties, not canonical dataclass fields.
    """

    capability_request_id: str
    turn_id: str
    generation_id: str
    correlation_id: str
    capability_id: str
    arguments: dict[str, Any]
    requested_scope: str
    idempotency_key: str
    requested_at: str
    provenance: dict[str, Any]

    def __init__(
        self,
        capability_id: str = "",
        arguments: dict[str, Any] | None = None,
        *,
        capability_request_id: str | None = None,
        turn_id: str = "",
        generation_id: str = "",
        correlation_id: str = "",
        requested_scope: str = "",
        idempotency_key: str = "",
        requested_at: str | None = None,
        provenance: dict[str, Any] | None = None,
        # Legacy constructor aliases — not dataclass fields.
        capability_name: str | None = None,
        request_id: str | None = None,
        cognitive_mode: str | None = None,
        session_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        canonical_capability_id = capability_id or capability_name or ""
        canonical_request_id = capability_request_id or request_id or f"cap_req_{_time.time_ns()}"
        canonical_requested_at = requested_at or _iso_timestamp()
        legacy_provenance = dict(provenance or {})
        if cognitive_mode is not None:
            legacy_provenance.setdefault("legacy_cognitive_mode", cognitive_mode)
        if session_id is not None:
            legacy_provenance.setdefault("legacy_session_id", session_id)
        if reason is not None:
            legacy_provenance.setdefault("legacy_reason", reason)

        object.__setattr__(self, "capability_request_id", canonical_request_id)
        object.__setattr__(self, "turn_id", turn_id)
        object.__setattr__(self, "generation_id", generation_id)
        object.__setattr__(self, "correlation_id", correlation_id)
        object.__setattr__(self, "capability_id", canonical_capability_id)
        object.__setattr__(self, "arguments", dict(arguments or {}))
        object.__setattr__(self, "requested_scope", requested_scope)
        object.__setattr__(self, "idempotency_key", idempotency_key or canonical_request_id)
        object.__setattr__(self, "requested_at", canonical_requested_at)
        object.__setattr__(self, "provenance", legacy_provenance)

    @property
    def capability_name(self) -> str:
        """Legacy alias for current manager/provider code."""
        return self.capability_id

    @property
    def request_id(self) -> str:
        """Legacy alias for current manager/provider code."""
        return self.capability_request_id

    @property
    def cognitive_mode(self) -> str:
        """Legacy metadata projection; not a canonical C-08 field."""
        return str(self.provenance.get("legacy_cognitive_mode", "conversation"))

    @property
    def session_id(self) -> str | None:
        """Legacy metadata projection; not a canonical C-08 field."""
        value = self.provenance.get("legacy_session_id")
        return str(value) if value is not None else None

    @property
    def reason(self) -> str:
        """Legacy metadata projection; not a canonical C-08 field."""
        return str(self.provenance.get("legacy_reason", ""))

    def to_canonical_dict(self) -> dict[str, Any]:
        """Serialize only canonical C-08 fields."""
        return {
            "capability_request_id": self.capability_request_id,
            "turn_id": self.turn_id,
            "generation_id": self.generation_id,
            "correlation_id": self.correlation_id,
            "capability_id": self.capability_id,
            "arguments": dict(self.arguments),
            "requested_scope": self.requested_scope,
            "idempotency_key": self.idempotency_key,
            "requested_at": self.requested_at,
            "provenance": dict(self.provenance),
        }


class CapabilityCallStatus(str, Enum):
    REQUESTED = "REQUESTED"
    AUTHORIZED = "AUTHORIZED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class CapabilityCall:
    """One C-08 invocation attempt.

    This is separate from CapabilityRequest, ToolResult, Evidence, and C-12
    Action. A call may fail while an externally meaningful Action is UNKNOWN.
    """

    capability_call_id: str
    capability_request_id: str
    status: str | CapabilityCallStatus = CapabilityCallStatus.REQUESTED
    started_at: str = field(default_factory=lambda: _iso_timestamp())
    completed_at: str | None = None
    provider: str = ""
    correlation_id: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)


class ToolResultStatus(str, Enum):
    SUCCESS = "success"
    DENIED = "denied"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class SideEffectState(str, Enum):
    NONE = "none"
    PLANNED = "planned"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ToolResult:
    """C-08 execution outcome.

    ToolResult is not Evidence. It links to cognition-supporting Evidence via
    evidence_refs, where each ref points to Evidence.evidence_id.
    """

    capability_call_id: str
    status: str | ToolResultStatus
    structured_output: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] | None = None
    started_at: str = field(default_factory=lambda: _iso_timestamp())
    completed_at: str | None = None
    side_effect_state: str | SideEffectState = SideEffectState.NONE
    evidence_refs: tuple[str, ...] = ()
    provider: str = ""
    schema_version: str = "1.0"


class EvidenceSourceType(str, Enum):
    CANONICAL_CONVERSATION = "CANONICAL_CONVERSATION"
    USER_REPORT = "USER_REPORT"
    TOOL_OBSERVATION = "TOOL_OBSERVATION"
    DOMAIN_PROVIDER = "DOMAIN_PROVIDER"
    EXTERNAL_SOURCE = "EXTERNAL_SOURCE"
    SYSTEM_OBSERVATION = "SYSTEM_OBSERVATION"
    DERIVED_DETERMINISTIC = "DERIVED_DETERMINISTIC"
    MODEL_INFERENCE = "MODEL_INFERENCE"


@dataclass(frozen=True, slots=True)
class Evidence:
    """Canonical C-12 Evidence object.

    Evidence supports cognition but does not become truth, memory, persona,
    identity, relationship state, ToolResult, Trace, or Action.
    """

    evidence_id: str
    source_type: str | EvidenceSourceType
    source_ref: str
    observed_at: str
    content_ref: str
    provenance: dict[str, Any] = field(default_factory=dict)
    integrity_metadata: dict[str, Any] = field(default_factory=dict)
    freshness: str = "unknown"
    confidence: float = 0.0
    correlation_id: str = ""
    retrieved_at: str = field(default_factory=lambda: _iso_timestamp())


# ── Legacy Result / Evidence Compatibility ──────────────────────────────────

@dataclass(frozen=True, slots=True)
class CapabilityResult:
    """Legacy compatibility wrapper for existing manager/provider code.

    The canonical C-08 result is ToolResult linked to separate Evidence. This
    wrapper remains temporarily so existing runtime code can migrate in phases.
    """
    capability_name: str
    status: str                   # "success" | "denied" | "unavailable" | "unknown" | "error"
    data: dict[str, Any] = field(default_factory=dict)
    provider: str = ""
    error_message: str = ""
    evidence: CapabilityEvidence | None = None
    duration_ms: int = 0
    schema_version: str = "1.0"

    @staticmethod
    def success(name: str, data: dict, provider: str = "", **kwargs) -> "CapabilityResult":
        return CapabilityResult(
            capability_name=name,
            status="success",
            data=data,
            provider=provider,
            **kwargs,
        )

    @staticmethod
    def denied(name: str, reason: str) -> "CapabilityResult":
        return CapabilityResult(
            capability_name=name,
            status="denied",
            error_message=reason,
        )

    @staticmethod
    def unavailable(name: str, provider: str, reason: str = "") -> "CapabilityResult":
        return CapabilityResult(
            capability_name=name,
            status="unavailable",
            provider=provider,
            error_message=reason or f"Provider {provider} is unreachable",
        )

    @staticmethod
    def unknown(name: str) -> "CapabilityResult":
        return CapabilityResult(
            capability_name=name,
            status="unknown",
            error_message=f"Capability '{name}' not registered",
        )

    @staticmethod
    def error(name: str, message: str) -> "CapabilityResult":
        return CapabilityResult(
            capability_name=name,
            status="error",
            error_message=message,
        )


@dataclass(frozen=True, slots=True)
class CapabilityEvidence:
    """Legacy capability audit entry.

    This is not canonical C-12 Evidence. New code should use Evidence and link
    from ToolResult.evidence_refs. This wrapper remains for EvidenceLedger and
    legacy tests until manager migration.
    """
    capability_name: str
    provider: str
    request_id: str
    timestamp: str = field(default_factory=lambda: _time.strftime("%Y-%m-%dT%H:%M:%S"))
    status: str = "success"
    input_schema: str = ""
    output_schema: str = ""


# ── Capability Provider Protocol ────────────────────────────────────────────

class CapabilityProvider(Protocol):
    """A thing that can execute a capability.

    Could be: local function, MCP adapter, HTTP API, mock.

    Providers supply capability, not cognition (P4).
    They return data. They do NOT assemble prompts, own reasoning, or define identity.
    """

    async def execute(self, request: CapabilityRequest) -> dict[str, Any]:
        """Execute the capability. Returns raw data dict."""
        ...

    async def health(self) -> tuple[bool, str]:
        """Check if provider is reachable. Returns (healthy, detail)."""
        ...


def _iso_timestamp() -> str:
    return _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())


# ── Exports ─────────────────────────────────────────────────────────────────

__all__ = [
    "CapabilityCall",
    "CapabilityCallStatus",
    "CapabilityDefinition",
    "CapabilityEvidence",
    "CapabilityLayer",
    "CapabilityProvider",
    "CapabilityRequest",
    "CapabilityResult",
    "CapabilityStatus",
    "Evidence",
    "EvidenceSourceType",
    "SideEffectState",
    "ToolResult",
    "ToolResultStatus",
]
