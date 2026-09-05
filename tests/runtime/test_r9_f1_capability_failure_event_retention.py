from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Any

import pytest

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityRequest,
    CapabilityStatus,
    ProviderExecutionOutcome,
    ToolResultStatus,
)
from julia_core.capability.policy import PermissionRule
from julia_core.events.store import EventStore
import julia_core.events.store as events_store_module
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge


MARKET_REPO = Path(os.environ.get(
    "RD1_L1_R9_F1_MARKET_ROOT",
    str(Path(__file__).resolve().parents[2].parent / "ai_theme_app_i2a"),
))


class FixtureProvider:
    def __init__(self, outcome: ProviderExecutionOutcome):
        self.outcome = outcome
        self.execute_calls = 0

    async def health(self) -> tuple[bool, str]:
        return True, "fixture provider ready"

    async def execute(self, request: CapabilityRequest):
        self.execute_calls += 1
        return self.outcome


def _capability_request() -> CapabilityRequest:
    return CapabilityRequest(
        "market.event.resolve",
        {
            "query": "R9-F1 bounded query",
            "normalized_theme": "Token出海",
            "time_window": {"date": "2026-07-19"},
        },
        capability_request_id="cap_req_r9_f1",
        turn_id="turn_r9_f1",
        generation_id="generation_r9_f1",
        correlation_id="conv:conv_r9_f1:turn:turn_r9_f1",
    )


async def _run_bridge(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    provider: FixtureProvider,
) -> tuple[Any, list[dict[str, Any]]]:
    monkeypatch.setattr(events_store_module, "_store", EventStore(str(tmp_path)))
    bridge = RuntimeCapabilityBridge()
    bridge.registry.register_definition(CapabilityDefinition(
        name="market.event.resolve",
        description="R9-F1 fixture resolver",
        layer=CapabilityLayer.WORLD,
        provider="ai_theme_app",
        permission_scope="market.event.resolve",
        status=CapabilityStatus.AVAILABLE,
    ))
    bridge.policy.add_rule(PermissionRule(
        "market.event.resolve",
        allow=True,
        reason="R9-F1 deterministic fixture",
    ))
    bridge.register_provider("ai_theme_app", provider)
    bridge.initialize()
    execution = await bridge._execute_request_with_events(_capability_request())
    event_path = next(tmp_path.glob("events-*.jsonl"))
    lines = [line for line in event_path.read_text(encoding="utf-8").splitlines() if line]
    import json
    events = [json.loads(line) for line in lines]
    return execution, events


@pytest.mark.asyncio
async def test_capability_failed_retains_whitelisted_diagnostics_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    secret = "R9_F1_FAKE_SECRET_DO_NOT_MATCH"
    details = {
        "operation_symbol": "event_resolve.py:MarketEventResolveOperation.execute",
        "failure_layer": "MarketEventResolveOperation._resolve",
        "exception_class": "FakeDatabaseError",
        "exception_message": f"password=*** bounded {'x' * 3000}",
        "sqlstate": "08006",
        "error_code": "R9_F1_FAKE_ERROR_CODE",
        "precollapse_provider_status": "unavailable",
        "process_pid": 123456,
        "observed_at": "2026-09-05T12:00:00+08:00",
        "resolver_query": "R9-F1 bounded query",
        "normalized_theme": "Token出海",
        "time_window": {"date": "2026-07-19"},
        "correlation_id": "conv:conv_r9_f1:turn:turn_r9_f1",
        "idempotency_id": "cap_req_r9_f1",
        "capability_request_id": "cap_req_r9_f1",
        "capability_call_id": None,
        "unapproved_raw_field": {"secret": secret},
    }
    outcome = ProviderExecutionOutcome(
        status=ToolResultStatus.UNAVAILABLE,
        structured_output={"raw_provider_output": {"secret": secret}},
        error={
            "code": "UPSTREAM_UNAVAILABLE",
            "message": "FakeDatabaseError",
            "details": details,
        },
    )

    execution, events = await _run_bridge(monkeypatch, tmp_path, FixtureProvider(outcome))
    failed = [event for event in events if event["event_type"] == "capability.failed"][0]
    payload = failed["payload"]
    provider_failure = payload["provider_failure"]

    assert execution.tool_result is not None
    assert execution.tool_result.status is ToolResultStatus.UNAVAILABLE
    assert [event["event_type"] for event in events].count("capability.started") == 1
    assert payload["status"] == "unavailable"
    assert payload["capability_id"] == "market.event.resolve"
    assert payload["capability_request_id"] == "cap_req_r9_f1"
    assert payload["capability_call_id"].startswith("cap_call_")
    assert failed["correlation_id"] == "conv:conv_r9_f1:turn:turn_r9_f1"
    assert provider_failure["error_code"] == "UPSTREAM_UNAVAILABLE"
    assert provider_failure["diagnostics"]["operation_symbol"]
    assert len(provider_failure["diagnostics"]["exception_message"]) <= 2048
    assert "unapproved_raw_field" not in provider_failure["diagnostics"]
    assert "raw_provider_output" not in payload
    assert secret not in str(payload)


