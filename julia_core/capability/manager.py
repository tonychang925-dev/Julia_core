"""M0.3 Capability Manager — the kernel of Julia's Capability Operating Layer.

The Manager owns the full invocation lifecycle:
  CapabilityRequest → Registry lookup → Permission check → Provider resolve → Execute → Evidence record → CapabilityResult

This is the single entry point for ALL external-world access.
No capability bypasses the Manager. No provider is called directly.

ADR-026: CapabilityManager is the missing kernel of Julia OS.
"""

from __future__ import annotations

import time as _time
from typing import Optional

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityEvidence,
    CapabilityProvider,
    CapabilityRequest,
    CapabilityResult,
    CapabilityStatus,
)
from julia_core.capability.policy import PermissionPolicy
from julia_core.capability.registry import CapabilityRegistry


# ── Evidence Ledger (inlined for M0) ────────────────────────────────────────

class EvidenceLedger:
    """Records every capability invocation. AC-4: Evidence Trace."""

    def __init__(self):
        self._entries: list[CapabilityEvidence] = []

    def record(self, entry: CapabilityEvidence):
        self._entries.append(entry)

    def last(self) -> Optional[CapabilityEvidence]:
        return self._entries[-1] if self._entries else None

    @property
    def entries(self) -> list[CapabilityEvidence]:
        return list(self._entries)

    @property
    def count(self) -> int:
        return len(self._entries)

    def last_for(self, capability_name: str) -> Optional[CapabilityEvidence]:
        for e in reversed(self._entries):
            if e.capability_name == capability_name:
                return e
        return None


# ── Capability Manager ──────────────────────────────────────────────────────

class CapabilityManager:
    """Request → Capability resolution with policy enforcement.

    Usage:
        manager = CapabilityManager(registry, policy, providers)
        result = await manager.execute(CapabilityRequest("system.time.read"))

    Flow:
        1. Registry lookup  — does this capability exist?
        2. Status check     — is it AVAILABLE (not DEGRADED/DISABLED)?
        3. Permission check — is Julia allowed to invoke this scope?
        4. Provider health  — is the provider reachable?
        5. Execute          — call provider.execute(request)
        6. Evidence record  — write audit trail
        7. Return result    — CapabilityResult to Reasoning
    """

    def __init__(
        self,
        registry: CapabilityRegistry,
        policy: PermissionPolicy,
        providers: dict[str, CapabilityProvider],
    ):
        self.registry = registry
        self.policy = policy
        self.providers = providers
        self.evidence = EvidenceLedger()

    # ── Execute ──────────────────────────────────────────────────────────

    async def execute(self, request: CapabilityRequest) -> CapabilityResult:
        """Full capability invocation lifecycle."""
        start = _time.time()

        # Step 1: Registry lookup
        definition = self.registry.get(request.capability_name)
        if definition is None:
            return CapabilityResult.unknown(request.capability_name)

        # Step 2: Status check
        if definition.status == CapabilityStatus.DISABLED:
            return CapabilityResult.denied(
                request.capability_name,
                f"Capability '{request.capability_name}' is DISABLED",
            )
        if definition.status == CapabilityStatus.DEGRADED:
            # DEGRADED means we attempt but record the risk
            pass

        # Step 3: Permission check
        allowed, reason = self.policy.check(definition.permission_scope)
        if not allowed:
            self._record_evidence(definition, request, "denied")
            return CapabilityResult.denied(request.capability_name, reason)

        # Step 4: Resolve provider
        provider = self._resolve_provider(definition)
        if provider is None:
            return CapabilityResult.unavailable(
                request.capability_name,
                definition.provider,
                f"No provider '{definition.provider}' registered",
            )

        # Step 5: Provider health
        healthy, detail = await provider.health()
        if not healthy:
            return CapabilityResult.unavailable(
                request.capability_name,
                definition.provider,
                detail,
            )

        # Step 6: Execute
        try:
            data = await provider.execute(request)
            duration_ms = int((_time.time() - start) * 1000)
            result = CapabilityResult.success(
                name=request.capability_name,
                data=data,
                provider=definition.provider,
                duration_ms=duration_ms,
                schema_version=definition.schema_version,
            )
            self._record_evidence(definition, request, "success")
            return result
        except Exception as exc:
            duration_ms = int((_time.time() - start) * 1000)
            self._record_evidence(definition, request, "error")
            return CapabilityResult.error(
                request.capability_name,
                f"Provider '{definition.provider}' error: {exc}",
            )

    # ── Helpers ───────────────────────────────────────────────────────────

    def _resolve_provider(self, definition: CapabilityDefinition) -> Optional[CapabilityProvider]:
        """Find the provider for this capability."""
        return self.providers.get(definition.provider)

    def _record_evidence(self, definition: CapabilityDefinition, request: CapabilityRequest, status: str):
        """Write audit trail entry (AC-4)."""
        self.evidence.record(CapabilityEvidence(
            capability_name=request.capability_name,
            provider=definition.provider,
            request_id=request.request_id,
            status=status,
            input_schema=definition.schema_version,
            output_schema=definition.schema_version,
        ))

    # ── Introspection ─────────────────────────────────────────────────────

    async def resolve_definition(self, name: str) -> Optional[CapabilityDefinition]:
        """Look up a capability definition without executing."""
        return self.registry.get(name)

    def list_available(self) -> list[CapabilityDefinition]:
        """List all capabilities with status AVAILABLE."""
        return [
            d for d in self.registry.all()
            if d.status == CapabilityStatus.AVAILABLE
        ]

    def list_by_layer(self, layer) -> list[CapabilityDefinition]:
        """List capabilities in a given layer."""
        return self.registry.by_layer(layer)


__all__ = ["CapabilityManager", "EvidenceLedger"]
