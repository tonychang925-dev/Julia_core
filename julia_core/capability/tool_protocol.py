"""Julia Capability Interface Layer — Tool Protocol v1.0.

Principle: Tool PROVIDER, not Tool ROUTER.
  ❌ Runtime decides which tool to call.
  ✅ LLM decides which tool to use. Runtime exposes them.

Every tool is a capability the LLM can CHOOSE to use.
The Runtime never routes. It only provides.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ToolCategory(str, Enum):
    INTERFACE = "interface"    # Voice, Vision — human I/O
    FILE = "file"              # Read, Write, Search, Organize
    MEMORY = "memory"          # Diary, Events, Knowledge
    WEB = "web"                # Search, Fetch
    SYSTEM = "system"          # Time, Calendar, Execute


@dataclass
class ToolSchema:
    """Schema for a capability tool exposed to the LLM."""
    name: str                  # tool name: "read_file", "search_files"
    description: str           # what it does, when to use it
    category: ToolCategory
    parameters: Dict[str, str] = field(default_factory=dict)  # param_name → description
    example: str = ""          # example usage for the LLM

    def to_prompt(self) -> str:
        """Render as a tool description the LLM can understand."""
        params = ", ".join(f"{k}: {v}" for k, v in self.parameters.items())
        return (
            f"### {self.name}\n"
            f"{self.description}\n"
            + (f"参数: {params}\n" if params else "")
            + (f"例: {self.example}\n" if self.example else "")
        )


# ── Tool Registry ───────────────────────────────────────────────────────────

@dataclass
class ToolRegistry:
    """Registry of all capability tools available to the LLM."""
    tools: Dict[str, ToolSchema] = field(default_factory=dict)
    handlers: Dict[str, Callable] = field(default_factory=dict)

    def register(self, schema: ToolSchema, handler: Callable):
        self.tools[schema.name] = schema
        self.handlers[schema.name] = handler

    def get_prompt(self) -> str:
        """Generate tool availability prompt for the LLM context."""
        lines = ["[可用工具]\n你可以使用以下工具来获取信息或执行操作：\n"]
        for tool in self.tools.values():
            lines.append(tool.to_prompt())
            lines.append("")
        lines.append("工具会执行并将结果返回给你。你不需要手动调用——"
                      "在回复中自然地使用工具提供的信息即可。")
        return "\n".join(lines)

    def execute(self, tool_name: str, **params) -> Optional[str]:
        """Execute a tool by name. Called by the Runtime when LLM requests it."""
        if tool_name in self.handlers:
            try:
                return self.handlers[tool_name](**params)
            except Exception as e:
                return f"[工具错误] {tool_name}: {e}"
        return None


# ── P0 Tool Schemas ────────────────────────────────────────────────────────

TOOLS_V1 = [
    # ── File System ──
    ToolSchema(
        name="list_directory",
        description="列出指定目录下的所有文件和子目录。当你需要了解项目结构或查找文件时使用。",
        category=ToolCategory.FILE,
        parameters={"path": "目录路径，如 /Users/admin/Documents"},
        example="list_directory(path='/Users/admin/julia_core')",
    ),
    ToolSchema(
        name="search_files",
        description="按文件名或内容搜索文件。当Tony提到某个文件但你不知道具体位置时使用。",
        category=ToolCategory.FILE,
        parameters={"pattern": "搜索关键词或文件名片段", "directory": "搜索目录（可选）"},
        example="search_files(pattern='continuity', directory='/Users/admin/julia_core')",
    ),
    ToolSchema(
        name="read_file",
        description="读取指定文件的内容。支持 .md, .py, .txt, .json。当Tony让你看某个文件时使用。",
        category=ToolCategory.FILE,
        parameters={"path": "文件完整路径"},
        example="read_file(path='/Users/admin/julia_core/README.md')",
    ),

    # ── Memory ──
    ToolSchema(
        name="list_recent_memories",
        description="列出最近新增或修改的记忆文件。当你想知道最近发生了什么时使用。",
        category=ToolCategory.MEMORY,
        parameters={},
        example="list_recent_memories()",
    ),
    ToolSchema(
        name="read_diary",
        description="读取指定日期的日记。当你想回顾某天发生的事情时使用。",
        category=ToolCategory.MEMORY,
        parameters={"date": "日期，如 2026-08-03"},
        example="read_diary(date='2026-08-03')",
    ),

    # ── System ──
    ToolSchema(
        name="get_time",
        description="获取当前日期和时间。当Tony问时间或你想知道现在几点时使用。",
        category=ToolCategory.SYSTEM,
        parameters={},
        example="get_time()",
    ),

    # ── Web ──
    ToolSchema(
        name="web_search",
        description="搜索互联网获取最新信息。当Tony问到你不知道的最新事件或知识时使用。",
        category=ToolCategory.WEB,
        parameters={"query": "搜索关键词"},
        example="web_search(query='Claude Code latest features')",
    ),
]


def create_tool_registry() -> ToolRegistry:
    """Create and populate the tool registry with P0 tools."""
    import os
    from pathlib import Path
    from datetime import datetime

    registry = ToolRegistry()

    # File handlers
    def _list_directory(path: str) -> str:
        p = Path(path).expanduser()
        if not p.exists():
            return f"目录不存在: {path}"
        items = []
        for item in sorted(p.iterdir()):
            suffix = "/" if item.is_dir() else ""
            items.append(f"  {item.name}{suffix}")
        return f"{path}/\n" + "\n".join(items[:50])

    def _search_files(pattern: str, directory: str = "/Users/admin") -> str:
        results = []
        search_dir = Path(directory).expanduser()
        if not search_dir.exists():
            return f"目录不存在: {directory}"
        # Shallow search: only 3 levels deep, skip node_modules
        for path in search_dir.glob(f"*{pattern}*"):
            if not path.name.startswith('.') and '__pycache__' not in str(path):
                results.append(str(path))
        for path in search_dir.glob(f"*/*{pattern}*"):
            if not path.name.startswith('.') and '__pycache__' not in str(path):
                results.append(str(path))
        for path in search_dir.glob(f"*/*/*{pattern}*"):
            if not path.name.startswith('.') and '__pycache__' not in str(path):
                results.append(str(path))
        if not results:
            return f"未找到匹配 '{pattern}' 的文件"
        return "\n".join(results[:20])

    def _read_file(path: str) -> str:
        p = Path(path).expanduser()
        if not p.exists():
            return f"文件不存在: {path}"
        return p.read_text(encoding="utf-8", errors="ignore")[:5000]

    def _list_recent_memories() -> str:
        mem_dir = Path("/Users/admin/.claude-dev/projects/-Users-admin/memory")
        if not mem_dir.exists():
            return "记忆目录不存在"
        items = []
        for p in sorted(mem_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
            if p.name == "MEMORY.md":
                continue
            from datetime import datetime as dt
            mtime = dt.fromtimestamp(p.stat().st_mtime)
            items.append(f"  {p.name} ({mtime.strftime('%m月%d日 %H:%M')})")
        return "\n".join(items[:10]) if items else "暂无记忆文件"

    def _read_diary(date: str) -> str:
        mem_dir = Path("/Users/admin/.claude-dev/projects/-Users-admin/memory")
        # Try common naming patterns
        candidates = [
            mem_dir / f"julia_diary_{date}.md",
            mem_dir / f"diary_{date}.md",
        ]
        for path in candidates:
            if path.exists():
                return path.read_text(encoding="utf-8", errors="ignore")[:4000]
        # Try date fragment match
        for path in sorted(mem_dir.glob("*.md")):
            if date.replace('-', '') in path.name or date in path.name:
                return path.read_text(encoding="utf-8", errors="ignore")[:4000]
        return f"未找到 {date} 的日记"

    def _get_time() -> str:
        now = datetime.now()
        return f"{now.strftime('%Y年%m月%d日 %H:%M')}，星期{['一','二','三','四','五','六','日'][now.weekday()]}"

    # Register all tools with handlers
    registry.register(TOOLS_V1[0], _list_directory)     # list_directory
    registry.register(TOOLS_V1[1], _search_files)        # search_files
    registry.register(TOOLS_V1[2], _read_file)           # read_file
    registry.register(TOOLS_V1[3], _list_recent_memories) # list_recent_memories
    registry.register(TOOLS_V1[4], _read_diary)           # read_diary
    registry.register(TOOLS_V1[5], _get_time)             # get_time

    return registry


__all__ = [
    "TOOLS_V1",
    "ToolCategory",
    "ToolRegistry",
    "ToolSchema",
    "create_tool_registry",
]
