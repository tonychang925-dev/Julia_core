"""R0.2 Runtime Capability Bridge — unified facade over CapabilityManager.

This is the migration layer between the old runtime/capability.py and
the new capability/manager.py. It provides:

  1. Unified initialization: registry + policy + all providers
  2. Backward-compatible tool manifest for LLM context
  3. Backward-compatible tool execution for LLM tool calls
  4. New intent-based capability resolution for workflow routing

After full migration (R3), this becomes the sole capability interface.
The old runtime/capability.py is relegated to legacy compat.

ADR-026 P1: Runtime is Authority — the bridge is Runtime-owned.
ADR-026 P4: Provider supplies capability, not cognition.
"""

from __future__ import annotations

import json as _json
import copy as _copy
import asyncio
import os
import threading
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from julia_core.capability.manager import CapabilityExecution, CapabilityManager
from julia_core.capability.manager import ProviderAlreadyBoundError
from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityRequest,
    CapabilityStatus,
    IdempotencySupport,
    SideEffectClass,
)
from julia_core.capability.policy import PermissionPolicy
from julia_core.capability.registry import CapabilityRegistry
from julia_core.research.registration import register_research_event_enrichment


# ── P3-CC I1a: composition-root canonical C-08 safety metadata ──────────────
# Construction configuration ONLY. This table is never consulted as execution
# authority after canonicalization; the final registered CapabilityDefinition
# in the single CapabilityRegistry is the canonical runtime source.

@dataclass(frozen=True, slots=True)
class _CanonicalCapabilityMetadata:
    """Explicit fail-closed C-08 metadata for one production definition."""
    side_effect_class: SideEffectClass
    data_sensitivity: str
    idempotency_support: IdempotencySupport = IdempotencySupport.NONE


_P3CC_CANONICAL_METADATA: dict[str, _CanonicalCapabilityMetadata] = {
    # Local filesystem (READ_ONLY reads).
    "file.read": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "local_user_files"),
    "file.search": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "local_user_files"),
    "file.list": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "local_user_files"),
    # Frozen Market executable surface + legacy ai_theme domain reads.
    "market.event.resolve": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "market_observe"),
    "market.event.read": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "market_observe"),
    "market.snapshot.read": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "market_observe"),
    "market.alert.query": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "market_observe"),
    "market.intelligence.observe": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "market_observe"),
    "market.decision.explain": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "market_observe"),
    "market.stock.history": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "market_observe"),
    "market.stock.auction": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "market_observe"),
    "market.theme.constituents": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "market_observe"),
    "market.theme.capital": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "market_observe"),
    "market.regime.read": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "market_observe"),
    # Controlled D1 external observation (read; no external mutation).
    "research.event.enrich": _CanonicalCapabilityMetadata(SideEffectClass.READ_ONLY, "external_research_observation"),
    # External review session submission (governed, manual ingress only).
    "engineering.code_review": _CanonicalCapabilityMetadata(SideEffectClass.EXTERNAL_SIDE_EFFECT, "engineering_code_review"),
}


def _canonicalized_definition(
    definition: CapabilityDefinition,
    metadata: _CanonicalCapabilityMetadata,
) -> CapabilityDefinition:
    """Re-register one definition with explicit C-08 metadata.

    Preserves every existing authority field (name, description, layer,
    provider, permission_scope, input_schema, adapter, status, schema_version)
    and any already-declared output_schema / latency hints. This is metadata
    convergence, not behavioral routing: provider selection, permission scope,
    administrative status, input schema, adapter, and availability are
    unchanged.
    """
    return CapabilityDefinition(
        name=definition.name,
        description=definition.description,
        layer=definition.layer,
        provider=definition.provider,
        permission_scope=definition.permission_scope,
        input_schema=dict(definition.input_schema),
        adapter=definition.adapter,
        status=definition.status,
        schema_version=definition.schema_version,
        output_schema=dict(definition.output_schema),
        side_effect_class=metadata.side_effect_class,
        idempotency_support=metadata.idempotency_support,
        latency_cost_hints=dict(definition.latency_cost_hints),
        data_sensitivity=metadata.data_sensitivity,
    )


@dataclass(frozen=True, slots=True)
class CapabilityPreAuthorizationFailure:
    """Bridge-local non-canonical transport/control signal.

    Distinguishes UNKNOWN / DISABLED pre-authorization resolution failure from
    malformed request-decoding failure (None) and from a recognized execution
    (CapabilityExecution). It is NOT a canonical lifecycle object and NOT an
    AuthorizationDecision / CapabilityResult / ToolResult / Evidence.
    """
    capability_id: str
    reason: str  # "UNKNOWN" | "DISABLED"


class ProviderAlreadyRegisteredError(RuntimeError):
    """A different provider is already bound to a provider namespace."""


class ProviderBindingRejectedError(RuntimeError):
    """A test/mock/fake implementation cannot bind in production composition.

    NCF-A7 A1-6 (S12): production composition rejects unauthorized, test, mock,
    fake, stub, or fixture providers. Test doubles may register only under an
    explicit test composition profile.
    """


class CapabilityBridgeAlreadyConfiguredError(RuntimeError):
    """A different canonical capability bridge is already installed."""


