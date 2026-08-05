"""v3.0.1 Personal Information — Calendar integration.

LLM decides: check schedule, find free time, remind about events.
Runtime does: connect to calendar provider. Nothing more.

Provider abstraction: Google Calendar (MCP) or local file.
LLM never knows which backend.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional


class CalendarTool:
    """Schedule awareness. LLM decides when to check, what to surface."""

    tool_name = "get_calendar"
    tool_description = "查看Tony的日程安排。当Tony问'今天有什么安排'或你想提醒他时使用。"

    _calendar_path = Path(os.environ.get(
        "JULIA_CALENDAR_PATH",
        str(Path.home() / ".julia" / "calendar.json"),
    ))

    @classmethod
    def today(cls) -> str:
        """Get today's events."""
        events = cls._load_events()
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_events = [e for e in events if e.get("date") == today_str]

        if not today_events:
            return f"今天 ({today_str}) 暂无日程安排。"

        lines = [f"📅 {today_str} 日程:"]
        for e in sorted(today_events, key=lambda x: x.get("time", "23:59")):
            time_str = e.get("time", "全天")
            lines.append(f"  {time_str} — {e.get('title', '未命名')}")
        return "\n".join(lines)

    @classmethod
    def upcoming(cls, days: int = 7) -> str:
        """Get upcoming events for the next N days."""
        events = cls._load_events()
        today = datetime.now().date()
        cutoff = today + timedelta(days=days)

        upcoming = []
        for e in events:
            try:
                event_date = datetime.strptime(e.get("date", ""), "%Y-%m-%d").date()
                if today <= event_date <= cutoff:
                    upcoming.append(e)
            except ValueError:
                continue

        if not upcoming:
            return f"未来 {days} 天暂无日程。"

        lines = [f"📅 未来 {days} 天日程:"]
        for e in sorted(upcoming, key=lambda x: x.get("date", "") + x.get("time", "23:59")):
            date_str = e.get("date", "")
            time_str = e.get("time", "全天")
            lines.append(f"  {date_str} {time_str} — {e.get('title', '未命名')}")
        return "\n".join(lines)

    @classmethod
    def add_event(cls, date: str, time: str, title: str) -> str:
        """Add an event to the calendar."""
        events = cls._load_events()
        events.append({"date": date, "time": time, "title": title})
        cls._save_events(events)
        return f"已添加: {date} {time} — {title}"

    @classmethod
    def _load_events(cls) -> List[dict]:
        if cls._calendar_path.exists():
            try:
                return json.loads(cls._calendar_path.read_text())
            except Exception:
                pass
        return []

    @classmethod
    def _save_events(cls, events: List[dict]):
        cls._calendar_path.parent.mkdir(parents=True, exist_ok=True)
        cls._calendar_path.write_text(json.dumps(events, ensure_ascii=False, indent=2))


def register_calendar_tools(registry):
    """Register calendar tools in capability registry."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    registry.register(
        ToolSchema(
            name="get_calendar_today",
            description=CalendarTool.tool_description,
            category=ToolCategory.SYSTEM,
            parameters={},
            example="get_calendar_today()",
        ),
        lambda: CalendarTool.today(),
    )

    registry.register(
        ToolSchema(
            name="get_calendar_upcoming",
            description="查看未来几天的日程安排。用于早间简报或提醒。",
            category=ToolCategory.SYSTEM,
            parameters={"days": "未来天数（默认7天）"},
            example="get_calendar_upcoming(days=7)",
        ),
        lambda days=7: CalendarTool.upcoming(int(days)),
    )

    registry.register(
        ToolSchema(
            name="add_calendar_event",
            description="添加日程。当Tony说'提醒我...'或'记一下...'时使用。",
            category=ToolCategory.SYSTEM,
            parameters={"date": "日期 (YYYY-MM-DD)", "time": "时间 (HH:MM 或 全天)", "title": "事件标题"},
            example="add_calendar_event(date='2026-08-05', time='15:00', title='团队会议')",
        ),
        lambda date="", time="全天", title="": CalendarTool.add_event(date, time, title),
    )
