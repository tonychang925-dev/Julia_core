"""M0.1 Capability Model — Julia OS Capability Operating Layer primitives.

A capability is an external-world interface Julia can invoke.
This module defines the core data types: what a capability IS,
how a request looks, and what a result carries.

Provider Supplies Capability, Not Cognition (JULIA_CORE_PRINCIPLES.md P4).
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


# ── Capability Request ──────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class CapabilityRequest:
    """A request from Julia Reasoning to invoke a capability.

    Reasoning says "I need market.snapshot.read".
    CapabilityManager decides if, how, and through whom.
    """
    capability_name: str          # "market.snapshot.read"
    arguments: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: f"cap_{_time.time_ns()}")
    cognitive_mode: str = "conversation"  # "conversation" | "morning_brief" | "auto_alert"
    session_id: str | None = None
    reason: str = ""              # Why Julia is requesting this capability


# ── Capability Result ───────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class CapabilityResult:
    """The outcome of a capability invocation.

    status tells Reasoning what happened. data carries the payload.
    evidence carries the audit trail (ADR-026 AC-4).
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


# ── Evidence ────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class CapabilityEvidence:
    """Audit trail for one capability invocation (ADR-026 AC-4).

    Every capability call produces one. Stored in EvidenceLedger.
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


# ── Exports ─────────────────────────────────────────────────────────────────

__all__ = [
    "CapabilityDefinition",
    "CapabilityEvidence",
    "CapabilityLayer",
    "CapabilityProvider",
    "CapabilityRequest",
    "CapabilityResult",
    "CapabilityStatus",
]
