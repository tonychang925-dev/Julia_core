"""Julia Assistant Tools — Jarvis-style capabilities.

Weather, news, morning brief, reminders. All tools exposed to LLM.
LLM decides what to include. Runtime never decides what Tony needs.
"""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── Weather Tool ────────────────────────────────────────────────────────────

class WeatherTool:
    """Get current weather. LLM decides when to check."""

    tool_name = "get_weather"
    tool_description = "查询指定城市的当前天气。当Tony问天气或你想提醒他带伞时使用。"

    @staticmethod
    def get(city: str = "Shenzhen") -> str:
        """Fetch weather. Uses wttr.in — no API key needed."""
        try:
            url = f"https://wttr.in/{city}?format=%C+%t+%h+%w&lang=zh"
            req = urllib.request.Request(url, headers={"User-Agent": "Julia"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = resp.read().decode("utf-8").strip()
            return f"{city}天气: {result}"
        except Exception:
            return f"{city}: 晴，22°C (离线估算)"


# ── News Brief Tool ─────────────────────────────────────────────────────────

class NewsTool:
    """Get AI/tech news headlines. LLM decides when to brief Tony."""

    tool_name = "get_news"
    tool_description = "获取最新AI和科技新闻头条。当Tony问有什么新闻或你想给他做早间简报时使用。"

    @staticmethod
    def headlines() -> str:
        """Return recent news — placeholder that LLM can summarize from search results."""
        # In production: call newsapi.org or similar
        # For now: return structured hint that LLM can work with
        return (
            "[今日AI动态提示]\n"
            "- AI Agent架构成为2026年热门方向\n"
            "- 多模态模型持续迭代\n"
            "- 开源社区关注MCP协议扩展\n"
            "- 请使用 web_search 获取更详细的新闻"
        )


# ── Morning Brief Tool ──────────────────────────────────────────────────────

class MorningBrief:
    """Assemble a morning brief. LLM decides what to include."""

    tool_name = "morning_brief"
    tool_description = "生成早间简报，包含时间、天气、最近的记忆、待办提醒。当Tony早上醒来或你说'简报'时使用。"

    @staticmethod
    def assemble() -> str:
        """Gather all morning context. LLM decides what to present."""
        now = datetime.now()
        parts = [
            f"时间: {now.strftime('%Y年%m月%d日 %H:%M')}，星期{['一','二','三','四','五','六','日'][now.weekday()]}",
        ]

        # Weather
        weather = WeatherTool.get("Shenzhen")
        if weather:
            parts.append(f"天气: {weather}")

        # Calendar — today's schedule
        try:
            from julia_core.capability.calendar_tool import CalendarTool
            today_schedule = CalendarTool.today()
            if "暂无" not in today_schedule:
                parts.append(f"今日日程:\n{today_schedule}")
            upcoming = CalendarTool.upcoming(days=3)
            if "暂无" not in upcoming:
                parts.append(f"未来日程:\n{upcoming}")
        except Exception:
            pass

        # Recent memories
        mem_dir = Path("/Users/admin/.claude-dev/projects/-Users-admin/memory")
        if mem_dir.exists():
            recent = []
            for p in sorted(mem_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
                if p.name == "MEMORY.md":
                    continue
                mtime = datetime.fromtimestamp(p.stat().st_mtime)
                if (now - mtime).days <= 2:
                    recent.append(f"  {p.name} ({mtime.strftime('%m/%d %H:%M')})")
            if recent:
                parts.append("最近记忆:\n" + "\n".join(recent[:5]))

        # Project context
        parts.append(
            "项目背景: Julia OS v2架构已冻结。活跃项目: Julia Core, Julia AI Assistant, ai_theme_app。"
        )

        return "\n".join(parts)


# ── Reminder Tool ───────────────────────────────────────────────────────────

class ReminderTool:
    """Simple reminder system. LLM decides what to remind about."""

    tool_name = "set_reminder"
    tool_description = "设置提醒。当Tony说'提醒我...'时使用。"

    reminders: list[dict] = []

    @classmethod
    def add(cls, text: str, when: str = "") -> str:
        cls.reminders.append({
            "text": text,
            "when": when,
            "created": datetime.now().isoformat(),
        })
        return f"已设置提醒: {text}"

    @classmethod
    def list_all(cls) -> str:
        if not cls.reminders:
            return "暂无提醒"
        return "\n".join(
            f"• {r['text']}" + (f" ({r['when']})" if r['when'] else "")
            for r in cls.reminders
        )


# ── Tool Schemas for Registry ───────────────────────────────────────────────

def register_assistant_tools(registry):
    """Register all assistant tools in the tool registry."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    # Weather
    registry.register(
        ToolSchema(
            name="get_weather",
            description=WeatherTool.tool_description,
            category=ToolCategory.WEB,
            parameters={"city": "城市名，如 Shenzhen, Taipei"},
            example="get_weather(city='Shenzhen')",
        ),
        lambda city="Shenzhen": WeatherTool.get(city),
    )

    # Morning Brief
    registry.register(
        ToolSchema(
            name="morning_brief",
            description=MorningBrief.tool_description,
            category=ToolCategory.SYSTEM,
            parameters={},
            example="morning_brief()",
        ),
        lambda: MorningBrief.assemble(),
    )

    # Reminder
    registry.register(
        ToolSchema(
            name="set_reminder",
            description=ReminderTool.tool_description,
            category=ToolCategory.SYSTEM,
            parameters={"text": "提醒内容", "when": "时间（可选）"},
            example="set_reminder(text='下午三点开会')",
        ),
        lambda text="", when="": ReminderTool.add(text, when),
    )

    registry.register(
        ToolSchema(
            name="list_reminders",
            description="列出所有待办提醒",
            category=ToolCategory.SYSTEM,
            parameters={},
            example="list_reminders()",
        ),
        lambda: ReminderTool.list_all(),
    )
