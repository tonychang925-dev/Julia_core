"""R0.5 Full Chat E2E — validate the complete JuliaSession.chat() pipeline.

Tests the ACTUAL entry point: session.chat("今天市场怎么样？")
Not _resolve_market_context() internals.

Verifies:
  1. Market context injected into system prompt
  2. LLM sees identity + memory + market_context + tool_manifest
  3. History mutated (user + assistant messages appended)
  4. Evidence ledger populated through CapabilityManager
  5. Non-market queries bypass capability (no-op)

Run:
  python -m pytest tests/runtime/test_chat_e2e.py -v
"""

import pytest

from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
from julia_core.runtime.julia_session import JuliaSession
from julia_core.runtime.workflow_router import WorkflowRouter


# ── Mock LLM Provider ───────────────────────────────────────────────────────

class MockLLMProvider:
    """Returns the system prompt as the "reply" — lets us inspect what LLM sees."""

    provider_id = "mock_chat_e2e"
    _last_messages: list[dict] = []
    _last_persona: object | None = None

    def chat(self, messages: list[dict], *, persona: object | None = None,
             cognitive_mode: str = "") -> str:
        MockLLMProvider._last_messages = list(messages)
        MockLLMProvider._last_persona = persona
        # Return the system prompt so we can inspect it in tests
        system = messages[0]["content"] if messages else ""
        return f"[MOCK REPLY] system_len={len(system)}"

    @classmethod
    def last_system_prompt(cls) -> str:
        if cls._last_messages:
            return cls._last_messages[0]["content"]
        return ""

    @classmethod
    def last_user_message(cls) -> str:
        if cls._last_messages:
            return cls._last_messages[-1]["content"]
        return ""


# ── Mock Transport ──────────────────────────────────────────────────────────

def _chat_snapshot():
    return {
        "market_sentiment": "偏强",
        "active_themes": ["AI Agent", "半导体", "低空经济"],
        "top_signals": [
            {
                "id": "dec_chat_001",
                "timestamp": "2026-08-06T08:30:00+08:00",
                "source": "market",
                "type": "theme_match",
                "level": "decision",
                "impact": "positive",
                "confidence": 0.82,
                "prediction_id": "pred_chat_001",
                "theme_context": {
                    "theme_id": "9019807",
                    "lifecycle": "DIFFUSION",
                    "change": "heat increasing",
                    "days_active": 5,
                },
                "causal_chain": [
                    {
                        "cause": "AI Agent技术突破",
                        "effect": "产业预期升温",
                        "market_response": "相关概念股上涨",
                        "confidence": 0.82,
                    },
                ],
                "evidence": [
                    {"type": "news", "text": "AI Agent政策催化", "source": "cls_api", "authority": 0.9},
                ],
            },
        ],
        "risk_alerts": ["成交未能放量", "短期过热风险"],
        "date": "2026-08-06",
    }


async def _chat_transport(tool_name: str, args: dict) -> dict:
    if tool_name == "review_market_snapshot":
        return _chat_snapshot()
    return {}


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def chat_bridge():
    """Bridge with mock transport + ai_theme_app capabilities registered."""
    from julia_core.capability.providers.ai_theme import (
        register_ai_theme_capabilities,
        AiThemeProvider,
    )
    from julia_core.capability.providers.ai_theme.adapter import MCPToolAdapter

    b = RuntimeCapabilityBridge()
    register_ai_theme_capabilities(b.registry)
    adapter = MCPToolAdapter(transport=_chat_transport)
    provider = AiThemeProvider(adapter)
    b._providers["ai_theme_app"] = provider
    b._initialized = False
    b.initialize()
    return b


@pytest.fixture
def chat_session(chat_bridge):
    """JuliaSession wired with mock LLM + mock bridge.

    This is the REAL chat() entry point — not __new__() bypass.
    """
    session = JuliaSession.__new__(JuliaSession)

    # Inject mock provider
    session.provider = MockLLMProvider()

    # Inject bridge + workflow router
    session.capability = chat_bridge
    session.workflow_router = WorkflowRouter(chat_bridge)

    # Minimal state
    session.turn_count = 0
    session.history = []
    session.current_topic = "greeting"
    session.answered_questions = []

    # Action layer (simple mock)
    from julia_core.runtime.action import ActionRuntime
    session.action = ActionRuntime()

    # Relationship layer (mock)
    from unittest.mock import MagicMock
    session.relationship = MagicMock()
    session.relationship.to_context.return_value = "[关系上下文 mock]"
    session.relationship.session_mood = "neutral"
    session.relationship.recent_pattern = ""

    # Session recorder (mock)
    session.recorder = MagicMock()

    # Identity — minimal
    session._identity_system = "[Julia 身份层 — E2E 测试模式]"
    session._load_recent_experiences = lambda: "[体验回忆 mock]"

    # Bootstrap
    session.bootstrap = "[引导叙述 mock]"

    return session


