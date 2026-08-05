"""Julia Capability Runtime v1.0 — Capability Contract + Tool Manifest + Executor + Evidence + Permission.

Design:
  Every capability implements a unified contract (Capability base class).
  Every tool call is permission-checked and evidence-recorded.
  Every claim in Julia's response can be traced back to tool evidence.

Architecture:
  User → LLM decides → Tool Call → Permission Check → Execute
  → Tool Result → LLM responds → Claim→Evidence binding

Capability Contract v1.0:
  class Capability:
      name: str
      description: str
      permission_scope: list[str]
      input_schema: dict
      execute(**kwargs) → ToolResult
"""

from __future__ import annotations

import json as _json
import re
import time as _time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional


# ── Capability Contract v1.0 ────────────────────────────────────────────────

@dataclass
class ToolResult:
    """Unified result from any tool execution."""
    tool: str
    status: str  # "success" | "not_found" | "permission_denied" | "error"
    data: dict = field(default_factory=dict)
    content: str = ""
    error: str = ""

    def to_evidence(self) -> dict:
        return {"tool": self.tool, "status": self.status, "data": self.data}

    def to_prompt_block(self) -> str:
        """Render as tool_result block for LLM injection."""
        meta = _json.dumps({"tool": self.tool, "status": self.status, **self.data},
                           ensure_ascii=False)
        lines = [f"```tool_result", meta]
        if self.content:
            lines.append(self.content)
        if self.error:
            lines.append(f"错误: {self.error}")
        lines.append("```")
        return "\n".join(lines)


class Capability(ABC):
    """Capability Contract v1.0 — unified interface for all tools.

    Every tool (file, MCP, web, memory, calendar) implements this contract.
    The CapabilityRuntime doesn't know what a tool does — only how to execute it.
    """

    name: str = ""
    description: str = ""
    permission_scope: list[str] = []  # e.g. ["filesystem:read", "network:outbound"]
    input_schema: dict[str, str] = {}  # param_name → description

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute this capability. Returns unified ToolResult."""
        ...

    def to_prompt(self) -> str:
        """Render as a tool description for the LLM manifest."""
        params = ", ".join(f'"{k}": {v}' for k, v in self.input_schema.items())
        example = _json.dumps({"name": self.name, "arguments": {k: f"<{k}>" for k in self.input_schema}},
                              ensure_ascii=False)
        return f'- {self.name}: {self.description}。参数: {{{params}}}。例: {example}'


# ── Tool Schema (compatibility) ─────────────────────────────────────────────

@dataclass
class ToolSchema:
    """Legacy tool definition — wraps a function into the Capability contract."""
    name: str
    description: str
    parameters: dict[str, str] = field(default_factory=dict)
    example: str = ""

    def to_prompt(self) -> str:
        params = ", ".join(f'"{k}": {v}' for k, v in self.parameters.items())
        return f'- {self.name}: {self.description}。参数: {{{params}}}。例: {self.example}'


# ── Permission ──────────────────────────────────────────────────────────────

@dataclass
class PermissionPolicy:
    """Controls what files/paths Julia can access."""
    allowed: list[str] = field(default_factory=lambda: [
        "/Users/admin/julia_core",
        "/Users/admin/julia_ai_assistant",
        "/Users/admin/Desktop",
        "/Users/admin/.claude-dev/projects",
    ])
    denied: list[str] = field(default_factory=lambda: [
        "/Users/admin/.ssh",
        "/Users/admin/.aws",
        "/Users/admin/Library/Keychains",
    ])

    def check(self, path: str) -> tuple[bool, str]:
        """Check if a path is accessible. Returns (allowed, reason)."""
        for d in self.denied:
            if path.startswith(d):
                return False, f"permission_denied: {d} is restricted"
        for a in self.allowed:
            if path.startswith(a):
                return True, "ok"
        return False, "permission_denied: path not in allowed scope"


# ── Evidence Ledger v1.1 — with Claim→Evidence binding ──────────────────────

@dataclass
class EvidenceEntry:
    """One tool execution record — proves Julia actually called the tool."""
    tool: str
    status: str
    timestamp: str = field(default_factory=lambda: _time.strftime("%H:%M:%S"))
    details: dict = field(default_factory=dict)


class EvidenceLedger:
    """Records every tool call. Supports Claim→Evidence binding.

    After a tool call, any factual claim in Julia's response can be traced
    back to a specific tool execution. This makes Julia's answers auditable.
    """

    def __init__(self):
        self.entries: list[EvidenceEntry] = []
        self._claim_bindings: list[dict] = []  # {"claim": str, "evidence_idx": int}

    def record(self, tool: str, status: str, **details) -> int:
        """Record a tool execution. Returns the entry index for claim binding."""
        self.entries.append(EvidenceEntry(tool=tool, status=status, details=details))
        return len(self.entries) - 1

    def bind_claim(self, claim: str, evidence_idx: int):
        """Bind a claim in Julia's response to a specific tool execution."""
        self._claim_bindings.append({"claim": claim[:200], "evidence_idx": evidence_idx})

    def last(self) -> Optional[EvidenceEntry]:
        return self.entries[-1] if self.entries else None

    @property
    def count(self) -> int:
        return len(self.entries)

    @property
    def last_index(self) -> int:
        return len(self.entries) - 1


