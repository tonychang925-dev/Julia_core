"""Phase 2.2 Heartbeat Test — Julia's first neural connection to Market Brain.

Verifies: Julia Core MCP Client → ai_theme_app MCP Server → DecisionEnvelope v1.1.

This is the moment Julia first "sees" the market. Not interprets — sees.

Run from ai_theme_app directory (where mcp_server is importable):
    cd /Users/admin/Desktop/ai_theme_app
    PYTHONPATH=.:../julia_core python3 -m pytest ../julia_core/tests/test_market_brain_connection.py -v
"""
import sys
import asyncio
import pytest

# Ensure ai_theme_app is on path (for mcp_server imports)
ai_theme_path = "/Users/admin/Desktop/ai_theme_app"
if ai_theme_path not in sys.path:
    sys.path.insert(0, ai_theme_path)


class TestJuliaHeartbeat:
    """Can Julia connect to Market Brain at all?"""

    @pytest.mark.asyncio
    async def test_julia_can_see_market(self):
        """The moment Julia first connects to ai_theme_app."""
        from julia_core.mcp_client import MarketBrainClient

        brain = MarketBrainClient()

        snapshot = await brain.review_market_snapshot()

        assert snapshot is not None
        assert snapshot.market_sentiment in ("偏强", "偏弱", "中性", "")
        assert len(snapshot.active_themes) >= 0
        print(f"\n[JULIA HEARTBEAT] Market Snapshot received: {snapshot.market_sentiment}")


class TestThemeQuery:
    """Can Julia query a specific theme?"""

    @pytest.mark.asyncio
    async def test_query_robot_theme(self):
        from julia_core.mcp_client import MarketBrainClient

        brain = MarketBrainClient()
        status = await brain.query_theme_status("robot_001")

        assert status is not None
        assert status.heat_score > 0
        assert len(status.leaders) > 0
        print(f"\n[JULIA QUERY] Robot theme: {status.lifecycle}, heat={status.heat_score}")


class TestActiveAlerts:
    """Can Julia see L4 alerts?"""

    @pytest.mark.asyncio
    async def test_list_alerts(self):
        from julia_core.mcp_client import MarketBrainClient

        brain = MarketBrainClient()
        alerts = await brain.list_active_alerts(level="decision")

        assert isinstance(alerts, list)
        assert len(alerts) > 0
        assert alerts[0].level == "decision"
        print(f"\n[JULIA ALERTS] {len(alerts)} active L4 alerts")


class TestExplainDecision:
    """Can Julia explain WHY a decision was made?"""

    @pytest.mark.asyncio
    async def test_explain(self):
        from julia_core.mcp_client import MarketBrainClient

        brain = MarketBrainClient()
        explanation = await brain.explain_decision("dec_20260806_001")

        assert explanation is not None
        assert explanation.supporting_evidence > 0
        assert len(explanation.risk_factors) > 0
        print(f"\n[JULIA EXPLAIN] {explanation.summary}")


class TestSubscription:
    """Can Julia subscribe to observation channels?"""

    @pytest.mark.asyncio
    async def test_subscribe(self):
        from julia_core.mcp_client import MarketBrainClient

        brain = MarketBrainClient()
        state = await brain.subscribe_agent_channel(["AI_AGENT", "SEMICONDUCTOR", "RISK_ALERT"])

        assert state.active
        assert len(state.subscribed) > 0
        print(f"\n[JULIA SUBSCRIBE] Channels: {state.subscribed}")


class TestV1_1Schema:
    """Do MCP responses contain v1.1 fields?"""

    @pytest.mark.asyncio
    async def test_causal_chain_present(self):
        """v1.1 field: causal_chain must be present on DecisionEnvelope."""
        from julia_core.mcp_client import MarketBrainClient

        brain = MarketBrainClient()
        alerts = await brain.list_active_alerts(level="decision")

        for alert in alerts:
            assert hasattr(alert, 'causal_chain'), f"DecisionEnvelope {alert.id} missing causal_chain"
            assert hasattr(alert, 'theme_context'), f"DecisionEnvelope {alert.id} missing theme_context"
            assert hasattr(alert, 'prediction_id'), f"DecisionEnvelope {alert.id} missing prediction_id"
        print(f"\n[JULIA SCHEMA] All {len(alerts)} alerts have v1.1 fields")


if __name__ == "__main__":
    # Allow running directly: python3 tests/test_market_brain_connection.py
    asyncio.run(TestJuliaHeartbeat().test_julia_can_see_market())
    asyncio.run(TestThemeQuery().test_query_robot_theme())
    asyncio.run(TestActiveAlerts().test_list_alerts())
    asyncio.run(TestExplainDecision().test_explain())
    asyncio.run(TestSubscription().test_subscribe())
    asyncio.run(TestV1_1Schema().test_causal_chain_present())
    print("\n✅ Julia heartbeat — all 6 tests passed")