class CapabilityBridgeNotConfigured(RuntimeError):
    """A canonical capability bridge was requested before explicit configuration.

    NCF-A7 A1-3 (S6): an unconfigured getter is a typed NOT_CONFIGURED failure.
    The getter never auto-constructs the authority.
    """


class _UnavailableAiThemeProvider:
    """Explicitly-unavailable provider for failed ai_theme initialization.

    Not a fallback/mock: health() reports False and execute() returns an
    unavailable marker. The manager turns this into a typed
    ToolResult(UNAVAILABLE) — never a fake market result and never an
    alternate provider.
    """

    def __init__(self, reason: str):
        self.reason = reason

    async def health(self) -> tuple[bool, str]:
        return False, f"ai_theme_app provider unavailable: {self.reason}"

    async def execute(self, request) -> dict:
        return {"status": "unavailable", "error": self.reason}


_FAILURE_DIAGNOSTIC_FIELDS = frozenset({
    "operation_symbol",
    "failure_layer",
    "exception_class",
    "exception_message",
    "sqlstate",
    "pgcode",
    "errno",
    "error_code",
    "precollapse_provider_status",
    "process_pid",
    "observed_at",
    "resolver_query",
    "normalized_theme",
    "time_window",
    "correlation_id",
    "idempotency_id",
    "capability_request_id",
    "capability_call_id",
})
_MAX_FAILURE_DIAGNOSTIC_TEXT = 2048
_MAX_FAILURE_DIAGNOSTIC_ITEMS = 16


def _bounded_failure_diagnostic(value: Any, *, depth: int = 0) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        normalized = " ".join(value.split())
        if len(normalized) <= _MAX_FAILURE_DIAGNOSTIC_TEXT:
            return normalized
        return normalized[:_MAX_FAILURE_DIAGNOSTIC_TEXT - 3].rstrip() + "..."
    if depth >= 3:
        return str(value)[:_MAX_FAILURE_DIAGNOSTIC_TEXT]
    if isinstance(value, Mapping):
        return {
            str(key)[:128]: _bounded_failure_diagnostic(item, depth=depth + 1)
            for index, (key, item) in enumerate(value.items())
            if index < _MAX_FAILURE_DIAGNOSTIC_ITEMS
        }
    if isinstance(value, (list, tuple)):
        return [
            _bounded_failure_diagnostic(item, depth=depth + 1)
            for item in value[:_MAX_FAILURE_DIAGNOSTIC_ITEMS]
        ]
    return str(value)[:_MAX_FAILURE_DIAGNOSTIC_TEXT]


def _provider_failure_projection(tool_result: Any) -> dict[str, Any] | None:
    error = getattr(tool_result, "error", None)
    if not isinstance(error, Mapping):
        return None
    details = error.get("details", {})
    if not isinstance(details, Mapping):
        details = {}
    candidate_details = dict(details)
    pre_collapse_failure = details.get("pre_collapse_failure")
    if isinstance(pre_collapse_failure, Mapping):
        candidate_details.update(pre_collapse_failure)
    diagnostics = {
        name: _bounded_failure_diagnostic(_copy.deepcopy(candidate_details[name]))
        for name in sorted(_FAILURE_DIAGNOSTIC_FIELDS)
        if name in candidate_details
    }
    error_code = error.get("code")
    if not diagnostics and not isinstance(error_code, str):
        return None
    projection = {"diagnostics": diagnostics}
    if isinstance(error_code, str):
        projection["error_code"] = error_code
    return projection


class LocalProviderRouter:
    """Narrow local namespace dispatcher for file.* capabilities.

    This resolves the provider="local" namespace expected by CapabilityDefinition
    without adding semantic routing. Dispatch is deterministic and uses only the
    canonical capability_id from CapabilityRequest.
    """

    def __init__(self, providers: dict):
        self._providers = dict(providers)

    async def execute(self, request: CapabilityRequest) -> dict:
        provider = self._providers.get(request.capability_id)
        if provider is None:
            return {
                "status": "unavailable",
                "error": f"local provider for {request.capability_id} is not registered",
            }
        return await provider.execute(request)

    async def health(self) -> tuple[bool, str]:
        if not self._providers:
            return False, "local filesystem providers are not registered"
        return True, "local filesystem namespace — available"


