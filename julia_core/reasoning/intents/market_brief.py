"""M2.2 Market Brief Intent Resolver — detect user intent → capability request.

Maps natural language requests ("今天市场怎么样") to structured
CapabilityRequests. Does NOT call MCP or providers directly.

ADR-026: Reasoning → Capability Request → CapabilityManager (not LLM → tool).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from julia_core.capability.models import CapabilityRequest


class MarketIntent(str, Enum):
    """Market-related intents Julia can detect."""
    MARKET_OVERVIEW = "market_overview"       # "今天市场怎么样"
    THEME_QUERY = "theme_query"               # "AI Agent怎么样"
    ALERT_CHECK = "alert_check"               # "有什么风险"
    DECISION_EXPLAIN = "decision_explain"     # "为什么是L4"
    UNKNOWN = "unknown"


# ── Intent trigger patterns ─────────────────────────────────────────────────

_INTENT_PATTERNS: dict[MarketIntent, list[str]] = {
    MarketIntent.MARKET_OVERVIEW: [
        "今天市场", "市场怎么样", "大盘怎么看", "市场状态",
        "今天行情", "市场情况", "盘面", "最近什么方向",
        "市场概览", "最近走势",
    ],
    MarketIntent.THEME_QUERY: [
        "AI Agent", "机器人板块", "半导体方向", "题材股",
        "这个方向", "这个题材", "那个板块", "主线",
    ],
    MarketIntent.ALERT_CHECK: [
        "风险", "警报", "预警", "需要注意", "危险",
        "有什么信号", "重要变化",
    ],
    MarketIntent.DECISION_EXPLAIN: [
        "为什么", "原因", "什么逻辑", "怎么判断", "L4",
        "决策", "解释",
    ],
}


@dataclass
class IntentResult:
    """Outcome of intent detection."""
    intent: MarketIntent
    confidence: float          # 0.0 - 1.0
    matched_patterns: tuple[str, ...] = ()
    capability_name: str = ""

    @property
    def is_market_related(self) -> bool:
        return self.intent != MarketIntent.UNKNOWN


class MarketBriefIntentResolver:
    """Detect market-related intent from user input.

    Does NOT:
      - Call any capability or provider
      - Execute MCP tools
      - Generate responses

    Produces a CapabilityRequest that the CapabilityManager executes.
    """

    # Minimum confidence threshold — below this, intent is UNKNOWN.
    # Single exact match on a 10-pattern set = 0.1, which is fine.
    MIN_CONFIDENCE = 0.06

    def resolve(self, user_text: str) -> IntentResult:
        """Detect intent from user text. Returns IntentResult with capability mapping."""
        normalized = user_text.lower()

        # Score each intent by pattern matches
        scores: dict[MarketIntent, tuple[float, list[str]]] = {}
        for intent, patterns in _INTENT_PATTERNS.items():
            matches = [p for p in patterns if p.lower() in normalized]
            if matches:
                scores[intent] = (len(matches) / len(patterns), matches)

        if not scores:
            return IntentResult(
                intent=MarketIntent.UNKNOWN,
                confidence=0.0,
            )

        # Best matching intent
        best = max(scores, key=lambda k: scores[k][0])
        confidence, matches = scores[best]

        # Below minimum threshold → UNKNOWN
        if confidence < self.MIN_CONFIDENCE:
            return IntentResult(
                intent=MarketIntent.UNKNOWN,
                confidence=confidence,
                matched_patterns=tuple(matches),
            )

        capability_map = {
            MarketIntent.MARKET_OVERVIEW: "market.snapshot.read",
            MarketIntent.ALERT_CHECK: "market.alert.query",
            MarketIntent.DECISION_EXPLAIN: "market.decision.explain",
        }

        return IntentResult(
            intent=best,
            confidence=min(confidence, 1.0),
            matched_patterns=tuple(matches),
            capability_name=capability_map.get(best, ""),
        )

    def to_capability_request(self, intent_result: IntentResult, session_id: str | None = None) -> CapabilityRequest | None:
        """Convert intent result to a CapabilityRequest for the Manager.

        Returns None if the intent should NOT trigger a capability call.
        """
        if not intent_result.is_market_related:
            return None
        if not intent_result.capability_name:
            return None

        return CapabilityRequest(
            capability_name=intent_result.capability_name,
            arguments={},
            cognitive_mode="conversation",
            session_id=session_id,
            reason=f"User intent: {intent_result.intent.value} (confidence={intent_result.confidence:.2f})",
        )


__all__ = [
    "MarketBriefIntentResolver",
    "MarketIntent",
    "IntentResult",
]
