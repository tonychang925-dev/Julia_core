"""RD1-L1-F2 Research Desk regressions — P3-CC I2-B model-owned ingress.

I2-A retired the deterministic user-text Research Desk ingress
(``_build_research_desk_resolver_call`` / keyword admission). I2-B retires the
last pre-cognitive Market semantic routers and fences the Context OS Market
seam. Research execution therefore requires Julia cognition to emit the
governed top-level ``research.run_brief`` capability request; user-text
keywords are never authority.

Reclassification (I2-B §18/§23):
  A. REMOVED  — deterministic keyword admission of Research; "no first-pass
     model tool call needed"; exact resolver-field extraction. Replaced by
     negative zero-authority tests: research/market/trading wording + model
     silent → zero Research / Market execution.
  B. PRESERVED under model-owned ingress — full same-turn chain
     (resolve → read → enrich → C1 → C2 → brief), selected_event_id
     provenance, UNRESOLVED / AMBIGUOUS / provider-unavailable typed stops
     (ResearchTurnNotReady), read-failure fail-closed, product trace.
  D. REMOVED  — legacy exact-phrase admission patterns.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from julia_core.capability.models import ProviderExecutionOutcome, ToolResultStatus
from julia_core.runtime.julia_session import ResearchTurnNotReady


_I4_PATH = Path(__file__).with_name("test_i4_same_turn_research_orchestration.py")
_spec = importlib.util.spec_from_file_location("rd1_i4_regressions", _I4_PATH)
assert _spec is not None and _spec.loader is not None
I4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(I4)


CONTROLLED_REQUEST = (
    "请研究2026年9月4日“国产DUV光刻机”这一半导体设备主题的市场变化，"
    "形成事实研究简报；不要给出任何交易建议。"
)

RESEARCH_WORDING = [
    "请研究国产DUV光刻机最近的市场变化",
    "调研某个市场事件",
    "形成事实研究简报",
    "查证某一市场事件",
    "围绕某主题做事实研究",
    CONTROLLED_REQUEST,
]

MARKET_TRIGGERS = [
    "今天市场怎么样",
    "看看盘面",
    "最近什么方向",
    "有什么风险",
    "市场预警",
    "看看盘面，有什么风险？",
]

TRADING_WORDING = ["能买吗", "给我买点", "目标价多少", "仓位怎么配"]

NEGATED_RESEARCH_WORDING = [
    "不要调用研究能力。",
    "不要研究市场。",
    "这次不需要做市场研究。",
    "我说的是“不要研究”，不是让你研究。",
    "只回答我这句话，不要进入市场研究流程。",
]


async def _consume(session, text, *, conversation_id, turn_id):
    """Consume one full streaming turn; returns (chunks, products)."""
    products = []
    chunks = [
        chunk
        async for chunk in session.process_stream(
            text,
            [],
            conversation_id=conversation_id,
            turn_id=turn_id,
            research_product_hook=I4.research_hook,
            product_sink=products.append,
        )
    ]
    return chunks, products


# ── Class A replacements: wording alone is NOT authority ─────────────────────

@pytest.mark.parametrize("text", RESEARCH_WORDING)
@pytest.mark.asyncio
async def test_research_wording_model_silent_no_research_execution(monkeypatch, text):
    """Explicit research wording + model emits NO capability → zero Research /
    zero Market execution and one ordinary answer pass."""
    provider = I4.OrdinaryProvider()
    market = I4.MarketProvider()
    research = I4.ResearchProvider()
    session = I4.session(monkeypatch, market=market, research=research, cognition=provider)
    chunks, products = await _consume(
        session, text, conversation_id="conv", turn_id="turn-silent-research"
    )
    assert chunks == ["ordinary answer"]
    assert len(provider.stream_calls) == 1
    assert market.requests == [] and research.requests == []
    assert products == []


@pytest.mark.parametrize("text", MARKET_TRIGGERS)
@pytest.mark.asyncio
async def test_market_trigger_model_silent_no_prefetch(monkeypatch, text):
    """Dynamic Proof A/B: legacy market trigger text alone + model emits no
    capability → ordinary cognition with ZERO capability execution and ZERO
    pre-cognitive prefetch (seam is fenced in julia_session)."""
    provider = I4.OrdinaryProvider()
    market = I4.MarketProvider()
    research = I4.ResearchProvider()
    session = I4.session(monkeypatch, market=market, research=research, cognition=provider)
    chunks, products = await _consume(
        session, text, conversation_id="conv", turn_id="turn-market-silent"
    )
    assert chunks == ["ordinary answer"]
    assert len(provider.stream_calls) == 1
    assert market.requests == [] and research.requests == []
    assert products == []


@pytest.mark.parametrize("text", TRADING_WORDING)
@pytest.mark.asyncio
async def test_trading_wording_model_silent_ordinary_cognition(monkeypatch, text):
    provider = I4.OrdinaryProvider()
    market = I4.MarketProvider()
    research = I4.ResearchProvider()
    session = I4.session(monkeypatch, market=market, research=research, cognition=provider)
    chunks, products = await _consume(
        session, text, conversation_id="conv", turn_id="turn-trading-silent"
    )
    assert chunks == ["ordinary answer"]
    assert market.requests == [] and research.requests == []
    assert products == []


@pytest.mark.parametrize("text", NEGATED_RESEARCH_WORDING)
@pytest.mark.asyncio
async def test_negated_research_wording_model_silent_no_research(monkeypatch, text):
    provider = I4.OrdinaryProvider()
    market = I4.MarketProvider()
    research = I4.ResearchProvider()
    session = I4.session(monkeypatch, market=market, research=research, cognition=provider)
    chunks, products = await _consume(
        session, text, conversation_id="conv", turn_id="turn-negated-silent"
    )
    assert chunks == ["ordinary answer"]
    assert market.requests == [] and research.requests == []
    assert products == []


# ── Class B: model-owned research.run_brief → full same-turn chain ──────────

@pytest.mark.asyncio
async def test_model_emits_research_run_brief_full_same_turn_chain(monkeypatch):
    """Julia cognition selects research.run_brief → governed chain
    resolve → read → enrich → C1 → C2 → research.brief.v1 product."""
    market = I4.MarketProvider()
    research = I4.ResearchProvider(mode="report_only")
    session = I4.session(monkeypatch, market=market, research=research)
    runtime, repository = I4.conversation()
    ctx = runtime.begin_turn_streaming(
        conversation_id="conv", turn_id="turn-full-chain", modality="text",
        input=CONTROLLED_REQUEST,
    )
    products = []
    chunks = [
        chunk
        async for chunk in session.process_stream(
            CONTROLLED_REQUEST,
            ctx.history,
            conversation_id="conv",
            turn_id="turn-full-chain",
            interaction=ctx.interaction,
            research_product_hook=I4.research_hook,
            product_sink=products.append,
        )
    ]
    result = runtime.commit_streaming_turn(ctx, "".join(chunks))

    assert chunks == ["Julia's same-turn research answer retains the governed uncertainty."]
    assert [request.capability_id for request in market.requests] == [
        "market.event.resolve",
        "market.event.read",
    ]
    assert market.requests[1].arguments == {"event_id": 501}
    assert len(research.requests) == 1
    assert len(products) == 1
    assert products[0]["contract_version"] == "julia.product.events.v1"
    assert products[0]["research_brief"]["contract_version"] == "research.brief.v1"
    assert products[0]["research_brief"]["key_drivers"][0]["support_level"] == "REPORT_ONLY_LEAD"
    assert products[0]["trace"]["capability_request_ids"]
    assert result.conversation_id == "conv" and result.turn_id == "turn-full-chain"
    transcript = repository.find_turn("conv", "turn-full-chain")
    assert [message.role for message in transcript] == ["user", "assistant"]


@pytest.mark.asyncio
async def test_neutral_text_model_selects_research_chain(monkeypatch):
    """Dynamic Proof D: neutral text + model emits research.run_brief → full
    I2-A chain (keywords are NOT required for model-owned selection)."""
    market = I4.MarketProvider()
    research = I4.ResearchProvider(mode="report_only")
    session = I4.session(monkeypatch, market=market, research=research)
    chunks, products = await _consume(
        session, "帮我把这件事搞清楚", conversation_id="conv", turn_id="turn-neutral"
    )
    assert chunks == ["Julia's same-turn research answer retains the governed uncertainty."]
    assert [request.capability_id for request in market.requests] == [
        "market.event.resolve",
        "market.event.read",
    ]
    assert len(research.requests) == 1
    assert len(products) == 1


@pytest.mark.asyncio
async def test_market_selected_event_id_is_only_identity_source(monkeypatch):
    """Class B: the resolver's selected_event_id is the sole identity source for
    read and research provenance (no user-text-derived event identity)."""
    market = I4.MarketProvider()
    research = I4.ResearchProvider(mode="report_only")
    session = I4.session(monkeypatch, market=market, research=research)
    _, products = await _consume(
        session, CONTROLLED_REQUEST, conversation_id="conv", turn_id="turn-market-id"
    )
    assert market.requests[0].arguments.get("event_id") is None
    assert market.requests[1].arguments == {"event_id": 501}
    assert research.requests[0].provenance["market_event_id"] == 501
    assert products[0]["trace"]["capability_request_ids"]


# ── Class B: typed fail-closed stops (ResearchTurnNotReady, no fallback) ─────

class _UnavailableResolverMarket(I4.MarketProvider):
    async def execute(self, request):
        self.requests.append(request)
        if request.capability_id != "market.event.resolve":
            raise AssertionError("resolver failure must stop before read")
        return ProviderExecutionOutcome(
            status=ToolResultStatus.UNAVAILABLE,
            structured_output=I4.envelope(
                "market.event.resolve",
                {"state": "UPSTREAM_UNAVAILABLE"},
                "unavailable",
            ),
            error={"code": "UPSTREAM_UNAVAILABLE", "message": "market unavailable"},
        )


@pytest.mark.asyncio
async def test_resolver_stop_states_raise_typed_research_turn_not_ready(monkeypatch):
    """UNRESOLVED / AMBIGUOUS / provider-unavailable resolver stops must stop
    cognition with ResearchTurnNotReady BEFORE read/research — and must NOT
    degrade into a generic TypeError or an ordinary-answer fallback."""
    for market in (
        I4.MarketProvider(state="UNRESOLVED"),
        I4.MarketProvider(state="AMBIGUOUS"),
        _UnavailableResolverMarket(),
    ):
        research = I4.ResearchProvider()
        session = I4.session(monkeypatch, market=market, research=research)
        with pytest.raises(ResearchTurnNotReady):
            [
                chunk
                async for chunk in session.process_stream(
                    CONTROLLED_REQUEST,
                    [],
                    conversation_id="conv",
                    turn_id="turn-stop",
                )
            ]
        assert [request.capability_id for request in market.requests] == ["market.event.resolve"]
        assert research.requests == []


@pytest.mark.asyncio
async def test_read_failure_stops_research_typed(monkeypatch):
    """market.event.read failure must stop the chain typed (ResearchTurnNotReady)
    with zero enrichment."""
    market = I4.MarketProvider(read_status=ToolResultStatus.UNAVAILABLE)
    research = I4.ResearchProvider()
    session = I4.session(monkeypatch, market=market, research=research)
    with pytest.raises(ResearchTurnNotReady):
        [
            chunk
            async for chunk in session.process_stream(
                CONTROLLED_REQUEST,
                [],
                conversation_id="conv",
                turn_id="turn-read-fail",
            )
        ]
    assert [request.capability_id for request in market.requests] == [
        "market.event.resolve",
        "market.event.read",
    ]
    assert research.requests == []


# ── Direct internal sub-capability: no automatic escalation ─────────────────

class _DirectResolveCognition:
    """Model emits an ordinary governed market.event.resolve only — never
    research.run_brief. C2 must never be reached."""

    def __init__(self):
        self.stream_calls = []

    async def stream_async(self, messages):
        self.stream_calls.append(list(messages))
        if len(self.stream_calls) == 1:
            call = {"name": "market.event.resolve", "arguments": {"query": "x"}}
            yield f"```tool_call\n{json.dumps(call, ensure_ascii=False)}\n```"
        else:
            yield "direct resolve answer"

    def chat(self, messages, **kwargs):  # pragma: no cover - must not be called
        raise AssertionError("direct market sub-capability must not escalate to C2")


@pytest.mark.asyncio
async def test_direct_market_event_resolve_no_escalation(monkeypatch):
    """Dynamic Proof F: a model-selected market.event.resolve remains an ordinary
    governed capability. NO automatic read / enrich / C2 / Research Brief."""
    market = I4.MarketProvider()
    research = I4.ResearchProvider()
    provider = _DirectResolveCognition()
    session = I4.session(monkeypatch, market=market, research=research, cognition=provider)
    chunks, products = await _consume(
        session, "今天半导体设备为什么变化？", conversation_id="conv", turn_id="turn-direct"
    )
    assert chunks == ["direct resolve answer"]
    assert [request.capability_id for request in market.requests] == ["market.event.resolve"]
    assert research.requests == []
    assert products == []


# ── Dynamic Proof C: model-selected ordinary Market capability remains valid ─

class _SnapshotCognition:
    """Model emits the governed ordinary market capability market.snapshot.read."""

    def __init__(self):
        self.stream_calls = []

    async def stream_async(self, messages):
        self.stream_calls.append(list(messages))
        if len(self.stream_calls) == 1:
            call = {"name": "market.snapshot.read", "arguments": {}}
            yield f"```tool_call\n{json.dumps(call, ensure_ascii=False)}\n```"
        else:
            yield "snapshot answer"

    def chat(self, messages, **kwargs):  # pragma: no cover - must not be called
        raise AssertionError("ordinary market capability must not escalate to C2")


class _SnapshotMarketProvider:
    """Serves only market.snapshot.read; resolve/read are not reachable."""

    def __init__(self):
        self.requests = []

    async def health(self):
        return True, "snapshot fixture"

    async def execute(self, request):
        self.requests.append(request)
        if request.capability_id != "market.snapshot.read":
            raise AssertionError(f"unexpected market capability: {request.capability_id}")
        return ProviderExecutionOutcome(
            status=ToolResultStatus.SUCCESS,
            structured_output=I4.envelope("market.snapshot.read", {
                "sentiment": "偏弱",
                "active_themes": ["AI Agent"],
                "risk_alerts": [],
            }),
        )


@pytest.mark.asyncio
async def test_model_selected_market_snapshot_read_executes_as_governed_capability(monkeypatch):
    """Model explicitly emits market.snapshot.read (user text is irrelevant) →
    typed governed execution + authorization + ToolResult continuation. Market
    capability behavior itself is NOT disabled by the semantic cutover; only
    Runtime user-text market selection is forbidden."""
    market = _SnapshotMarketProvider()
    research = I4.ResearchProvider()
    provider = _SnapshotCognition()
    session = I4.session(monkeypatch, market=market, research=research, cognition=provider)
    chunks, products = await _consume(
        session, "今天市场怎么样", conversation_id="conv", turn_id="turn-snapshot"
    )
    assert chunks == ["snapshot answer"]
    assert [request.capability_id for request in market.requests] == ["market.snapshot.read"]
    assert research.requests == []
    assert products == []


# ── Class B: file capability behavior unchanged (non-research) ──────────────

@pytest.mark.asyncio
async def test_file_capability_behavior_remains_unchanged(monkeypatch, tmp_path):
    target = tmp_path / "note.txt"
    target.write_text("file evidence", encoding="utf-8")

    class FileToolProvider:
        def __init__(self):
            self.stream_calls = []

        async def stream_async(self, messages):
            self.stream_calls.append(list(messages))
            if len(self.stream_calls) == 1:
                call = {"name": "file.read", "arguments": {"path": str(target)}}
                yield f"```tool_call\n{json.dumps(call, ensure_ascii=False)}\n```"
            else:
                yield "file answer"

    provider = FileToolProvider()
    market = I4.MarketProvider()
    research = I4.ResearchProvider()
    session = I4.session(monkeypatch, market=market, research=research, cognition=provider)
    chunks = [
        chunk
        async for chunk in session.process_stream(
            str(target),
            [],
            conversation_id="conv",
            turn_id="turn-file",
        )
    ]
    assert chunks == ["file answer"]
    assert len(provider.stream_calls) == 2
    assert market.requests == [] and research.requests == []
