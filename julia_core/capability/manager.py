"""M0.3 Capability Manager — the kernel of Julia's Capability Operating Layer.

The Manager owns the full invocation lifecycle. Current production still returns
legacy CapabilityResult for compatibility, but the internal execution spine now
records the canonical C-08/C-12 artifacts:

  CapabilityRequest -> AuthorizationDecision -> CapabilityCall -> Provider
      -> ToolResult + Evidence

CapabilityResult and EvidenceLedger remain compatibility surfaces for existing
runtime/provider callers; they are not the canonical execution truth.
"""

from __future__ import annotations

import time as _time
from dataclasses import dataclass
from typing import Any, Optional

from julia_core.capability.models import (
    CapabilityCall,
    CapabilityCallStatus,
    CapabilityDefinition,
    CapabilityEvidence,
    CapabilityProvider,
    CapabilityRequest,
    CapabilityResult,
    CapabilityStatus,
    Evidence,
    EvidenceSourceType,
    SideEffectState,
    ToolResult,
    ToolResultStatus,
)
from julia_core.capability.policy import AuthorizationDecision, AuthorizationStatus, PermissionPolicy
from julia_core.capability.registry import CapabilityRegistry


@dataclass(frozen=True, slots=True)
class CapabilityExecution:
    """Manager-local immutable carrier grouping one execution's canonical artifacts.

    NOT a new canonical lifecycle/domain object. Groups the existing
    AuthorizationDecision / CapabilityCall / ToolResult / Evidence belonging to
    ONE execution transaction so the bridge can deliver them without latest /
    list rediscovery.

    Invariants:
      - authorization-only (non-ALLOW): capability_call/tool_result = None,
        evidence = ().
      - executed: capability_call + tool_result present; evidence = exact tuple
        associated with tool_result.
      - all-None is INVALID (never represents unknown/DISABLED).
    """
    authorization_decision: AuthorizationDecision | None
    capability_call: CapabilityCall | None
    tool_result: ToolResult | None
    evidence: tuple[Evidence, ...]

    def __post_init__(self) -> None:
        """Enforce the valid artifact-combination invariants.

        Valid shapes (exactly one):
          - authorization-only: non-ALLOW decision, call/result = None,
            evidence = ().
          - executed: ALLOW decision, call + result present, matching
            capability_call_id, evidence exactly matching result.evidence_refs.

        All contradictory shapes fail closed.
        """
        decision = self.authorization_decision
        if decision is None:
            raise ValueError(
                "CapabilityExecution requires a non-None AuthorizationDecision; "
                "unknown/DISABLED pre-authorization resolution must not be represented here"
            )

        is_allow = (
            decision.decision == AuthorizationStatus.ALLOW
            or decision.decision == AuthorizationStatus.ALLOW.value
        )

        if not is_allow:
            if self.capability_call is not None:
                raise ValueError("non-ALLOW CapabilityExecution must not carry a CapabilityCall")
            if self.tool_result is not None:
                raise ValueError("non-ALLOW CapabilityExecution must not carry a ToolResult")
            if self.evidence:
                raise ValueError("non-ALLOW CapabilityExecution must not carry Evidence")
            return

        if self.capability_call is None:
            raise ValueError("ALLOW CapabilityExecution must carry a CapabilityCall")
        if self.tool_result is None:
            raise ValueError("ALLOW CapabilityExecution must carry a ToolResult")
        if self.tool_result.capability_call_id != self.capability_call.capability_call_id:
            raise ValueError(
                "ToolResult.capability_call_id must equal CapabilityCall.capability_call_id"
            )
        if tuple(e.evidence_id for e in self.evidence) != self.tool_result.evidence_refs:
            raise ValueError(
                "CapabilityExecution evidence must exactly match ToolResult.evidence_refs"
            )


class _PreAuthorizationResolutionError(Exception):
    """Manager-local: recognized capability hit pre-authorization unknown/DISABLED.

    Not a canonical lifecycle contract; used only so execute_typed() fails
    closed without fabricating an all-None CapabilityExecution.
    """


# ── Evidence Ledger (legacy compatibility view) ─────────────────────────────

