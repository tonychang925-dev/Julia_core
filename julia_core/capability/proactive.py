"""v3.4 Proactive Intelligence — Julia observes, suggests, Tony decides.

Not: "Tony asks → Julia responds"
But:  "Julia observes → Julia suggests → Tony decides"

Combines Calendar + Memory + Weather + Workflow into proactive awareness.
LLM decides what's worth surfacing. Runtime never routes.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional


class ProactiveObserver:
    """Observes patterns and surfaces suggestions. LLM decides what to surface."""

    @staticmethod
    def scan() -> str:
        """Scan all available context and surface what Julia notices.

        Combines: calendar, weather, recent memories, pending events.
        LLM decides what to present and how to frame it.
        """
        now = datetime.now()
        parts = [f"🕐 {now.strftime('%H:%M')} — Julia的主动观察:"]
        observations = []

        # 1. Calendar — what's coming up
        try:
            from julia_core.capability.calendar_tool import CalendarTool
            today = CalendarTool.today()
            if "暂无" not in today:
                observations.append(f"📅 今天: {today.split(chr(10))[1] if chr(10) in today else today}")
            upcoming = CalendarTool.upcoming(days=1)
            if "暂无" not in upcoming and "明天" not in upcoming:
                pass  # Only surface today for proactive
        except Exception:
            pass

        # 2. Weather — if it affects plans
        try:
            from julia_core.capability.assistant_tools import WeatherTool
            weather = WeatherTool.get("Shenzhen")
            if "雨" in weather or "雪" in weather or "台风" in weather:
                observations.append(f"🌧 {weather} — 提醒Tony带伞")
        except Exception:
            pass

        # 3. Recent memories — anything unresolved
        try:
            mem_dir = Path("/Users/admin/.claude-dev/projects/-Users-admin/memory")
            if mem_dir.exists():
                recent_files = sorted(mem_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:3]
                if recent_files:
                    observations.append(f"📝 最近记忆: {recent_files[0].name}")
        except Exception:
            pass

        # 4. Project context
        observations.append("💡 Julia OS v2.x 架构已冻结，28 个工具就绪。")

        if not observations:
            return "目前一切平稳，没有特别需要关注的事项。"

        return "\n".join(parts + observations)

    @staticmethod
    def suggest(context: str = "") -> str:
        """Generate a proactive suggestion based on context. LLM fills in details."""
        suggestions = [
            "📅 查看今天的日程安排",
            "📧 检查未读邮件",
            "🌤 查看天气并建议穿着",
            "📝 回顾最近的日记",
            "🔍 搜索项目相关的最新信息",
        ]
        return "Julia可以帮你:\n" + "\n".join(f"  {s}" for s in suggestions)


def register_proactive_tools(registry):
    """Register proactive intelligence tools."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    registry.register(
        ToolSchema(
            name="proactive_scan",
            description="主动扫描环境并发现值得关注的事项。当你想主动提醒Tony时使用。结合日历、天气、记忆等。",
            category=ToolCategory.SYSTEM,
            parameters={},
            example="proactive_scan()",
        ),
        lambda: ProactiveObserver.scan(),
    )

    registry.register(
        ToolSchema(
            name="suggest_actions",
            description="基于当前上下文建议Tony可以做的事情。在对话开始或Tony空闲时使用。",
            category=ToolCategory.SYSTEM,
            parameters={},
            example="suggest_actions()",
        ),
        lambda context="": ProactiveObserver.suggest(context),
    )
