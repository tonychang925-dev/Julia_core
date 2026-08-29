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

import copy as _copy
from dataclasses import dataclass, field
from enum import Enum
import time as _time
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


class CapabilityRequestAuthorityError(ValueError):
    """A caller attempted to embed non-semantic transport/provider authority."""


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
        object.__setattr__(self, "arguments", _copy.deepcopy(dict(arguments or {})))
        object.__setattr__(self, "requested_scope", requested_scope)
        object.__setattr__(self, "idempotency_key", idempotency_key or canonical_request_id)
        object.__setattr__(self, "requested_at", canonical_requested_at)
        object.__setattr__(self, "provenance", _copy.deepcopy(legacy_provenance))

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


_FORBIDDEN_TOP_LEVEL_AUTHORITY_KEYS = frozenset({
    "adapter",
    "base_url",
    "endpoint",
    "network_policy",
    "protocol",
    "provider",
    "provider_id",
    "provider_name",
    "proxy",
    "selected_provider",
    "transport",
})

_FORBIDDEN_RECURSIVE_AUTHORITY_KEYS = frozenset({
    "browser_command",
    "browser_session_id",
    "browser_session_ref",
    "chatgpt_url",
    "conversation_url",
    "dom_selector",
    "extension_nonce",
    "tab_id",
    "tab_ref",
})


def _find_recursive_authority_keys(value: Any) -> set[str]:
    found: set[str] = set()
    stack: list[Any] = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, child in current.items():
                name = str(key)
                if name in _FORBIDDEN_RECURSIVE_AUTHORITY_KEYS:
                    found.add(name)
                stack.append(child)
        elif isinstance(current, (list, tuple)):
            stack.extend(current)
    return found


def validate_capability_request_authority(request: CapabilityRequest) -> None:
    """Reject caller-supplied provider, transport, or browser authority."""
    top_level = set(request.arguments) | set(request.provenance)
    forbidden_top_level = top_level & _FORBIDDEN_TOP_LEVEL_AUTHORITY_KEYS
    if forbidden_top_level:
        raise CapabilityRequestAuthorityError(
            "caller-supplied provider/transport authority is forbidden: "
            + ", ".join(sorted(forbidden_top_level))
        )

    forbidden_browser = (
        _find_recursive_authority_keys(request.arguments)
        | _find_recursive_authority_keys(request.provenance)
    )
    if forbidden_browser:
        raise CapabilityRequestAuthorityError(
            "caller-supplied browser authority is forbidden: "
            + ", ".join(sorted(forbidden_browser))
        )


def sanitize_capability_request_authority(request: CapabilityRequest) -> CapabilityRequest:
    """Return a defensively copied provider-visible semantic request.

    Provider/transport-selection and browser authority are rejected before this
    returned view is created. The original caller-owned request is not mutated;
    nested request material is deep-copied and not shared with the provider.
    """
    validate_capability_request_authority(request)

    return CapabilityRequest(
        capability_id=request.capability_id,
        arguments=request.arguments,
        capability_request_id=request.capability_request_id,
        turn_id=request.turn_id,
        generation_id=request.generation_id,
        correlation_id=request.correlation_id,
        requested_scope=request.requested_scope,
        idempotency_key=request.idempotency_key,
        requested_at=request.requested_at,
        provenance=request.provenance,
    )


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




_ALLOWED_PROVIDER_OUTCOME_STATUSES = {
    ToolResultStatus.SUCCESS,
    ToolResultStatus.UNAVAILABLE,
    ToolResultStatus.ERROR,
    ToolResultStatus.TIMEOUT,
    ToolResultStatus.CANCELLED,
    ToolResultStatus.PARTIAL,
}


@dataclass(frozen=True, slots=True)
class ProviderExecutionOutcome:
    """Typed provider execution truth carrier.

    Providers may report only execution truth. Authorization outcomes such as
    DENIED remain owned by PermissionPolicy/CapabilityManager and are rejected
    as provider contract violations.
    """

    status: str | ToolResultStatus
    structured_output: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] | None = None
    side_effect_state: str | SideEffectState = SideEffectState.NONE

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", normalize_provider_status(self.status))
        object.__setattr__(self, "side_effect_state", normalize_side_effect_state(self.side_effect_state))
        object.__setattr__(
            self,
            "structured_output",
            _copy.deepcopy(dict(self.structured_output or {})),
        )
        if self.error is not None:
            object.__setattr__(self, "error", _copy.deepcopy(dict(self.error)))


def normalize_provider_status(status: str | ToolResultStatus) -> ToolResultStatus:
    try:
        normalized = status if isinstance(status, ToolResultStatus) else ToolResultStatus(str(status))
    except Exception as exc:
        raise ValueError(f"provider outcome status is invalid: {status!r}") from exc
    if normalized not in _ALLOWED_PROVIDER_OUTCOME_STATUSES:
        raise ValueError(
            f"provider outcome status {normalized.value!r} is not allowed; "
            "authorization truth belongs to PermissionPolicy/CapabilityManager"
        )
    return normalized


def normalize_side_effect_state(state: str | SideEffectState) -> SideEffectState:
    try:
        return state if isinstance(state, SideEffectState) else SideEffectState(str(state))
    except Exception as exc:
        raise ValueError(f"provider side_effect_state is invalid: {state!r}") from exc


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

    async def execute(self, request: CapabilityRequest) -> dict[str, Any] | ProviderExecutionOutcome:
        """Execute the capability. Returns legacy data dict or typed execution outcome."""
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
    "CapabilityRequestAuthorityError",
    "ProviderExecutionOutcome",
    "CapabilityResult",
    "CapabilityStatus",
    "Evidence",
    "EvidenceSourceType",
    "SideEffectState",
    "ToolResult",
    "normalize_provider_status",
    "normalize_side_effect_state",
    "sanitize_capability_request_authority",
    "validate_capability_request_authority",
    "ToolResultStatus",
]
