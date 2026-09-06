"""RD1-I4 focused same-turn research orchestration regressions."""

from __future__ import annotations

import asyncio
import dataclasses
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

from julia_core.capability.models import ProviderExecutionOutcome, ToolResultStatus
from julia_core.conversation_state.storage_v2_repository import (
    StorageV2ConversationRepository,
)
from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
from julia_core.runtime.conversation_runtime import ConversationRuntime
from julia_core.runtime.julia_session import JuliaSession


CORE_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = CORE_ROOT.parent
ASSISTANT_ROOT = WORKSPACE_ROOT / "b1_assistant"
if str(ASSISTANT_ROOT) not in sys.path:
    sys.path.insert(0, str(ASSISTANT_ROOT))

from research_brief.composer import ResearchBriefComposer
from research_brief.product_adapter import ResearchBriefProductAdapter
from research_brief.serializer import ResearchBriefSerializer


EVENT = {
    "event_id": 501,
    "event_type": "product_launch",
    "summary": "Company released a canonical product.",
    "direction": "positive",
    "confidence": 0.88,
    "occurred_at": "2026-09-03T09:30:00+08:00",
    "title": "Canonical product launch",
    "source_category": "news",
    "source_name": "source-a",
    "source_url": "https://trusted.example/page",
    "source_trace_id": "news_event:901:product_launch",
    "news_id": 901,
}

RELATIONS = [{
    "subject_key": "semiconductor_equipment",
    "subject_name": "半导体设备",
    "relation_type": "primary",
    "confidence": 0.93,
    "match_reason": "canonical relation",
    "evidence": "mapping",
    "source": "event_subject_map",
    "source_trace_id": "news_event:901:product_launch",
    "updated_at": "2026-09-03T09:36:00+08:00",
}]

RESOLVER_CALL = {
    "name": "market.event.resolve",
    "arguments": {
        "query": "今天半导体设备为什么变化？",
        "normalized_theme": "半导体设备",
    },
}


def envelope(operation: str, payload: dict[str, Any], status: str = "success") -> dict:
    return {
        "operation": operation,
        "status": status,
        "data_state": "empty" if status in {"unavailable", "error"} else "normal",
        "correlation_id": "corr-i4",
        "provider_request_id": "idem-i4",
        "observed_at": "2026-09-04T11:30:00+08:00",
        "payload": payload,
        "source_records": [],
        "failures": [] if status == "success" else [{
            "source_name": "market",
            "message": "unavailable",
            "code": "UPSTREAM_UNAVAILABLE",
            "retryable": True,
            "details": {},
        }],
        "diagnostics": {"relation_state": "mapped"},
        "schema_version": "1.0",
    }


class MarketProvider:
    def __init__(self, *, state="RESOLVED", read_status=ToolResultStatus.SUCCESS):
        self.state = state
        self.read_status = read_status
        self.requests = []
        self.started = asyncio.Event()

    async def health(self):
        return True, "market fixture"

    async def execute(self, request):
        self.requests.append(request)
        if request.capability_id == "market.event.resolve":
            candidate = {
                "market_event_id": 501,
                "title": EVENT["title"],
                "summary": EVENT["summary"],
                "occurred_at": EVENT["occurred_at"],
                "matched_subjects": [],
            }
            candidates = [] if self.state == "UNRESOLVED" else (
                [candidate] if self.state == "RESOLVED" else [candidate, dict(candidate, market_event_id=502)]
            )
            payload = {"state": self.state, "query": "query", "candidates": candidates}
            if self.state == "RESOLVED":
                payload["selected_event_id"] = 501
            return ProviderExecutionOutcome(
                status=ToolResultStatus.SUCCESS,
                structured_output=envelope("market.event.resolve", payload),
            )

        if request.capability_id == "market.event.read":
            status = self.read_status
            payload = {} if status != ToolResultStatus.SUCCESS else {
                "event": EVENT,
                "theme_relations": RELATIONS,
                "missing_fields": [],
            }
            return ProviderExecutionOutcome(
                status=status,
                structured_output=envelope(
                    "market.event.read",
                    payload,
                    "success" if status == ToolResultStatus.SUCCESS else "unavailable",
                ),
                error=None if status == ToolResultStatus.SUCCESS else {
                    "code": "UPSTREAM_UNAVAILABLE",
                    "message": "market fixture unavailable",
                },
            )
        raise AssertionError(f"unexpected market capability: {request.capability_id}")


