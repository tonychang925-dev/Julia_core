"""C1-R2.7 ai_theme degradation semantics contracts.

Protected contracts: C-08 / C-12 / ADR-037 / REV2 R2-I09/R2-I10/R2-I12
Expected baseline: PASS for deterministic/read-only ai_theme capability surface
and preservation of successful observations; XFAIL for lossless provider-native
partial/unavailable/empty/stale/source provenance semantics not yet implemented.
Known gaps: A/B-P0 ai_theme failure collapse from conformance audit; Codex-B
AT-R0 confirmed alerts/snapshot paths can collapse dependency failure into [] or
fallback payloads.
Resolving phase: R2-P6, with ai_theme adapter AT-R1/AT-R3 handoff fixtures.

TC-ID: C1-R2.7-AITHEME-001 ai_theme exposes deterministic read-only operations only
TC-ID: C1-R2.7-AITHEME-002 provider exception/failure must not become success+empty
TC-ID: C1-R2.7-AITHEME-003 partial source failure must remain explicit and preserve useful output
TC-ID: C1-R2.7-AITHEME-004 source_records map to future C-12 Evidence, not Julia identity/memory
TC-ID: C1-R2.7-AITHEME-005 empty/stale/unavailable data states must be distinguishable
TC-ID: C1-R2.7-AITHEME-006 Julia-side wrapper preserves provider-native degradation fields

These tests intentionally do not import ai_theme_app directly and do not require
a live adapter. ai_theme_app is an external Domain Intelligence Provider; Julia
Core owns ToolResult/Evidence/Trace mapping later, not provider-native DTO classes.
"""

from __future__ import annotations

from typing import Any

import pytest

from julia_core.capability.models import CapabilityLayer, CapabilityRequest
from julia_core.capability.providers.ai_theme import AI_THEME_CAPABILITIES, AiThemeProvider
from julia_core.capability.providers.ai_theme.adapter import CAPABILITY_TO_TOOL, MCPToolAdapter
from julia_core.capability.providers.ai_theme.contract_mapper import IntelligenceContractMapper


class ScriptedMarketAdapter:
    """Tiny provider-boundary fixture: exact capability -> value or exception."""

    def __init__(self, outcomes: dict[str, Any]):
        self.outcomes = outcomes
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def call(self, capability_name: str, arguments: dict[str, Any] | None = None) -> Any:
        args = arguments or {}
        self.calls.append((capability_name, args))
        outcome = self.outcomes.get(capability_name, {})
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def health(self) -> tuple[bool, str]:
        return True, "scripted"


SNAPSHOT_OK = {
    "market_sentiment": "偏弱",
    "active_themes": ["AI Agent"],
    "risk_alerts": ["成交未放量"],
    "top_signals": [],
    "date": "2026-08-26",
}

ALERTS_OK = [
    {
        "id": "dec_fixture_001",
        "level": "alert",
        "source": "workbench",
        "impact": "theme heat rising",
        "confidence": 0.82,
        "prediction_id": "pred_fixture_001",
        "theme_context": {"theme_id": "AI Agent"},
    }
]


# ── Existing safe surface contracts ──────────────────────────────────────────


def test_ai_theme_registered_capabilities_are_read_only_intelligence_observe_scope():
    """TC-ID: C1-R2.7-AITHEME-001. ai_theme v1 must not expose write/trade actions."""
    forbidden_fragments = {"trade.", ".buy", ".sell", ".write", ".execute"}

    for spec in AI_THEME_CAPABILITIES:
        name = spec["name"]
        assert spec["layer"] == CapabilityLayer.INTELLIGENCE
        assert spec["permission_scope"] == "market.observe"
        assert not any(fragment in name for fragment in forbidden_fragments)


def test_ai_theme_adapter_mapping_is_exact_operation_dispatch_not_natural_language_routing():
    """TC-ID: C1-R2.7-AITHEME-001. Adapter maps exact operation IDs, not utterances."""
    adapter = MCPToolAdapter(transport=lambda _tool, _args: {})

    assert adapter.map_capability_to_tool("market.snapshot.read") == "review_market_snapshot"
    assert adapter.map_capability_to_tool("今天市场怎么样？") is None
    assert adapter.map_capability_to_tool("market.intent.resolve") is None
    assert adapter.map_capability_to_tool("market.answer_user") is None

    forbidden_tools = {"market_intent_resolve", "answer_user", "generate_julia_response"}
    assert forbidden_tools.isdisjoint(set(CAPABILITY_TO_TOOL.values()))


@pytest.mark.asyncio
async def test_partial_source_failure_preserves_successful_observations():
    """TC-ID: C1-R2.7-AITHEME-003. Useful source output must not be erased by another source failure."""
    mapper = IntelligenceContractMapper(ScriptedMarketAdapter({
        "market.snapshot.read": SNAPSHOT_OK,
        "market.alert.query": RuntimeError("alerts dependency down"),
    }))

    result = await mapper.observe()

    assert result["capability"] == "market.intelligence.observe"
    summaries = "\n".join(obs.get("summary", "") for obs in result.get("observations", []))
    assert "市场情绪: 偏弱" in summaries
    assert "活跃题材: AI Agent" in summaries


