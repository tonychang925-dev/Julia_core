"""R0.7+R0.8.1: Gateway E2E + Real Session Failure tests.

R0.7: Validates the external body → Gateway → JuliaSession chain.
  POST /chat → gateway_server → get_session() → chat() → CapabilityManager

R0.8.1: Real init failure — JuliaSession() with failing provider.

This is the final Phase 0 gate: proving Julia OS has a real external
interface (HTTP), not just a Python library.

Run:
  python -m pytest tests/gateway/test_gateway_e2e.py -v
"""

import sys
import pytest
from unittest import mock
from fastapi.testclient import TestClient


# ── Mock LLM ────────────────────────────────────────────────────────────────

class _MockLLM:
    provider_id = "mock_gateway"
    def chat(self, messages, *, persona=None, cognitive_mode=""):
        system = messages[0]["content"] if messages else ""
        # Return the system prompt so we can verify market context
        return f"[GW REPLY] market_in_context={'市场情报' in system}"


# ── Mock Transport ──────────────────────────────────────────────────────────

def _gw_snapshot():
    return {
        "market_sentiment": "偏强",
        "active_themes": ["AI Agent", "半导体", "低空经济"],
        "top_signals": [
            {
                "id": "dec_gw_001",
                "timestamp": "2026-08-06T08:30:00+08:00",
                "source": "market",
                "type": "theme_match",
                "level": "decision",
                "impact": "positive",
                "confidence": 0.82,
                "prediction_id": "pred_gw_001",
                "causal_chain": [{"cause": "AI突破", "effect": "产业升温", "market_response": "上涨", "confidence": 0.82}],
                "evidence": [{"type": "news", "text": "AI Agent催化", "source": "cls", "authority": 0.9}],
            },
        ],
        "risk_alerts": ["成交未放量"],
        "date": "2026-08-06",
    }


async def _gw_transport(tool_name, args):
    if tool_name == "review_market_snapshot":
        return _gw_snapshot()
    return {}


# ── Gateway App Factory ─────────────────────────────────────────────────────

def _build_gateway_app():
    """Build the FastAPI app with all routes (same as gateway_server.main()).

    Uses REAL JuliaSession.get_session() with mocked LLM provider.
    """
    import sys as _sys
    from pathlib import Path

    # Ensure paths
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
    _sys.path.insert(0, "/Users/admin/julia_ai_assistant")
    _sys.path.insert(0, "/Users/admin/julia_core")

    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
    from fastapi.middleware.cors import CORSMiddleware
    from julia_core.runtime.julia_session import get_session
    from julia_core.runtime.session_store import get_store
    import re, json, time, logging

    app = FastAPI(title="Julia Gateway Test", version="test")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    def _clean(text):
        return re.sub(r'```tool_call\n.*?\n```', '', text, flags=re.DOTALL).strip()

    @app.post("/chat")
    async def chat_endpoint(req: Request):
        body = await req.json()
        text = body.get("text", "")
        sid = body.get("session_id", "test-session")
        js = get_session()
        store = get_store()
        reply = js.chat(text)
        reply = _clean(reply)
        store.touch(sid, topic=js.current_topic, user_msg=text, assistant_msg=reply)
        return {
            "reply": reply,
            "turn": js.turn_count,
            "session_id": sid,
            "topic": js.current_topic,
        }

    return app


# ── Fixture ──────────────────────────────────────────────────────────────────