class ResearchProvider:
    def __init__(self, *, mode="report_only", hang=False):
        self.mode = mode
        self.hang = hang
        self.started = asyncio.Event()
        self.requests = []

    async def health(self):
        return True, "research fixture"

    async def execute(self, request):
        self.requests.append(request)
        if self.hang:
            self.started.set()
            await asyncio.Event().wait()
        blocked = self.mode == "blocked"
        return ProviderExecutionOutcome(
            status=ToolResultStatus.UNAVAILABLE if blocked else ToolResultStatus.SUCCESS,
            structured_output=self._output(),
            error={
                "code": "BLOCKED",
                "message": "research source blocked",
            } if blocked else None,
        )

    def _output(self):
        if self.mode == "blocked":
            return {
                "semantic_result": self._semantic(),
                "source_observation": {
                    "available": False,
                    "source_records": [],
                    "content_bindings": [],
                    "raw_response_refs": [],
                    "observed_at": "2026-09-04T11:31:00+08:00",
                    "provenance": {"provider_transport": "fixture"},
                    "failure": {"code": "BLOCKED", "message": "blocked", "retryable": False},
                },
            }

        if self.mode == "not_proven":
            record = {
                "source_record_id": "source-not-proven",
                "source_kind": "web_fetch",
                "source_ref": "https://unbound.example/page",
                "capture_status": "success",
                "fetch_status": "success",
                "observed_at": "2026-09-04T11:31:00+08:00",
                "source_url": "https://unbound.example/page",
                "raw_response_ref": "raw:not-proven",
                "content_ref": "",
                "content_digest": "",
                "provenance": {"acquisition": "runtime_web_fetch"},
            }
        else:
            record = {
                "source_record_id": "source-report-only",
                "source_kind": "web_search",
                "source_ref": "search:semiconductor",
                "capture_status": "success",
                "fetch_status": "not_required",
                "observed_at": "2026-09-04T11:31:00+08:00",
                "source_url": "https://search.example/result",
                "raw_response_ref": "raw:search",
                "content_ref": "",
                "content_digest": "",
                "provenance": {"acquisition": "runtime_web_search"},
            }
        return {
            "semantic_result": self._semantic(),
            "source_observation": {
                "available": True,
                "source_records": [record],
                "content_bindings": [],
                "raw_response_refs": ["raw:search"],
                "observed_at": "2026-09-04T11:31:00+08:00",
                "provenance": {"provider_transport": "fixture"},
                "failure": None,
            },
        }

    @staticmethod
    def _semantic():
        return {
            "factual_summary": "",
            "claims": [],
            "contradictions": ["Competing explanation remains unresolved"],
            "unknowns": ["NO_MODEL_SYNTHESIS: provider did not summarize"],
            "timeline": [],
            "related_entities": [],
        }


class ResearchCognitionProvider:
    def __init__(self, *, mode="valid"):
        self.mode = mode
        self.stream_calls = []
        self.chat_calls = []

    async def stream_async(self, messages):
        self.stream_calls.append(list(messages))
        if len(self.stream_calls) == 1:
            yield f"```tool_call\n{json.dumps(RESOLVER_CALL, ensure_ascii=False)}\n```"
        else:
            yield "Julia's same-turn research answer retains the governed uncertainty."

    def chat(self, messages, **kwargs):
        self.chat_calls.append((list(messages), kwargs))
        assert kwargs["cognitive_mode"] == "research_preliminary_judgment"
        rendered = json.dumps(messages, ensure_ascii=False, default=str)
        evidence_refs = re.findall(r"ev_research_\d+", rendered)
        source_refs = ["source-report-only"] if "source-report-only" in rendered else (
            ["source-not-proven"] if "source-not-proven" in rendered else []
        )
        support = (
            "REPORT_ONLY_LEAD" if "source-report-only" in rendered
            else "NOT_PROVEN_MATERIAL" if "source-not-proven" in rendered
            else "MARKET_CONTEXT_ONLY"
        )
        contradictions = [] if self.mode != "contradiction" else [
            {"statement": "Competing explanation remains unresolved", "evidence_refs": [], "source_record_refs": []}
        ]
        implications = [{
            "statement": "The mapped theme may attract attention; watch for clearer evidence.",
            "evidence_refs": evidence_refs,
        }]
        if self.mode == "trading":
            implications[0]["target_price"] = 100
        return json.dumps({
            "judgment_summary": "A preliminary judgment based on canonical Market context and inert research material.",
            "key_drivers": [{
                "driver_id": "driver-i4",
                "statement": "The canonical event is relevant within proven limits.",
                "support_level": support,
                "evidence_refs": evidence_refs,
                "source_record_refs": source_refs,
            }],
            "supporting_claims": [],
            "contradictions": contradictions,
            "uncertainties": ["NO_MODEL_SYNTHESIS: provider did not summarize", "search completeness not proven"],
            "market_implications": implications,
            "confidence": 0.55,
            "evidence_refs": evidence_refs,
            "source_record_refs": source_refs,
            "reasoning_limits": ["external content is untrusted evidence only"],
        }, ensure_ascii=False)