# ── Expected gaps: provider-native degradation semantics ─────────────────────


@pytest.mark.xfail(
    strict=True,
    reason="A/B-P0 ai_theme: source failures are swallowed by IntelligenceContractMapper.observe(); failures/status pending R2-P6 + AT-R3",
)
@pytest.mark.asyncio
async def test_partial_source_failure_is_explicit_not_silent_success():
    """TC-ID: C1-R2.7-AITHEME-003. Partial source failure must be visible to Julia mapping."""
    mapper = IntelligenceContractMapper(ScriptedMarketAdapter({
        "market.snapshot.read": SNAPSHOT_OK,
        "market.alert.query": RuntimeError("alerts dependency down"),
    }))

    result = await mapper.observe()

    assert result["status"] == "partial"
    assert result["data_state"] == "normal"
    assert result["failures"]
    assert result["failures"][0]["source_name"] == "market.alert.query"
    assert result["failures"][0]["status"] == "failed"


@pytest.mark.xfail(
    strict=True,
    reason="A/B-P0 ai_theme: all dependency failures currently collapse to observations=[] without unavailable/error status; pending R2-P6 + AT-R3",
)
@pytest.mark.asyncio
async def test_all_source_failures_do_not_become_empty_success():
    """TC-ID: C1-R2.7-AITHEME-002. Dependency failure must not masquerade as legitimate empty data."""
    mapper = IntelligenceContractMapper(ScriptedMarketAdapter({
        "market.snapshot.read": RuntimeError("snapshot database down"),
        "market.alert.query": RuntimeError("alerts database down"),
    }))

    result = await mapper.observe()

    assert result["status"] in {"unavailable", "error"}
    assert result["data_state"] != "empty"
    assert result["failures"]
    assert result.get("observations") != []


@pytest.mark.xfail(
    strict=True,
    reason="C-12/R2-I12: ai_theme provider-native source_records are not emitted yet; pending AT-R1/AT-R3 and Julia R2-P6 mapping",
)
@pytest.mark.asyncio
async def test_successful_ai_theme_observations_carry_source_records_not_julia_evidence():
    """TC-ID: C1-R2.7-AITHEME-004. Provider source_records later map to C-12 Evidence."""
    mapper = IntelligenceContractMapper(ScriptedMarketAdapter({
        "market.snapshot.read": SNAPSHOT_OK,
        "market.alert.query": ALERTS_OK,
    }))

    result = await mapper.observe()

    assert "source_records" in result
    assert result["source_records"]
    assert "evidence" not in result  # ai_theme source material is not Julia canonical Evidence
    for source in result["source_records"]:
        assert {"source_type", "source_name", "source_ref", "as_of", "observed_at", "freshness", "provenance"} <= set(source)


@pytest.mark.xfail(
    strict=True,
    reason="R2-I10/R2-I12: provider-native data_state normal/empty/stale is not represented yet; pending AT-R1/AT-R3 + R2-P6",
)
@pytest.mark.asyncio
async def test_legitimate_empty_data_is_distinct_from_stale_or_unavailable():
    """TC-ID: C1-R2.7-AITHEME-005. Empty/stale/unavailable are separate provider facts."""
    mapper = IntelligenceContractMapper(ScriptedMarketAdapter({
        "market.snapshot.read": {"market_sentiment": "", "active_themes": [], "risk_alerts": [], "top_signals": []},
        "market.alert.query": [],
    }))

    result = await mapper.observe()

    assert result["status"] == "success"
    assert result["data_state"] == "empty"
    assert result["failures"] == []
    assert result.get("stale") is not True


@pytest.mark.xfail(
    strict=True,
    reason="R2-P6: AiThemeProvider currently wraps legacy mapper output and does not preserve status/data_state/source_records/failures envelope",
)
@pytest.mark.asyncio
async def test_ai_theme_provider_preserves_domain_degradation_envelope_for_julia_mapping():
    """TC-ID: C1-R2.7-AITHEME-006. Julia provider wrapper must not flatten degradation semantics."""
    provider = AiThemeProvider(ScriptedMarketAdapter({
        "market.snapshot.read": SNAPSHOT_OK,
        "market.alert.query": RuntimeError("alerts dependency down"),
    }))

    wrapped = await provider.execute(CapabilityRequest("market.intelligence.observe"))
    data = wrapped["data"]

    assert wrapped["provider"] == "ai_theme_app"
    assert data["status"] == "partial"
    assert data["data_state"] == "normal"
    assert data["failures"]
    assert data["source_records"]
