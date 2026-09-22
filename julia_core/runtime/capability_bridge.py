"""R0.2 Runtime Capability Bridge — unified facade over CapabilityManager.

This is the migration layer between the old runtime/capability.py and
the new capability/manager.py. It provides:

  1. Unified initialization: registry + policy + all providers
  2. Backward-compatible tool manifest for LLM context
  3. Backward-compatible tool execution for LLM tool calls
  4. Structured capability execution for Julia cognition selections

After full migration (R3), this becomes the sole capability interface.
The old runtime/capability.py is relegated to legacy compat.

ADR-026 P1: Runtime is Authority — the bridge is Runtime-owned.
ADR-026 P4: Provider supplies capability, not cognition.
"""

from __future__ import annotations

import json as _json
import re as _re
import threading as _threading
from dataclasses import dataclass
from dataclasses import replace
from typing import Optional

from julia_core.capability.manager import CapabilityExecution, CapabilityManager
from julia_core.capability.manager import ProviderAlreadyBoundError
from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityRequest,
    CapabilityStatus,
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)
from julia_core.capability.policy import PermissionPolicy
from julia_core.capability.registry import CapabilityRegistry
from julia_core.runtime.async_capability_runtime import AsyncCapabilityRuntime


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


@dataclass(frozen=True, slots=True)
class ToolCallDecodeFailure:
    """Bridge-local typed control outcome for an undecodable model call."""

    reason: str  # "MALFORMED_JSON" | "MISSING_NAME" | "INVALID_CALL_SHAPE"


class ProviderAlreadyRegisteredError(RuntimeError):
    """A different provider is already bound to a provider namespace."""


class _UnavailableProvider:
    """Explicitly-unavailable provider for a failed external binding.

    Not a fallback/mock: health() reports False and execute() returns an
    unavailable marker. The manager turns this into a typed
    ToolResult(UNAVAILABLE) — never a fake market result and never an
    alternate provider.
    """

    def __init__(self, reason: str):
        self.reason = reason

    async def health(self) -> tuple[bool, str]:
        return False, f"market provider unavailable: {self.reason}"

    async def execute(self, request) -> dict:
        return {"status": "unavailable", "error": self.reason}


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