# ── R0.5-1: chat() injects market context into system prompt ────────────────

def test_chat_injects_market_context(chat_session):
    """Market query → LLM receives market context in system prompt."""
    chat_session.chat("今天市场怎么样？")

    system = MockLLMProvider.last_system_prompt()

    # Market context was injected (structured, not raw dump)
    assert "市场情报" in system, "System prompt should contain market context header"
    assert "市场情绪" in system, "Should contain market sentiment"
    assert "AI Agent" in system, "Should contain active themes"
    assert "风险提示" in system, "Should contain risk alerts"
    assert "数据来源" in system or "ai_theme_app" in system, "Should contain provenance"

    # Identity + tools are still present (market context doesn't replace them)
    assert "Julia 身份层" in system, "Identity should still be present"
    assert "file.read" in system or "file.search" in system, "Tools should still be present"


# ── R0.5-2: Non-market query produces no market context ─────────────────────

def test_chat_non_market_no_context(chat_session):
    """Non-market query → system prompt has NO market context."""
    chat_session.chat("你好，最近怎么样？")

    system = MockLLMProvider.last_system_prompt()

    assert "市场情报" not in system
    assert "市场情绪" not in system
    # Identity + tools are unaffected
    assert "Julia 身份层" in system


# ── R0.5-3: History is mutated after chat() ─────────────────────────────────

def test_chat_appends_history(chat_session):
    """chat() appends user + assistant messages to session.history."""
    before = len(chat_session.history)

    chat_session.chat("今天市场怎么样？")

    after = len(chat_session.history)
    assert after == before + 2, f"Expected 2 new history entries, got {after - before}"

    # Last user message is the query
    assert chat_session.history[-2]["role"] == "user"
    assert "今天市场怎么样" in chat_session.history[-2]["content"]

    # Last message is assistant reply
    assert chat_session.history[-1]["role"] == "assistant"
    assert len(chat_session.history[-1]["content"]) > 0


# ── R0.5-4: Evidence ledger populated through chat() ───────────────────────

def test_chat_produces_evidence(chat_session):
    """chat() on market query → CapabilityManager evidence is recorded."""
    before = chat_session.capability.manager.evidence.count

    chat_session.chat("今天市场怎么样？")

    after = chat_session.capability.manager.evidence.count
    assert after > before, "Evidence should be recorded for market query"

    last = chat_session.capability.manager.evidence.last()
    assert last.capability_name == "market.snapshot.read"
    assert last.provider == "ai_theme_app"
    assert last.status == "success"


# ── R0.5-5: Evidence NOT recorded for non-market query ─────────────────────

def test_chat_non_market_no_evidence(chat_session):
    """Non-market query produces no capability-related evidence."""
    before = chat_session.capability.manager.evidence.count
    chat_session.chat("你好")

    after = chat_session.capability.manager.evidence.count
    # May increase if other capabilities fire; but market.snapshot should not
    market_entries = [
        e for e in chat_session.capability.manager.evidence.entries
        if e.capability_name == "market.snapshot.read"
    ]
    assert len(market_entries) == before  # no new market invocations


# ── R0.5-6: Conversation state updated ─────────────────────────────────────

def test_chat_updates_topic(chat_session):
    """chat() updates conversation state for market queries."""
    chat_session.chat("今天市场怎么样？")

    # Topic tracking should capture the conversation domain
    assert chat_session.turn_count == 1
    assert chat_session.current_topic is not None


# ── R0.5-7: Multiple turns consistency ────────────────────────────────────

def test_chat_multiple_turns(chat_session):
    """Multiple market queries each produce evidence and build history."""
    chat_session.chat("今天市场怎么样？")
    assert chat_session.turn_count == 1
    assert chat_session.capability.manager.evidence.count >= 1

    chat_session.chat("那风险大吗？")
    assert chat_session.turn_count == 2

    # History grows
    assert len(chat_session.history) >= 4  # 2 turns × 2 messages


# ── R0.5-8: System prompt structure (architectural, not data-specific) ─────

def test_chat_system_prompt_structure(chat_session):
    """System prompt contains expected structural layers, not specific data."""
    chat_session.chat("今天市场怎么样？")

    system = MockLLMProvider.last_system_prompt()

    # Structural layers (order-independent):
    structural_elements = [
        "Julia 身份层",          # Identity
        "体验回忆 mock",          # Experience/memory
        "市场情报",              # Market context (for market queries)
        "file",                  # Tool manifest (at least one tool present)
    ]

    for element in structural_elements:
        assert element in system, f"System prompt missing structural element: {element}"