@pytest.fixture
def gateway_client():
    """FastAPI TestClient with real JuliaSession + mock LLM + mock ai_theme_app.

    This is the REAL Gateway path:
      TestClient → POST /chat → get_session() → chat() → CapabilityManager
    """
    # Patch LLM import before get_session() is called
    fake_llm = mock.MagicMock()
    fake_llm.get_llm_provider = mock.MagicMock(return_value=_MockLLM())
    sys.modules["providers.llm.deepseek_provider"] = fake_llm
    sys.modules["providers.llm"] = mock.MagicMock()
    sys.modules["providers"] = mock.MagicMock()

    app = _build_gateway_app()

    # Now inject mock ai_theme_app into the session's bridge
    from julia_core.runtime.julia_session import get_session
    session = get_session()

    from julia_core.capability.providers.ai_theme import (
        register_ai_theme_capabilities,
        AiThemeProvider,
    )
    from julia_core.capability.providers.ai_theme.adapter import MCPToolAdapter

    register_ai_theme_capabilities(session.capability.registry)
    adapter = MCPToolAdapter(transport=_gw_transport)
    provider = AiThemeProvider(adapter)
    session.capability._providers["ai_theme_app"] = provider
    session.capability._initialized = False
    session.capability.initialize()

    client = TestClient(app)

    yield client

    # Cleanup
    sys.modules.pop("providers.llm.deepseek_provider", None)
    sys.modules.pop("providers.llm", None)
    sys.modules.pop("providers", None)


# ═══════════════════════════════════════════════════════════════════════════════
# R0.7: Gateway E2E
# ═══════════════════════════════════════════════════════════════════════════════