class RuntimeCapabilityBridge:
    """Unified capability facade for JuliaSession.

    Initializes the full Capability Operating Layer:
      CapabilityRegistry + PermissionPolicy + all providers + CapabilityManager.

    Provides:
      — tool_manifest() for the LLM tool manifest
      — execute_tool_typed() for typed capability delivery
      — resolve() for intent-based capability resolution
    """

    def __init__(self):
        # Registry
        self.registry = CapabilityRegistry()

        # Policy
        self.policy = PermissionPolicy.with_defaults()

        # Providers — populated lazily on first use
        self._providers: dict = {}
        self._manager: Optional[CapabilityManager] = None
        self._initialized = False

    def register_provider(
        self,
        provider_name: str,
        provider: object,
        *,
        profile: str | None = None,
    ) -> None:
        """Bind one product-owned implementation to a Core provider namespace.

        This is only an implementation binding. It registers no capability,
        grants no scope, changes no provider selection, and imports no product
        transport type. ``CapabilityDefinition.provider`` remains the sole
        selector and ``PermissionPolicy`` remains the sole authorization owner.

        NCF-A7 A1-6 (S12): in the production composition profile a provider must
        carry production identity (a real imported implementation, not an
        inline/test/mock/fake class). Test doubles are rejected in production
        and may register only under an explicit ``profile="test"`` composition
        (pytest runs are auto-detected as test profile unless overridden).
        """
        if not isinstance(provider_name, str) or not provider_name:
            raise ValueError("provider_name must be a non-empty string")
        if not callable(getattr(provider, "execute", None)):
            raise TypeError("provider must implement execute(request)")
        if not callable(getattr(provider, "health", None)):
            raise TypeError("provider must implement health()")

        resolved_profile = self._resolve_composition_profile(profile)
        if resolved_profile == "production":
            self._validate_production_provider(provider)

        existing = self._providers.get(provider_name)
        if existing is not None and existing is not provider:
            raise ProviderAlreadyRegisteredError(
                f"provider namespace '{provider_name}' is already bound"
            )

        if self._initialized and self._manager is not None:
            try:
                self._manager.bind_provider(provider_name, provider)
            except ProviderAlreadyBoundError as exc:
                raise ProviderAlreadyRegisteredError(
                    f"manager provider namespace '{provider_name}' is already bound"
                ) from exc
        self._providers[provider_name] = provider

    # ── Composition profile / production binding proof ───────────────────

    @staticmethod
    def _resolve_composition_profile(profile: str | None) -> str:
        """Resolve the effective composition profile.

        Order: explicit argument > JULIA_COMPOSITION_PROFILE env > auto-detect
        (pytest => test) > production. Production is the fail-closed default.
        """
        if profile in ("production", "test"):
            return profile
        env_profile = os.environ.get("JULIA_COMPOSITION_PROFILE", "").strip().lower()
        if env_profile in ("production", "test"):
            return env_profile
        try:
            import sys as _sys
            if any("pytest" in name for name in _sys.modules) or "PYTEST_CURRENT_TEST" in os.environ:
                return "test"
        except Exception:
            pass
        return "production"

    @staticmethod
    def _validate_production_provider(provider: object) -> None:
        """Reject test/mock/fake/stub/fixture implementations in production.

        A production provider must be a real imported class (not an inline
        ``__main__`` class) whose name and defining module carry no test double
        markers. Rejection is a typed ProviderBindingRejectedError.
        """
        provider_cls = type(provider)
        class_name = provider_cls.__name__
        module_name = getattr(provider_cls, "__module__", "") or ""
        _markers = ("mock", "fake", "stub", "fixture", "dummy", "spy", "testdouble")

        lowered = class_name.lower()
        if any(marker in lowered for marker in _markers):
            raise ProviderBindingRejectedError(
                f"provider class '{class_name}' is a test/mock implementation; "
                "not bindable in production composition"
            )

        if module_name in ("", "__main__"):
            raise ProviderBindingRejectedError(
                f"provider class '{class_name}' is not a real imported "
                "implementation (module must not be __main__/empty) in production"
            )

        lowered_module = module_name.lower()
        if any(marker in lowered_module for marker in _markers) or module_name.startswith("tests."):
            raise ProviderBindingRejectedError(
                f"provider module '{module_name}' is a test/mock module; "
                "not bindable in production composition"
            )

        # Optional: verify the class actually imports from a real module file.
        import sys as _sys
        module = _sys.modules.get(module_name)
        module_file = getattr(module, "__file__", "") or ""
        if not module_file:
            raise ProviderBindingRejectedError(
                f"provider module '{module_name}' has no resolvable __file__; "
                "not a real production implementation"
            )

    # ── Initialization ──────────────────────────────────────────────────

    def initialize(self):
        """Register all providers. Call once at session start."""
        if self._initialized:
            return

        # Local providers (R0.1)
        from julia_core.capability.providers.local.file_read import FileReadProvider
        from julia_core.capability.providers.local.file_search import FileSearchProvider
        from julia_core.capability.providers.local.directory_list import DirectoryListProvider

        if "local" not in self._providers:
            self._providers["local"] = LocalProviderRouter({
                "file.read": FileReadProvider(),
                "file.search": FileSearchProvider(),
                "file.list": DirectoryListProvider(),
            })

        # Register local capabilities
        self.registry.register_definition(CapabilityDefinition(
            name="file.read",
            description="Read file contents from the local filesystem",
            layer=CapabilityLayer.KNOWLEDGE,
            provider="local",
            permission_scope="file.read",
            input_schema={"path": "file path"},
            status=CapabilityStatus.AVAILABLE,
        ))
        self.registry.register_definition(CapabilityDefinition(
            name="file.search",
            description="Search for files by name pattern",
            layer=CapabilityLayer.KNOWLEDGE,
            provider="local",
            permission_scope="file.read",
            input_schema={"pattern": "search pattern"},
            status=CapabilityStatus.AVAILABLE,
        ))
        self.registry.register_definition(CapabilityDefinition(
            name="file.list",
            description="List directory contents",
            layer=CapabilityLayer.KNOWLEDGE,
            provider="local",
            permission_scope="file.read",
            input_schema={"path": "directory path"},
            status=CapabilityStatus.AVAILABLE,
        ))

        # ai_theme_app provider (M1). Product-owned provider injection must not
        # suppress capability registration; definitions remain runtime-owned.
        #
        # NCF-A7 A1-1 (S3): a missing canonical Market provider must NOT trigger
        # automatic provider construction (no create_frozen_market_provider()
        # fallback, no _UnavailableAiThemeProvider substitute). Registration of
        # the capability definitions is retained so the manager yields a typed
        # UNAVAILABLE ("No provider ... registered") on invocation; the caller
        # that wants a real Market provider must bind it explicitly first via
        # register_canonical_market_provider()/register_provider().
        from julia_core.capability.providers.ai_theme.frozen_market import (
            register_frozen_market_capabilities,
        )
        if "ai_theme_app" in self._providers:
            from julia_core.capability.providers.ai_theme import (
                register_ai_theme_capabilities,
            )
            register_ai_theme_capabilities(
                self.registry,
                status=CapabilityStatus.AVAILABLE,
            )
        else:
            # Provider absent: register definitions as REGISTERED only. No
            # alternate implementation is constructed. Invocation resolves to a
            # typed unavailable through the manager, never synthetic truth.
            register_frozen_market_capabilities(
                self.registry,
                status=CapabilityStatus.REGISTERED,
            )

        # External Code Review capability (Core semantic contract).
        # The provider (external_review) is implemented cross-repo in
        # Julia-AI-Assistant; Core registers only the CapabilityDefinition and
        # permission scope. Until that provider is bound, invocation returns a
        # typed UNAVAILABLE outcome (fail-closed, no fallback).
        from julia_core.review.registration import register_external_review_capability
        register_external_review_capability(self.registry, policy=self.policy)

        # RD1-C1 research capability. Provider binding remains explicit and
        # product-owned; without a binding the manager returns typed UNAVAILABLE.
        register_research_event_enrichment(self.registry, policy=self.policy)
        if "research_enrichment" not in self._providers:
            from julia_core.research.d1_provider import (
                create_d1_research_provider_from_environment,
            )
            try:
                self._providers["research_enrichment"] = (
                    create_d1_research_provider_from_environment()
                )
            except Exception as exc:
                import logging
                logging.getLogger("julia.capability").debug(
                    "controlled-live D1 research provider unbound: %s", exc
                )

        # P3-CC I1a: composition-root pre-activation metadata canonicalization.
        # Every production-reachable definition must carry explicit C-08 safety
        # metadata BEFORE CapabilityManager construction (frozen D2 v0.5 /
        # D3 v0.6 G5 foundation). Any failure aborts initialization CLOSED —
        # no manager, no executable manifest, no silent omission, no fallback.
        self._canonicalize_production_metadata()

        # Build the manager
        self._manager = CapabilityManager(
            self.registry,
            self.policy,
            self._flatten_providers(),
        )

        self._initialized = True

    def _canonicalize_production_metadata(self) -> None:
        """Apply C-08 safety metadata before CapabilityManager construction.

        Runs strictly before CapabilityManager construction. The Core canonical
        metadata table is a migration source for Core-owned baseline
        definitions, NOT a global capability allowlist:

          CASE A  capability_id in the Core table
                  → re-register with canonical Core metadata (authority fields
                    preserved)
          CASE B  capability_id not in the table AND mandatory metadata already
                  explicit (side_effect_class is not None AND
                  data_sensitivity.strip() != "")
                  → PASS THROUGH unchanged (product-owned declarative metadata;
                    grants no permission/provider/model authority)
          CASE C  capability_id not in the table AND metadata incomplete
                  → FAIL CLOSED initialization

        After canonicalization the single registry object is canonical. No
        warning-and-continue, no dropped definitions, no permissive defaults,
        no fallback.
        """
        for definition in self.registry.all_definitions():
            metadata = _P3CC_CANONICAL_METADATA.get(definition.name)
            if metadata is not None:
                # CASE A — Core-owned baseline definition.
                self.registry.register_definition(
                    _canonicalized_definition(definition, metadata)
                )
            # CASE B — external explicit definition: preserve exactly (no-op).

        # Validate every final production definition (CASE C enforcement).
        unclassified_side_effect = [
            d.name
            for d in self.registry.all_definitions()
            if d.side_effect_class is None
        ]
        unclassified_sensitivity = [
            d.name
            for d in self.registry.all_definitions()
            if not str(d.data_sensitivity or "").strip()
        ]
        if unclassified_side_effect or unclassified_sensitivity:
            raise RuntimeError(
                "P3-CC metadata gate failed: "
                f"unclassified_side_effect={unclassified_side_effect} "
                f"unclassified_data_sensitivity={unclassified_sensitivity}"
            )

    def _flatten_providers(self) -> dict:
        """Flatten nested provider dict into manager-compatible flat dict."""
        flat = {}
        for namespace, providers in self._providers.items():
            if isinstance(providers, dict):
                for name, provider in providers.items():
                    flat[f"{namespace}_{name}"] = provider
            else:
                flat[namespace] = providers
        # Override: ai_theme_app → flat key
        if "ai_theme_app" in self._providers and not isinstance(self._providers["ai_theme_app"], dict):
            flat["ai_theme_app"] = self._providers["ai_theme_app"]
        return flat

    async def register_canonical_market_provider(
        self,
        *,
        environment: Mapping[str, str] | None = None,
        database_gateway: Any | None = None,
        retain_modules: bool = False,
    ) -> tuple[Any, Any]:
        """Compose and register the one DB-backed frozen Market provider."""
        from julia_core.capability.providers.ai_theme.frozen_market import (
            compose_frozen_market_provider,
            create_frozen_market_provider,
            frozen_market_database_gateways_bound,
        )

        if database_gateway is None:
            provider, gateway = await compose_frozen_market_provider(
                environment,
                retain_modules=retain_modules,
            )
        else:
            provider = create_frozen_market_provider(
                environment,
                database_gateway=database_gateway,
            )
            gateway = database_gateway
        if not frozen_market_database_gateways_bound(provider.adapter):
            raise ValueError("canonical Market provider has no initialized DatabaseGateway")
        self.register_provider("ai_theme_app", provider)
        return provider, gateway


    @property
    def manager(self) -> CapabilityManager:
        if not self._initialized:
            self.initialize()
        return self._manager

    # ── Backward Compat: LLM Tool Manifest ──────────────────────────────

    def tool_manifest(self) -> str:
        """Generate tool prompt for LLM context.

        Compatible with old self.capability.tools.build_manifest().
        Uses new registry as the canonical source.
        """
        self.initialize()

        lines = [
            "[你可以使用的工具 — 结构化调用格式]",
            "",
            '当需要时在回复中包含: ```tool_call',
            '{"name": "工具名", "arguments": {"参数": "值"}}',
            '```',
            "",
            "可用工具:",
        ]

        # Local tools
        for d in self.registry.by_provider("local"):
            params = ", ".join(f'"{k}": {v}' for k, v in d.input_schema.items())
            lines.append(f'- {d.name}: {d.description}。参数: {{{params}}}')

        # Market tools
        for d in self.registry.by_provider("ai_theme_app"):
            lines.append(f'- {d.name}: {d.description}')
            if d.input_schema:
                params = ", ".join(f'"{k}": {v}' for k, v in d.input_schema.items())
                lines.append(f'  参数: {{{params}}}')

        # RD1-C1 research capability. The provider namespace remains explicit;
        # no provider transport is selected by model-visible context.
        research = self.registry.get("research.event.enrich")
        if research is not None:
            params = ", ".join(f'"{k}": {v}' for k, v in research.input_schema.items())
            lines.append(f'- {research.name}: {research.description}。参数: {{{params}}}')

        lines.extend([
            "",
            "工具调用后会收到执行结果。基于结果回答，不要编造。",
            "",
            "[工具规则 — 必须遵守]",
            "1. 只有用户明确要求读取/搜索/列出时才使用工具。",
            '2. 没有工具调用时，禁止说"我读了""我找到了""我搜索了"。',
            "3. 文件不存在 → 直接告知用户，不猜测内容。",
            "4. 工具调用格式: ```tool_call\\n{JSON}\\n```",
            "5. 一个回复最多一个工具调用。",
        ])
        return "\n".join(lines)

    def execute_tool_typed(
        self,
        tool_json: str,
        *,
        turn_id: str = "",
        generation_id: str = "",
        correlation_id: str = "",
    ) -> CapabilityExecution | CapabilityPreAuthorizationFailure | None:
        """P3.2.2B typed delivery seam.

        Decodes the same tool-call JSON, normalizes legacy names, and delivers
        the exact CapabilityExecution from Manager for recognized, non-DISABLED
        capabilities. Returns a CapabilityPreAuthorizationFailure for
        UNKNOWN/DISABLED and None for malformed input. Never flattens the
        carrier, never scans Manager lists, never selects latest artifacts.
        """
        self.initialize()

        resolved = self._resolve_tool_request(
            tool_json,
            turn_id=turn_id,
            generation_id=generation_id,
            correlation_id=correlation_id,
        )
        if isinstance(resolved, (CapabilityPreAuthorizationFailure, type(None))):
            return resolved

        checked = self._precheck_request(resolved)
        if isinstance(checked, CapabilityPreAuthorizationFailure):
            self._emit_preauthorization_failure(checked, turn_id, generation_id, correlation_id)
            return checked
        return self._run_manager_sync(checked)

    async def execute_tool_typed_async(
        self,
        tool_json: str,
        *,
        turn_id: str = "",
        generation_id: str = "",
        correlation_id: str = "",
    ) -> CapabilityExecution | CapabilityPreAuthorizationFailure | None:
        """Await one governed model-requested capability in the caller's loop."""
        resolved = self._resolve_tool_request(
            tool_json,
            turn_id=turn_id,
            generation_id=generation_id,
            correlation_id=correlation_id,
        )
        if isinstance(resolved, (CapabilityPreAuthorizationFailure, type(None))):
            return resolved

        checked = self._precheck_request(resolved)
        if isinstance(checked, CapabilityPreAuthorizationFailure):
            self._emit_preauthorization_failure(checked, turn_id, generation_id, correlation_id)
            return checked
        return await self._execute_request_with_events(checked)

    async def execute_capability_request_async(
        self, request: CapabilityRequest
    ) -> CapabilityExecution | CapabilityPreAuthorizationFailure:
        """Await one already-built governed request without JSON re-encoding."""
        self.initialize()
        checked = self._precheck_request(request)
        if isinstance(checked, CapabilityPreAuthorizationFailure):
            self._emit_preauthorization_failure(
                checked,
                request.turn_id,
                request.generation_id,
                request.correlation_id,
            )
            return checked
        return await self._execute_request_with_events(checked)

    def _resolve_tool_request(
        self,
        tool_json: str,
        *,
        turn_id: str,
        generation_id: str,
        correlation_id: str,
    ) -> CapabilityRequest | CapabilityPreAuthorizationFailure | None:
        try:
            call = _json.loads(tool_json)
            name = call["name"]
            args = call.get("arguments", {})
        except (_json.JSONDecodeError, KeyError, TypeError):
            return None

        legacy_to_new = {
            "read_file": "file.read",
            "search_files": "file.search",
            "list_directory": "file.list",
        }
        capability_id = legacy_to_new.get(name, name)

        # PRE-P4 + External Review gate: the generic model tool-call path must
        # NEVER invoke engineering.code_review. External review is manual /
        # explicit operator-triggered ONLY; a model/generated tool-call cannot
        # grant itself that authority (A).
        if capability_id == "engineering.code_review":
            return CapabilityPreAuthorizationFailure(
                capability_id,
                "GOVERNED_INGRESS_REQUIRED",
            )

        if capability_id != "research.event.enrich":
            request = CapabilityRequest(
                capability_id=capability_id,
                arguments=args,
                reason=f"LLM tool call: {name}",
                turn_id=turn_id,
                generation_id=generation_id,
                correlation_id=correlation_id,
            )
            return request

        try:
            from julia_core.research.adapter import MarketEventResearchAdapter
            context = {"event": args["event"], "theme_relations": args["theme_relations"]}
            return MarketEventResearchAdapter().build_request(
                context,
                turn_id=turn_id,
                generation_id=generation_id,
                correlation_id=correlation_id,
            )
        except Exception:
            return CapabilityPreAuthorizationFailure(
                capability_id,
                "INVALID_MARKET_CONTEXT",
            )

    def _precheck_request(
        self, request: CapabilityRequest
    ) -> CapabilityRequest | CapabilityPreAuthorizationFailure:
        definition = self.manager.registry.get(request.capability_id)
        if definition is None:
            return CapabilityPreAuthorizationFailure(request.capability_id, "UNKNOWN")
        if definition.status == CapabilityStatus.DISABLED:
            return CapabilityPreAuthorizationFailure(request.capability_id, "DISABLED")
        return request

    @staticmethod
    def _emit_preauthorization_failure(
        failure: CapabilityPreAuthorizationFailure,
        turn_id: str,
        generation_id: str,
        correlation_id: str,
    ) -> None:
        from julia_core.events.models import EventCategory, create_event
        from julia_core.events.store import get_event_store

        get_event_store().append(create_event(
            source="runtime",
            event_type="capability.failed",
            category=EventCategory.CAPABILITY,
            payload={
                "capability_id": failure.capability_id,
                "reason": failure.reason,
                "turn_id": turn_id,
                "generation_id": generation_id,
            },
            correlation_id=correlation_id,
        ))

    def _run_manager_sync(self, request: CapabilityRequest) -> CapabilityExecution:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.manager.execute_typed(request))
                    return future.result(timeout=30)
            return asyncio.run(self.manager.execute_typed(request))
        except RuntimeError:
            return asyncio.run(self.manager.execute_typed(request))

    async def _execute_request_with_events(
        self, request: CapabilityRequest
    ) -> CapabilityExecution:
        import asyncio
        from julia_core.events.models import EventCategory, create_event
        from julia_core.events.store import get_event_store

        def emit(event_type: str, payload: dict) -> None:
            get_event_store().append(create_event(
                source="runtime",
                event_type=event_type,
                category=EventCategory.CAPABILITY,
                payload=payload,
                correlation_id=request.correlation_id,
            ))

        started_payload = {
            "capability_id": request.capability_id,
            "capability_request_id": request.capability_request_id,
            "turn_id": request.turn_id,
            "generation_id": request.generation_id,
            "idempotency_key": request.idempotency_key,
        }
        emit("capability.started", started_payload)
        try:
            execution = await self.manager.execute_typed(request)
        except asyncio.CancelledError:
            emit("capability.cancelled", dict(started_payload))
            raise
        except Exception:
            failed_payload = dict(started_payload)
            failed_payload["reason"] = "manager_execution_exception"
            emit("capability.failed", failed_payload)
            raise

        completed_payload = dict(started_payload)
        if execution.capability_call is not None:
            completed_payload["capability_call_id"] = execution.capability_call.capability_call_id
        if execution.tool_result is not None:
            completed_payload["status"] = execution.tool_result.status.value
            completed_payload["evidence_refs"] = list(execution.tool_result.evidence_refs)
            provider_failure = _provider_failure_projection(execution.tool_result)
            if provider_failure is not None:
                completed_payload["provider_failure"] = provider_failure
        outcome_status = str(completed_payload.get("status", "failed"))
        emit(
            "capability.completed" if outcome_status in ("success", "partial") else "capability.failed",
            completed_payload,
        )
        return execution

    # ── Evidence Gate (backward compat) ─────────────────────────────────

    def requires_tool(self, user_text: str) -> bool:
        """Check if user question needs external evidence (file/market read).

        Backward compatible with old runtime/capability.py requires_tool().
        """
        lower = user_text.lower()

        # Market intent — needs capability
        market_triggers = [
            "今天市场", "市场怎么样", "大盘怎么看", "市场状态",
            "今天行情", "市场情况", "盘面", "最近什么方向",
            "风险", "警报", "预警",
        ]
        for kw in market_triggers:
            if kw in user_text:
                return True

        # File access triggers
        file_triggers = [
            "读一下", "读取", "打开", "看看文件", "帮我看看", "查看文件",
            "列出目录", "有什么文件", "搜索一下", "找一下",
            "最新日志", "日记", "昨天的", "代码", "README", "源码",
        ]
        for kw in file_triggers:
            if kw in user_text:
                return True

        # File paths
        if "/Users/" in user_text or "/tmp/" in user_text:
            return True

        return False

    def detect_tool_call(self, text: str) -> Optional[str]:
        """Detect structured tool_call block in LLM output.

        Backward compatible with old _detect_tool_call().
        """
        import re
        m = re.search(r'```tool_call\s*\n(.*?)\n```', text, re.DOTALL)
        if m:
            return m.group(1).strip()
        m = re.search(r'TOOL:\s*(\w+)\(([^)]+)\)', text)
        if m:
            name, raw = m.group(1), m.group(2)
            kv = re.match(r'(\w+)\s*=\s*"([^"]+)"', raw)
            if kv:
                return _json.dumps({"name": name, "arguments": {kv.group(1): kv.group(2)}})
            val = raw.strip().strip('"').strip("'")
            key = "path" if name in ("read_file", "list_directory") else "pattern"
            return _json.dumps({"name": name, "arguments": {key: val}})
        return None

    # ── New Path: Intent-based Capability Resolution ─────────────────────

    async def resolve_market_intent(self, user_text: str, session_id: str = None):
        """Resolve market intent through MarketBriefPipeline.

        This is the R0.3 integration point — called by WorkflowRouter.
        """
        from julia_core.reasoning.market_brief_pipeline import MarketBriefPipeline
        pipeline = MarketBriefPipeline(self.manager)
        return await pipeline.process(user_text, session_id)