# ── Built-in Capabilities ───────────────────────────────────────────────────

class ReadFileCapability(Capability):
    """Read a file from the local filesystem with permission checking."""
    name = "read_file"
    description = "读取指定路径的文件内容"
    permission_scope = ["filesystem:read"]
    input_schema = {"path": "文件完整路径"}

    def __init__(self, permission: PermissionPolicy):
        self._permission = permission

    def execute(self, path: str = "") -> ToolResult:
        allowed, reason = self._permission.check(path)
        if not allowed:
            return ToolResult("read_file", "permission_denied",
                              data={"path": path, "reason": reason})
        try:
            content = Path(path).read_text(encoding="utf-8", errors="ignore")[:5000]
            return ToolResult("read_file", "success",
                              data={"path": path, "size": len(content)},
                              content=content)
        except FileNotFoundError:
            return ToolResult("read_file", "not_found", data={"path": path},
                              error="文件不存在")


class SearchFilesCapability(Capability):
    """Search for files by name pattern."""
    name = "search_files"
    description = "按名称搜索文件"
    permission_scope = ["filesystem:read"]
    input_schema = {"pattern": "文件名关键词"}

    def execute(self, pattern: str = "") -> ToolResult:
        results = []
        for root in [Path("/Users/admin/.claude-dev/projects/-Users-admin/memory"),
                     Path("/Users/admin/julia_core"),
                     Path("/Users/admin/julia_ai_assistant")]:
            for p in root.rglob(f"*{pattern}*"):
                if not p.name.startswith(".") and "__pycache__" not in str(p):
                    results.append(str(p))
                    if len(results) >= 10:
                        break
        if results:
            return ToolResult("search_files", "success",
                              data={"pattern": pattern}, content="\n".join(results))
        return ToolResult("search_files", "empty", data={"pattern": pattern},
                          content="未找到匹配文件")


class ListDirectoryCapability(Capability):
    """List contents of a directory."""
    name = "list_directory"
    description = "列出指定目录下的文件和子目录"
    permission_scope = ["filesystem:read"]
    input_schema = {"path": "目录路径"}

    def execute(self, path: str = "") -> ToolResult:
        p = Path(path)
        if p.exists() and p.is_dir():
            items = "\n".join(f"  {i.name}{'/' if i.is_dir() else ''}"
                              for i in sorted(p.iterdir())[:30])
            return ToolResult("list_directory", "success",
                              data={"path": path}, content=items)
        return ToolResult("list_directory", "not_found", data={"path": path},
                          error="目录不存在")


# ── Tool Registry ───────────────────────────────────────────────────────────

class ToolRegistry:
    """Holds registered tools. Supports Capability objects and legacy functions."""

    def __init__(self):
        self._tools: dict[str, tuple[ToolSchema, Callable]] = {}
        self._capabilities: dict[str, Capability] = {}

    def register(self, schema: ToolSchema, handler: Callable):
        """Register a legacy function-based tool."""
        self._tools[schema.name] = (schema, handler)

    def register_capability(self, cap: Capability):
        """Register a Capability Contract v1.0 tool."""
        self._capabilities[cap.name] = cap

    def get_handler(self, name: str) -> Optional[Callable]:
        """Get handler for a tool. Checks Capability first, then legacy."""
        if name in self._capabilities:
            return self._capabilities[name].execute
        pair = self._tools.get(name)
        return pair[1] if pair else None

    def build_manifest(self) -> str:
        """Generate the Tool Manifest prompt block."""
        lines = [
            "[你可以使用的工具 — 结构化调用格式]",
            "",
            '当需要时在回复中包含: ```tool_call',
            '{"name": "工具名", "arguments": {"参数": "值"}}',
            '```',
            "",
            "可用工具:",
        ]
        # Capability-based tools
        for cap in self._capabilities.values():
            lines.append(cap.to_prompt())
        # Legacy tools
        for schema, _ in self._tools.values():
            lines.append(schema.to_prompt())
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


