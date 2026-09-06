"""RD1-L1-F2 deterministic Research Desk ingress regressions."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from julia_core.capability.models import ProviderExecutionOutcome, ToolResultStatus
from julia_core.runtime.julia_session import JuliaSession


_I4_PATH = Path(__file__).with_name("test_i4_same_turn_research_orchestration.py")
_spec = importlib.util.spec_from_file_location("rd1_i4_regressions", _I4_PATH)
assert _spec is not None and _spec.loader is not None
I4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(I4)


CONTROLLED_REQUEST = (
    "请研究2026年9月4日“国产DUV光刻机”这一半导体设备主题的市场变化，"
    "形成事实研究简报；不要给出任何交易建议。"
)


@pytest.mark.parametrize(
    "text",
    [
        "请研究国产DUV光刻机最近的市场变化",
        "调研某个市场事件",
        "形成事实研究简报",
        "查证某一市场事件",
        "围绕某主题做事实研究",
        CONTROLLED_REQUEST,
    ],
)
def test_l1_f2_t01_t02_explicit_research_desk_phrases_admit_deterministically(text):
    call = json.loads(JuliaSession._build_research_desk_resolver_call(text))
    assert call["name"] == "market.event.resolve"
    assert call["arguments"]["query"] == " ".join(text.split())


def test_l1_f2_t02_controlled_request_extracts_only_frozen_resolver_fields():
    call = json.loads(JuliaSession._build_research_desk_resolver_call(CONTROLLED_REQUEST))
    assert call["arguments"] == {
        "query": " ".join(CONTROLLED_REQUEST.split()),
        "normalized_theme": "国产DUV光刻机",
        "time_window": {"date": "2026-09-04"},
    }


@pytest.mark.asyncio
async def test_l1_f2_t02_full_chain_needs_no_first_pass_model_tool_call(monkeypatch):
    class FinalContinuationProvider(I4.ResearchCognitionProvider):
        def __init__(self):
            super().__init__()
            self.stream_calls = []

        async def stream_async(self, messages):
            self.stream_calls.append(list(messages))
            yield "deterministic same-turn research answer"

    cognition = FinalContinuationProvider()
    market = I4.MarketProvider()
    research = I4.ResearchProvider(mode="report_only")
    session = I4.session(monkeypatch, market=market, research=research, cognition=cognition)
    runtime, repository = I4.conversation()
    context = runtime.begin_turn_streaming(
        conversation_id="conv",
        turn_id="turn-l1-f2",
        modality="text",
        input=CONTROLLED_REQUEST,
    )
    products = []
    chunks = [
        chunk
        async for chunk in session.process_stream(
            CONTROLLED_REQUEST,
            context.history,
            conversation_id="conv",
            turn_id="turn-l1-f2",
            interaction=context.interaction,
            research_product_hook=I4.research_hook,
            product_sink=products.append,
        )
    ]
    result = runtime.commit_streaming_turn(context, "".join(chunks))

    assert chunks == ["deterministic same-turn research answer"]
    assert len(cognition.stream_calls) == 1
    assert "```tool_call" not in json.dumps(cognition.stream_calls[0], ensure_ascii=False)
    assert [request.capability_id for request in market.requests] == [
        "market.event.resolve",
        "market.event.read",
    ]
    assert market.requests[1].arguments == {"event_id": 501}
    assert len(research.requests) == 1
    assert products[0]["research_brief"]["key_drivers"][0]["support_level"] == "REPORT_ONLY_LEAD"
    assert result.conversation_id == "conv" and result.turn_id == "turn-l1-f2"
    transcript = repository.find_turn("conv", "turn-l1-f2")
    assert [message.role for message in transcript] == ["user", "assistant"]


@pytest.mark.parametrize(
    "text",
    [
        "今天市场怎么样",
        "看看盘面",
        "最近什么方向",
        "有什么风险",
        "市场预警",
    ],
)
def test_l1_f2_t03_t16_ordinary_market_status_is_not_research_desk(text):
    assert JuliaSession._build_research_desk_resolver_call(text) is None


@pytest.mark.asyncio
async def test_l1_f2_t03_ordinary_market_status_keeps_existing_two_pass_behavior(monkeypatch):
    provider = I4.OrdinaryProvider()
    market = I4.MarketProvider()
    research = I4.ResearchProvider()
    session = I4.session(monkeypatch, market=market, research=research, cognition=provider)
    products = []
    chunks = [
        chunk
        async for chunk in session.process_stream(
            "今天市场怎么样",
            [],
            conversation_id="conv",
            turn_id="turn-status",
            research_product_hook=I4.research_hook,
            product_sink=products.append,
        )
    ]
    assert len(provider.stream_calls) == 2
    assert chunks == ["ordinary answer"]
    assert market.requests == [] and research.requests == [] and products == []


@pytest.mark.parametrize("text", ["能买吗", "给我买点", "目标价多少", "仓位怎么配"])
def test_l1_f2_t04_trading_requests_do_not_enter_research_desk(text):
    assert JuliaSession._build_research_desk_resolver_call(text) is None


@pytest.mark.asyncio
async def test_l1_f2_t04_trading_request_uses_ordinary_cognition_without_research(monkeypatch):
    provider = I4.OrdinaryProvider()
    market = I4.MarketProvider()
    research = I4.ResearchProvider()
    session = I4.session(monkeypatch, market=market, research=research, cognition=provider)
    chunks = [
        chunk
        async for chunk in session.process_stream(
            "目标价多少",
            [],
            conversation_id="conv",
            turn_id="turn-trading",
        )
    ]
    assert chunks == ["ordinary answer"]
    assert market.requests == [] and research.requests == []


@pytest.mark.asyncio
async def test_l1_f2_t07_t08_t09_resolver_stop_states_stop_before_d1(monkeypatch):
    class UnavailableResolverMarket(I4.MarketProvider):
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

    cases = [
        I4.MarketProvider(state="UNRESOLVED"),
        I4.MarketProvider(state="AMBIGUOUS"),
        UnavailableResolverMarket(),
    ]
    for market in cases:
        research = I4.ResearchProvider()
        session = I4.session(monkeypatch, market=market, research=research)
        chunks = [
            chunk
            async for chunk in session.process_stream(
                CONTROLLED_REQUEST,
                [],
                conversation_id="conv",
                turn_id="turn-stop",
            )
        ]
        assert chunks
        assert [request.capability_id for request in market.requests] == ["market.event.resolve"]
        assert research.requests == []


@pytest.mark.asyncio
async def test_l1_f2_t10_market_selected_event_id_is_only_identity_source(monkeypatch):
    market = I4.MarketProvider()
    research = I4.ResearchProvider(mode="report_only")
    session = I4.session(monkeypatch, market=market, research=research)
    products = []
    [
        chunk
        async for chunk in session.process_stream(
            CONTROLLED_REQUEST,
            [],
            conversation_id="conv",
            turn_id="turn-market-id",
            research_product_hook=I4.research_hook,
            product_sink=products.append,
        )
    ]
    assert market.requests[0].arguments.get("event_id") is None
    assert market.requests[1].arguments == {"event_id": 501}
    assert research.requests[0].provenance["market_event_id"] == 501
    assert products[0]["trace"]["capability_request_ids"]


@pytest.mark.asyncio
async def test_l1_f2_t14_model_generated_market_tool_call_still_works(monkeypatch):
    market = I4.MarketProvider()
    research = I4.ResearchProvider(mode="report_only")
    provider = I4.ResearchCognitionProvider()
    session = I4.session(monkeypatch, market=market, research=research, cognition=provider)
    products = []
    chunks = [
        chunk
        async for chunk in session.process_stream(
            "今天半导体设备为什么变化？",
            [],
            conversation_id="conv",
            turn_id="turn-model-call",
            research_product_hook=I4.research_hook,
            product_sink=products.append,
        )
    ]
    assert chunks == ["Julia's same-turn research answer retains the governed uncertainty."]
    assert len(provider.stream_calls) == 2
    assert [request.capability_id for request in market.requests] == [
        "market.event.resolve",
        "market.event.read",
    ]
    assert len(research.requests) == 1


@pytest.mark.asyncio
async def test_l1_f2_t15_file_capability_behavior_remains_unchanged(monkeypatch, tmp_path):
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
