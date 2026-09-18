"""RD1 P1-I3: Market public result survives C03 evidence re-entry unchanged."""
from __future__ import annotations

from copy import deepcopy

from julia_core.capability.models import ToolResult, ToolResultStatus
from julia_core.runtime.context_execution_runtime import (
    CognitiveContextPackage,
    ContextExecutionRuntime,
)


def _market_envelope(*, payload, operation_status="SUCCESS", data_state="READY", failures=None):
    return {
        "contract_version": "market-public.v1",
        "capability_id": "market.event.resolve",
        "request_id": "req-market-1",
        "correlation_id": "corr-market-1",
        "operation_status": operation_status,
        "data_state": data_state,
        "payload": payload,
        "provenance": {
            "provenance_status": "PROVENANCE_INCOMPLETE",
            "source_refs": ["jyhf"],
            "public_object_refs": ["event:1"],
            "capability_call_ref": "market.event.resolve",
            "correlation_id": "corr-market-1",
        },
        "failures": list(failures or []),
        "boundary_identity_ref": "market.public",
        "runtime_observation": None,
        "produced_at": "2026-09-17T00:00:00+00:00",
    }


def _tool_result(envelope):
    return ToolResult(
        capability_call_id="cap-call-market-1",
        status=ToolResultStatus.SUCCESS,
        structured_output=envelope,
        evidence_refs=(),
        provider="market",
    )


def test_market_envelope_is_preserved_as_structured_tool_output():
    envelope = _market_envelope(payload={"rows": [{"item_id": "event:1", "score": 0.9}]})
    delta = ContextExecutionRuntime().project_tool_result(
        parent_package=CognitiveContextPackage(
            conversation_id="conv",
            turn_id="turn",
            generation_id="before",
        ),
        tool_result=_tool_result(envelope),
        generation_id="after",
    )

    projected = delta.evidence_frame["tool_result"]["structured_output"]
    assert projected == envelope
    assert projected["operation_status"] == "SUCCESS"
    assert projected["data_state"] == "READY"
    assert projected["provenance"]["provenance_status"] == "PROVENANCE_INCOMPLETE"
    assert projected["failures"] == []


def test_market_projection_is_a_defensive_snapshot_not_shared_nested_state():
    envelope = _market_envelope(payload={"rows": [{"item_id": "event:1"}]})
    tool_result = _tool_result(envelope)
    expected = deepcopy(envelope)

    delta = ContextExecutionRuntime().project_tool_result(
        tool_result=tool_result,
        generation_id="after",
    )

    tool_result.structured_output["payload"]["rows"][0]["item_id"] = "mutated"
    tool_result.structured_output["provenance"]["source_refs"].append("mutated-source")

    assert delta.evidence_frame["tool_result"]["structured_output"] == expected


def test_large_market_payload_does_not_drop_tool_result_from_model_visible_context():
    payload = [
        {
            "item_id": f"event:{index}",
            "headline": "market-observation-" + ("x" * 800),
        }
        for index in range(200)
    ]
    envelope = _market_envelope(payload=payload)
    delta = ContextExecutionRuntime().project_tool_result(
        tool_result=_tool_result(envelope),
        generation_id="after",
    )

    messages = delta.to_messages([], "")
    system_text = messages[0]["content"]

    assert "[evidence]" in system_text
    assert "tool_result:" in system_text
    assert "capability_id=market.event.resolve" in system_text
    assert "operation_status=SUCCESS" in system_text
    assert "data_state=READY" in system_text
    assert "provenance_status=PROVENANCE_INCOMPLETE" in system_text
    assert "…[truncated]" in system_text


def test_market_domain_failure_reenters_as_market_failure_not_core_error():
    envelope = _market_envelope(
        payload=None,
        operation_status="FAILURE",
        data_state="NOT_APPLICABLE",
        failures=[{
            "kind": "MarketObjectNotFound",
            "code": "event_not_found",
            "message": "Event was not found",
        }],
    )
    delta = ContextExecutionRuntime().project_tool_result(
        tool_result=_tool_result(envelope),
        generation_id="after",
    )

    projected_tool = delta.evidence_frame["tool_result"]
    projected_market = projected_tool["structured_output"]

    assert projected_tool["status"] == "success"
    assert projected_market["operation_status"] == "FAILURE"
    assert projected_market["data_state"] == "NOT_APPLICABLE"
    assert projected_market["failures"][0]["kind"] == "MarketObjectNotFound"
    assert "error" not in projected_tool


def test_sequence_tail_omission_is_always_explicit_at_budget_edge():
    values = ["x" * 397 for _ in range(21)]
    rendered = CognitiveContextPackage()._render_value(
        values,
        depth=0,
        char_budget=8000,
    )

    assert "…[truncated]" in rendered
    assert "[1 more]" in rendered


def test_sequence_renderer_slices_bounded_prefix_without_full_materialization():
    class NoIterList(list):
        def __iter__(self):
            raise AssertionError("renderer must not materialize the full sequence")

    values = NoIterList(["x" * 50 for _ in range(100)])
    rendered = CognitiveContextPackage()._render_value(
        values,
        depth=0,
        char_budget=8000,
    )

    assert "…[truncated]" in rendered
    assert "[80 more]" in rendered
