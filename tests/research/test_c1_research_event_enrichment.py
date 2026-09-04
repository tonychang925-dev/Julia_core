"""Focused C1 regression for research.event.enrich."""

from __future__ import annotations

import pytest

from julia_core.capability.models import (
    CapabilityCall,
    CapabilityStatus,
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)
from julia_core.capability.policy import PermissionPolicy
from julia_core.capability.registry import CapabilityRegistry
from julia_core.research import (
    MarketEventContractError,
    MarketEventResearchAdapter,
    RESEARCH_EVENT_ENRICH_CAPABILITY,
    RESEARCH_EVENT_ENRICH_SCOPE,
    ResearchEvidenceNormalizer,
    VerificationState,
    register_research_event_enrichment,
)


DIGEST = "a" * 64


def market_context(**event_overrides):
    event = {
        "event_id": 123,
        "event_type": "policy_change",
        "summary": "Policy changed",
        "direction": "positive",
        "confidence": 0.82,
        "occurred_at": "2026-09-04T08:00:00Z",
        "title": "Policy changed",
        "source_category": "news",
        "source_name": "Example",
        "source_url": "https://example.test/policy",
        "source_trace_id": "news_event:456:policy_change",
        "news_id": 456,
    }
    event.update(event_overrides)
    return {
        "event": event,
        "theme_relations": [{
            "subject_key": "9010270",
            "subject_name": "Example Subject",
            "relation_type": "benefit",
            "confidence": 0.7,
            "match_reason": "mapping",
            "evidence": "relation evidence",
            "source": "event_subject_map",
            "source_trace_id": "news_event:456:policy_change",
            "updated_at": "2026-09-04T08:01:00Z",
        }],
    }


def adapter_request():
    return MarketEventResearchAdapter().build_request(
        market_context(),
        correlation_id="corr-research",
        capability_request_id="req_research",
    )


def capability_call(request):
    return CapabilityCall(
        capability_call_id="call_research",
        capability_request_id=request.capability_request_id,
        provider="research_enrichment",
        correlation_id=request.correlation_id,
    )


def source_record(**overrides):
    value = {
        "source_record_id": "source-1",
        "source_kind": "web_fetch",
        "source_ref": "https://example.test/policy",
        "capture_status": "success",
        "fetch_status": "success",
        "observed_at": "2026-09-04T08:02:00Z",
        "source_url": "https://example.test/policy",
        "raw_response_ref": "raw:provider:1",
        "content_ref": "content:runtime:1",
        "content_digest": DIGEST,
        "provenance": {"acquisition": "runtime_web_fetch"},
    }
    value.update(overrides)
    return value


def content_binding(**overrides):
    request = adapter_request()
    value = {
        "source_record_id": "source-1",
        "content_ref": "content:runtime:1",
        "digest": DIGEST,
        "extract_ref": "extract:runtime:1",
        "locator": "text:0-120",
        "provenance": {
            "capability_request_id": request.capability_request_id,
            "capability_call_id": "call_research",
            "runtime_observation_ref": "raw:provider:1",
        },
    }
    value.update(overrides)
    return value


def semantic_payload(claim_overrides=None):
    claim = {
        "claim_id": "claim-1",
        "text": "The policy changed",
        "source_record_ids": ["source-1"],
        "verification_state": "SOURCE_VERIFIED",
    }
    claim.update(claim_overrides or {})
    return {
        "factual_summary": "Provider summary",
        "claims": [claim],
        "contradictions": [],
        "unknowns": [],
        "timeline": [],
        "related_entities": [],
    }


def observation_payload(records=None, bindings=None, **overrides):
    value = {
        "available": True,
        "source_records": [source_record()] if records is None else records,
        "content_bindings": [content_binding()] if bindings is None else bindings,
        "raw_response_refs": ["raw:provider:1"],
        "observed_at": "2026-09-04T08:02:00Z",
        "provenance": {"provider_transport": "governed_fixture"},
        "failure": None,
    }
    value.update(overrides)
    return value


def normalize(structured_output, status=ToolResultStatus.SUCCESS, error=None):
    request = adapter_request()
    call = capability_call(request)
    outcome = ProviderExecutionOutcome(
        status=status,
        structured_output=structured_output,
        error=error,
        side_effect_state=SideEffectState.NONE,
    )
    return ResearchEvidenceNormalizer().normalize_provider_outcome(
        outcome,
        request=request,
        call=call,
    )


def verification(result):
    return result.observation.claim_verification_states["claim-1"]


