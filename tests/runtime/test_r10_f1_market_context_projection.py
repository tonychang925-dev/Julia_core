"""R10-F1 Market read to frozen research-context projection tests."""

from __future__ import annotations

import copy

import pytest

from julia_core.research.adapter import (
    MarketEventContractError,
    MarketEventResearchAdapter,
)
from julia_core.runtime.research_continuation import _project_market_read_payload


MARKET_EVENT = {
    "event_id": 215257,
    "event_type": "theme_event",
    "summary": "Token出海主题发生市场变化。",
    "direction": "positive",
    "confidence": "0.90",
    "occurred_at": "2026-07-19T09:30:00+08:00",
    "title": "Token出海",
    "source_category": "news",
    "source_name": "market-source",
    "source_url": "https://market.example/token-overseas",
    "source_trace_id": "public.news_event.id:215257",
    "news_id": 215257,
}

MARKET_RELATION = {
    "subject_key": "token_overseas",
    "subject_name": "Token出海",
    "relation_type": "primary",
    "confidence": "0.95",
    "match_reason": "canonical theme mapping",
    "evidence": "market relation fixture",
    "source": "event_subject_map",
    "source_trace_id": "public.news_event.id:215257",
    "updated_at": "2026-07-19T09:36:00+08:00",
    "created_at": "2026-07-19T09:35:00+08:00",
    "run_id": "market-run-001",
}


def market_payload() -> dict:
    return {
        "event": copy.deepcopy(MARKET_EVENT),
        "theme_relations": [copy.deepcopy(MARKET_RELATION)],
        "missing_fields": [],
    }


def test_market_read_projects_to_research_enrich_request() -> None:
    projected = _project_market_read_payload(market_payload(), 215257)
    validated = MarketEventResearchAdapter().validate_context(projected)
    request = MarketEventResearchAdapter().build_request(
        validated,
        turn_id="turn-r10-f1",
        generation_id="gen-r10-f1",
        correlation_id="corr-r10-f1",
    )

    assert request.capability_id == "research.event.enrich"
    assert request.arguments["event"]["event_id"] == 215257
    assert request.arguments["event"]["confidence"] == 0.90
    assert request.provenance["market_event_id"] == 215257
    assert request.provenance["source_trace_id"] == MARKET_EVENT["source_trace_id"]


def test_relation_transport_extras_are_explicitly_projected_out() -> None:
    projected = _project_market_read_payload(market_payload(), 215257)

    assert "created_at" not in projected["theme_relations"][0]
    assert "run_id" not in projected["theme_relations"][0]
    assert set(projected["theme_relations"][0]) == {
        "subject_key", "subject_name", "relation_type", "confidence",
        "match_reason", "evidence", "source", "source_trace_id", "updated_at",
    }


def test_empty_relations_are_preserved() -> None:
    payload = market_payload()
    payload["theme_relations"] = []

    projected = _project_market_read_payload(payload, 215257)

    assert projected["theme_relations"] == []


def test_unapproved_semantic_field_fails_closed() -> None:
    payload = market_payload()
    payload["event"]["trade_recommendation"] = "buy"

    with pytest.raises(MarketEventContractError, match="not in frozen research contract"):
        _project_market_read_payload(payload, 215257)


def test_event_id_mismatch_fails_closed() -> None:
    payload = market_payload()
    payload["event"]["event_id"] = 215258

    with pytest.raises(MarketEventContractError, match="does not match selected_event_id"):
        _project_market_read_payload(payload, 215257)


def test_missing_required_event_field_fails_closed() -> None:
    payload = market_payload()
    del payload["event"]["source_trace_id"]

    with pytest.raises(MarketEventContractError, match="event fields missing"):
        _project_market_read_payload(payload, 215257)


def test_invalid_relation_fails_closed() -> None:
    payload = market_payload()
    del payload["theme_relations"][0]["source_trace_id"]

    with pytest.raises(MarketEventContractError, match="relation fields missing"):
        _project_market_read_payload(payload, 215257)


def test_missing_fields_are_not_included_in_frozen_context() -> None:
    payload = market_payload()
    payload["missing_fields"] = ["source_name"]

    projected = _project_market_read_payload(payload, 215257)

    assert "missing_fields" not in projected


def test_adapter_strict_unknown_field_rejection_remains_intact() -> None:
    context = _project_market_read_payload(market_payload(), 215257)
    context["event"]["trade_recommendation"] = "buy"

    with pytest.raises(MarketEventContractError, match="not in frozen M0 contract"):
        MarketEventResearchAdapter().validate_context(context)