class EvidenceLedger:
    """Compatibility audit ledger for legacy callers.

    Canonical cognition-supporting evidence is stored on CapabilityManager as
    ``canonical_evidence``. This ledger remains a read-compatible audit view for
    older tests/runtime code that expect CapabilityEvidence entries for success,
    denied, unavailable, and error outcomes.
    """

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

    Public compatibility contract:
        execute(request) -> CapabilityResult

    Canonical internal lifecycle:
        CapabilityRequest -> AuthorizationDecision -> CapabilityCall -> Provider
        -> ToolResult + Evidence
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
        self._authorization_decisions: list[AuthorizationDecision] = []
        self._capability_calls: list[CapabilityCall] = []
        self._tool_results: list[ToolResult] = []
        self._canonical_evidence: list[Evidence] = []

    # ── Canonical artifact inspection ────────────────────────────────────

    @property
    def authorization_decisions(self) -> list[AuthorizationDecision]:
        return list(self._authorization_decisions)

    @property
    def capability_calls(self) -> list[CapabilityCall]:
        return list(self._capability_calls)

    @property
    def tool_results(self) -> list[ToolResult]:
        return list(self._tool_results)

    @property
    def canonical_evidence(self) -> list[Evidence]:
        return list(self._canonical_evidence)

    # ── Execute ──────────────────────────────────────────────────────────

    async def execute(self, request: CapabilityRequest) -> CapabilityResult:
        """Legacy compatibility entry point.

        Recognized capabilities run through the single typed execution spine
        (_execute_recognized) and derive a legacy CapabilityResult from the
        exact canonical artifacts. Unknown/DISABLED pre-authorization paths
        preserve their existing legacy-only returns.
        """
        definition = self.registry.get(request.capability_name)
        if definition is None:
            return CapabilityResult.unknown(request.capability_name)
        if definition.status == CapabilityStatus.DISABLED:
            return CapabilityResult.denied(
                request.capability_name,
                f"Capability '{request.capability_name}' is DISABLED",
            )
        execution = await self._execute_recognized(request, definition)
        return self._legacy_from_execution(request, execution)

    async def execute_typed(self, request: CapabilityRequest) -> CapabilityExecution:
        """Typed execution entry point (P3.2.1).

        Returns one immutable CapabilityExecution carrying the exact canonical
        artifacts from this invocation. Pre-authorization unknown/DISABLED
        resolution has no canonical AuthorizationDecision and fails closed via
        _PreAuthorizationResolutionError (never an all-None bundle).
        """
        definition = self.registry.get(request.capability_name)
        if definition is None:
            raise _PreAuthorizationResolutionError(
                f"unknown capability '{request.capability_name}'"
            )
        if definition.status == CapabilityStatus.DISABLED:
            raise _PreAuthorizationResolutionError(
                f"capability '{request.capability_name}' is DISABLED"
            )
        return await self._execute_recognized(request, definition)

    async def _execute_recognized(
        self,
        request: CapabilityRequest,
        definition: CapabilityDefinition,
    ) -> CapabilityExecution:
        """Single typed execution spine for a recognized capability.

        ONE invocation executes the provider at most once. Canonical artifacts
        flow directly from this transaction into the returned carrier; no
        global/latest/list rediscovery.
        """
        start = _time.time()

        if definition.status == CapabilityStatus.DEGRADED:
            # DEGRADED means we attempt but record the risk.
            pass

        # Permission check
        decision = self.policy.check(definition.permission_scope)
        self._authorization_decisions.append(decision)
        if not self._is_authorized(decision):
            # Authorization denial/confirmation/elevation is not execution
            # failure. Provider health/execute must not be reached.
            self._record_legacy_evidence(definition, request, "denied")
            return CapabilityExecution(decision, None, None, ())

        # From this point onward, we have an authorized invocation attempt.
        call = self._start_call(definition, request)

        # Resolve provider
        provider = self._resolve_provider(definition)
        if provider is None:
            completed_call, result = self._finish_call_with_result(
                call,
                status=CapabilityCallStatus.FAILED,
                tool_status=ToolResultStatus.UNAVAILABLE,
                provider=definition.provider,
                started_at=call.started_at,
                error={
                    "code": "provider_not_found",
                    "message": f"No provider '{definition.provider}' registered",
                },
            )
            self._record_legacy_evidence(definition, request, "unavailable")
            return CapabilityExecution(decision, completed_call, result, ())

        # Provider health
        healthy, detail = await provider.health()
        if not healthy:
            completed_call, result = self._finish_call_with_result(
                call,
                status=CapabilityCallStatus.FAILED,
                tool_status=ToolResultStatus.UNAVAILABLE,
                provider=definition.provider,
                started_at=call.started_at,
                error={"code": "provider_unhealthy", "message": detail},
            )
            self._record_legacy_evidence(definition, request, "unavailable")
            return CapabilityExecution(decision, completed_call, result, ())

        # Execute
        executing_call = self._replace_call(call, status=CapabilityCallStatus.EXECUTING)
        try:
            data = await provider.execute(request)
            duration_ms = int((_time.time() - start) * 1000)
            evidence = self._record_canonical_observation_evidence(
                definition=definition,
                request=request,
                call=executing_call,
                data=data,
            )
            evidence_refs = (evidence.evidence_id,) if evidence is not None else ()
            completed_call, result = self._finish_call_with_result(
                executing_call,
                status=CapabilityCallStatus.COMPLETED,
                tool_status=ToolResultStatus.SUCCESS,
                provider=definition.provider,
                started_at=executing_call.started_at,
                structured_output=data,
                evidence_refs=evidence_refs,
                duration_ms=duration_ms,
                schema_version=definition.schema_version,
            )
            self._record_legacy_evidence(definition, request, "success")
            return CapabilityExecution(
                decision,
                completed_call,
                result,
                (evidence,) if evidence is not None else (),
            )
        except Exception as exc:
            completed_call, result = self._finish_call_with_result(
                executing_call,
                status=CapabilityCallStatus.FAILED,
                tool_status=ToolResultStatus.ERROR,
                provider=definition.provider,
                started_at=executing_call.started_at,
                error={"code": "provider_exception", "message": f"Provider '{definition.provider}' error: {exc}"},
                schema_version=definition.schema_version,
            )
            self._record_legacy_evidence(definition, request, "error")
            return CapabilityExecution(decision, completed_call, result, ())

    def _legacy_from_execution(self, request: CapabilityRequest, execution: CapabilityExecution) -> CapabilityResult:
        """Derive the legacy CapabilityResult from the typed execution carrier."""
        if execution.tool_result is None:
            assert execution.authorization_decision is not None
            return CapabilityResult.denied(request.capability_name, execution.authorization_decision.reason)
        return self._legacy_from_tool_result(request, execution.tool_result)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _resolve_provider(self, definition: CapabilityDefinition) -> Optional[CapabilityProvider]:
        """Find the provider for this capability."""
        return self.providers.get(definition.provider)

    @staticmethod
    def _is_authorized(decision: AuthorizationDecision) -> bool:
        return decision.decision == AuthorizationStatus.ALLOW or decision.decision == AuthorizationStatus.ALLOW.value

    def _start_call(self, definition: CapabilityDefinition, request: CapabilityRequest) -> CapabilityCall:
        call = CapabilityCall(
            capability_call_id=f"cap_call_{_time.time_ns()}",
            capability_request_id=request.capability_request_id,
            status=CapabilityCallStatus.AUTHORIZED,
            provider=definition.provider,
            correlation_id=request.correlation_id,
            provenance={
                "capability_id": request.capability_id,
                "permission_scope": definition.permission_scope,
                "schema_version": definition.schema_version,
            },
        )
        self._capability_calls.append(call)
        return call

    def _replace_call(self, call: CapabilityCall, *, status: CapabilityCallStatus, completed_at: str | None = None) -> CapabilityCall:
        updated = CapabilityCall(
            capability_call_id=call.capability_call_id,
            capability_request_id=call.capability_request_id,
            status=status,
            started_at=call.started_at,
            completed_at=completed_at,
            provider=call.provider,
            correlation_id=call.correlation_id,
            provenance=dict(call.provenance),
        )
        for i, existing in enumerate(self._capability_calls):
            if existing.capability_call_id == call.capability_call_id:
                self._capability_calls[i] = updated
                return updated
        raise ValueError(
            f"CapabilityCall '{call.capability_call_id}' not found for exact-ID replacement"
        )

    def _finish_call_with_result(
        self,
        call: CapabilityCall,
        *,
        status: CapabilityCallStatus,
        tool_status: ToolResultStatus,
        provider: str,
        started_at: str,
        structured_output: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
        evidence_refs: tuple[str, ...] = (),
        duration_ms: int = 0,
        schema_version: str = "1.0",
    ) -> tuple[CapabilityCall, ToolResult]:
        completed_at = _iso_timestamp()
        completed_call = self._replace_call(call, status=status, completed_at=completed_at)
        result = ToolResult(
            capability_call_id=completed_call.capability_call_id,
            status=tool_status,
            structured_output=dict(structured_output or {}),
            error=error,
            started_at=started_at,
            completed_at=completed_at,
            side_effect_state=SideEffectState.NONE,
            evidence_refs=evidence_refs,
            provider=provider,
            schema_version=schema_version,
        )
        self._tool_results.append(result)
        return completed_call, result

    def _record_canonical_observation_evidence(
        self,
        *,
        definition: CapabilityDefinition,
        request: CapabilityRequest,
        call: CapabilityCall,
        data: dict[str, Any],
    ) -> Evidence | None:
        """Create generic TOOL_OBSERVATION Evidence from actual provider data.

        The Manager records only that provider observation material exists. It
        does not interpret market/domain meaning and does not convert provider
        source_records into Julia domain Evidence; that belongs to later
        domain-specific mapping.
        """
        if not data:
            return None

        evidence = Evidence(
            evidence_id=f"ev_{_time.time_ns()}",
            source_type=EvidenceSourceType.TOOL_OBSERVATION,
            source_ref=f"capability:{definition.name}:provider:{definition.provider}",
            observed_at=_iso_timestamp(),
            content_ref=f"tool_result:{call.capability_call_id}:structured_output",
            provenance={
                "capability_request_id": request.capability_request_id,
                "capability_call_id": call.capability_call_id,
                "capability_id": request.capability_id,
                "provider": definition.provider,
                "schema_version": definition.schema_version,
                "provider_material_keys": sorted(data.keys()),
            },
            integrity_metadata={"material_type": "provider_structured_output"},
            freshness="unknown",
            confidence=1.0,
            correlation_id=request.correlation_id,
        )
        self._canonical_evidence.append(evidence)
        return evidence

    def _legacy_from_tool_result(self, request: CapabilityRequest, result: ToolResult) -> CapabilityResult:
        status = result.status.value if hasattr(result.status, "value") else str(result.status)
        error_message = ""
        if isinstance(result.error, dict):
            error_message = str(result.error.get("message", ""))

        if status == ToolResultStatus.SUCCESS.value:
            return CapabilityResult.success(
                name=request.capability_name,
                data=dict(result.structured_output),
                provider=result.provider,
                duration_ms=0,
                schema_version=result.schema_version,
            )
        if status == ToolResultStatus.UNAVAILABLE.value:
            return CapabilityResult.unavailable(request.capability_name, result.provider, error_message)
        if status == ToolResultStatus.ERROR.value:
            return CapabilityResult.error(request.capability_name, error_message)
        if status == ToolResultStatus.DENIED.value:
            return CapabilityResult.denied(request.capability_name, error_message)
        return CapabilityResult(
            capability_name=request.capability_name,
            status=status,
            data=dict(result.structured_output),
            provider=result.provider,
            error_message=error_message,
            schema_version=result.schema_version,
        )

    def _record_legacy_evidence(self, definition: CapabilityDefinition, request: CapabilityRequest, status: str):
        """Write legacy audit view entry for current callers/tests."""
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


def _iso_timestamp() -> str:
    return _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())


__all__ = ["CapabilityManager", "CapabilityExecution", "EvidenceLedger"]
