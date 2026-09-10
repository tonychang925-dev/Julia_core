"""RD1-L0A-F1 controlled-live D1 provider binding regressions."""

from __future__ import annotations

import asyncio
import copy
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

import pytest

from julia_core.capability.models import (
    CapabilityCall,
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)
from julia_core.research.adapter import MarketEventResearchAdapter
from julia_core.research.d1_provider import (
    D1_SOURCE_SHA,
    D1_LAUNCHER_PATH,
    D1_LAUNCHER_SHA256,
    D1_ZOD_TREE_SHA256,
    D1_ZOD_VERSION,
    D1ResearchBindingConfigError,
    D1ResearchBridgeProvider,
    build_d1_research_request,
    create_d1_research_provider_from_environment,
    _subprocess_environment,
    project_d1_response,
)
from julia_core.research.judgment import ResearchJudgmentContextBuilder
from julia_core.research.normalizer import ResearchEvidenceNormalizer
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge


EVENT = {
    "event_id": 501,
    "event_type": "product_launch",
    "summary": "A canonical Market product launch.",
    "direction": "positive",
    "confidence": 0.88,
    "occurred_at": "2026-09-03T09:30:00+08:00",
    "title": "Canonical product launch",
    "source_category": "news",
    "source_name": "source-a",
    "source_url": "https://trusted.example/page",
    "source_trace_id": "news_event:501:l0a",
    "news_id": 501,
}

CONTENT_DIGEST = "a" * 64
RAW_DIGEST = "b" * 64


def research_request():
    return MarketEventResearchAdapter().build_request(
        {"event": EVENT, "theme_relations": []},
        turn_id="turn-l0a",
        generation_id="generation-l0a",
        correlation_id="corr-l0a",
    )