def test_gateway_health(gateway_client):
    """GET /health returns ok."""
    resp = gateway_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_gateway_chat_market_query(gateway_client):
    """POST /chat with market query → reply contains market context."""
    resp = gateway_client.post("/chat", json={
        "text": "今天市场怎么样？",
        "session_id": "gw-test-1",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert len(data["reply"]) > 0
    assert data["topic"] is not None
    assert data["turn"] >= 1


def test_gateway_chat_market_context_injected(gateway_client):
    """Market query through gateway → LLM receives market context."""
    resp = gateway_client.post("/chat", json={
        "text": "大盘怎么看",
        "session_id": "gw-test-2",
    })
    assert resp.status_code == 200
    data = resp.json()

    # Mock LLM returns "market_in_context=True" when market context was injected
    assert "market_in_context=True" in data["reply"]


def test_gateway_chat_non_market(gateway_client):
    """Non-market query → market context NOT injected."""
    resp = gateway_client.post("/chat", json={
        "text": "你好",
        "session_id": "gw-test-3",
    })
    assert resp.status_code == 200
    data = resp.json()

    # Mock LLM returns "market_in_context=False" for non-market queries
    assert "market_in_context=False" in data["reply"]


def test_gateway_chat_evidence_recorded(gateway_client):
    """Gateway chat → evidence recorded through CapabilityManager."""
    gateway_client.post("/chat", json={
        "text": "今天市场怎么样？",
        "session_id": "gw-test-4",
    })

    from julia_core.runtime.julia_session import get_session
    session = get_session()
    assert session.capability.manager.evidence.count >= 1
    last = session.capability.manager.evidence.last()
    assert last.capability_name == "market.snapshot.read"
    assert last.provider == "ai_theme_app"


def test_gateway_chat_multi_turn(gateway_client):
    """Multiple gateway calls maintain session state."""
    client = gateway_client
    sid = "gw-multi"

    r1 = client.post("/chat", json={"text": "今天市场怎么样？", "session_id": sid})
    assert r1.status_code == 200
    t1 = r1.json()["turn"]

    r2 = client.post("/chat", json={"text": "那风险大吗？", "session_id": sid})
    assert r2.status_code == 200
    t2 = r2.json()["turn"]

    assert t2 > t1  # Turn count increments across requests


# ═══════════════════════════════════════════════════════════════════════════════
# R0.8.1: Real init + provider failure
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def failing_gateway_client():
    """Gateway with real JuliaSession.__init__() but failing ai_theme_app provider."""
    fake_llm = mock.MagicMock()
    fake_llm.get_llm_provider = mock.MagicMock(return_value=_MockLLM())
    sys.modules["providers.llm.deepseek_provider"] = fake_llm
    sys.modules["providers.llm"] = mock.MagicMock()
    sys.modules["providers"] = mock.MagicMock()

    app = _build_gateway_app()

    from julia_core.runtime.julia_session import get_session
    session = get_session()

    # Register capabilities but with failing provider
    from julia_core.capability.providers.ai_theme import register_ai_theme_capabilities
    register_ai_theme_capabilities(session.capability.registry)

    class FailingProvider:
        async def execute(self, request):
            return {"error": "should not be called"}
        async def health(self):
            return False, "ai_theme_app MCP unreachable: connection refused"

    session.capability._providers["ai_theme_app"] = FailingProvider()
    session.capability._initialized = False
    session.capability.initialize()

    client = TestClient(app)
    yield client

    sys.modules.pop("providers.llm.deepseek_provider", None)
    sys.modules.pop("providers.llm", None)
    sys.modules.pop("providers", None)


# ═══════════════════════════════════════════════════════════════════════════════
# R0.9.1: Production Gateway App (real create_app, not rebuilt)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def production_gateway_client():
    """FastAPI TestClient against the REAL production create_app().

    This is NOT a rebuilt app — it's the actual gateway_server.create_app()
    that runs in production. Only the LLM provider is mocked.
    """
    fake_llm = mock.MagicMock()
    fake_llm.get_llm_provider = mock.MagicMock(return_value=_MockLLM())
    sys.modules["providers.llm.deepseek_provider"] = fake_llm
    sys.modules["providers.llm"] = mock.MagicMock()
    sys.modules["providers"] = mock.MagicMock()

    from julia_core.runtime.gateway_server import create_app
    app = create_app()

    # Inject mock ai_theme_app into the session
    from julia_core.runtime.julia_session import get_session
    session = get_session()
    from julia_core.capability.providers.ai_theme import (
        register_ai_theme_capabilities, AiThemeProvider,
    )
    from julia_core.capability.providers.ai_theme.adapter import MCPToolAdapter
    register_ai_theme_capabilities(session.capability.registry)
    adapter = MCPToolAdapter(transport=_gw_transport)
    provider = AiThemeProvider(adapter)
    session.capability._providers["ai_theme_app"] = provider
    session.capability._initialized = False
    session.capability.initialize()

    client = TestClient(app)
    yield client

    sys.modules.pop("providers.llm.deepseek_provider", None)
    sys.modules.pop("providers.llm", None)
    sys.modules.pop("providers", None)


def test_production_app_health(production_gateway_client):
    """Production create_app() GET /health returns ok."""
    resp = production_gateway_client.get("/health")
    assert resp.status_code == 200


def test_production_app_chat_market(production_gateway_client):
    """Production app POST /chat with market query works."""
    resp = production_gateway_client.post("/chat", json={
        "text": "今天市场怎么样？",
        "session_id": "prod-test",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert "market_in_context=True" in data["reply"]


def test_production_app_sessions_endpoint(production_gateway_client):
    """Production app GET /sessions returns list."""
    resp = production_gateway_client.get("/sessions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_real_init_failure_does_not_crash(failing_gateway_client):
    """Real JuliaSession with failing provider → chat() returns normally."""
    resp = failing_gateway_client.post("/chat", json={
        "text": "今天市场怎么样？",
        "session_id": "fail-test",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    # Returns a response (not empty, not server error)
    assert len(data["reply"]) > 0


def test_real_init_failure_no_market_context(failing_gateway_client):
    """Real session + failing provider → no market context injected."""
    failing_gateway_client.post("/chat", json={
        "text": "大盘怎么看",
        "session_id": "fail-test-2",
    })

    # Mock LLM returns "market_in_context=False" — no market context
    from julia_core.runtime.julia_session import get_session
    session = get_session()
    # No SUCCESSFUL market invocations
    market_success = [
        e for e in session.capability.manager.evidence.entries
        if e.capability_name == "market.snapshot.read" and e.status == "success"
    ]
    assert len(market_success) == 0

    # R0.9.3: Failure evidence IS recorded (unavailable status)
    failure_evidence = [
        e for e in session.capability.manager.evidence.entries
        if e.capability_name == "market.snapshot.read" and e.status == "unavailable"
    ]
    assert len(failure_evidence) >= 1, (
        "Provider failure should record evidence with status=unavailable"
    )
