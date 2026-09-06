"""Narrow same-turn Market→research→judgment→brief continuation.

This is not a generic workflow runtime. It sequences one frozen research chain
inside the existing Julia cognition turn and returns Context OS messages for
final Julia continuation.
"""

from __future__ import annotations

import json as _json
from collections.abc import Mapping, Sequence
from math import isfinite
from dataclasses import dataclass
from typing import Any, Callable

from julia_core.capability.models import (
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResult,
    ToolResultStatus,
)
from julia_core.research.adapter import MarketEventContractError, MarketEventResearchAdapter
from julia_core.research.normalizer import ResearchEvidenceNormalizer

_PROJECTED_EVENT_FIELDS = (
    "event_id", "event_type", "summary", "direction", "confidence",
    "occurred_at", "title", "source_category", "source_name", "source_url",
    "source_trace_id", "news_id",
)
_PROJECTED_RELATION_FIELDS = (
    "subject_key", "subject_name", "relation_type", "confidence",
    "match_reason", "evidence", "source", "source_trace_id", "updated_at",
)
_RELATION_TRANSPORT_EXTRAS = frozenset({"created_at", "run_id"})


def _numeric_confidence(value: Any, field_name: str) -> float:
    if (
        value is None
        or isinstance(value, (bool, Mapping))
        or (isinstance(value, Sequence) and not isinstance(value, str))
    ):
        raise MarketEventContractError(f"{field_name} must be numeric")
    try:
        numeric_value = float(value)
    except (TypeError, ValueError, OverflowError):
        raise MarketEventContractError(f"{field_name} must be numeric") from None
    if not isfinite(numeric_value):
        raise MarketEventContractError(f"{field_name} must be finite")
    return numeric_value