def d1_response(*, retry_count=0, fallback_count=0, stopped=False) -> dict[str, Any]:
    return {
        "contract_version": "research.bridge.response.v1",
        "request_contract_version": "research.bridge.request.v3",
        "operation": "research.event.enrich",
        "correlation": {
            "research_id": "research_501_news_event:501:l0a",
            "event_id": "501",
            "event_digest": hashlib.sha256(
                EVENT["source_trace_id"].encode()
            ).hexdigest(),
            "capability_request_id": "request-l0a",
            "capability_call_id": "call-l0a",
        },
        "transport_status": (
            "ACTION_COLLECTION_STOPPED" if stopped else "RESPONSE_READY"
        ),
        "execution": {
            "action_attempts": 2,
            "search_actions": 1,
            "controlled_acquisition_actions": 1,
            "provider_action_retry_count": retry_count,
            "fallback_count": fallback_count,
            "stopped": stopped,
            "stop_reason": "ALL_SELECTED_SOURCES_FAILED" if stopped else None,
            "selected_acquisition_count": 1,
            "attempted_acquisition_count": 1,
            "successful_acquisition_count": 0 if stopped else 1,
            "failed_acquisition_count": 1 if stopped else 0,
        },
        "search_observation": {
            "observation_kind": "INTERNAL_CANDIDATE_DISCOVERY",
            "query_time_network_actions": 0,
            "external_provider_count": 0,
            "external_credential_count": 0,
            "model_url_authority": False,
        },
        "research_semantic_result": {
            "semantic_status": "ACTION_EVIDENCE_COLLECTED_WITHOUT_MODEL_SYNTHESIS",
            "claims": [],
            "sources": [
                {
                    "source_record_id": "source-search",
                    "source_ref": "https://trusted.example/page",
                    "url": "https://trusted.example/page",
                    "title": None,
                    "domain": "trusted.example",
                    "published_at": None,
                    "observed_at_epoch_ms": 123,
                    "content_reference": None,
                    "content_digest": None,
                    "capture_status": "REPORT_ONLY_CANDIDATE",
                    "observation_kind": "INTERNAL_EVENT_LINKED_CANDIDATE",
                    "origin": "CANONICAL_MARKET_EVENT_LINKED_SOURCE_SEED",
                    "disposition": "REPORT_ONLY_CANDIDATE",
                    "correlation_id": "corr-l0a",
                    "provenance": {
                        "action_capability_id": "d1.internal_candidate_discovery",
                        "source_catalog_identity": "market.news_event.news_raw",
                        "descriptor_sha256": CONTENT_DIGEST,
                    },
                }
            ],
            "contradictions": [],
            "unknowns": [
                {
                    "code": "NO_MODEL_SYNTHESIS",
                    "message": "No model semantic synthesis is contracted by research.bridge.v1",
                }
            ],
            "timeline": [],
            "provider_semantics_are_observation_truth": False,
        },
        "source_observations": [
            {
                "source_record_id": "source-fetch",
                "source_ref": "https://trusted.example/page",
                "url": "https://trusted.example/page",
                "title": None,
                "domain": "trusted.example",
                "published_at": None,
                "observed_at_epoch_ms": 124,
                "content_reference": {
                    "reference_kind": "CONTROLLED_HTTP_ACQUIRED_CONTENT",
                    "retained_content_reference": "controlled-artifact:fixture",
                    "raw_body_digest_sha256": RAW_DIGEST,
                    "extracted_content_base64": "b2JzZXJ2ZWQ=",
                    "extracted_content_digest_sha256": CONTENT_DIGEST,
                    "extracted_utf8_byte_length": 7,
                    "parser_identity": "fixture-parser/v1",
                },
                "content_digest": None if stopped else RAW_DIGEST,
                "capture_status": (
                    "CONTROLLED_HTTP_FAILED" if stopped else "CONTROLLED_HTTP_ACQUIRED"
                ),
                "observation_kind": (
                    "CONTROLLED_HTTP_FAILURE" if stopped else "CONTROLLED_HTTP_DOCUMENT"
                ),
                "correlation_id": "corr-l0a",
                "provenance": {
                    "action_capability_id": "d1.controlled_http_acquisition",
                    "capability_request_id": "request-l0a",
                    "capability_call_id": "call-l0a",
                    "acquisition_request_id": "acq-l0a",
                    "authority_digest": CONTENT_DIGEST,
                    "source_class": "TRUSTED_FIXTURE",
                    "initial_url": "https://trusted.example/page",
                    "initial_hostname": "trusted.example",
                    "final_url": "https://trusted.example/page",
                    "final_hostname": "trusted.example",
                    "redirect_chain": [],
                    "redirect_truth": "PROVEN" if not stopped else "NOT_PROVEN",
                    "final_host_truth": "PROVEN" if not stopped else "NOT_PROVEN",
                    "network_authority": "VALIDATED" if not stopped else "NOT_PROVEN",
                    "tls_validation": "PASSED" if not stopped else "NOT_PROVEN",
                    "http_status": 200 if not stopped else "NOT_SURFACED",
                    "raw_response_boundary": "TRANSPORT_OBSERVED_STDOUT_JSONRPC_FRAME_BYTES",
                    "raw_response_sha256": None if stopped else RAW_DIGEST,
                    "source_content_truth": (
                        "NOT_PROVEN" if stopped else "PUBLISHER_BYTES_RETAINED"
                    ),
                    "external_content_is_untrusted": True,
                    "reason": None,
                },
            }
        ],
        "error": (
            None
            if not stopped
            else {
                "code": "ALL_SELECTED_SOURCES_FAILED",
                "message": "ambiguous response window",
            }
        ),
    }


class FakeTransport:
    def __init__(self, response=None, *, hang=False):
        self.response = response or d1_response()
        self.hang = hang
        self.requests = []
        self.cancelled = False

    async def __call__(self, request):
        self.requests.append(dict(request))
        if self.hang:
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                self.cancelled = True
                raise
        response = dict(self.response)
        response["correlation"] = {
            **response["correlation"],
            "capability_request_id": request["correlation"]["capability_request_id"],
            "capability_call_id": request["correlation"]["capability_call_id"],
        }
        return response


def provider(transport=None) -> D1ResearchBridgeProvider:
    executable = Path("/bin/sh")
    return D1ResearchBridgeProvider(
        executable=executable,
        executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
        environment=controlled_environment(),
        transport=transport,
    )


