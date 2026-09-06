"""Governed adapter for the research.event.enrich capability seam."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from julia_core.capability.models import CapabilityRequest
from julia_core.research.contracts import (
    MarketEvent,
    MarketEventContext,
    MarketEventRelation,
)

RESEARCH_EVENT_ENRICH_CAPABILITY = "research.event.enrich"
RESEARCH_EVENT_ENRICH_SCOPE = "research.enrich"
MARKET_EVENT_CONTRACT_VERSION = "market.event.read.v1"

_EVENT_REQUIRED = frozenset({
    "event_id", "event_type", "summary", "direction", "confidence", "occurred_at",
    "title", "source_category", "source_name", "source_url", "source_trace_id", "news_id",
})
_RELATION_REQUIRED = frozenset({
    "subject_key", "subject_name", "relation_type", "confidence", "match_reason",
    "evidence", "source", "source_trace_id", "updated_at",
})
_NULLABLE_EVENT_FIELDS = frozenset({
    "occurred_at", "title", "source_name", "source_url", "news_id",
})


class MarketEventContractError(ValueError):
    """The supplied Market payload violates the frozen M0 contract."""


class MarketEventResearchAdapter:
    """Projects the frozen M0 Market event read into a C-08 request."""

    def build_request(
        self,
        context: MarketEventContext | Mapping[str, Any],
        *,
        turn_id: str = "",
        generation_id: str = "",
        correlation_id: str = "",
        capability_request_id: str | None = None,
    ) -> CapabilityRequest:
        normalized = self.validate_context(context)
        event = normalized.event
        return CapabilityRequest(
            capability_id=RESEARCH_EVENT_ENRICH_CAPABILITY,
            capability_request_id=capability_request_id,
            arguments={
                "event": self._event_to_dict(event),
                "theme_relations": [self._relation_to_dict(item) for item in normalized.theme_relations],
            },
            requested_scope=RESEARCH_EVENT_ENRICH_SCOPE,
            turn_id=turn_id,
            generation_id=generation_id,
            correlation_id=correlation_id,
            idempotency_key=f"research-event-{event.event_id}-{event.source_trace_id}",
            provenance={
                "contract_version": MARKET_EVENT_CONTRACT_VERSION,
                "market_event_id": event.event_id,
                "source_trace_id": event.source_trace_id,
                "source": "julia_core.research.adapter",
            },
        )

    def validate_context(
        self, context: MarketEventContext | Mapping[str, Any]
    ) -> MarketEventContext:
        if isinstance(context, MarketEventContext):
            return context
        if not isinstance(context, Mapping):
            raise MarketEventContractError("market context must be an object")

        unknown = set(context) - {"event", "theme_relations"}
        if unknown:
            raise MarketEventContractError(f"unknown market context fields: {sorted(unknown)}")
        if "event" not in context:
            raise MarketEventContractError("market context requires event")

        event = self._parse_event(context["event"])
        relations_value = context.get("theme_relations", [])
        if not isinstance(relations_value, Sequence) or isinstance(relations_value, (str, bytes)):
            raise MarketEventContractError("theme_relations must be an array")
        relations = tuple(self._parse_relation(item) for item in relations_value)
        return MarketEventContext(event=event, theme_relations=relations)

    def _parse_event(self, value: Any) -> MarketEvent:
        if not isinstance(value, Mapping):
            raise MarketEventContractError("event must be an object")
        keys = set(value)
        missing = _EVENT_REQUIRED - keys
        unknown = keys - _EVENT_REQUIRED
        if missing:
            raise MarketEventContractError(f"event fields missing: {sorted(missing)}")
        if unknown:
            raise MarketEventContractError(f"event fields not in frozen M0 contract: {sorted(unknown)}")
        for name in _EVENT_REQUIRED - _NULLABLE_EVENT_FIELDS:
            if value[name] is None or (isinstance(value[name], str) and not value[name].strip()):
                raise MarketEventContractError(f"event field is required: {name}")
        if not isinstance(value["event_id"], int) or isinstance(value["event_id"], bool):
            raise MarketEventContractError("event.event_id must be an integer news_event.id")
        if not isinstance(value["confidence"], (int, float)) or isinstance(value["confidence"], bool):
            raise MarketEventContractError("event.confidence must be numeric")
        if value["news_id"] is not None and (
            not isinstance(value["news_id"], int) or isinstance(value["news_id"], bool)
        ):
            raise MarketEventContractError("event.news_id must be an integer or null")
        if value["source_category"] not in {"news", "intel"}:
            raise MarketEventContractError("event.source_category must be news or intel")
        return MarketEvent(
            event_id=value["event_id"],
            event_type=str(value["event_type"]),
            summary=str(value["summary"]),
            direction=str(value["direction"]),
            confidence=float(value["confidence"]),
            occurred_at=self._optional_str(value["occurred_at"]),
            title=self._optional_str(value["title"]),
            source_category=value["source_category"],
            source_name=self._optional_str(value["source_name"]),
            source_url=self._optional_str(value["source_url"]),
            source_trace_id=str(value["source_trace_id"]),
            news_id=value["news_id"],
        )

    def _parse_relation(self, value: Any) -> MarketEventRelation:
        if not isinstance(value, Mapping):
            raise MarketEventContractError("each theme relation must be an object")
        keys = set(value)
        missing = _RELATION_REQUIRED - keys
        unknown = keys - _RELATION_REQUIRED
        if missing:
            raise MarketEventContractError(f"theme relation fields missing: {sorted(missing)}")
        if unknown:
            raise MarketEventContractError(f"theme relation fields not in frozen M0 contract: {sorted(unknown)}")
        if not isinstance(value["confidence"], (int, float)) or isinstance(value["confidence"], bool):
            raise MarketEventContractError("theme relation confidence must be numeric")
        return MarketEventRelation(
            subject_key=str(value["subject_key"]),
            subject_name=str(value["subject_name"]),
            relation_type=str(value["relation_type"]),
            confidence=float(value["confidence"]),
            match_reason=str(value["match_reason"]),
            evidence=str(value["evidence"]),
            source=str(value["source"]),
            source_trace_id=str(value["source_trace_id"]),
            updated_at=str(value["updated_at"]),
        )

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        return None if value is None else str(value)

    @staticmethod
    def _event_to_dict(event: MarketEvent) -> dict[str, Any]:
        return {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "summary": event.summary,
            "direction": event.direction,
            "confidence": event.confidence,
            "occurred_at": event.occurred_at,
            "title": event.title,
            "source_category": event.source_category,
            "source_name": event.source_name,
            "source_url": event.source_url,
            "source_trace_id": event.source_trace_id,
            "news_id": event.news_id,
        }

    @staticmethod
    def _relation_to_dict(relation: MarketEventRelation) -> dict[str, Any]:
        return {
            "subject_key": relation.subject_key,
            "subject_name": relation.subject_name,
            "relation_type": relation.relation_type,
            "confidence": relation.confidence,
            "match_reason": relation.match_reason,
            "evidence": relation.evidence,
            "source": relation.source,
            "source_trace_id": relation.source_trace_id,
            "updated_at": relation.updated_at,
        }


__all__ = [
    "MARKET_EVENT_CONTRACT_VERSION",
    "MarketEventContractError",
    "MarketEventResearchAdapter",
    "RESEARCH_EVENT_ENRICH_CAPABILITY",
    "RESEARCH_EVENT_ENRICH_SCOPE",
]