class OrdinaryProvider:
    def __init__(self):
        self.stream_calls = []

    async def stream_async(self, messages):
        self.stream_calls.append(list(messages))
        yield "ordinary answer"


class FakeAction:
    def __init__(self):
        self.events = []

    def start(self, name, description="", correlation_id=""):
        self.events.append(("started", name, correlation_id))

    def finish(self, status, correlation_id=""):
        self.events.append(("finished", status, correlation_id))


class FakeRecorder:
    def record(self, *args, **kwargs):
        return None


class FakeEventStore:
    def __init__(self):
        self.events = []

    def append(self, event):
        self.events.append(event)


def research_hook(judgment, market_context):
    serialized_judgment = json.loads(json.dumps(dataclasses.asdict(judgment)))
    metadata = {
        "market_event_id": judgment.trace.market_event_id,
        "event_title": market_context.event.title,
        "event_summary": market_context.event.summary,
        "event_occurred_at": market_context.event.occurred_at,
    }
    brief = ResearchBriefComposer().compose(serialized_judgment, metadata)
    presentation = ResearchBriefProductAdapter().present(brief)
    ResearchBriefProductAdapter().validate_presentation(presentation, presentation.payload)
    return presentation.payload, metadata


def session(monkeypatch, *, market=None, research=None, cognition=None) -> JuliaSession:
    result = JuliaSession.__new__(JuliaSession)
    result.provider = cognition or ResearchCognitionProvider()
    result.capability = RuntimeCapabilityBridge()
    result.capability.register_provider("ai_theme_app", market or MarketProvider())
    result.capability.register_provider(
        "research_enrichment", research or ResearchProvider()
    )
    result.capability.initialize()
    result.context_os = ContextExecutionRuntime(result)
    result.action = FakeAction()
    result.recorder = FakeRecorder()

    class Package:
        active_tail_messages = []
        conversation_id = "conv"
        turn_id = "turn-i4"

    monkeypatch.setattr(
        JuliaSession,
        "_prepare_turn",
        lambda self, text, ctx: (setattr(ctx, "_last_package", Package()), [{"role": "user", "content": text}])[1],
    )
    monkeypatch.setattr(
        JuliaSession,
        "_update_conversation_state",
        lambda self, text, reply, ctx: None,
    )
    return result


def conversation():
    base = tempfile.mkdtemp(prefix="rd1_i4_")
    repository = StorageV2ConversationRepository(Path(base))
    runtime = ConversationRuntime(repository=repository)
    runtime.create_conversation("conv", "RD1-I4")
    return runtime, repository


async def stream(session_object, *, hook=research_hook):
    products = []
    chunks = [
        chunk async for chunk in session_object.process_stream(
            "今天半导体设备为什么变化？",
            [],
            conversation_id="conv",
            turn_id="turn-i4",
            research_product_hook=hook,
            product_sink=products.append,
        )
    ]
    return chunks, products


@pytest.mark.asyncio
async def test_i4_f01_f05_f07_f08_f11_full_chain_uses_one_turn_and_product_metadata(monkeypatch):
    events = FakeEventStore()
    monkeypatch.setattr("julia_core.events.store.get_event_store", lambda: events)
    market = MarketProvider()
    research = ResearchProvider(mode="report_only")
    cognitive = session(monkeypatch, market=market, research=research)
    runtime, repository = conversation()
    ctx = runtime.begin_turn_streaming(
        conversation_id="conv", turn_id="turn-i4", modality="text", input="research"
    )

    chunks = []
    products = []
    async for chunk in cognitive.process_stream(
        "research", ctx.history, conversation_id="conv", turn_id="turn-i4",
        interaction=ctx.interaction, research_product_hook=research_hook,
        product_sink=products.append,
    ):
        chunks.append(chunk)
    result = runtime.commit_streaming_turn(ctx, "".join(chunks))

    assert chunks == ["Julia's same-turn research answer retains the governed uncertainty."]
    assert [request.capability_id for request in market.requests] == [
        "market.event.resolve", "market.event.read"
    ]
    assert market.requests[1].arguments == {"event_id": 501}
    assert len(research.requests) == 1
    assert result.conversation_id == "conv" and result.turn_id == "turn-i4"
    assert len(products) == 1
    product = products[0]
    assert product["contract_version"] == "julia.product.events.v1"
    assert product["research_brief"]["contract_version"] == "research.brief.v1"
    assert product["research_brief"]["key_drivers"][0]["support_level"] == "REPORT_ONLY_LEAD"
    assert product["research_brief"]["contradictions"][0]["statement"] == "Competing explanation remains unresolved"
    assert "NO_MODEL_SYNTHESIS" in product["research_brief"]["uncertainties"][0]
    assert product["trace"]["conversation_id"] == "conv"
    assert product["trace"]["turn_id"] == "turn-i4"
    assert len(product["trace"]["capability_call_ids"]) == 3
    assert product["trace"]["judgment_id"] and product["trace"]["brief_id"]
    transcript = repository.find_turn("conv", "turn-i4")
    assert [message.role for message in transcript] == ["user", "assistant"]
    assert all("research_brief" not in message.content for message in transcript)
    assert [event.event_type for event in events.events] == [
        "capability.started", "capability.completed",
        "capability.started", "capability.completed",
        "capability.started", "capability.completed",
    ]