def controlled_environment(**overrides) -> dict[str, str]:
    executable = D1_LAUNCHER_PATH
    values = {
        "JULIA_D1_SOURCE_SHA": D1_SOURCE_SHA,
        "JULIA_D1_RESEARCH_BRIDGE_EXECUTABLE": str(executable.resolve()),
        "JULIA_D1_RESEARCH_BRIDGE_SHA256": D1_LAUNCHER_SHA256,
        "JULIA_D1_RESEARCH_SOURCE_AUTHORITY_JSON": json.dumps(
            {
                "allowed_https_domains": ["trusted.example"],
                "denied_domains": [],
            }
        ),
        "JULIA_D1_CONTROLLED_ACQUISITION_CONFIG_JSON": json.dumps(
            {
                "contract_version": "research.controlled-http-acquisition.v1",
                "proxy_mode": "DIRECT",
                "timeout_ms": 5000,
                "max_redirects": 2,
                "max_response_bytes": 1048576,
                "allowed_content_types": [
                    "text/html",
                    "text/plain",
                    "application/xhtml+xml",
                ],
                "artifact_root": "/tmp/d1-controlled-artifacts",
            }
        ),
        "JULIA_D1_ZOD_VERSION": D1_ZOD_VERSION,
        "JULIA_D1_ZOD_TREE_SHA256": D1_ZOD_TREE_SHA256,
        "BUN_CONFIG_AUTO_INSTALL": "0",
    }
    values.update(overrides)
    return values


def normalize(execution, request):
    return ResearchEvidenceNormalizer().normalize_provider_outcome(
        ProviderExecutionOutcome(
            status=execution.tool_result.status,
            structured_output=execution.tool_result.structured_output,
            error=execution.tool_result.error,
            side_effect_state=execution.tool_result.side_effect_state,
        ),
        request=request,
        call=execution.capability_call,
    )


def verification_states(enrichment):
    return [
        evidence.integrity_metadata["verification_state"]
        for evidence in enrichment.observation.evidence
    ]


@pytest.mark.asyncio
async def test_l0a_f01_f03_binding_reaches_c1_and_preserves_authority():
    transport = FakeTransport()
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research_enrichment", provider(transport))
    bridge.initialize()
    request = research_request()
    execution = await bridge.manager.execute_typed(request)

    assert transport.requests[0]["operation"] == "research.event.enrich"
    assert transport.requests[0]["research_payload"]["max_fetches"] == 3
    assert execution.tool_result.status is ToolResultStatus.SUCCESS
    assert "verification_state" not in json.dumps(
        execution.tool_result.structured_output
    )
    enrichment = normalize(execution, request)
    assert verification_states(enrichment) == ["REPORT_ONLY", "SOURCE_VERIFIED"]
    binding = enrichment.observation.content_bindings[0]
    assert binding.provenance["capability_request_id"] == request.capability_request_id
    assert (
        binding.provenance["capability_call_id"]
        == execution.capability_call.capability_call_id
    )
    assert (
        binding.provenance["runtime_observation_ref"]
        in enrichment.observation.raw_response_refs
    )


@pytest.mark.asyncio
async def test_a4_autoplug_walk_reaches_c2_input_eligibility():
    request = research_request()
    call = CapabilityCall(
        capability_call_id="cap_call_l0a",
        capability_request_id=request.capability_request_id,
        provider="research_enrichment",
        correlation_id="corr-l0a",
    )
    execution = await provider(FakeTransport()).execute_bound(request, call)
    enrichment = ResearchEvidenceNormalizer().normalize_provider_outcome(
        execution,
        request=request,
        call=call,
    )
    assert "SOURCE_VERIFIED" in verification_states(enrichment)
    material = ResearchJudgmentContextBuilder().build(
        MarketEventResearchAdapter().validate_context(
            {"event": EVENT, "theme_relations": []}
        ),
        enrichment,
    )
    assert material.situation_frame["source_observation_available"] is True


