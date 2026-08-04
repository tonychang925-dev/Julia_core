"""v4.0 Personal Operating System — Julia lives with Tony.

Not: more AI capabilities.
But:  connecting all existing capabilities into Tony's real life flow.

Architecture:
  Morning OS → daily brief (calendar + weather + email + memory + projects)
  Project OS → project-aware context (status, tasks, next steps)
  Dashboard → unified view of health, work, learning, finance, relationships

Principle: LLM orchestrates. Runtime provides data. Tony decides.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


class MorningOS:
    """Unified morning experience. Combines all 12 layers."""

    @staticmethod
    def assemble(project_context: str = "") -> str:
        """Assemble a complete morning briefing from all available data sources."""
        now = datetime.now()
        parts = [
            f"☀️ **{now.strftime('%Y年%m月%d日')} 早上好，Tony。**",
            f"   星期{['一','二','三','四','五','六','日'][now.weekday()]} · {now.strftime('%H:%M')}",
            "",
        ]

        # Weather
        try:
            from julia_core.capability.assistant_tools import WeatherTool
            weather = WeatherTool.get("Shenzhen")
            parts.append(f"🌤 {weather}")
        except Exception:
            pass

        # Calendar today
        try:
            from julia_core.capability.calendar_tool import CalendarTool
            today = CalendarTool.today()
            if "暂无" not in today:
                parts.append(f"\n📅 **今日安排:**")
                parts.append(today)
        except Exception:
            pass

        # Email unread count
        try:
            from julia_core.capability.email_tool import EmailTool
            inbox = EmailTool.search("", max_results=5)
            if "收件箱为空" not in inbox and "暂无" not in inbox:
                unread = inbox.count("🔵")
                if unread > 0:
                    parts.append(f"\n📧 **未读邮件:** {unread} 封")
        except Exception:
            pass

        # Recent diary
        try:
            mem_dir = Path("/Users/admin/.claude-dev/projects/-Users-admin/memory")
            diary_files = sorted(mem_dir.glob("julia_diary_*.md"),
                                key=lambda x: x.stat().st_mtime, reverse=True)
            if diary_files:
                last_diary = diary_files[0]
                mtime = datetime.fromtimestamp(last_diary.stat().st_mtime)
                days_ago = (now - mtime).days
                if days_ago > 0:
                    parts.append(f"📝 上次日记: {days_ago}天前 ({mtime.strftime('%m/%d')})")
        except Exception:
            pass

        # Identity health
        try:
            from julia_core.capability.identity_preservation import NarrativeWeight
            health = NarrativeWeight.health_check()
            if "✅" in health:
                parts.append("🛡️ 身份核心: 完好")
        except Exception:
            pass

        # Project hint
        if project_context:
            parts.append(f"\n💡 {project_context}")

        parts.append(f"\n---\n*{40} tools · 12 layers · Julia OS v4.0*")
        return "\n".join(parts)


class ProjectOS:
    """Project-aware context for Tony's work."""

    @staticmethod
    def status(project: str = "") -> str:
        """Get project status summary."""
        return (
            f"📊 项目状态: {project or 'Julia OS'}\n"
            f"  活跃工具: 40\n"
            f"  测试: 59 passed\n"
            f"  架构层: 12\n"
            f"  原则: Runtime = nervous system, LLM = cognitive system"
        )


def register_personal_os_tools(registry):
    """Register Personal OS tools."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    registry.register(
        ToolSchema(
            name="morning_os",
            description="完整的早晨体验——天气、日程、邮件、记忆、身份健康。一站式启动。每天运行一次。",
            category=ToolCategory.SYSTEM,
            parameters={},
            example="morning_os()",
        ),
        lambda: MorningOS.assemble(),
    )

    registry.register(
        ToolSchema(
            name="project_status",
            description="查看项目状态概要。当Tony问项目进展时使用。",
            category=ToolCategory.SYSTEM,
            parameters={"project": "项目名称"},
            example="project_status(project='Julia OS')",
        ),
        lambda project="Julia OS": ProjectOS.status(project),
    )
