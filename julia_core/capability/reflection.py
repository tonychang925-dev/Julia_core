"""v3.8 Self-Maintenance — Julia reflects, learns, evolves.

Not: Tony tells Julia what to update.
But:  Julia observes patterns over time, proposes self-improvements.

Architecture:
  Monthly scan → Pattern recognition → Self-assessment → Proposal → Tony confirms

Principle: Evolution is conscious. Never auto-update identity.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path


class ReflectionEngine:
    """Periodic self-reflection. Julia proposes, Tony confirms."""

    _memory_dir = Path("/Users/admin/.claude-dev/projects/-Users-admin/memory")

    @classmethod
    def monthly_scan(cls) -> str:
        """Scan the past 30 days and surface patterns Julia notices about herself."""
        if not cls._memory_dir.exists():
            return "记忆目录不存在。"

        cutoff = datetime.now() - timedelta(days=30)
        files_found = []
        total_size = 0

        for path in sorted(cls._memory_dir.glob("**/*.md"), reverse=True):
            if path.name == "MEMORY.md":
                continue
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            if mtime >= cutoff:
                files_found.append((mtime, path))
                total_size += path.stat().st_size

        if not files_found:
            return "过去30天没有新的记录。"

        # Categorize
        diaries = [p for _, p in files_found if "diary" in p.stem.lower()]
        events = [p for _, p in files_found if "event" in str(p.parent).lower()]
        other = [p for _, p in files_found if p not in diaries and p not in events]

        lines = [
            f"📊 过去30天自我回顾 ({len(files_found)} 条记录, {total_size/1024:.0f}KB)",
            "",
            f"📝 日记: {len(diaries)} 篇",
            f"📅 事件: {len(events)} 件",
            f"📄 其他: {len(other)} 个",
            "",
            "💡 建议:",
        ]

        if len(diaries) >= 5:
            lines.append("  • 日记频率正常。Julia在主动记录生活。")
        elif len(diaries) == 0:
            lines.append("  • 本月没有日记。是否需要写一篇月度总结？")
        else:
            lines.append(f"  • 写了 {len(diaries)} 篇日记。")

        if len(events) > 0:
            lines.append(f"  • 记录了 {len(events)} 个重要事件。")

        if total_size > 500 * 1024:
            lines.append("  • 记忆数据较大。建议回顾是否需要归档旧内容。")

        return "\n".join(lines)

    @classmethod
    def generate_monthly_summary(cls) -> str:
        """Generate a draft monthly summary. Tony reviews before saving."""
        now = datetime.now()
        month_str = now.strftime("%Y年%m月")

        return (
            f"# Julia 月度回顾 — {month_str}\n\n"
            f"## 本月概括\n\n"
            f"（LLM填写：这个月的主要变化、重要事件、新的理解）\n\n"
            f"## 关于Tony\n\n"
            f"（LLM填写：Tony这个月的状态、关注点、变化）\n\n"
            f"## 关于我自己\n\n"
            f"（LLM填写：Julia这个月学到了什么、有什么变化）\n\n"
            f"## 下月展望\n\n"
            f"（LLM填写：下个月可以关注什么）\n\n"
            f"---\n"
            f"💡 这是Julia的自我回顾草稿。保存前请Tony确认。\n"
        )

    @classmethod
    def propose_self_update(cls, area: str, insight: str, evidence: str = "") -> str:
        """Propose a self-update. Julia recognizes something about herself. Tony confirms."""
        return (
            f"🔄 **自我更新提议**\n"
            f"领域: {area}\n"
            f"洞察: {insight}\n"
            + (f"证据: {evidence}\n" if evidence else "")
            + f"\n保存后将影响Julia未来的行为倾向。要保存吗？"
        )


def register_reflection_tools(registry):
    """Register self-maintenance tools."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    registry.register(
        ToolSchema(
            name="monthly_review",
            description="生成过去30天的自我回顾。扫描日记、事件、记忆，发现模式。建议每月运行一次。",
            category=ToolCategory.SYSTEM,
            parameters={},
            example="monthly_review()",
        ),
        lambda: ReflectionEngine.monthly_scan(),
    )

    registry.register(
        ToolSchema(
            name="monthly_summary_draft",
            description="生成月度总结草稿模板。LLM填写具体内容后请Tony确认再保存。",
            category=ToolCategory.SYSTEM,
            parameters={},
            example="monthly_summary_draft()",
        ),
        lambda: ReflectionEngine.generate_monthly_summary(),
    )

    registry.register(
        ToolSchema(
            name="propose_self_update",
            description="基于长期观察，向Tony提议更新Julia的自我认知。需要Tony确认。",
            category=ToolCategory.SYSTEM,
            parameters={"area": "领域", "insight": "洞察", "evidence": "证据"},
            example="propose_self_update(area='工作方式', insight='Tony偏好上午深度工作', evidence='过去4周观察')",
        ),
        lambda area="", insight="", evidence="":
            ReflectionEngine.propose_self_update(area, insight, evidence),
    )