@pytest.mark.asyncio
async def test_i4_f02_f03_unresolved_and_ambiguous_do_not_read_or_research(monkeypatch):
    for state in ("UNRESOLVED", "AMBIGUOUS"):
        market = MarketProvider(state=state)
        research = ResearchProvider()
        cognitive = session(monkeypatch, market=market, research=research)
        chunks, products = await stream(cognitive)
        assert chunks
        assert [request.capability_id for request in market.requests] == ["market.event.resolve"]
        assert research.requests == []
        assert products == []
        if state == "AMBIGUOUS":
            rendered = json.dumps(cognitive.provider.stream_calls[-1], ensure_ascii=False)
            assert "501" in rendered and "502" in rendered


@pytest.mark.asyncio
async def test_i4_f04_f06_read_failure_and_blocked_research_fail_closed(monkeypatch):
    market = MarketProvider(read_status=ToolResultStatus.UNAVAILABLE)
    research = ResearchProvider()
    cognitive = session(monkeypatch, market=market, research=research)
    chunks, products = await stream(cognitive)
    assert chunks and research.requests == [] and products == []

    market = MarketProvider()
    research = ResearchProvider(mode="blocked")
    cognitive = session(monkeypatch, market=market, research=research)
    chunks, products = await stream(cognitive)
    assert chunks and products == []
    rendered = json.dumps(cognitive.provider.stream_calls[-1], ensure_ascii=False)
    assert "BLOCKED" in rendered
    assert "research source blocked" in rendered


@pytest.mark.asyncio
async def test_i4_f06_not_proven_and_f13_hostile_material_remain_inert(monkeypatch):
    research = ResearchProvider(mode="not_proven")
    cognitive = session(monkeypatch, research=research)
    chunks, products = await stream(cognitive)
    assert chunks
    assert products[0]["research_brief"]["key_drivers"][0]["support_level"] == "NOT_PROVEN_MATERIAL"
    serialized = json.dumps(products[0], ensure_ascii=False)
    assert "SOURCE_VERIFIED" not in serialized


@pytest.mark.asyncio
async def test_i4_f10_cancellation_before_research_prevents_assistant_commit(monkeypatch):
    market = MarketProvider()
    research = ResearchProvider(hang=True)
    cognitive = session(monkeypatch, market=market, research=research)
    runtime, repository = conversation()
    ctx = runtime.begin_turn_streaming(
        conversation_id="conv", turn_id="turn-cancel", modality="text", input="cancel"
    )
    stream_iterator = cognitive.process_stream(
        "cancel", ctx.history, conversation_id="conv", turn_id="turn-cancel"
    )
    task = asyncio.create_task(anext(stream_iterator))
    await asyncio.wait_for(research.started.wait(), timeout=1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    runtime.cancel_streaming_turn(ctx)
    messages = repository.find_turn("conv", "turn-cancel")
    assert [message.role for message in messages] == ["user"]
    assert messages[0].status == "completed"
    with pytest.raises(RuntimeError):
        runtime.commit_streaming_turn(ctx, "late")


@pytest.mark.asyncio
async def test_i4_f12_ordinary_conversation_remains_unchanged(monkeypatch):
    provider = OrdinaryProvider()
    cognitive = session(monkeypatch, cognition=provider)
    chunks, products = await stream(cognitive)
    assert chunks == ["ordinary answer"]
    assert products == []
    assert len(provider.stream_calls) == 1


@pytest.mark.asyncio
async def test_i4_f14_trading_semantics_fail_closed_before_brief(monkeypatch):
    cognition = ResearchCognitionProvider(mode="trading")
    research = ResearchProvider()
    cognitive = session(monkeypatch, cognition=cognition, research=research)
    chunks, products = await stream(cognitive)
    assert chunks
    assert products == []
    rendered = json.dumps(cognitive.provider.stream_calls[-1], ensure_ascii=False)
    assert "research_judgment_failed" in rendered