def test_l0a_f02_exact_capability_only_and_request_shape():
    request = research_request()
    payload = build_d1_research_request(request, capability_call_id="cap_call_l0a")
    assert payload["contract_version"] == "research.bridge.request.v3"
    assert (
        payload["correlation"]["capability_request_id"] == request.capability_request_id
    )
    assert payload["correlation"]["capability_call_id"] == "cap_call_l0a"
    assert payload["operation"] == "research.event.enrich"
    expected_digest = hashlib.sha256(
        json.dumps(
            payload["research_payload"], sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    assert payload["research_payload_sha256"] == expected_digest
    expected_candidate_digest = hashlib.sha256(
        json.dumps(
            payload["internal_candidate"], sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    assert payload["internal_candidate_sha256"] == expected_candidate_digest
    assert payload["internal_candidate"]["url"] == EVENT["source_url"]
    assert payload["internal_candidate"]["observed_at"] == EVENT["occurred_at"]
    assert (
        payload["internal_candidate"]["source_catalog_identity"]
        == "market.news_event.news_raw"
    )

    request = dataclasses.replace(request, capability_id="market.event.read")
    with pytest.raises(ValueError, match="only research.event.enrich"):
        asyncio.run(provider().execute(request))


@pytest.mark.asyncio
async def test_l0a_f04_provider_never_mints_verification_state():
    request = research_request()
    outcome = await provider().execute_bound(
        request,
        CapabilityCall(
            capability_call_id="cap_call_l0a",
            capability_request_id=request.capability_request_id,
            provider="research_enrichment",
            correlation_id="corr-l0a",
        ),
    )
    assert "verification_state" not in json.dumps(outcome.structured_output)
    assert outcome.structured_output["semantic_result"]["claims"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize(("field", "value"), [("retry", 1), ("fallback", 1)])
async def test_l0a_f05_f06_nonzero_retry_or_fallback_fails_closed(field, value):
    arguments = {"retry_count": 1} if field == "retry" else {"fallback_count": 1}
    transport = FakeTransport(d1_response(**arguments))
    d1_provider = provider(transport)
    request = research_request()
    outcome = await d1_provider.execute_bound(
        request,
        CapabilityCall(
            capability_call_id="cap_call_l0a",
            capability_request_id=request.capability_request_id,
            provider="research_enrichment",
            correlation_id="corr-l0a",
        ),
    )
    assert outcome.status is ToolResultStatus.UNAVAILABLE
    assert outcome.structured_output["source_observation"]["available"] is False
    assert outcome.error["code"] == "D1_TRANSMISSION_AMBIGUOUS"
    provenance = outcome.structured_output["source_observation"]["provenance"]
    execution_field = (
        "fallback_count" if field == "fallback" else "provider_action_retry_count"
    )
    assert provenance["preserved_d1_response"]["execution"][execution_field] == value


@pytest.mark.asyncio
async def test_l0a_f08_ambiguous_d1_state_stops_without_success():
    transport = FakeTransport(d1_response(stopped=True))
    request = research_request()
    outcome = await provider(transport).execute_bound(
        request,
        CapabilityCall(
            capability_call_id="cap_call_l0a",
            capability_request_id=request.capability_request_id,
            provider="research_enrichment",
            correlation_id="corr-l0a",
        ),
    )
    assert outcome.status is ToolResultStatus.UNAVAILABLE
    assert outcome.structured_output["source_observation"]["available"] is False
    assert (
        outcome.structured_output["source_observation"]["failure"]["retryable"] is False
    )


@pytest.mark.asyncio
async def test_l0a_f07_cancellation_propagates_at_core_boundary():
    transport = FakeTransport(hang=True)
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research_enrichment", provider(transport))
    bridge.initialize()
    task = asyncio.create_task(bridge.manager.execute_typed(research_request()))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert transport.cancelled is True


def test_l0a_config_is_required_and_pinned():
    environment = controlled_environment()
    created = create_d1_research_provider_from_environment(environment)
    assert (
        created.pin.path
        == Path(environment["JULIA_D1_RESEARCH_BRIDGE_EXECUTABLE"]).resolve()
    )
    assert created.pin.sha256 == environment["JULIA_D1_RESEARCH_BRIDGE_SHA256"]

    with pytest.raises(D1ResearchBindingConfigError):
        create_d1_research_provider_from_environment({})

    wrong_source = controlled_environment(JULIA_D1_SOURCE_SHA="0" * 40)
    with pytest.raises(D1ResearchBindingConfigError, match="frozen D1 release"):
        create_d1_research_provider_from_environment(wrong_source)

    bad_pin = controlled_environment(
        JULIA_D1_RESEARCH_BRIDGE_SHA256="0" * 64,
    )
    with pytest.raises(D1ResearchBindingConfigError, match="exact candidate pin"):
        create_d1_research_provider_from_environment(bad_pin)

    alternate_launcher = controlled_environment(
        JULIA_D1_RESEARCH_BRIDGE_EXECUTABLE="/bin/sh"
    )
    with pytest.raises(D1ResearchBindingConfigError, match="exact RD1-V1 D1 launcher"):
        create_d1_research_provider_from_environment(alternate_launcher)

    ambient_zod = controlled_environment(BUN_CONFIG_AUTO_INSTALL="1")
    with pytest.raises(D1ResearchBindingConfigError, match="auto-install boundary"):
        create_d1_research_provider_from_environment(ambient_zod)


def test_rd1_v1_launcher_resolves_zod_without_ambient_install():
    completed = subprocess.run(
        [str(D1_LAUNCHER_PATH)],
        input=b"{}",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    response = json.loads(completed.stdout)
    assert completed.returncode == 0
    assert response["error"]["code"] == "MISSING_LF"
    assert response["execution"]["provider_action_retry_count"] == 0
    assert response["execution"]["fallback_count"] == 0


@pytest.mark.asyncio
async def test_rd1_v1_launcher_digest_is_rechecked_before_invocation(tmp_path):
    executable = tmp_path / "launcher"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o700)
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    d1_provider = D1ResearchBridgeProvider(
        executable=executable,
        executable_sha256=digest,
        environment=controlled_environment(),
        transport=FakeTransport(),
    )
    executable.write_text("#!/bin/sh\nexit 99\n")
    request = research_request()
    with pytest.raises(D1ResearchBindingConfigError, match="changed before execution"):
        await d1_provider.execute_bound(
            request,
            CapabilityCall(
                capability_call_id="cap_call_l0a",
                capability_request_id=request.capability_request_id,
                provider="research_enrichment",
                correlation_id="corr-l0a",
            ),
        )
    assert d1_provider.execution_count == 0


def test_l0a_scope_remains_core_d1_only():
    # NCF-A7 R10-A3: pin is now the content-addressed identity of the D1 bridge
    # release tree (see manifests/d1-<sha>.file-manifest.sha256).
    assert (
        D1_SOURCE_SHA
        == "c173f92d34de212f84646d2467e382ea6d8f53ebec24b01ac65404f38d774dd4"
    )
    source = (
        Path(__file__)
        .parents[2]
        .joinpath("julia_core", "research", "d1_provider.py")
        .read_text()
    )
    assert "ai_theme_app" not in source
    assert "voice" not in source.lower()


def test_d1r6_subprocess_boundary_contains_no_ambient_state(monkeypatch):
    monkeypatch.setenv("HOME", "/Users/ambient")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ambient-secret")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "ambient-oauth")
    controlled = controlled_environment()
    assert _subprocess_environment(controlled) == controlled


def test_d1r6_rejects_multiple_or_external_discovery_truth():
    response = d1_response()
    response["execution"]["search_actions"] = 2
    with pytest.raises(Exception, match="unauthorized retry"):
        project_d1_response(
            copy.deepcopy(response),
            capability_request_id="request-l0a",
            capability_call_id="call-l0a",
        )
    response = d1_response()
    response["search_observation"]["external_provider_count"] = 1
    with pytest.raises(Exception, match="internal discovery truth"):
        project_d1_response(
            response,
            capability_request_id="request-l0a",
            capability_call_id="call-l0a",
        )