@pytest.mark.skipif(not MARKET_REPO.exists(), reason="combined Market checkout is unavailable")
@pytest.mark.asyncio
async def test_combined_market_failure_reaches_core_event_store(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    class FakeDatabaseError(ConnectionError):
        sqlstate = "08006"
        pgcode = "08006"
        errno = 7
        code = "R9_F1_FAKE_ERROR_CODE"

    class FakeGateway:
        def __init__(self):
            self.resolve_calls = 0
            self.read_calls = 0

        async def resolve_market_event_candidates(
            self, *, query, normalized_theme=None, time_window=None, limit=20
        ):
            self.resolve_calls += 1
            raise FakeDatabaseError(
                "resolver failed password=R9_F1_FAKE_SECRET_DO_NOT_MATCH"
            )

        async def get_news_event_for_match(self, event_id):
            self.read_calls += 1
            raise AssertionError("resolver failure must stop before read")

        async def get_event_subject_mappings_by_event_ids(self, event_ids):
            raise AssertionError("resolver failure must stop before relation read")

    market_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == "stock_processing_service" or name.startswith("stock_processing_service.")
    }
    saved_path = sys.path[:]
    for name in market_modules:
        del sys.modules[name]
    sys.path.insert(0, str(MARKET_REPO))
    try:
        from stock_processing_service.application.services.julia_domain_adapter import (
            DomainIntelligenceAdapter,
        )
        from julia_core.capability.providers.ai_theme.frozen_market import MarketDomainAdapterProvider

        gateway = FakeGateway()
        adapter = DomainIntelligenceAdapter(database_gateway=gateway)
        market_provider = MarketDomainAdapterProvider(adapter)
    finally:
        sys.path[:] = saved_path
        for name in [
            name
            for name in sys.modules
            if name == "stock_processing_service" or name.startswith("stock_processing_service.")
        ]:
            del sys.modules[name]
        sys.modules.update(market_modules)

    class CombinedProvider(FixtureProvider):
        async def execute(self, request: CapabilityRequest):
            self.execute_calls += 1
            assert request.capability_id == "market.event.resolve"
            return await market_provider.execute(request)

    provider = CombinedProvider(None)
    execution, events = await _run_bridge(monkeypatch, tmp_path, provider)
    failed = [event for event in events if event["event_type"] == "capability.failed"][0]
    payload = failed["payload"]
    diagnostics = payload["provider_failure"]["diagnostics"]

    assert execution.tool_result is not None
    assert execution.tool_result.status is ToolResultStatus.UNAVAILABLE
    assert payload["status"] == "unavailable"
    assert payload["provider_failure"]["error_code"] == "UPSTREAM_UNAVAILABLE"
    assert diagnostics["exception_class"] == "FakeDatabaseError"
    assert diagnostics["exception_message"].startswith("resolver failed password=***")
    assert diagnostics["sqlstate"] == "08006"
    assert diagnostics["pgcode"] == "08006"
    assert diagnostics["error_code"] == "R9_F1_FAKE_ERROR_CODE"
    assert diagnostics["normalized_theme"] == "Token出海"
    assert diagnostics["time_window"] == {"date": "2026-07-19"}
    assert diagnostics["resolver_query"] == "R9-F1 bounded query"
    assert diagnostics["process_pid"] > 0
    assert diagnostics["observed_at"]
    assert diagnostics["capability_call_id"] is None
    assert payload["capability_call_id"].startswith("cap_call_")
    assert "R9_F1_FAKE_SECRET_DO_NOT_MATCH" not in str(payload)
    assert "raw_provider_output" not in payload
    assert gateway.resolve_calls == 1
    assert gateway.read_calls == 0
    assert provider.execute_calls == 1