def test_market_contract_projects_exact_capability_request_and_registration():
    adapter = MarketEventResearchAdapter()
    request = adapter.build_request(market_context(), correlation_id="corr-research")
    assert request.capability_id == RESEARCH_EVENT_ENRICH_CAPABILITY
    assert request.requested_scope == RESEARCH_EVENT_ENRICH_SCOPE
    assert set(request.arguments) == {"event", "theme_relations"}
    assert set(request.arguments["event"]) == {
        "event_id", "event_type", "summary", "direction", "confidence", "occurred_at",
        "title", "source_category", "source_name", "source_url", "source_trace_id", "news_id",
    }

    registry = CapabilityRegistry()
    policy = PermissionPolicy()
    definition = register_research_event_enrichment(registry, policy, status=CapabilityStatus.AVAILABLE)
    assert definition.provider == "research_enrichment"
    assert policy.check(RESEARCH_EVENT_ENRICH_SCOPE).allowed


def test_frozen_market_contract_rejects_unfrozen_event_field():
    context = market_context(related_symbols=["000001.SZ"])
    with pytest.raises(MarketEventContractError, match="frozen M0 contract"):
        MarketEventResearchAdapter().validate_context(context)


def test_runtime_bound_claim_can_become_source_verified():
    result = normalize({
        "semantic_result": semantic_payload(),
        "source_observation": observation_payload(),
    })
    assert verification(result) == "SOURCE_VERIFIED"
    evidence = result.observation.evidence[0]
    assert evidence.integrity_metadata["verification_state"] == "SOURCE_VERIFIED"
    assert evidence.integrity_metadata["content_digest"] == DIGEST
    assert result.tool_result.evidence_refs == (evidence.evidence_id,)
    assert result.semantic_result is not result.observation


def test_provider_source_verified_label_alone_is_not_authority():
    result = normalize({
        "semantic_result": semantic_payload(),
        "source_observation": observation_payload(bindings=[]),
    })
    assert verification(result) == "NOT_PROVEN"
    semantic_binding = result.observation.evidence[0].integrity_metadata["semantic_binding"]
    assert semantic_binding["provider_label_authoritative"] is False


def test_websearch_only_source_is_report_only_even_with_provider_label():
    records = [source_record(
        source_kind="web_search",
        capture_status="success",
        fetch_status="not_required",
        content_ref="",
    )]
    result = normalize({
        "semantic_result": semantic_payload(),
        "source_observation": observation_payload(records=records, bindings=[]),
    })
    assert verification(result) == "REPORT_ONLY"


def test_fetched_url_without_content_binding_is_not_proven():
    result = normalize({
        "semantic_result": semantic_payload(),
        "source_observation": observation_payload(bindings=[]),
    })
    assert verification(result) == "NOT_PROVEN"
    assert result.observation.evidence[0].content_ref == source_record()["content_ref"]


def test_claim_referencing_missing_source_record_is_not_proven():
    result = normalize({
        "semantic_result": semantic_payload({"source_record_ids": ["missing-source"]}),
        "source_observation": observation_payload(),
    })
    assert verification(result) == "NOT_PROVEN"


def test_missing_digest_is_not_proven():
    result = normalize({
        "semantic_result": semantic_payload(),
        "source_observation": observation_payload(bindings=[content_binding(digest="")]),
    })
    assert verification(result) == "NOT_PROVEN"


def test_missing_binding_provenance_is_not_proven():
    result = normalize({
        "semantic_result": semantic_payload(),
        "source_observation": observation_payload(bindings=[content_binding(provenance={})]),
    })
    assert verification(result) == "NOT_PROVEN"


def test_blocked_provider_mints_blocked_without_synthesizing_observation():
    result = normalize(
        {
            "semantic_result": semantic_payload(),
            "source_observation": observation_payload(
                available=False,
                source_records=[],
                content_bindings=[],
                failure={"code": "research_provider_blocked", "message": "blocked"},
            ),
        },
        status=ToolResultStatus.UNAVAILABLE,
        error={"code": "research_provider_blocked", "message": "blocked"},
    )
    assert verification(result) == "BLOCKED"
    assert result.observation.available is False
    assert result.tool_result.status is ToolResultStatus.UNAVAILABLE


def test_failed_provider_preserves_failure_as_not_proven():
    result = normalize(
        {
            "semantic_result": semantic_payload(),
            "source_observation": observation_payload(
                available=False,
                source_records=[],
                content_bindings=[],
                failure={"code": "provider_failed", "message": "failed"},
            ),
        },
        status=ToolResultStatus.ERROR,
        error={"code": "provider_failed", "message": "failed"},
    )
    assert verification(result) == "NOT_PROVEN"
    assert result.observation.available is False


def test_semantic_result_with_unavailable_observation_is_not_proven():
    result = normalize({
        "semantic_result": semantic_payload(),
    })
    assert verification(result) == "NOT_PROVEN"
    assert result.observation.available is False
    assert result.observation.source_records == ()
    assert result.tool_result.evidence_refs
