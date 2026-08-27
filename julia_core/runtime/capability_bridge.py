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
from typing import Optional

from julia_core.capability.manager import CapabilityManager
from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityRequest,
    CapabilityStatus,
)
from julia_core.capability.policy import PermissionPolicy
from julia_core.capability.registry import CapabilityRegistry


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

    Provides both:
      — Backward compat: tool_manifest() + execute_tool() for LLM tool calls
      — New path: resolve() for intent-based capability resolution
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

    # ── Initialization ──────────────────────────────────────────────────

    def initialize(self):
        """Register all providers. Call once at session start."""
        if self._initialized:
            return

        # Local providers (R0.1)
        from julia_core.capability.providers.local.file_read import FileReadProvider
        from julia_core.capability.providers.local.file_search import FileSearchProvider
        from julia_core.capability.providers.local.directory_list import DirectoryListProvider

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

        # ai_theme_app provider (M1) — only if not already injected (tests)
        if "ai_theme_app" not in self._providers:
            try:
                from julia_core.capability.providers.ai_theme import (
                    register_ai_theme_capabilities,
                    create_ai_theme_provider,
                )
                register_ai_theme_capabilities(self.registry)
                self._providers["ai_theme_app"] = create_ai_theme_provider()
            except Exception:
                import logging; logging.getLogger("julia.failclosed").warning("silent fallback removed at julia_core.julia_core.runtime.capability_bridge:113", exc_info=True)

        # Build the manager
        self._manager = CapabilityManager(
            self.registry,
            self.policy,
            self._flatten_providers(),
        )

        self._initialized = True

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

        lines.extend([
            "",
            "工具调用后会收到 ```tool_result``` 块。基于结果回答，不要编造。",
            "",
            "[工具规则 — 必须遵守]",
            "1. 只有用户明确要求读取/搜索/列出时才使用工具。",
            '2. 没有工具调用时，禁止说"我读了""我找到了""我搜索了"。',
            "3. 文件不存在 → 直接告知用户，不猜测内容。",
            "4. 工具调用格式: ```tool_call\\n{JSON}\\n```",
            "5. 一个回复最多一个工具调用。",
        ])
        return "\n".join(lines)

    # ── Backward Compat: LLM Tool Execution ─────────────────────────────

    def execute_tool(self, tool_json: str) -> Optional[str]:
        """Execute a tool call from LLM output. Backward compatible with
        old self.capability.execute().

        Routes through CapabilityManager for permission + evidence.
        """
        self.initialize()

        try:
            call = _json.loads(tool_json)
            name = call["name"]
            args = call.get("arguments", {})
        except (_json.JSONDecodeError, KeyError):
            return None

        # Map legacy tool names to new capability names
        legacy_to_new = {
            "read_file": "file.read",
            "search_files": "file.search",
            "list_directory": "file.list",
        }
        capability_name = legacy_to_new.get(name, name)

        # Build request
        request = CapabilityRequest(
            capability_name=capability_name,
            arguments=args,
            reason=f"LLM tool call: {name}",
        )

        # Execute through manager (sync wrapper around async)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In event loop: create task (simplified — returns result)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.manager.execute(request))
                    result = future.result(timeout=30)
            else:
                result = asyncio.run(self.manager.execute(request))
        except RuntimeError:
            result = asyncio.run(self.manager.execute(request))

        # Format result for LLM
        return self._format_tool_result(result)

    def _format_tool_result(self, result) -> str:
        """Format CapabilityResult as tool_result block for LLM."""
        data = result.data if hasattr(result, 'data') else {}
        status = result.status if hasattr(result, 'status') else "unknown"

        meta = _json.dumps({
            "tool": result.capability_name if hasattr(result, 'capability_name') else "?",
            "status": status,
            "provider": result.provider if hasattr(result, 'provider') else "",
        }, ensure_ascii=False)

        content = ""
        if isinstance(data, dict):
            if "content" in data:
                content = data["content"]
            elif "items" in data:
                content = "\n".join(data["items"])
            elif "matches" in data:
                content = "\n".join(data["matches"])
            elif "error" in data:
                content = data["error"]
            else:
                content = _json.dumps(data, ensure_ascii=False, indent=2)

        return f"```tool_result\n{meta}\n{content}\n```"

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


def get_capability_bridge() -> RuntimeCapabilityBridge:
    global _bridge
    if _bridge is None:
        _bridge = RuntimeCapabilityBridge()
        _bridge.initialize()
    return _bridge