# ── Singleton ───────────────────────────────────────────────────────────────

_bridge: Optional[RuntimeCapabilityBridge] = None
_bridge_lock = threading.Lock()


def configure_capability_bridge(bridge: RuntimeCapabilityBridge) -> RuntimeCapabilityBridge:
    """Install one explicitly composed bridge as the process canonical bridge.

    The caller constructs the bridge and registers product-owned providers before
    calling this function. Exact-object reconfiguration is idempotent; replacing
    a live bridge with a different object fails closed.
    """
    if not isinstance(bridge, RuntimeCapabilityBridge):
        raise TypeError("bridge must be a RuntimeCapabilityBridge")

    global _bridge
    with _bridge_lock:
        if _bridge is not None and _bridge is not bridge:
            raise CapabilityBridgeAlreadyConfiguredError(
                "a canonical capability bridge is already configured"
            )
        if not bridge._initialized:
            bridge.initialize()
        _bridge = bridge
        return _bridge


def get_capability_bridge() -> RuntimeCapabilityBridge:
    global _bridge
    with _bridge_lock:
        if _bridge is None:
            # NCF-A7 A1-3 (S6): an unconfigured getter must NOT auto-construct
            # the authority. The composition root must explicitly build and
            # install the bridge via configure_capability_bridge().
            raise CapabilityBridgeNotConfigured(
                "no canonical capability bridge is configured; "
                "compose and call configure_capability_bridge(bridge) first"
            )
        return _bridge


