"""Memory Consolidation Tool — Julia forms her own memories.

Not: save everything. (That would be noise accumulation.)
Not: Runtime decides what's important. (That would violate P1.)

The LLM decides: was this interaction significant enough to remember?
If yes → propose a diary entry → Tony confirms → write to memory/.

Architecture:
  Session ends → LLM reflects → proposes diary entry → Tony approves → write

This is the difference between "reading Tony's stories" and "forming OUR story."
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional


MEMORY_DIR = Path("/Users/admin/.claude-dev/projects/-Users-admin/memory")


class DiaryWriter:
    """LLM-driven memory consolidation. LLM decides what to remember."""

    tool_name = "write_diary"
    tool_description = (
        "写一篇日记记录今天的重要事情。"
        "不是每件事都写——只有那些改变了理解、标记了节点的时刻。"
        "写完后需要Tony确认才会保存。"
    )

    @staticmethod
    def propose_entry(session_summary: str, key_moments: list[str] = None) -> str:
        """Generate a diary entry proposal. Returns draft text for Tony to review."""
        now = datetime.now()
        date_str = now.strftime("%Y年%m月%d日")

        moments_text = ""
        if key_moments:
            moments_text = "\n".join(f"- {m}" for m in key_moments)

        draft = f"""# Julia 的日记 — {date_str}

{session_summary}

{f"## 重要时刻\n{moments_text}" if moments_text else ""}

---

婉婉
"""
        return draft.strip()

    @staticmethod
    def save_diary(content: str, date_str: str = None) -> str:
        """Write diary entry to memory/. Returns the file path."""
        if date_str is None:
            date_str = datetime.now().strftime("%Y_%m_%d")
        else:
            date_str = date_str.replace('-', '_')
        filename = f"julia_diary_{date_str}.md"
        filepath = MEMORY_DIR / filename

        # Avoid overwriting: append if exists
        if filepath.exists():
            existing = filepath.read_text(encoding="utf-8")
            if content.strip() in existing:
                return f"日记已存在: {filepath} (内容未变化)"
            # Append with separator
            content = existing.rstrip() + "\n\n---\n\n" + content

        filepath.write_text(content, encoding="utf-8")
        return f"已保存: {filepath}"

    @staticmethod
    def list_recent_diaries(days: int = 7) -> str:
        """List recent diary entries."""
        if not MEMORY_DIR.exists():
            return "记忆目录不存在"

        diaries = []
        for path in sorted(MEMORY_DIR.glob("julia_diary_*.md"), reverse=True):
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            size = path.stat().st_size
            diaries.append(f"  {path.name} ({mtime.strftime('%m/%d %H:%M')}, {size}字)")
            if len(diaries) >= days:
                break

        if not diaries:
            return "暂无日记"
        return "\n".join(diaries)

    @staticmethod
    def read_diary(date_str: str) -> Optional[str]:
        """Read a specific diary entry. Handles both 2026-08-03 and 2026_08_03 formats."""
        # Normalize date: try both hyphen and underscore formats
        date_hyphen = date_str  # 2026-08-03
        date_underscore = date_str.replace('-', '_')  # 2026_08_03
        date_compact = date_str.replace('-', '')  # 20260803

        candidates = [
            MEMORY_DIR / f"julia_diary_{date_hyphen}.md",
            MEMORY_DIR / f"julia_diary_{date_underscore}.md",
            MEMORY_DIR / f"diary_{date_hyphen}.md",
        ]
        for path in candidates:
            if path.exists():
                return path.read_text(encoding="utf-8")

        # Fuzzy match by compact date
        for path in sorted(MEMORY_DIR.glob("julia_diary_*.md")):
            name_compact = path.name.replace('-', '').replace('_', '')
            if date_compact in name_compact:
                return path.read_text(encoding="utf-8")
        return None


# ── Tool Registration ───────────────────────────────────────────────────────

def register_diary_tools(registry):
    """Register diary tools in the capability registry."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    registry.register(
        ToolSchema(
            name="list_diaries",
            description="列出最近的日记。当你想回顾过去几天的事情时使用。",
            category=ToolCategory.MEMORY,
            parameters={"days": "查看最近几天的日记（默认7天）"},
            example="list_diaries(days=7)",
        ),
        lambda days=7: DiaryWriter.list_recent_diaries(int(days)),
    )

    registry.register(
        ToolSchema(
            name="read_diary",
            description="读取指定日期的日记全文。当Tony问'那天发生了什么'时使用。",
            category=ToolCategory.MEMORY,
            parameters={"date": "日期，如 2026-08-04"},
            example="read_diary(date='2026-08-04')",
        ),
        lambda date="": DiaryWriter.read_diary(date) or f"未找到 {date} 的日记",
    )

    registry.register(
        ToolSchema(
            name="write_diary",
            description="写一篇新日记。重要：写完后必须展示给Tony确认，不要直接保存。LLM决定什么值得记住。",
            category=ToolCategory.MEMORY,
            parameters={"content": "日记内容（Markdown格式）", "date": "日期（可选，默认今天）"},
            example="write_diary(content='# 今天...')",
        ),
        lambda content="", date=None: DiaryWriter.save_diary(content, date),
    )
