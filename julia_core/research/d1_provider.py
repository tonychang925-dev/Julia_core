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

D1_SOURCE_SHA = "b8ae48a9972ba5bf2f0e4b1db5a1025e38e97e82"
D1_REQUEST_CONTRACT_VERSION = "research.bridge.request.v1"
D1_RESPONSE_CONTRACT_VERSION = "research.bridge.response.v1"
D1_PROMPT_FORMAT_VERSION = "research.event-enrichment-prompt.v1"
D1_RETRY_COUNT = 0
D1_FALLBACK_COUNT = 0
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CONFIG_REQUIRED = (
    "JULIA_D1_SOURCE_SHA",
    "JULIA_D1_RESEARCH_BRIDGE_EXECUTABLE",
    "JULIA_D1_RESEARCH_BRIDGE_SHA256",
    "CLAUDE_CLIENT_EXECUTION_LAUNCH_SECRET",
    "CLAUDE_CLIENT_EXECUTION_SOURCE_FD",
    "CLAUDE_CLIENT_EXECUTION_SOURCE_PATH",
    "CLAUDE_CLIENT_EXECUTION_MAX_ROOT",
    "CLAUDE_CLIENT_WEBFETCH_NETWORK_AUTHORITY_JSON",
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
            raise D1ResearchBindingConfigError("executable SHA-256 must be 64 lowercase hex chars")
        if not self.pin.path.is_file() or not os.access(self.pin.path, os.X_OK):
            raise D1ResearchBindingConfigError("pinned D1 executable must be a readable executable file")
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
        bridge_request = build_d1_research_request(request)
        capability_request_id = request.capability_request_id
        capability_call_id = call.capability_call_id if call is not None else ""
        if not capability_request_id or not capability_call_id:
            raise D1ResearchTransmissionError(
                "capability request and runtime call identities are required"
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
        missing = [name for name in _CONFIG_REQUIRED if not self.environment.get(name, "").strip()]
        if missing:
            raise D1ResearchBindingConfigError(
                f"controlled-live D1 environment is incomplete: {', '.join(missing)}"
            )
        if _SHA256.fullmatch(self.environment["JULIA_D1_RESEARCH_BRIDGE_SHA256"].lower()) is None:
            raise D1ResearchBindingConfigError("JULIA_D1_RESEARCH_BRIDGE_SHA256 is invalid")
        if self.environment.get("JULIA_D1_SOURCE_SHA") != D1_SOURCE_SHA:
            raise D1ResearchBindingConfigError(
                f"JULIA_D1_SOURCE_SHA must equal frozen D1 commit {D1_SOURCE_SHA}"
            )
        try:
            authority = json.loads(self.environment["CLAUDE_CLIENT_WEBFETCH_NETWORK_AUTHORITY_JSON"])
        except json.JSONDecodeError as exc:
            raise D1ResearchBindingConfigError("WebFetch network authority JSON is invalid") from exc
        if (
            not isinstance(authority, Mapping)
            or not isinstance(authority.get("allowed_https_domains"), list)
            or not isinstance(authority.get("denied_domains"), list)
        ):
            raise D1ResearchBindingConfigError("WebFetch network authority shape is invalid")

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
                            None if preserved_response is None else dict(preserved_response)
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

    def __init__(self, *, executable: Path, environment: Mapping[str, str], timeout_seconds: float):
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
            raise D1ResearchTransmissionError("D1 executable must emit exactly one response line")
        try:
            response = json.loads(lines[0])
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise D1ResearchTransmissionError("D1 executable emitted invalid JSON") from exc
        if not isinstance(response, dict):
            raise D1ResearchTransmissionError("D1 executable response must be an object")
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


def build_d1_research_request(request: CapabilityRequest) -> dict[str, Any]:
    event = request.arguments.get("event")
    if not isinstance(event, Mapping):
        raise D1ResearchBindingConfigError("research request event is required")
    source_trace_id = str(event.get("source_trace_id", ""))
    if not source_trace_id.strip():
        raise D1ResearchBindingConfigError("research request source_trace_id is required")
    title = str(event.get("title") or event.get("event_type") or "")
    summary = str(event.get("summary") or "")
    query = f"{title}: {summary}".strip()
    if len(query.encode("utf-8")) < 2:
        raise D1ResearchBindingConfigError("research query must contain at least two UTF-8 bytes")
    payload = {
        "fetch_prompt": "Return factual source material only",
        "format": D1_PROMPT_FORMAT_VERSION,
        "max_fetches": 3,
        "query": query,
    }
    return {
        "contract_version": D1_REQUEST_CONTRACT_VERSION,
        "operation": RESEARCH_EVENT_ENRICH_CAPABILITY,
        "correlation": {
            "research_id": f"research_{event.get('event_id')}_{source_trace_id}",
            "event_id": str(event.get("event_id")),
            "event_digest": hashlib.sha256(source_trace_id.encode("utf-8")).hexdigest(),
        },
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
    execution = response["execution"]
    if (
        execution.get("provider_action_retry_count") != D1_RETRY_COUNT
        or execution.get("fallback_count") != D1_FALLBACK_COUNT
    ):
        raise D1ResearchTransmissionError(
            "D1 reported nonzero retry or fallback execution state"
        )

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
        raw_sha = provenance.get("raw_response_sha256") if isinstance(provenance, Mapping) else None
        if not isinstance(reference, Mapping) or raw_sha is None:
            continue
        digest = str(reference.get("content_digest", ""))
        content_ref = f"inline_content:{digest}"
        runtime_ref = _raw_response_ref(raw_sha)
        bindings.append({
            "source_record_id": observation.get("source_record_id", ""),
            "content_ref": content_ref,
            "digest": digest,
            "extract_ref": content_ref,
            "locator": "full_provider_observed_content",
            "provenance": {
                "capability_request_id": capability_request_id,
                "capability_call_id": capability_call_id,
                "runtime_observation_ref": runtime_ref,
                "action_capability_id": "claude.web_fetch",
                "execution_attempt_id": provenance.get("execution_attempt_id") or "",
                "provider_tool_authority_id": provenance.get("provider_tool_authority_id") or "",
                "raw_response_sha256": raw_sha,
                "content_digest": digest,
                "external_content_is_untrusted": True,
            },
        })

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
            "failure": None if error is None else {
                "code": error["code"],
                "message": error["message"],
                "retryable": False,
            },
        },
    }
    stopped = response.get("transport_status") == "ACTION_COLLECTION_STOPPED"
    return ProviderExecutionOutcome(
        status=ToolResultStatus.UNAVAILABLE if stopped else ToolResultStatus.SUCCESS,
        structured_output=structured,
        error=None if error is None else dict(error),
        side_effect_state=SideEffectState.NONE,
    )


def _search_record(response: Mapping[str, Any], source: Mapping[str, Any]) -> dict[str, Any]:
    provenance = source.get("provenance")
    raw_sha = provenance.get("raw_response_sha256") if isinstance(provenance, Mapping) else None
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


def _fetch_record(response: Mapping[str, Any], observation: Mapping[str, Any]) -> dict[str, Any]:
    provenance = observation.get("provenance")
    raw_sha = provenance.get("raw_response_sha256") if isinstance(provenance, Mapping) else None
    reference = observation.get("content_reference")
    content_digest = str(observation.get("content_digest") or "")
    if isinstance(reference, Mapping) and reference.get("content_digest"):
        content_digest = str(reference["content_digest"])
    capture = observation.get("capture_status")
    status = (
        "success" if capture == "PROVIDER_ACTION_COMPLETED"
        else "blocked" if capture == "BLOCKED_BEFORE_ACTION"
        else "failed_or_ambiguous"
    )
    return {
        "source_record_id": observation.get("source_record_id", ""),
        "source_kind": "web_fetch",
        "source_ref": observation.get("source_ref", ""),
        "capture_status": status,
        "fetch_status": status,
        "observed_at": _iso_utc(observation["observed_at_epoch_ms"]),
        "source_url": observation.get("url"),
        "raw_response_ref": _raw_response_ref(raw_sha),
        "content_ref": "" if not content_digest else f"inline_content:{content_digest}",
        "content_digest": content_digest,
        "provenance": {
            **(dict(provenance) if isinstance(provenance, Mapping) else {}),
            "bridge_contract_version": response["contract_version"],
            "research_id": response["correlation"]["research_id"],
        },
    }


def _validate_d1_response_shape(response: Mapping[str, Any]) -> None:
    required = {
        "contract_version", "request_contract_version", "operation", "correlation",
        "transport_status", "execution", "search_observation",
        "research_semantic_result", "source_observations", "error",
    }
    if set(response) != required:
        raise D1ResearchTransmissionError("D1 response field set mismatch")
    if (
        response["contract_version"] != D1_RESPONSE_CONTRACT_VERSION
        or response["request_contract_version"] != D1_REQUEST_CONTRACT_VERSION
        or response["operation"] != RESEARCH_EVENT_ENRICH_CAPABILITY
    ):
        raise D1ResearchTransmissionError("D1 response contract mismatch")
    if response["transport_status"] not in {"RESPONSE_READY", "ACTION_COLLECTION_STOPPED"}:
        raise D1ResearchTransmissionError("D1 transport status is ambiguous")
    correlation = response["correlation"]
    execution = response["execution"]
    if not isinstance(correlation, Mapping) or not isinstance(execution, Mapping):
        raise D1ResearchTransmissionError("D1 correlation or execution truth is malformed")


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
    env = {key: value for key, value in os.environ.items()}
    env.update({key: value for key, value in config.items() if value is not None})
    return env


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