def _project_market_read_payload(
    payload: Any, selected_event_id: int
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise MarketEventContractError("market.event.read payload must be an object")

    payload_fields = set(payload)
    unknown_payload_fields = payload_fields - {
        "event", "theme_relations", "missing_fields"
    }
    if unknown_payload_fields:
        raise MarketEventContractError(
            f"unknown market.event.read payload fields: {sorted(unknown_payload_fields)}"
        )

    missing_fields = payload.get("missing_fields")
    if missing_fields is not None and (
        not isinstance(missing_fields, list)
        or any(not isinstance(item, str) for item in missing_fields)
    ):
        raise MarketEventContractError("missing_fields must be an array of strings")

    event = payload.get("event")
    if not isinstance(event, Mapping):
        raise MarketEventContractError("market.event.read event must be an object")
    event_fields = set(event)
    missing_event_fields = frozenset(_PROJECTED_EVENT_FIELDS) - event_fields
    unknown_event_fields = event_fields - frozenset(_PROJECTED_EVENT_FIELDS)
    if missing_event_fields:
        raise MarketEventContractError(
            f"market.event.read event fields missing: {sorted(missing_event_fields)}"
        )
    if unknown_event_fields:
        raise MarketEventContractError(
            "market.event.read event fields not in frozen research contract: "
            f"{sorted(unknown_event_fields)}"
        )
    if event["event_id"] != selected_event_id:
        raise MarketEventContractError("projected event_id does not match selected_event_id")

    projected_event = {
        name: event[name] for name in _PROJECTED_EVENT_FIELDS
    }
    projected_event["confidence"] = _numeric_confidence(
        projected_event["confidence"], "event.confidence"
    )

    relations = payload.get("theme_relations", [])
    if not isinstance(relations, list):
        raise MarketEventContractError("market.event.read theme_relations must be an array")
    projected_relations = []
    for relation in relations:
        if not isinstance(relation, Mapping):
            raise MarketEventContractError(
                "each market.event.read theme relation must be an object"
            )
        relation_fields = set(relation)
        missing_relation_fields = (
            frozenset(_PROJECTED_RELATION_FIELDS) - relation_fields
        )
        unknown_relation_fields = (
            relation_fields
            - frozenset(_PROJECTED_RELATION_FIELDS)
            - _RELATION_TRANSPORT_EXTRAS
        )
        if missing_relation_fields:
            raise MarketEventContractError(
                "market.event.read theme relation fields missing: "
                f"{sorted(missing_relation_fields)}"
            )
        if unknown_relation_fields:
            raise MarketEventContractError(
                "market.event.read theme relation fields not in frozen research contract: "
                f"{sorted(unknown_relation_fields)}"
            )
        projected_relation = {
            name: relation[name] for name in _PROJECTED_RELATION_FIELDS
        }
        projected_relation["confidence"] = _numeric_confidence(
            projected_relation["confidence"], "theme relation confidence"
        )
        projected_relations.append(projected_relation)

    return {"event": projected_event, "theme_relations": projected_relations}


@dataclass(frozen=True, slots=True)
class ResearchContinuationMaterial:
    messages: list[dict[str, str]]
    product: dict[str, Any] | None
    trace: dict[str, Any]
    failure: str = ""


class SameTurnResearchContinuation:
    """Execute the frozen I4 research chain for one already-open Julia turn."""

    def __init__(self, session):
        self.session = session
        self.market_adapter = MarketEventResearchAdapter()
        self.normalizer = ResearchEvidenceNormalizer()

    async def run(
        self,
        *,
        resolver_tool_json: str,
        turn_context,
        parent_package,
        research_product_hook: Callable[[Any, Any], Any] | None,
        product_sink: Callable[[dict[str, Any]], None] | None,
    ) -> ResearchContinuationMaterial:
        capability_requests = []
        capability_calls = []
        event_names = []

        def remember(execution) -> None:
            request_id = getattr(execution.tool_result, "capability_call_id", "")
            capability_calls.append(request_id)

        def finish(execution) -> None:
            self.session.action.finish(
                self.session._outcome_action_status(execution),
                correlation_id=turn_context.correlation_id,
            )

        resolver_execution = await self._execute(
            resolver_tool_json, turn_context, "resolver"
        )
        if resolver_execution.tool_result is not None:
            remember(resolver_execution)
            capability_requests.append(
                resolver_execution.capability_call.capability_request_id
            )
        finish(resolver_execution)
        event_names.append("capability.completed" if self._succeeded(resolver_execution) else "capability.failed")

        resolver_delta = self.session._dispatch_typed_outcome(
            resolver_execution,
            turn_context,
            parent_package=parent_package,
        )
        if resolver_delta is None:
            raise ValueError("malformed market.event.resolve request")

        envelope = self._envelope(resolver_execution)
        resolver_state = str(envelope.get("payload", {}).get("state", ""))
        if envelope.get("status") not in {"success", "partial"} or resolver_state not in {
            "RESOLVED", "UNRESOLVED", "AMBIGUOUS"
        }:
            return self._stop(
                resolver_delta.to_messages(resolver_delta.active_tail_messages, ""),
                capability_requests,
                capability_calls,
                event_names,
                turn_context,
                failure="market_event_resolution_failed",
            )

        if resolver_state != "RESOLVED":
            resolver_delta.situation_frame = {
                "mode": "market_event_resolution_continuation",
                "state": resolver_state,
                "candidates": envelope.get("payload", {}).get("candidates", []),
            }
            return self._stop(
                resolver_delta.to_messages(resolver_delta.active_tail_messages, ""),
                capability_requests,
                capability_calls,
                event_names,
                turn_context,
                failure=f"market_event_resolution_{resolver_state.lower()}",
            )

        selected_event_id = envelope["payload"].get("selected_event_id")
        if isinstance(selected_event_id, bool) or not isinstance(selected_event_id, int):
            return self._failure_messages(
                resolver_execution,
                turn_context,
                parent_package,
                capability_requests,
                capability_calls,
                event_names,
                "selected_event_id_missing",
            )

        read_json = _json.dumps({
            "name": "market.event.read",
            "arguments": {"event_id": selected_event_id},
        })
        self.session._execute_tool_with_action(read_json, turn_context)
        read_execution = await self._execute(read_json, turn_context, "market_read")
        if read_execution.tool_result is not None:
            remember(read_execution)
            capability_requests.append(
                read_execution.capability_call.capability_request_id
            )
        finish(read_execution)
        event_names.append("capability.completed" if self._succeeded(read_execution) else "capability.failed")

        read_delta = self.session._dispatch_typed_outcome(
            read_execution,
            turn_context,
            parent_package=parent_package,
        )
        read_envelope = self._envelope(read_execution)
        if not self._succeeded(read_execution) or read_envelope.get("status") not in {
            "success", "partial"
        }:
            return self._failure_messages(
                read_execution,
                turn_context,
                parent_package,
                capability_requests,
                capability_calls,
                event_names,
                "market_event_read_failed",
                fallback_delta=read_delta,
            )

        payload = read_envelope.get("payload") or {}
        try:
            market_context = _project_market_read_payload(payload, selected_event_id)
            validated_market = self.market_adapter.validate_context(market_context)
            research_request = self.market_adapter.build_request(
                validated_market,
                turn_id=turn_context.turn_id,
                generation_id=f"gen_research_{turn_context.turn_count}",
                correlation_id=turn_context.correlation_id,
            )
        except Exception:
            return self._failure_messages(
                read_execution,
                turn_context,
                parent_package,
                capability_requests,
                capability_calls,
                event_names,
                "market_context_projection_failed",
                fallback_delta=read_delta,
            )

        self.session.action.start(
            "research.event.enrich",
            "Execute governed event research",
            correlation_id=turn_context.correlation_id,
        )
        research_execution = await self.session.capability.execute_capability_request_async(
            research_request
        )
        if research_execution.tool_result is not None:
            capability_requests.append(research_request.capability_request_id)
            capability_calls.append(research_execution.capability_call.capability_call_id)
        finish(research_execution)
        event_names.append("capability.completed" if self._succeeded(research_execution) else "capability.failed")

        research_delta = self.session._dispatch_typed_outcome(
            research_execution,
            turn_context,
            parent_package=parent_package,
        )
        if research_delta is None or not self._succeeded(research_execution):
            return self._failure_messages(
                research_execution,
                turn_context,
                parent_package,
                capability_requests,
                capability_calls,
                event_names,
                "research_enrichment_failed",
                fallback_delta=research_delta,
            )

        try:
            provider_outcome = ProviderExecutionOutcome(
                status=research_execution.tool_result.status,
                structured_output=research_execution.tool_result.structured_output,
                error=research_execution.tool_result.error,
                side_effect_state=research_execution.tool_result.side_effect_state,
            )
            enrichment = self.normalizer.normalize_provider_outcome(
                provider_outcome,
                request=research_request,
                call=research_execution.capability_call,
            )
            judgment = self.session.form_preliminary_research_judgment(
                validated_market,
                enrichment,
                conversation_id=turn_context.conversation_id,
                turn_id=turn_context.turn_id,
            )
        except Exception:
            return self._failure_messages(
                research_execution,
                turn_context,
                parent_package,
                capability_requests,
                capability_calls,
                event_names,
                "research_judgment_failed",
                fallback_delta=research_delta,
            )

        if research_product_hook is None:
            return self._failure_messages(
                research_execution,
                turn_context,
                parent_package,
                capability_requests,
                capability_calls,
                event_names,
                "research_product_binding_missing",
                fallback_delta=research_delta,
            )

        try:
            hooked = research_product_hook(judgment, validated_market)
            if isinstance(hooked, tuple):
                research_brief, _ = hooked
            else:
                research_brief = hooked
            continuation_package = self.session.context_os.project_research_product_continuation(
                parent_package=parent_package,
                judgment=judgment,
                research_brief=research_brief,
                conversation_id=turn_context.conversation_id,
                turn_id=turn_context.turn_id,
                generation_id=f"gen_research_final_{turn_context.turn_count}",
            )
        except Exception:
            return self._failure_messages(
                research_execution,
                turn_context,
                parent_package,
                capability_requests,
                capability_calls,
                event_names,
                "research_brief_composition_failed",
                fallback_delta=research_delta,
            )

        trace = {
            "conversation_id": turn_context.conversation_id,
            "turn_id": turn_context.turn_id,
            "correlation_id": turn_context.correlation_id,
            "capability_request_ids": capability_requests,
            "capability_call_ids": capability_calls,
            "judgment_id": judgment.judgment_id,
            "brief_id": research_brief.get("brief_id", ""),
        }
        product = {
            "contract_version": "julia.product.events.v1",
            "events": [{"type": name} for name in event_names],
            "research_brief": research_brief,
            "trace": trace,
        }
        if product_sink is not None:
            product_sink(product)
        return ResearchContinuationMaterial(
            messages=continuation_package.to_messages(
                continuation_package.active_tail_messages,
                "",
            ),
            product=product,
            trace=trace,
        )

    async def _execute(self, tool_json: str, turn_context, stage: str):
        self.session._execute_tool_with_action(tool_json, turn_context)
        return await self.session.capability.execute_tool_typed_async(
            tool_json,
            turn_id=turn_context.turn_id,
            generation_id=f"gen_{stage}_{turn_context.turn_count}",
            correlation_id=turn_context.correlation_id,
        )

    @staticmethod
    def _succeeded(execution) -> bool:
        result = getattr(execution, "tool_result", None)
        if result is None:
            return False
        status = result.status.value if hasattr(result.status, "value") else str(result.status)
        return status in {ToolResultStatus.SUCCESS.value, ToolResultStatus.PARTIAL.value}

    @staticmethod
    def _envelope(execution) -> dict[str, Any]:
        result = getattr(execution, "tool_result", None)
        structured = dict(result.structured_output or {}) if result is not None else {}
        data = structured.get("data")
        return dict(data if isinstance(data, dict) else structured)

    def _failure_messages(
        self,
        execution,
        turn_context,
        parent_package,
        request_ids,
        call_ids,
        events,
        reason,
        *,
        fallback_delta=None,
    ) -> ResearchContinuationMaterial:
        call = getattr(execution, "capability_call", None)
        call_id = call.capability_call_id if call is not None else ""
        failure = ToolResult(
            capability_call_id=call_id,
            status=ToolResultStatus.ERROR,
            error={"code": reason, "message": reason},
            side_effect_state=SideEffectState.NONE,
        )
        if fallback_delta is not None:
            delta = fallback_delta
        else:
            delta = self.session.context_os.project_tool_result(
                parent_package=parent_package,
                tool_result=failure,
                evidence=(),
                generation_id=f"gen_research_failure_{turn_context.turn_count}",
            )
        delta.situation_frame = {
            "mode": "research_continuation_failure",
            "reason": reason,
        }
        messages = delta.to_messages(delta.active_tail_messages, "")
        return self._stop(
            messages,
            request_ids,
            call_ids,
            events,
            turn_context,
            failure=reason,
        )

    @staticmethod
    def _stop(
        messages,
        request_ids,
        call_ids,
        events,
        turn_context,
        *,
        failure,
    ) -> ResearchContinuationMaterial:
        return ResearchContinuationMaterial(
            messages=messages,
            product=None,
            trace={
                "conversation_id": turn_context.conversation_id,
                "turn_id": turn_context.turn_id,
                "correlation_id": turn_context.correlation_id,
                "capability_request_ids": request_ids,
                "capability_call_ids": call_ids,
                "judgment_id": "",
                "brief_id": "",
            },
            failure=failure,
        )