class _ResearchProviderContractAdapter:
    """Validate the minimal source-bearing READ_ONLY Research evidence contract."""

    def __init__(self, provider: object):
        self._provider = provider

    async def health(self) -> tuple[bool, str]:
        return await self._provider.health()

    async def execute(self, request):
        outcome = await self._provider.execute(request)
        if isinstance(outcome, ProviderExecutionOutcome):
            if outcome.status not in (
                ToolResultStatus.SUCCESS,
                ToolResultStatus.PARTIAL,
            ):
                return replace(outcome, structured_output={})
            invalid_reason = self._invalid_evidence_reason(
                outcome.structured_output,
                request.arguments.get("query"),
            )
            if (
                invalid_reason is None
                and outcome.side_effect_state is SideEffectState.NONE
            ):
                return outcome
            if invalid_reason is None:
                invalid_reason = "READ_ONLY research evidence requires side_effect_state=NONE"
        elif isinstance(outcome, dict):
            declared_status = str(outcome.get("status", "")).strip().lower()
            non_evidence_failure = declared_status in {
                ToolResultStatus.UNAVAILABLE.value,
                ToolResultStatus.ERROR.value,
                ToolResultStatus.TIMEOUT.value,
                ToolResultStatus.CANCELLED.value,
            }
            if non_evidence_failure:
                error = outcome.get("error")
                return ProviderExecutionOutcome(
                    status=ToolResultStatus(declared_status),
                    structured_output={},
                    error=(
                        dict(error)
                        if isinstance(error, dict)
                        else {"code": declared_status, "message": str(error or declared_status)}
                    ),
                )
            invalid_reason = self._invalid_evidence_reason(
                outcome,
                request.arguments.get("query"),
            )
            if invalid_reason is None and self._legacy_side_effect_is_read_only(outcome):
                return outcome
            if invalid_reason is None:
                invalid_reason = (
                    "explicit legacy research side_effect_state must be none or absent"
                )
        else:
            return outcome

        return ProviderExecutionOutcome(
            status=ToolResultStatus.ERROR,
            structured_output={},
            error={
                "code": "research_contract_invalid",
                "message": f"research.web.query evidence contract invalid: {invalid_reason}",
            },
            side_effect_state=SideEffectState.UNKNOWN,
        )

    @staticmethod
    def _invalid_evidence_reason(output: object, requested_query: object) -> str | None:
        if not isinstance(output, dict):
            return "structured_output must be a mapping"
        if not isinstance(output.get("query"), str) or not output["query"].strip():
            return "query must be a non-empty string"
        if not isinstance(requested_query, str) or not requested_query.strip():
            return "request query must be a non-empty string"
        if output["query"].strip() != requested_query.strip():
            return "returned query must exactly match requested query"
        if not isinstance(output.get("findings"), list):
            return "findings must be a list"
        sources = output.get("sources")
        if not isinstance(sources, list) or not sources:
            return "sources must be a non-empty list"
        finding_binding_failure = _ResearchProviderContractAdapter._invalid_finding_binding_reason(
            output["findings"],
            sources,
        )
        if finding_binding_failure is not None:
            return finding_binding_failure
        if any(
            not isinstance(source, dict)
            or not (
                (isinstance(source.get("ref"), str) and source["ref"].strip())
                or (isinstance(source.get("url"), str) and source["url"].strip())
            )
            for source in sources
        ):
            return "every source must have a non-empty ref or url"
        if "limitations" not in output or not isinstance(output["limitations"], list):
            return "limitations must be present as a list"
        if not isinstance(output.get("provider"), str) or not output["provider"].strip():
            return "provider must be a non-empty string"
        if not isinstance(output.get("produced_at"), str) or not output["produced_at"].strip():
            return "produced_at must be non-empty"
        return None

    @staticmethod
    def _legacy_side_effect_is_read_only(output: dict) -> bool:
        declared_side_effect = output.get("side_effect_state")
        return declared_side_effect is None or (
            isinstance(declared_side_effect, str)
            and declared_side_effect.strip().lower() == SideEffectState.NONE.value
        )

    @staticmethod
    def _invalid_finding_binding_reason(findings: list, sources: list) -> str | None:
        declared_refs = {
            token
            for source in sources
            if isinstance(source, dict)
            for key in ("ref", "url")
            if isinstance(source.get(key), str) and source[key].strip()
            for token in (source[key],)
        }
        for finding in findings:
            if not isinstance(finding, dict):
                return "every finding must be a mapping"
            source_ref = finding.get("source_ref")
            source_refs = finding.get("source_refs")
            refs = []
            if "source_ref" in finding:
                if not isinstance(source_ref, str) or not source_ref.strip():
                    return "finding source_ref must be a non-empty string when present"
                refs.append(source_ref)
            if source_refs is not None:
                if not isinstance(source_refs, list) or not source_refs:
                    return "finding source_refs must be a non-empty list when present"
                if any(
                    not isinstance(ref, str) or not ref.strip() for ref in source_refs
                ):
                    return "finding source_refs entries must be non-empty strings"
                refs.extend(source_refs)
            if not refs:
                return "every finding must declare source_ref or non-empty source_refs"
            if any(ref not in declared_refs for ref in refs):
                return "every finding source reference must resolve to a declared source ref or url"
        return None


