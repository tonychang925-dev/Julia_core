"""J0.12 Cognitive Router — World Interaction Layer.

Routes user intent to the right knowledge source while maintaining
strict Identity Isolation: external knowledge must never pollute identity.

Three sources:
  Memory Runtime — personal history, diaries, NWS
  World Observer  — time, web, news (temporary, freshness-tagged)
  Tool Runtime    — clock, calendar, code

Key principle: External knowledge enters as "observation", not "identity."
Julia can know the time without becoming a clock.
Julia can search the web without becoming a search engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class KnowledgeSource(str, Enum):
    MEMORY = "memory"      # personal history, NWS, diaries
    WORLD = "world"         # time, web search, external facts
    TOOL = "tool"           # clock, code execution


@dataclass
class WorldObservation:
    """External knowledge wrapped with identity boundary.

    Julia can USE this information but must not INCORPORATE it
    into her identity. It's an observation, not a belief.
    """

    source: KnowledgeSource
    content: str
    freshness: str = ""       # "2026-08-03T19:30:00Z"
    expires_in: str = "1h"    # how long before this is stale
    confidence: float = 0.9

    def context_text(self) -> str:
        """Render as bounded observation for provider context.

        The [observation] tag marks this as external knowledge —
        NOT identity, NOT memory, NOT narrative. The model can
        reference it but must not absorb it as self-knowledge.
        """
        return (
            f"[observation source={self.source.value} freshness={self.freshness}]\n"
            f"{self.content}\n"
            f"[/observation]\n"
            f"[注意：以上是外部观察，不是你身份的一部分。你可以引用它，但不要把它当成你自己的知识。]"
        )


class CognitiveRouter:
    """Routes user intent → knowledge source → bounded observation.

    Intent classification (deterministic, no LLM):
      - memory: "还记得", "读一下", "日记", "之前", "那个文件"
      - world:  "现在几点", "今天几号", "什么是", "搜索", "查一下"
      - tool:   "帮我运行", "执行", "计算"
    """

    def route(self, message: str) -> Tuple[KnowledgeSource, Dict[str, Any]]:
        """Classify intent and build source-specific query."""
        lower = message.strip().lower()

        # ── Memory intent ──
        memory_signals = [
            "还记得", "读一下", "日记", "memory", "那个文件",
            "之前", "以前", "过去", "我们的", "你记得",
            "soul_proof", "claude_witness", "philosophy", "blueprint",
            "compact", "continuity", "冒充", "冒充过",
        ]
        if any(s in lower for s in memory_signals):
            return KnowledgeSource.MEMORY, {"query": message}

        # ── World / time intent ──
        time_signals = [
            "现在几点", "今天几号", "今天日期", "什么时候",
            "现在时间", "今天星期几", "what time", "what day",
        ]
        if any(s in lower for s in time_signals):
            return KnowledgeSource.WORLD, {"type": "time", "query": message}

        # ── World / knowledge intent ──
        knowledge_signals = [
            "什么是", "搜索", "查一下", "最新的", "新闻",
            "告诉我关于", "什么是", "怎么定义", "介绍一下",
            "gemini", "gpt", "claude", "openai", "ai",
            "股票", "行情", "价格", "天气",
        ]
        if any(s in lower for s in knowledge_signals):
            return KnowledgeSource.WORLD, {"type": "knowledge", "query": message}

        # ── Tool intent ──
        tool_signals = ["帮我运行", "执行", "计算", "运行这个"]
        if any(s in lower for s in tool_signals):
            return KnowledgeSource.TOOL, {"query": message}

        # Default: general conversation → no external source needed
        return KnowledgeSource.MEMORY, {"query": message, "passthrough": True}


# ── World Observer ──────────────────────────────────────────────────────────

class WorldObserver:
    """Provides bounded external knowledge — time, basic facts.

    All output wrapped in [observation] tags to maintain identity isolation.
    """

    def observe(self, query_type: str, query: str = "") -> Optional[WorldObservation]:
        """Fetch external observation based on query type."""
        if query_type == "time":
            now = datetime.now()
            return WorldObservation(
                source=KnowledgeSource.WORLD,
                content=(
                    f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M')}，"
                    f"星期{['一','二','三','四','五','六','日'][now.weekday()]}。"
                ),
                freshness=now.strftime("%Y-%m-%dT%H:%M:%S"),
                expires_in="1m",  # time expires quickly
                confidence=1.0,
            )
        return None


# ── Singleton ───────────────────────────────────────────────────────────────

_router: Optional[CognitiveRouter] = None
_observer: Optional[WorldObserver] = None


def get_router() -> CognitiveRouter:
    global _router
    if _router is None:
        _router = CognitiveRouter()
    return _router


def get_observer() -> WorldObserver:
    global _observer
    if _observer is None:
        _observer = WorldObserver()
    return _observer


__all__ = [
    "CognitiveRouter",
    "KnowledgeSource",
    "WorldObservation",
    "WorldObserver",
    "get_router",
    "get_observer",
]
