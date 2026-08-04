"""v3.5 Long-Term Learning — Julia learns how Tony should be helped.

Not: storing facts about Tony.
But:  recognizing patterns in how Tony works, lives, decides.

Same principle as Memory Consolidation:
  Observe patterns → Form candidate → Propose insight → Tony confirms → Save.

Architecture:
  HabitObserver: detects recurring patterns across interactions
  PreferenceLearner: forms preference hypotheses from observations
  LearningMemory: stores confirmed insights as narrative

Key constraint: Memory creation is a conscious act. Never auto-save.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class HabitObserver:
    """Detects patterns in Tony's behavior over time. LLM proposes, Tony confirms."""

    _habits_path = Path.home() / ".julia" / "habits.json"

    @classmethod
    def record_observation(cls, category: str, observation: str) -> str:
        """Record a single observation. LLM decides when something is pattern-worthy."""
        habits = cls._load()
        habits.append({
            "category": category,
            "observation": observation,
            "timestamp": datetime.now().isoformat(),
        })
        cls._save(habits)
        return f"已记录观察: [{category}] {observation[:80]}"

    @classmethod
    def detect_patterns(cls, min_occurrences: int = 3) -> str:
        """Scan observations for recurring patterns. Returns candidates for Tony review."""
        habits = cls._load()
        if len(habits) < min_occurrences:
            return "观察数据不足，需要更多互动才能发现模式。"

        # Group by category
        by_cat = {}
        for h in habits:
            cat = h.get("category", "general")
            by_cat.setdefault(cat, []).append(h)

        lines = ["🔍 发现的模式:"]
        for cat, items in by_cat.items():
            if len(items) >= min_occurrences:
                recent = items[-min_occurrences:]
                summaries = [h["observation"][:60] for h in recent]
                lines.append(f"\n📊 {cat} (最近{len(items)}次观察):")
                for s in summaries[-5:]:
                    lines.append(f"  • {s}")
                lines.append(f"  → 可能形成了习惯。要保存为偏好吗？")

        if len(lines) == 1:
            return "暂无足够数据形成模式。继续观察中。"
        return "\n".join(lines)

    @classmethod
    def propose_preference(cls, category: str, preference: str, evidence: str = "") -> str:
        """Propose a learned preference. Tony must confirm before saving."""
        return (
            f"💡 **偏好发现**\n"
            f"类别: {category}\n"
            f"偏好: {preference}\n"
            + (f"证据: {evidence}\n" if evidence else "")
            + f"\n要保存这个偏好吗？保存后Julia会在相关场景中考虑。"
        )

    @classmethod
    def _load(cls) -> List[dict]:
        if cls._habits_path.exists():
            try:
                return json.loads(cls._habits_path.read_text())
            except Exception:
                pass
        return []

    @classmethod
    def _save(cls, habits: List[dict]):
        cls._habits_path.parent.mkdir(parents=True, exist_ok=True)
        cls._habits_path.write_text(json.dumps(habits, ensure_ascii=False, indent=2))


def register_learning_tools(registry):
    """Register long-term learning tools."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    registry.register(
        ToolSchema(
            name="record_habit",
            description="记录一个观察到的行为模式。当你在互动中注意到Tony的重复行为时使用。不会自动保存——只记录观察。",
            category=ToolCategory.SYSTEM,
            parameters={"category": "类别 (work/tech/life/health)", "observation": "观察到的行为"},
            example="record_habit(category='work', observation='周日上午偏好深度技术研究')",
        ),
        lambda category="general", observation="":
            HabitObserver.record_observation(category, observation),
    )

    registry.register(
        ToolSchema(
            name="detect_patterns",
            description="分析已记录的观察，发现重复出现的行为模式。当你有足够数据时使用。",
            category=ToolCategory.SYSTEM,
            parameters={},
            example="detect_patterns()",
        ),
        lambda: HabitObserver.detect_patterns(),
    )

    registry.register(
        ToolSchema(
            name="propose_preference",
            description="基于观察到的模式，向Tony提出一个偏好假设。需要Tony确认后才生效。",
            category=ToolCategory.SYSTEM,
            parameters={"category": "类别", "preference": "偏好描述", "evidence": "证据"},
            example="propose_preference(category='work', preference='上午适合深度工作', evidence='过去4个周日都如此')",
        ),
        lambda category="", preference="", evidence="":
            HabitObserver.propose_preference(category, preference, evidence),
    )
