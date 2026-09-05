"""R10-F2 semantic numeric representation normalization tests."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any

import pytest

from julia_core.research.adapter import MarketEventResearchAdapter
from julia_core.runtime.research_continuation import (
    _numeric_confidence,
    _project_market_read_payload,
)


EVENT = {
    "event_id": 215257,
    "event_type": "theme_event",
    "summary": "Token出海 canonical market event.",
    "direction": "neutral",
    "confidence": Decimal("0.90"),
    "occurred_at": "2026-07-19T18:46:35.697877+08:00",
    "title": "Token出海",
    "source_category": "news",
    "source_name": "akshare_realtime",
    "source_url": "https://market.example/token-overseas",
    "source_trace_id": "news_event:62120:产品发布",
    "news_id": 62120,
}

RELATION = {
    "subject_key": "9064061",
    "subject_name": "Token出海",
    "relation_type": "primary",
    "confidence": Decimal("0.95"),
    "match_reason": "direct_theme_name_hit",
    "evidence": '{"reason":"direct_theme_name_hit"}',
    "source": "structured_theme_match",
    "source_trace_id": "trace_215257",
    "updated_at": "2026-07-19T10:46:39.397167+00:00",
    "created_at": "2026-07-19T10:46:39.397167+00:00",
    "run_id": "realtime_20260719_094737",
}


def payload() -> dict[str, Any]:
    return {
        "event": deepcopy(EVENT),
        "theme_relations": [deepcopy(RELATION)],
        "missing_fields": [],
    }


@pytest.mark.parametrize("confidence", [1, 0.9, "0.9", Decimal("0.9")])
def test_event_and_relation_accept_finite_numeric_representations(
    confidence: Any,
) -> None:
    market_payload = payload()
    market_payload["event"]["confidence"] = confidence
    market_payload["theme_relations"][0]["confidence"] = confidence

    projected = _project_market_read_payload(market_payload, 215257)

    assert projected["event"]["confidence"] == float(confidence)
    assert projected["theme_relations"][0]["confidence"] == float(confidence)


@pytest.mark.parametrize(
    "confidence",
    [
        True,
        False,
        None,
        "",
        "abc",
        [],
        {},
        object(),
        float("nan"),
        float("inf"),
        float("-inf"),
        Decimal("NaN"),
        Decimal("Infinity"),
    ],
)
def test_non_semantic_numeric_representations_fail_closed(confidence: Any) -> None:
    with pytest.raises(Exception) as error:
        _numeric_confidence(confidence, "event.confidence")

    assert error.value.__class__.__name__ == "MarketEventContractError"


def test_decimal_projection_reaches_research_enrich_request() -> None:
    projected = _project_market_read_payload(payload(), 215257)
    validated = MarketEventResearchAdapter().validate_context(projected)
    request = MarketEventResearchAdapter().build_request(
        validated,
        turn_id="turn-r10-f2",
        generation_id="gen-r10-f2",
        correlation_id="corr-r10-f2",
    )

    assert projected["event"]["confidence"] == 0.90
    assert projected["theme_relations"][0]["confidence"] == 0.95
    assert request.capability_id == "research.event.enrich"
    assert request.arguments["event"]["event_id"] == 215257
    assert request.arguments["theme_relations"][0]["confidence"] == 0.95
    assert request.provenance["market_event_id"] == 215257
    assert request.provenance["source_trace_id"] == EVENT["source_trace_id"]
    assert request.arguments["event"]["source_name"] == EVENT["source_name"]
    assert request.arguments["event"]["source_url"] == EVENT["source_url"]
    assert request.arguments["event"]["news_id"] == EVENT["news_id"]