def _reset_capability_bridge() -> None:
    """Test-support only: clear the process-local canonical bridge.

    Production never calls this; it exists so tests that compose a bridge for
    JuliaSession can restore process state between cases.
    """
    global _bridge
    with _bridge_lock:
        _bridge = None


async def run_controlled_brain(port: int = 18090) -> None:
    """Run 18090 only after explicit DB-backed Market composition."""
    import sys
    from pathlib import Path

    source_root = Path(os.environ["JULIA_MARKET_SOURCE_ROOT"]).expanduser().resolve(strict=True)
    preloaded_market_modules = sorted(
        name for name in sys.modules
        if name == "stock_processing_service" or name.startswith("stock_processing_service.")
    )
    preloaded_db_modules = sorted(
        name for name in sys.modules
        if name == "database_service" or name.startswith("database_service.")
    )

    bridge = RuntimeCapabilityBridge()
    provider, gateway = await bridge.register_canonical_market_provider(retain_modules=True)
    bridge.initialize()
    configured_bridge = configure_capability_bridge(bridge)
    resolve_operation = provider.adapter._operations["market.event.resolve"]
    read_operation = provider.adapter._operations["market.event.read"]
    provider_health = await provider.health()
    gateway_health = await gateway.health_check()

    identity_ok = all((
        configured_bridge is bridge,
        bridge.manager.providers["ai_theme_app"] is provider,
        resolve_operation._database_gateway is gateway,
        read_operation._database_gateway is gateway,
        provider.source_sha == os.environ["JULIA_MARKET_SOURCE_SHA"],
        provider_health[0] is True,
        gateway_health is True,
        bridge.registry.get("market.event.resolve").status.value == "available",
        bridge.registry.get("market.event.read").status.value == "available",
    ))
    if not identity_ok:
        await gateway.close()
        raise RuntimeError("controlled Market composition identity/readiness failed")

    def pinned_module_path(module_name: str) -> Path:
        parts = module_name.split(".")
        module_path = source_root.joinpath(*parts).with_suffix(".py")
        package_path = source_root.joinpath(*parts, "__init__.py")
        if module_path.is_file():
            return module_path.resolve()
        if package_path.is_file():
            return package_path.resolve()
        raise RuntimeError(f"pinned Market module path unavailable: {module_name}")

    adapter_path = pinned_module_path(type(provider.adapter).__module__)
    event_resolve_path = pinned_module_path(type(resolve_operation).__module__)
    event_read_path = pinned_module_path(type(read_operation).__module__)
    db_module_paths = {
        name: str(Path(module.__file__).resolve())
        for name, module in sys.modules.items()
        if (name == "database_service" or name.startswith("database_service."))
        and getattr(module, "__file__", None)
    }
    module_paths_ok = all(
        path.is_relative_to(source_root)
        for path in (adapter_path, event_resolve_path, event_read_path, *map(Path, db_module_paths.values()))
    )
    if not module_paths_ok:
        await gateway.close()
        raise RuntimeError("controlled Market/DB module provenance escaped the pinned source root")

    postgres_manager_path = Path(sys.modules["database_service.managers.postgres_manager"].__file__).resolve()
    postgres_manager_source = postgres_manager_path.read_text(encoding="utf-8")
    event_resolve_source = event_resolve_path.read_text(encoding="utf-8")

    legacy_path = os.environ.get("JULIA_LEGACY_CONVERSATION_PATH")
    if not legacy_path:
        await gateway.close()
        raise RuntimeError("JULIA_LEGACY_CONVERSATION_PATH is required for controlled Brain")
    from private_data.wiring import wire_legacy_composition
    wire_legacy_composition(legacy_repo_path=legacy_path)

    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from voice_api.routes import router
    from voice_api.openai_compat import router as openai_router
    from voice_api.conversation_routes import router as conversation_router
    from voice_api.conversation_management import router as conversation_router_management
    import uvicorn

    app = FastAPI(title="Julia Voice API", version="1.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(router)
    app.include_router(openai_router)
    app.include_router(conversation_router)
    app.include_router(conversation_router_management)

    attestation = {
        "composition_version": "r9-d2c",
        "market_source_root": str(source_root),
        "market_source_sha": provider.source_sha,
        "adapter_tree_digest": os.environ["JULIA_MARKET_TREE_DIGEST"],
        "db_runtime_tree_digest": os.environ["JULIA_MARKET_DB_RUNTIME_DIGEST"],
        "preloaded_market_module_count": len(preloaded_market_modules),
        "preloaded_db_module_count": len(preloaded_db_modules),
        "bridge_identity": id(bridge),
        "provider_identity": id(provider),
        "gateway_identity": id(gateway),
        "manager_provider_identity_pass": bridge.manager.providers["ai_theme_app"] is provider,
        "resolver_gateway_identity_pass": resolve_operation._database_gateway is gateway,
        "reader_gateway_identity_pass": read_operation._database_gateway is gateway,
        "gateway_initialized": gateway._initialized is True,
        "gateway_select_1": gateway_health is True,
        "provider_health": list(provider_health),
        "market_event_resolve_status": bridge.registry.get("market.event.resolve").status.value,
        "market_event_read_status": bridge.registry.get("market.event.read").status.value,
        "adapter_path": str(adapter_path),
        "stock_processing_service_path": str(source_root / "stock_processing_service/__init__.py"),
        "event_resolve_path": str(event_resolve_path),
        "event_read_path": str(event_read_path),
        "database_gateway_path": str(Path(sys.modules["database_service.gateway"].__file__).resolve()),
        "postgres_manager_path": str(postgres_manager_path),
        "db_module_paths": db_module_paths,
        "all_market_modules_from_pinned_root": True,
        "r9_f1_observability_present": all(token in event_resolve_source for token in (
            "operation_symbol", "failure_layer", "exception_class", "exception_message", "sqlstate",
            "pgcode", "process_pid", "resolver_query", "correlation_id", "idempotency_id",
        )),
        "r9_f1a_closure_present": all(token in event_resolve_source for token in (
            "redact_diagnostics", "_bounded_text", "precollapse_provider_status",
        )),
        "d2b_data_conversion_present": all(token in postgres_manager_source for token in (
            "def _decode_json_array", "json.loads(value)",
            'candidate["matched_subjects"] = _decode_json_array',
        )),
        "d2b_post_resolve_observability_present": all(token in event_resolve_source for token in (
            "CANDIDATE_FAILURE_LAYER", "candidate_index", "raw_candidate_count",
            "matched_subjects_type", "pre_collapse_failure",
        )),
        "trace_source_sha": provider.source_sha,
        "filesystem_has_git": (source_root / ".git").exists(),
        "user_turns": 0,
        "real_resolver_executions": 0,
        "d1_executions": 0,
        "market_event_read_executions": 0,
        "db_writes": 0,
    }
    attestation_path = Path(os.environ.get(
        "JULIA_CONTROLLED_COMPOSITION_ATTESTATION",
        f"/tmp/julia-controlled-composition-{os.getpid()}.json",
    ))
    attestation_path.parent.mkdir(parents=True, exist_ok=True)
    attestation_path.write_text(_json.dumps(attestation, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    server = uvicorn.Server(uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
    ))
    try:
        await server.serve()
    finally:
        await gateway.close()
