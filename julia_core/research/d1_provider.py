"""Controlled-live provider binding for the frozen D1 research bridge."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from julia_core.capability.models import (
    CapabilityCall,
    CapabilityRequest,
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)
from julia_core.research.adapter import RESEARCH_EVENT_ENRICH_CAPABILITY

# NCF-A7 R10-A3: D1 release identity. Content-addressed hash of the D1 bridge
# release tree (manifests/d1-<sha>.file-manifest.sha256). Replaced the prior
# 0e1b5ca commit-label after the reference-based response transport fix
# (extracted content is no longer inlined on the D1→Core IPC envelope).
D1_SOURCE_SHA = "c173f92d34de212f84646d2467e382ea6d8f53ebec24b01ac65404f38d774dd4"
D1_REQUEST_CONTRACT_VERSION = "research.bridge.request.v3"
D1_RESPONSE_CONTRACT_VERSION = "research.bridge.response.v1"
D1_PROMPT_FORMAT_VERSION = "research.event-enrichment-prompt.v1"
D1_RETRY_COUNT = 0
D1_FALLBACK_COUNT = 0
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CONFIG_REQUIRED = (
    "JULIA_D1_SOURCE_SHA",
    "JULIA_D1_RESEARCH_BRIDGE_EXECUTABLE",
    "JULIA_D1_RESEARCH_BRIDGE_SHA256",
    "JULIA_D1_RESEARCH_SOURCE_AUTHORITY_JSON",
    "JULIA_D1_CONTROLLED_ACQUISITION_CONFIG_JSON",
)


class D1ResearchBindingConfigError(ValueError):
    """The controlled-live D1 binding is incomplete or invalid."""


class D1ResearchTransmissionError(RuntimeError):
    """D1 execution ended in an ambiguous or invalid transmission state."""


class D1Transport(Protocol):
    async def __call__(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        """Return one parsed D1 research.bridge.response.v1 object."""


@dataclass(frozen=True, slots=True)
class D1ExecutablePin:
    path: Path
    sha256: str


class D1ResearchBridgeProvider:
    """Bind research.event.enrich to one pinned, one-shot D1 executable.

    The provider owns transport only. It performs no retry, no fallback, no
    verification-state minting, and no semantic synthesis.
    """

    def __init__(
        self,
        *,
        executable: str | Path,
        executable_sha256: str,
        environment: Mapping[str, str] | None = None,
        transport: D1Transport | None = None,
        timeout_seconds: float = 120.0,
    ):
        self.pin = D1ExecutablePin(
            path=Path(executable).expanduser().resolve(strict=True),
            sha256=str(executable_sha256).lower(),
        )
        if _SHA256.fullmatch(self.pin.sha256) is None:
            raise D1ResearchBindingConfigError(
                "executable SHA-256 must be 64 lowercase hex chars"
            )
        if not self.pin.path.is_file() or not os.access(self.pin.path, os.X_OK):
            raise D1ResearchBindingConfigError(
                "pinned D1 executable must be a readable executable file"
            )
        observed = _file_sha256(self.pin.path)
        if observed != self.pin.sha256:
            raise D1ResearchBindingConfigError(
                f"D1 executable digest mismatch: expected {self.pin.sha256}, observed {observed}"
            )
        if not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
            raise D1ResearchBindingConfigError("timeout_seconds must be positive")
        self.environment = dict(environment or {})
        self.transport = transport
        self.timeout_seconds = float(timeout_seconds)
        self._require_boundary_environment()
        self.execution_count = 0

    async def health(self) -> tuple[bool, str]:
        try:
            observed = _file_sha256(self.pin.path)
        except OSError as exc:
            return False, f"pinned D1 executable unavailable: {exc}"
        if observed != self.pin.sha256:
            return False, "pinned D1 executable digest mismatch"
        return True, f"D1 research bridge pinned at sha256:{observed}"

    async def execute(self, request: CapabilityRequest) -> ProviderExecutionOutcome:
        return await self.execute_bound(request, None)

    async def execute_bound(
        self, request: CapabilityRequest, call: CapabilityCall | None
    ) -> ProviderExecutionOutcome:
        if request.capability_id != RESEARCH_EVENT_ENRICH_CAPABILITY:
            raise ValueError("D1 provider accepts only research.event.enrich")
        self._require_boundary_environment()
        capability_request_id = request.capability_request_id
        capability_call_id = call.capability_call_id if call is not None else ""
        if not capability_request_id or not capability_call_id:
            raise D1ResearchTransmissionError(
                "capability request and runtime call identities are required"
            )
        bridge_request = build_d1_research_request(
            request, capability_call_id=capability_call_id
        )

        self.execution_count += 1
        transport = self.transport or D1SubprocessTransport(
            executable=self.pin.path,
            environment=self.environment,
            timeout_seconds=self.timeout_seconds,
        )
        preserved_response: Mapping[str, Any] | None = None
        try:
            response = await transport(bridge_request)
            preserved_response = response
            return project_d1_response(
                response,
                capability_request_id=capability_request_id,
                capability_call_id=capability_call_id,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            return self._ambiguous_outcome(
                bridge_request,
                code="D1_TRANSMISSION_AMBIGUOUS",
                message=str(exc),
                preserved_response=preserved_response,
            )

    def _require_boundary_environment(self) -> None:
        missing = [
            name
            for name in _CONFIG_REQUIRED
            if not self.environment.get(name, "").strip()
        ]
        if missing:
            raise D1ResearchBindingConfigError(
                f"controlled-live D1 environment is incomplete: {', '.join(missing)}"
            )
        if (
            _SHA256.fullmatch(
                self.environment["JULIA_D1_RESEARCH_BRIDGE_SHA256"].lower()
            )
            is None
        ):
            raise D1ResearchBindingConfigError(
                "JULIA_D1_RESEARCH_BRIDGE_SHA256 is invalid"
            )
        if self.environment.get("JULIA_D1_SOURCE_SHA") != D1_SOURCE_SHA:
            raise D1ResearchBindingConfigError(
                f"JULIA_D1_SOURCE_SHA must equal frozen D1 commit {D1_SOURCE_SHA}"
            )
        try:
            authority = json.loads(
                self.environment["JULIA_D1_RESEARCH_SOURCE_AUTHORITY_JSON"]
            )
        except json.JSONDecodeError as exc:
            raise D1ResearchBindingConfigError(
                "trusted research source authority JSON is invalid"
            ) from exc
        if (
            not isinstance(authority, Mapping)
            or not isinstance(authority.get("allowed_https_domains"), list)
            or not isinstance(authority.get("denied_domains"), list)
        ):
            raise D1ResearchBindingConfigError(
                "trusted research source authority shape is invalid"
            )
        try:
            acquisition = json.loads(
                self.environment["JULIA_D1_CONTROLLED_ACQUISITION_CONFIG_JSON"]
            )
        except json.JSONDecodeError as exc:
            raise D1ResearchBindingConfigError(
                "controlled acquisition config JSON is invalid"
            ) from exc
        required = {
            "contract_version",
            "proxy_mode",
            "timeout_ms",
            "max_redirects",
            "max_response_bytes",
            "allowed_content_types",
            "artifact_root",
        }
        if (
            not isinstance(acquisition, Mapping)
            or set(acquisition) != required
            or acquisition.get("contract_version")
            != "research.controlled-http-acquisition.v1"
            or acquisition.get("proxy_mode") != "DIRECT"
            or not isinstance(acquisition.get("allowed_content_types"), list)
            or not isinstance(acquisition.get("artifact_root"), str)
            or not acquisition.get("artifact_root", "").startswith("/")
        ):
            raise D1ResearchBindingConfigError(
                "controlled acquisition config shape is invalid"
            )

    def _ambiguous_outcome(
        self,
        request: Mapping[str, Any],
        *,
        code: str,
        message: str,
        preserved_response: Mapping[str, Any] | None = None,
    ) -> ProviderExecutionOutcome:
        request_bytes = _canonical_json(request).encode("utf-8")
        return ProviderExecutionOutcome(
            status=ToolResultStatus.UNAVAILABLE,
            structured_output={
                "semantic_result": _no_model_semantics(),
                "source_observation": {
                    "source_records": [],
                    "content_bindings": [],
                    "raw_response_refs": [],
                    "observed_at": "",
                    "provenance": {
                        "d1_source_sha": D1_SOURCE_SHA,
                        "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
                        "transmission_state": "AMBIGUOUS",
                        "preserved_d1_response": (
                            None
                            if preserved_response is None
                            else dict(preserved_response)
                        ),
                    },
                    "available": False,
                    "failure": {"code": code, "message": message, "retryable": False},
                },
            },
            error={"code": code, "message": message, "retryable": False},
            side_effect_state=SideEffectState.UNKNOWN,
        )


class D1SubprocessTransport:
    """One-shot asyncio transport for the deployment-pinned D1 launcher."""

    def __init__(
        self,
        *,
        executable: Path,
        environment: Mapping[str, str],
        timeout_seconds: float,
    ):
        self.executable = executable
        self.environment = environment
        self.timeout_seconds = timeout_seconds

    async def __call__(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        process = await asyncio.create_subprocess_exec(
            str(self.executable),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=_subprocess_environment(self.environment),
        )
        request_bytes = (_canonical_json(request) + "\n").encode("utf-8")
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(request_bytes), timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            await _terminate(process)
            raise D1ResearchTransmissionError("D1 executable deadline exceeded")
        except asyncio.CancelledError:
            await _terminate(process)
            raise
        if process.returncode != 0:
            detail = stderr.decode("utf-8", errors="replace").strip()
            raise D1ResearchTransmissionError(
                f"D1 executable failed with exit={process.returncode}: {detail}"
            )
        lines = stdout.splitlines()
        if len(lines) != 1:
            raise D1ResearchTransmissionError(
                "D1 executable must emit exactly one response line"
            )
        try:
            response = json.loads(lines[0])
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise D1ResearchTransmissionError(
                "D1 executable emitted invalid JSON"
            ) from exc
        if not isinstance(response, dict):
            raise D1ResearchTransmissionError(
                "D1 executable response must be an object"
            )
        return response


def create_d1_research_provider_from_environment(
    environment: Mapping[str, str] | None = None,
    *,
    transport: D1Transport | None = None,
) -> D1ResearchBridgeProvider:
    env = dict(environment if environment is not None else os.environ)
    configured = any(name in env for name in _CONFIG_REQUIRED)
    if not configured:
        raise D1ResearchBindingConfigError(
            "controlled-live D1 provider configuration is required"
        )
    return D1ResearchBridgeProvider(
        executable=env["JULIA_D1_RESEARCH_BRIDGE_EXECUTABLE"],
        executable_sha256=env["JULIA_D1_RESEARCH_BRIDGE_SHA256"],
        environment=env,
        transport=transport,
    )


def build_d1_research_request(
    request: CapabilityRequest,
    *,
    capability_call_id: str,
) -> dict[str, Any]:
    event = request.arguments.get("event")
    if not isinstance(event, Mapping):
        raise D1ResearchBindingConfigError("research request event is required")
    source_trace_id = str(event.get("source_trace_id", ""))
    if not source_trace_id.strip():
        raise D1ResearchBindingConfigError(
            "research request source_trace_id is required"
        )
    title = str(event.get("title") or event.get("event_type") or "")
    summary = str(event.get("summary") or "")
    query = f"{title}: {summary}".strip()
    if len(query.encode("utf-8")) < 2:
        raise D1ResearchBindingConfigError(
            "research query must contain at least two UTF-8 bytes"
        )
    payload = {
        "fetch_prompt": "Return factual source material only",
        "format": D1_PROMPT_FORMAT_VERSION,
        "max_fetches": 3,
        "query": query,
    }
    internal_candidate = {
        "contract_version": "research.internal-candidate.v1",
        "url": str(event.get("source_url") or ""),
        "title": title or None,
        "snippet_or_summary": summary,
        "rank_or_score": 0,
        "source_catalog_identity": "market.news_event.news_raw",
        "event_id": str(event.get("event_id")),
        "news_id": event.get("news_id"),
        "source_trace_id": source_trace_id,
        "observed_at": str(event.get("occurred_at") or ""),
    }
    return {
        "contract_version": D1_REQUEST_CONTRACT_VERSION,
        "operation": RESEARCH_EVENT_ENRICH_CAPABILITY,
        "correlation": {
            "research_id": f"research_{event.get('event_id')}_{source_trace_id}",
            "event_id": str(event.get("event_id")),
            "event_digest": hashlib.sha256(source_trace_id.encode("utf-8")).hexdigest(),
            "capability_request_id": request.capability_request_id,
            "capability_call_id": capability_call_id,
        },
        "internal_candidate": internal_candidate,
        "internal_candidate_sha256": hashlib.sha256(
            _canonical_json(internal_candidate).encode("utf8")
        ).hexdigest(),
        "research_payload": payload,
        "research_payload_sha256": _payload_sha256(payload),
    }


def project_d1_response(
    response: Mapping[str, Any],
    *,
    capability_request_id: str,
    capability_call_id: str,
) -> ProviderExecutionOutcome:
    if not capability_request_id or not capability_call_id:
        raise D1ResearchTransmissionError(
            "capability request and runtime call identities are required"
        )
    _validate_d1_response_shape(response)
    correlation = response["correlation"]
    if (
        correlation.get("capability_request_id") != capability_request_id
        or correlation.get("capability_call_id") != capability_call_id
    ):
        raise D1ResearchTransmissionError("D1 runtime correlation mismatch")
    execution = response["execution"]
    if (
        execution.get("provider_action_retry_count") != D1_RETRY_COUNT
        or execution.get("fallback_count") != D1_FALLBACK_COUNT
        or execution.get("attempted_acquisition_count")
        != execution.get("selected_acquisition_count")
        or execution.get("search_actions") != 1
        or execution.get("controlled_acquisition_actions") > 1
        or execution.get("selected_acquisition_count") > 1
    ):
        raise D1ResearchTransmissionError(
            "D1 reported unauthorized retry, fallback, or candidate count"
        )
    discovery = response.get("search_observation")
    if (
        not isinstance(discovery, Mapping)
        or discovery.get("observation_kind") != "INTERNAL_CANDIDATE_DISCOVERY"
        or discovery.get("query_time_network_actions") != 0
        or discovery.get("external_provider_count") != 0
        or discovery.get("external_credential_count") != 0
        or discovery.get("model_url_authority") is not False
    ):
        raise D1ResearchTransmissionError("D1 internal discovery truth is invalid")

    semantic = response.get("research_semantic_result")
    sources = semantic.get("sources", []) if isinstance(semantic, Mapping) else []
    observations = response.get("source_observations", [])
    records: dict[str, dict[str, Any]] = {}
    raw_refs: set[str] = set()
    for source in sources if isinstance(sources, list) else []:
        record = _search_record(response, source)
        records[record["source_record_id"]] = record
        raw_ref = record["raw_response_ref"]
        if raw_ref:
            raw_refs.add(raw_ref)
    for observation in observations if isinstance(observations, list) else []:
        record = _fetch_record(response, observation)
        records[record["source_record_id"]] = record
        raw_ref = record["raw_response_ref"]
        if raw_ref:
            raw_refs.add(raw_ref)

    bindings = []
    for observation in observations if isinstance(observations, list) else []:
        reference = observation.get("content_reference")
        provenance = observation.get("provenance")
        raw_sha = (
            provenance.get("raw_response_sha256")
            if isinstance(provenance, Mapping)
            else None
        )
        if not isinstance(reference, Mapping) or raw_sha is None:
            continue
        digest = str(reference.get("raw_body_digest_sha256", ""))
        extracted_digest = str(reference.get("extracted_content_digest_sha256", ""))
        content_ref = str(reference.get("retained_content_reference", ""))
        runtime_ref = f"controlled_raw_body:{raw_sha}"
        if (
            observation.get("capture_status") != "CONTROLLED_HTTP_ACQUIRED"
            or provenance.get("action_capability_id")
            != "d1.controlled_http_acquisition"
            or provenance.get("final_host_truth") != "PROVEN"
            or provenance.get("redirect_truth") != "PROVEN"
            or provenance.get("network_authority") != "VALIDATED"
            or provenance.get("tls_validation") != "PASSED"
            or provenance.get("http_status") == "NOT_SURFACED"
        ):
            continue
        bindings.append(
            {
                "source_record_id": observation.get("source_record_id", ""),
                "content_ref": content_ref,
                "digest": digest,
                "extract_ref": f"controlled_extract:{extracted_digest}",
                "locator": "full_deterministically_extracted_document",
                "provenance": {
                    "capability_request_id": capability_request_id,
                    "capability_call_id": capability_call_id,
                    "runtime_observation_ref": runtime_ref,
                    "action_capability_id": "d1.controlled_http_acquisition",
                    "acquisition_request_id": provenance.get("acquisition_request_id")
                    or "",
                    "authority_digest": provenance.get("authority_digest") or "",
                    "source_class": provenance.get("source_class") or "",
                    "initial_url": provenance.get("initial_url") or "",
                    "initial_hostname": provenance.get("initial_hostname") or "",
                    "final_url": provenance.get("final_url") or "",
                    "final_hostname": provenance.get("final_hostname") or "",
                    "redirect_chain": provenance.get("redirect_chain", []),
                    "redirect_truth": "PROVEN",
                    "final_host_truth": "PROVEN",
                    "network_authority": "VALIDATED",
                    "tls_validation": "PASSED",
                    "http_status": provenance.get("http_status"),
                    "raw_response_sha256": raw_sha,
                    "extracted_content_sha256": extracted_digest,
                    "retained_content_reference": content_ref,
                    "parser_identity": reference.get("parser_identity"),
                    "external_content_is_untrusted": True,
                },
            }
        )

    observed_times = []
    for source in sources if isinstance(sources, list) else []:
        value = source.get("observed_at_epoch_ms")
        if isinstance(value, int) and not isinstance(value, bool):
            observed_times.append(value)
    for observation in observations if isinstance(observations, list) else []:
        value = observation.get("observed_at_epoch_ms")
        if isinstance(value, int) and not isinstance(value, bool):
            observed_times.append(value)
    observed_at = _iso_utc(max(observed_times)) if observed_times else ""
    transport_ready = response.get("transport_status") == "RESPONSE_READY"
    error = response.get("error")
    if transport_ready and (
        not bindings or execution.get("successful_acquisition_count", 0) < 1
    ):
        raise D1ResearchTransmissionError(
            "D1 success lacked controlled acquired evidence"
        )
    if not transport_ready and execution.get("successful_acquisition_count", 0) != 0:
        raise D1ResearchTransmissionError(
            "stopped D1 response claimed successful acquisition"
        )
    structured = {
        "semantic_result": _no_model_semantics(),
        "source_observation": {
            "source_records": list(records.values()),
            "content_bindings": bindings,
            "raw_response_refs": list(raw_refs),
            "observed_at": observed_at,
            "provenance": {
                "bridge_contract_version": response["contract_version"],
                "bridge_operation": response["operation"],
                "research_id": response["correlation"]["research_id"],
                "event_id": response["correlation"]["event_id"],
                "event_digest": response["correlation"]["event_digest"],
                "execution": dict(execution),
                "external_content_is_untrusted": True,
            },
            "available": bool(bindings) and transport_ready,
            "failure": (
                None
                if error is None
                else {
                    "code": error["code"],
                    "message": error["message"],
                    "retryable": False,
                }
            ),
        },
    }
    stopped = response.get("transport_status") == "ACTION_COLLECTION_STOPPED"
    return ProviderExecutionOutcome(
        status=ToolResultStatus.UNAVAILABLE if stopped else ToolResultStatus.SUCCESS,
        structured_output=structured,
        error=None if error is None else dict(error),
        side_effect_state=SideEffectState.NONE,
    )


def _search_record(
    response: Mapping[str, Any], source: Mapping[str, Any]
) -> dict[str, Any]:
    provenance = source.get("provenance")
    raw_sha = (
        provenance.get("raw_response_sha256")
        if isinstance(provenance, Mapping)
        else None
    )
    return {
        "source_record_id": source.get("source_record_id", ""),
        "source_kind": "web_search",
        "source_ref": source.get("source_ref", ""),
        "capture_status": "report_only",
        "fetch_status": "not_fetched",
        "observed_at": _optional_iso_utc(source.get("observed_at_epoch_ms")),
        "source_url": source.get("url"),
        "raw_response_ref": _raw_response_ref(raw_sha),
        "content_ref": "",
        "content_digest": "",
        "provenance": {
            **(dict(provenance) if isinstance(provenance, Mapping) else {}),
            "bridge_contract_version": response["contract_version"],
            "research_id": response["correlation"]["research_id"],
        },
    }


def _fetch_record(
    response: Mapping[str, Any], observation: Mapping[str, Any]
) -> dict[str, Any]:
    provenance = observation.get("provenance")
    raw_sha = (
        provenance.get("raw_response_sha256")
        if isinstance(provenance, Mapping)
        else None
    )
    reference = observation.get("content_reference")
    content_digest = str(observation.get("content_digest") or "")
    if isinstance(reference, Mapping) and reference.get("content_digest"):
        content_digest = str(reference["content_digest"])
    capture = observation.get("capture_status")
    status = (
        "success"
        if capture == "CONTROLLED_HTTP_ACQUIRED"
        else "blocked" if capture == "BLOCKED_BEFORE_ACTION" else "failed"
    )
    return {
        "source_record_id": observation.get("source_record_id", ""),
        "source_kind": "controlled_http",
        "source_ref": observation.get("source_ref", ""),
        "capture_status": status,
        "fetch_status": status,
        "observed_at": _iso_utc(observation["observed_at_epoch_ms"]),
        "source_url": observation.get("url"),
        "raw_response_ref": "" if raw_sha is None else f"controlled_raw_body:{raw_sha}",
        "content_ref": (
            str(reference.get("retained_content_reference", ""))
            if isinstance(reference, Mapping)
            else ""
        ),
        "content_digest": content_digest,
        "provenance": {
            **(dict(provenance) if isinstance(provenance, Mapping) else {}),
            "bridge_contract_version": response["contract_version"],
            "research_id": response["correlation"]["research_id"],
        },
    }


def _validate_d1_response_shape(response: Mapping[str, Any]) -> None:
    required = {
        "contract_version",
        "request_contract_version",
        "operation",
        "correlation",
        "transport_status",
        "execution",
        "search_observation",
        "research_semantic_result",
        "source_observations",
        "error",
    }
    if set(response) != required:
        raise D1ResearchTransmissionError("D1 response field set mismatch")
    if (
        response["contract_version"] != D1_RESPONSE_CONTRACT_VERSION
        or response["request_contract_version"] != D1_REQUEST_CONTRACT_VERSION
        or response["operation"] != RESEARCH_EVENT_ENRICH_CAPABILITY
    ):
        raise D1ResearchTransmissionError("D1 response contract mismatch")
    if response["transport_status"] not in {
        "RESPONSE_READY",
        "ACTION_COLLECTION_STOPPED",
    }:
        raise D1ResearchTransmissionError("D1 transport status is ambiguous")
    correlation = response["correlation"]
    execution = response["execution"]
    if not isinstance(correlation, Mapping) or not isinstance(execution, Mapping):
        raise D1ResearchTransmissionError(
            "D1 correlation or execution truth is malformed"
        )
    if set(correlation) != {
        "research_id",
        "event_id",
        "event_digest",
        "capability_request_id",
        "capability_call_id",
    }:
        raise D1ResearchTransmissionError("D1 correlation field set mismatch")
    if set(execution) != {
        "action_attempts",
        "search_actions",
        "controlled_acquisition_actions",
        "provider_action_retry_count",
        "fallback_count",
        "stopped",
        "stop_reason",
        "selected_acquisition_count",
        "attempted_acquisition_count",
        "successful_acquisition_count",
        "failed_acquisition_count",
    }:
        raise D1ResearchTransmissionError("D1 execution truth field set mismatch")


def _no_model_semantics() -> dict[str, Any]:
    return {
        "factual_summary": "",
        "claims": [],
        "contradictions": [],
        "unknowns": [
            "NO_MODEL_SYNTHESIS: No model semantic synthesis is contracted by research.bridge.v1"
        ],
        "timeline": [],
        "related_entities": [],
    }


def _raw_response_ref(raw_sha: Any) -> str:
    value = "" if raw_sha is None else str(raw_sha)
    return f"stdio_raw_response:{value}" if value else ""


def _payload_sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _optional_iso_utc(epoch_ms: Any) -> str:
    return "" if epoch_ms is None else _iso_utc(epoch_ms)


def _iso_utc(epoch_ms: int) -> str:
    seconds, _ = divmod(int(epoch_ms), 1000)
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(seconds))


def _subprocess_environment(config: Mapping[str, str]) -> dict[str, str]:
    return {key: value for key, value in config.items() if value is not None}


async def _terminate(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    process.kill()
    try:
        await process.wait()
    except ProcessLookupError:
        pass


__all__ = [
    "D1_SOURCE_SHA",
    "D1ResearchBindingConfigError",
    "D1ResearchBridgeProvider",
    "D1ResearchTransmissionError",
    "D1SubprocessTransport",
    "build_d1_research_request",
    "create_d1_research_provider_from_environment",
    "project_d1_response",
]
