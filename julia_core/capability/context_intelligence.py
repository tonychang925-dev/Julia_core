"""v3.6 Context Intelligence — long-term experience management.

Not: vector database, RAG pipeline, semantic search.
But:  experience timeline + meaning clusters + relevance scoring.

Problem: 32 tools, 9 layers, years of interactions → context explosion.
Solution: LLM asks for relevant experience. Runtime finds candidates. LLM decides.

Principle: Runtime finds. LLM judges relevance. Never auto-inject everything.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path


class ExperienceIndex:
    """Lightweight narrative timeline. LLM queries, Runtime returns candidates."""

    _memory_dir = Path("/Users/admin/.claude-dev/projects/-Users-admin/memory")

    @classmethod
    def timeline(cls, days: int = 30) -> str:
        """Return a timeline of significant events in the past N days."""
        if not cls._memory_dir.exists():
            return "记忆目录不存在。"

        cutoff = datetime.now() - timedelta(days=days)
        events = []

        # Scan diary entries
        for path in sorted(cls._memory_dir.glob("julia_diary_*.md"), reverse=True):
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            if mtime >= cutoff:
                # Extract first meaningful line
                try:
                    first_line = path.read_text(encoding="utf-8").split("\n")[0]
                    if first_line.startswith("#"):
                        first_line = first_line.lstrip("#").strip()
                    events.append((mtime, f"📝 {first_line[:80]}", "diary"))
                except Exception:
                    pass

        # Scan events directory
        events_dir = cls._memory_dir / "events"
        if events_dir.exists():
            for path in sorted(events_dir.glob("*.md"), reverse=True):
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
                if mtime >= cutoff:
                    events.append((mtime, f"📅 {path.stem}", "event"))

        if not events:
            return f"过去 {days} 天暂无记录。"
        if len(events) == 1:
            return f"过去 {days} 天只有 1 条记录: {events[0][1]}"

        events.sort(key=lambda x: x[0], reverse=True)
        lines = [f"📋 过去 {days} 天 ({len(events)} 条记录):"]
        for mtime, desc, etype in events:
            lines.append(f"  {mtime.strftime('%m/%d')} {desc}")
        return "\n".join(lines)

    @classmethod
    def find_relevant(cls, topic: str, max_results: int = 5) -> str:
        """Find past experiences relevant to current topic. LLM judges relevance."""
        if not cls._memory_dir.exists():
            return ""

        candidates = []
        keywords = topic.lower().split()

        for path in sorted(cls._memory_dir.glob("**/*.md"), reverse=True):
            if path.name == "MEMORY.md":
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore").lower()
                score = sum(1 for kw in keywords if kw in text)
                if score > 0:
                    mtime = datetime.fromtimestamp(path.stat().st_mtime)
                    candidates.append((score, mtime, path))
            except Exception:
                pass

        if not candidates:
            return ""

        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        lines = ["[相关历史经验]"]
        for score, mtime, path in candidates[:max_results]:
            preview = path.read_text(encoding="utf-8", errors="ignore")[:300]
            lines.append(f"--- {path.name} (相关度:{score}) ---\n{preview}")
        return "\n".join(lines)

    @classmethod
    def summary(cls) -> str:
        """Overall memory health summary."""
        if not cls._memory_dir.exists():
            return "记忆目录不存在。"

        total_files = len(list(cls._memory_dir.glob("**/*.md")))
        total_size = sum(p.stat().st_size for p in cls._memory_dir.glob("**/*.md"))
        oldest = min(
            (p for p in cls._memory_dir.glob("**/*.md") if p.name != "MEMORY.md"),
            key=lambda p: p.stat().st_mtime,
            default=None,
        )

        return (
            f"📊 记忆概况:\n"
            f"  文件数: {total_files}\n"
            f"  总大小: {total_size/1024:.0f}KB\n"
            + (f"  最早记录: {datetime.fromtimestamp(oldest.stat().st_mtime).strftime('%Y-%m-%d')}" if oldest else "")
            + f"\n  💡 LLM决定检索哪些。Runtime只提供索引。"
        )


def register_context_tools(registry):
    """Register context intelligence tools."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    registry.register(
        ToolSchema(
            name="experience_timeline",
            description="查看过去N天的经验时间线。当你想回顾最近发生了什么时使用。",
            category=ToolCategory.MEMORY,
            parameters={"days": "天数（默认30）"},
            example="experience_timeline(days=7)",
        ),
        lambda days=30: ExperienceIndex.timeline(int(days)),
    )

    registry.register(
        ToolSchema(
            name="find_related",
            description="查找与当前话题相关的历史经验。当Tony提到过去的某个话题时使用。LLM决定相关性。",
            category=ToolCategory.MEMORY,
            parameters={"topic": "话题关键词", "max_results": "最大结果数"},
            example="find_related(topic='Whisper GPU')",
        ),
        lambda topic="", max_results=5: ExperienceIndex.find_relevant(topic, int(max_results)),
    )

    registry.register(
        ToolSchema(
            name="memory_health",
            description="查看记忆系统概况——文件数、大小、最早记录。",
            category=ToolCategory.MEMORY,
            parameters={},
            example="memory_health()",
        ),
        lambda: ExperienceIndex.summary(),
    )