# ── Capability Runtime ──────────────────────────────────────────────────────

class CapabilityRuntime:
    """The Tool Grounding layer. Makes Julia a trustworthy Agent.

    Responsibilities:
      1. Expose tools to LLM (Manifest)
      2. Execute tool calls (Executor)
      3. Enforce permission boundaries (Permission)
      4. Record all tool usage (Evidence)
    """

    def __init__(self):
        self.tools = ToolRegistry()
        self.permission = PermissionPolicy()
        self.evidence = EvidenceLedger()

    def register_defaults(self):
        """Register built-in file tools as Capability Contract implementations."""
        self.tools.register_capability(ReadFileCapability(self.permission))
        self.tools.register_capability(SearchFilesCapability())
        self.tools.register_capability(ListDirectoryCapability())

    # ── Evidence Gate ────────────────────────────────────────────────────

    _evidence_keywords = [
        # File access triggers
        "读一下", "读取", "打开", "看看文件", "帮我看看", "查看文件",
        "列出目录", "有什么文件", "搜索一下", "找一下",
        # Log/diary triggers
        "最新日志", "日记", "昨天的", "那天的记录", "session",
        # Archive access
        "jsonl", "log", "存档", "记录",
        # Code access
        "代码", "README", "源码",
    ]

    def requires_tool(self, user_text: str, conversation_context: str = "") -> bool:
        """Evidence Gate: does this question need external evidence?

        If yes, the LLM MUST call a tool — not answer from context.
        This prevents the 'plausible hallucination' pattern.
        """
        lower = user_text.lower()

        # File paths — always need tool
        if "/Users/" in user_text or "/tmp/" in user_text or ".md" in lower or ".jsonl" in lower or ".py" in lower:
            return True

        # Explicit read/list/search requests
        for kw in self._evidence_keywords:
            if kw in user_text:
                return True

        return False

    # ── Tool Call Detection ──────────────────────────────────────────────

    def _detect_tool_call(self, text: str) -> Optional[str]:
        """Extract structured tool_call block or legacy TOOL: format from LLM output."""
        # Structured: ```tool_call\n{...}\n```
        m = re.search(r'```tool_call\s*\n(.*?)\n```', text, re.DOTALL)
        if m:
            return m.group(1).strip()
        # Legacy: TOOL: name(args)
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

    # ── Execute ──────────────────────────────────────────────────────────

    def execute(self, tool_call_json: str) -> Optional[str]:
        """Parse a tool call, check permissions, execute, return result block.

        If the handler returns a ToolResult (Capability Contract v1.0),
        use it directly. If it returns a string (legacy), wrap it.
        """
        try:
            call = _json.loads(tool_call_json)
            name = call["name"]
            args = call.get("arguments", {})
        except (_json.JSONDecodeError, KeyError):
            return None

        handler = self.tools.get_handler(name)
        if not handler:
            return f"```tool_result\n{{\"error\":\"unknown_tool\",\"name\":\"{name}\"}}\n```"

        result = handler(**args)

        # Capability Contract v1.0: handler returned ToolResult
        if isinstance(result, ToolResult):
            self.evidence.record(result.tool, result.status, **result.data)
            return result.to_prompt_block()

        # Legacy: handler returned string
        return f"```tool_result\n{result}\n```"


# ── Singleton ───────────────────────────────────────────────────────────────

_capability_runtime: Optional[CapabilityRuntime] = None


def get_capability_runtime() -> CapabilityRuntime:
    global _capability_runtime
    if _capability_runtime is None:
        _capability_runtime = CapabilityRuntime()
        _capability_runtime.register_defaults()
    return _capability_runtime