_MARKET_INPUT_SCHEMAS = {
    "market.event.resolve": {
        "feed_date": "optional YYYY-MM-DD event feed date",
        "stock_id": "optional exact source stock identifier",
        "limit": "maximum event count from 1 through 200",
    },
    "market.event.read": {
        "event_id": "integer news_event id; exactly one selector required",
        "item_id": "canonical source-namespaced event id; exactly one selector required",
    },
    "market.product.read": {"subject_key": "exact Market product subject key"},
    "market.product.linkage.read": {
        "subject_key": "exact Market product subject key",
        "mapping_scope": "pool, all, or leader_overlay",
        "include_leaders": "boolean leader overlay selector",
        "limit": "maximum linkage row count",
    },
    "market.state.read": {"trade_date": "exact YYYY-MM-DD trade date"},
    "market.stock.quote.read": {
        "stock_id": "exact source-namespaced stock identifier, for example 600519.SH",
        "trade_date": "exact YYYY-MM-DD trade date",
    },
}


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
        self.async_runtime = AsyncCapabilityRuntime()
        self._closing = False
        self._closed = False
        self._provider_lock = _threading.RLock()

    def register_provider(self, provider_name: str, provider: object) -> None:
        """Bind one product-owned implementation to a Core provider namespace.

        This is only an implementation binding. It registers no capability,
        grants no scope, changes no provider selection, and imports no product
        transport type. ``CapabilityDefinition.provider`` remains the sole
        selector and ``PermissionPolicy`` remains the sole authorization owner.

        Namespace check + Manager bind + bridge-map write are one atomic bridge
        operation so concurrent composition binders cannot both succeed.
        """
        if not isinstance(provider_name, str) or not provider_name:
            raise ValueError("provider_name must be a non-empty string")
        if not callable(getattr(provider, "execute", None)):
            raise TypeError("provider must implement execute(request)")
        if not callable(getattr(provider, "health", None)):
            raise TypeError("provider must implement health()")

        with self._provider_lock:
            if self._closing or self._closed:
                raise RuntimeError("runtime capability bridge is closing or closed")

            existing = self._providers.get(provider_name)
            if existing is not None and existing is not provider:
                raise ProviderAlreadyRegisteredError(
                    f"provider namespace '{provider_name}' is already bound"
                )
            if existing is provider:
                return

            if self._initialized and self._manager is not None:
                try:
                    self._manager.bind_provider(
                        provider_name,
                        self._provider_for_manager(provider_name, provider),
                    )
                except ProviderAlreadyBoundError as exc:
                    raise ProviderAlreadyRegisteredError(
                        f"manager provider namespace '{provider_name}' is already bound"
                    ) from exc
            self._providers[provider_name] = provider

    # ── Initialization ──────────────────────────────────────────────────

    def initialize(self):
        """Register all providers. Call once at session start."""
        with self._provider_lock:
            self._initialize_locked()

    def _initialize_locked(self):
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

        # Market is a generic provider namespace. The public Market provider is
        # bound by the application/runtime composition root; Core never imports
        # Market private code or manufactures an unavailable substitute.
        from julia_core.capability.providers.market_public import (
            market_public_supports_stock_quote,
        )

        try:
            stock_quote_supported = market_public_supports_stock_quote()
        except ImportError:
            stock_quote_supported = False

        market_capabilities = {
            "market.event.resolve": "Resolve structured Market event criteria",
            "market.event.read": "Read one structured Market event",
            "market.product.read": "Read one structured Market product",
            "market.product.linkage.read": "Read product-to-stock relationship evidence",
            "market.state.read": "Read exact-date whole-market state evidence",
        }
        if stock_quote_supported:
            market_capabilities["market.stock.quote.read"] = (
                "Read one exact stock/date daily quote"
            )

        for name, description in market_capabilities.items():
            self.registry.register_definition(CapabilityDefinition(
                name=name,
                description=description,
                layer=CapabilityLayer.INTELLIGENCE,
                provider="market",
                permission_scope="market.observe",
                input_schema=_MARKET_INPUT_SCHEMAS[name],
                status=CapabilityStatus.AVAILABLE,
            ))

        self.registry.register_definition(CapabilityDefinition(
            name="research.web.query",
            description="Query source-bearing external web research evidence",
            layer=CapabilityLayer.INTELLIGENCE,
            provider="research",
            permission_scope="research.observe",
            input_schema={"query": "research question"},
            status=CapabilityStatus.AVAILABLE,
        ))

        # External Code Review capability (Core semantic contract).
        # The provider (external_review) is implemented cross-repo in
        # Julia-AI-Assistant; Core registers only the CapabilityDefinition and
        # permission scope. Until that provider is bound, invocation returns a
        # typed UNAVAILABLE outcome (fail-closed, no fallback).
        from julia_core.review.registration import register_external_review_capability
        register_external_review_capability(self.registry, policy=self.policy)

        # Build the manager
        self._manager = CapabilityManager(
            self.registry,
            self.policy,
            self._flatten_providers(),
        )

        self._initialized = True


    @staticmethod
    def _provider_for_manager(provider_name: str, provider: object) -> object:
        if provider_name == "research":
            return _ResearchProviderContractAdapter(provider)
        return provider


    def _flatten_providers(self) -> dict:
        """Flatten nested provider dict into manager-compatible flat dict."""
        flat = {}
        for namespace, providers in self._providers.items():
            if isinstance(providers, dict):
                for name, provider in providers.items():
                    flat[f"{namespace}_{name}"] = provider
            else:
                flat[namespace] = providers
            if namespace == "research":
                flat[namespace] = _ResearchProviderContractAdapter(providers)
        # Override: ai_theme_app → flat key
        if "ai_theme_app" in self._providers and not isinstance(self._providers["ai_theme_app"], dict):
            flat["ai_theme_app"] = self._providers["ai_theme_app"]
        return flat

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
        for d in self.registry.by_provider("market"):
            lines.append(f'- {d.name}: {d.description}')
            if d.input_schema:
                params = ", ".join(f'"{k}": {v}' for k, v in d.input_schema.items())
                lines.append(f'  参数: {{{params}}}')

        # Research tools
        for d in self.registry.by_provider("research"):
            params = ", ".join(f'"{k}": {v}' for k, v in d.input_schema.items())
            lines.append(f'- {d.name}: {d.description}。参数: {{{params}}}')

        policy = self.invocation_policy()
        file_policy = policy["epistemic_rules"]["file"]
        external_policy = policy["epistemic_rules"]["external_evidence"]
        evidence_policy = policy["evidence_role"]
        limits = policy["limits"]

        lines.extend([
            "",
            "工具调用后会收到执行结果。基于结果回答，不要编造。",
            "",
            "[工具规则 — 必须遵守]",
            f"1. {file_policy['rule']}",
            f"2. {external_policy['rule']}",
            '3. 没有工具调用时，禁止说"我读了""我找到了""我搜索了"。',
            f"4. {evidence_policy['rule']}",
            "5. 文件不存在 → 直接告知用户，不猜测内容。",
            f"6. 工具调用格式: {policy['invocation_protocol']['format']}",
            f"7. {limits['rule']}",
        ])
        return "\n".join(lines)

    def invocation_policy(self) -> dict:
        """Return Core's structured model-visible capability invocation policy."""
        self.initialize()
        return {
            "invocation_protocol": {
                "format": "```tool_call\\n{JSON}\\n```",
                "structured_call_required": True,
                "raw_user_text_routing": False,
            },
            "epistemic_rules": {
                "file": {
                    "capability_prefix": "file.*",
                    "requires_explicit_user_intent": True,
                    "rule": "file.* 只有在Tony明确要求读取/搜索/列出文件时才可以调用。",
                },
                "external_evidence": {
                    "capability_prefixes": ["market.*", "research.*"],
                    "read_only": True,
                    "julia_may_request_when_evidence_missing": True,
                    "rule": "market.* / research.* 是READ_ONLY证据能力；当回答当前问题缺少外部证据时，Julia可以主动发起结构化调用。",
                },
            },
            "evidence_role": {
                "tool_result_is_evidence_not_final_judgment": True,
                "julia_second_pass_interpretation_required": True,
                "rule": "工具结果只是证据，不是最终判断；Julia必须在第二次思考中独立解读。",
            },
            "limits": {
                "max_tool_calls_per_model_response": 1,
                "rule": "一个回复最多一个工具调用。",
            },
        }

    def execute_tool_typed(
        self,
        tool_json: str,
    ) -> CapabilityExecution | CapabilityPreAuthorizationFailure | ToolCallDecodeFailure:
        """P3.2.2B typed delivery seam.

        Decodes the same tool-call JSON, normalizes legacy names, and delivers
        the exact CapabilityExecution from Manager for recognized, non-DISABLED
        capabilities. Returns a CapabilityPreAuthorizationFailure for
        UNKNOWN/DISABLED and ToolCallDecodeFailure for malformed input. Never flattens the
        carrier, never scans Manager lists, never selects latest artifacts.
        """
        self.initialize()

        try:
            call = _json.loads(tool_json)
        except (_json.JSONDecodeError, TypeError):
            return ToolCallDecodeFailure("MALFORMED_JSON")
        if not isinstance(call, dict):
            return ToolCallDecodeFailure("INVALID_CALL_SHAPE")
        if (
            "name" not in call
            or not isinstance(call["name"], str)
            or not call["name"].strip()
        ):
            return ToolCallDecodeFailure("MISSING_NAME")
        if "arguments" not in call or not isinstance(call["arguments"], dict):
            return ToolCallDecodeFailure("INVALID_CALL_SHAPE")
        try:
            name = call["name"]
            args = call.get("arguments", {})
        except (KeyError, TypeError):
            return ToolCallDecodeFailure("INVALID_CALL_SHAPE")

        # Map legacy tool names to new capability names
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

        # Deterministic pre-check against the audited immutable registry.
        definition = self.manager.registry.get(capability_id)
        if definition is None:
            return CapabilityPreAuthorizationFailure(capability_id, "UNKNOWN")
        if definition.status == CapabilityStatus.DISABLED:
            return CapabilityPreAuthorizationFailure(capability_id, "DISABLED")

        request = CapabilityRequest(
            capability_name=capability_id,
            arguments=args,
            reason=f"LLM tool call: {name}",
        )

        return self.async_runtime.run(lambda: self.manager.execute_typed(request))

    def close(self) -> None:
        """Close async providers and terminate the generic capability loop."""
        with self._provider_lock:
            if self._closed:
                return

            self._closing = True
            self.initialize()
            self.async_runtime.close(self._providers)
            self._closed = True

    # ── Evidence Gate (backward compat) ─────────────────────────────────

    _EXPLICIT_FILE_INTENT = _re.compile(
        r"(?:读取|读一下|打开|查看|看看|列出|搜索|找)"
        r"(?:一下|这个|该|下)?\s*"
        r"(?:文件|目录|日志|日记|README(?:\.md)?|源码)"
    )

    def requires_tool(self, user_text: str) -> bool:
        """Force retry only for explicit private-file intent."""
        stripped = user_text.strip()
        return bool(
            self._EXPLICIT_FILE_INTENT.search(stripped)
            or "/Users/" in stripped
            or "/tmp/" in stripped
            or stripped.startswith(("~/", "./"))
        )

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

# ── Singleton ───────────────────────────────────────────────────────────────

_bridge: Optional[RuntimeCapabilityBridge] = None

# Construction + initialize() must publish one fully initialized bridge.
# RLock keeps this safe if initialization ever reaches a helper that asks for
# the singleton again on the same thread.
_bridge_lock = _threading.RLock()


def get_capability_bridge() -> RuntimeCapabilityBridge:
    global _bridge
    with _bridge_lock:
        if _bridge is None:
            _bridge = RuntimeCapabilityBridge()
        _bridge.initialize()
        return _bridge
