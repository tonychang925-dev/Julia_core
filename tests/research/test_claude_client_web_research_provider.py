from __future__ import annotations

import asyncio
import base64
import copy
import hashlib
import json
from pathlib import Path

import pytest

from julia_core.capability.models import (
    CapabilityRequest,
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)
from julia_core.research import (
    ClaudeClientExecutionConfig,
    ClaudeClientWebResearchProvider,
)
from julia_core.runtime import capability_bridge as bridge_module
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
from julia_core.runtime.julia_session import JuliaSession


RAW_BYTES = b'{"content":[]}\n'
RAW_SHA256 = hashlib.sha256(RAW_BYTES).hexdigest()
QUERY = "latest robotics industry external catalysts"
TOOL_JSON = json.dumps({"name": "research.web.query", "arguments": {"query": QUERY}})
PROVIDER_SYNTHESIS = (
    "Provider natural-language synthesis mentioning https://must-not-become-a-source.example/path"
)


def source_observation() -> dict:
    return {
        "contract_version": "claude.websearch.source-observation.v1",
        "source_identity_status": "PROVIDER_STRUCTURED_SOURCE_IDENTITY_PRESENT",
        "source_binding": "PROVIDER_RESULTS_FIELD",
        "sources": [
            {
                "source_id": "src_provider_bound_identity",
                "url": "https://provider.example/robotics-catalysts",
                "title": "Provider Robotics Catalyst Source",
                "published_at": "2026-09-01T00:00:00Z",
                "page_age": "2026-09-01",
                "provider_observation_ref": {
                    "execution_attempt_id": "exec_attempt_test",
                    "provider_result_path": "$.results[0].content[0]",
                    "provider_tool_use_id": "provider_tool_use_test",
                    "raw_response_boundary": "TRANSPORT_OBSERVED_STDOUT_JSONRPC_FRAME_BYTES",
                    "raw_response_sha256": RAW_SHA256,
                    "raw_response_classification": "EXECUTION_PROVENANCE_ONLY",
                },
            }
        ],
        "reason": None,
    }


class FakeStdin:
    def __init__(self, process: "FakeProcess"):
        self.process = process

    def write(self, payload: bytes) -> None:
        self.process.writes.append(payload)

    async def drain(self) -> None:
        return None


class FakeStdout:
    def __init__(self, process: "FakeProcess"):
        self.process = process

    async def readline(self) -> bytes:
        if self.process.hang:
            await asyncio.sleep(10)
        response = self.process.responses.pop(0)
        return (json.dumps(response) + "\n").encode("utf-8")


class FakeStderr:
    async def read(self) -> bytes:
        return b""


class FakeProcess:
    def __init__(self, responses: list[dict], *, hang: bool = False):
        self.responses = list(responses)
        self.writes: list[bytes] = []
        self.stdin = FakeStdin(self)
        self.stdout = FakeStdout(self)
        self.stderr = FakeStderr()
        self.returncode: int | None = None
        self.terminated = False
        self.hang = hang

    async def wait(self) -> int | None:
        self.returncode = 0 if self.returncode is None else self.returncode
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = -15

    def kill(self) -> None:
        self.returncode = -9


def execution_responses(content: list[dict], *, ok: bool = True) -> list[dict]:
    execute = (
        {
            "ok": True,
            "kind": "stdio_tools_call_completed",
            "execution_status": "COMPLETED",
            "side_effect_state": "SUCCEEDED",
            "tools_call_transmission_count": 1,
            "retry_count": 0,
            "execution_attempt_id": "exec_attempt_test",
            "provider_tool_authority_id": "authority_test",
            "provider_request_id": "provider_request_test",
            "capability_request_id": "cap_req_test",
            "capability_call_id": "cap_call_test",
            "correlation_id": "corr_test",
            "stdio_provider_session_id": "stdio_session_test",
            "jsonrpc_request_id": "jsonrpc_test",
            "response": {"content": content},
            "raw_response": {
                "boundary": "TRANSPORT_OBSERVED_STDOUT_JSONRPC_FRAME_BYTES",
                "completeness": "COMPLETE",
                "byte_size": len(RAW_BYTES),
                "sha256": RAW_SHA256,
                "base64": base64.b64encode(RAW_BYTES).decode("ascii"),
                "lf_delimiter_observed": True,
                "stdio_provider_session_id": "stdio_session_test",
                "execution_attempt_id": "exec_attempt_test",
                "provider_tool_authority_id": "authority_test",
                "jsonrpc_request_id": "jsonrpc_test",
                "observed_at_epoch_ms": 1780000000000,
            },
            "raw_response_trusted": True,
            "provider_tool_name": "WebSearch",
            "authorized_query": QUERY,
            "network_policy_compatibility": "NO_ENFORCEABLE_NETWORK_RESTRICTION",
            "external_result_truth": "NOT_PROVEN",
            "external_freshness_truth": "NOT_PROVEN",
            "search_index_completeness_truth": "NOT_PROVEN",
            "source_observation": source_observation(),
        }
        if ok
        else {
            "ok": False,
            "kind": "stdio_tools_call_failed",
            "code": "provider_error",
            "message": "provider indicated isError=true",
            "execution_status": "SENT_OR_POSSIBLY_SENT",
            "side_effect_state": "UNKNOWN",
            "tools_call_transmission_count": 1,
            "retry_count": 0,
        }
    )
    return [
        {
            "ok": True,
            "type": "ADMITTED",
            "admission": {"execution_admission_id": "exec_adm_test"},
        },
        {
            "ok": True,
            "type": "STARTED",
            "execution": {"execution_attempt_id": "exec_attempt_test"},
        },
        execute,
        {"ok": True, "type": "SHUTDOWN_ACCEPTED"},
    ]


def make_config(tmp_path: Path, **overrides) -> ClaudeClientExecutionConfig:
    repository = tmp_path / "Claude_client"
    authority_root = tmp_path / "authority"
    repository.mkdir(exist_ok=True)
    authority_root.mkdir(exist_ok=True)
    (repository / "execution_boundary.ts").write_text("", encoding="utf-8")
    source = authority_root / "source.txt"
    source.write_text("trusted authority source", encoding="utf-8")
    bun = tmp_path / "bun"
    bun.write_text("", encoding="utf-8")
    bun.chmod(0o755)
    values = {
        "repository_root": repository,
        "launch_secret": "launch-secret-0123456789",
        "source_path": source,
        "max_root": authority_root,
        "worker_id": "worker-test",
        "policy_digest": "b" * 64,
        "provider_authority_json": json.dumps({"executable": "/provider"}),
        "bun_path": str(bun),
        "timeout_seconds": 2.0,
    }
    values.update(overrides)
    return ClaudeClientExecutionConfig(**values)


def install_process(
    monkeypatch: pytest.MonkeyPatch,
    responses: list[dict],
    *,
    hang: bool = False,
) -> FakeProcess:
    process = FakeProcess(responses, hang=hang)
    captured: dict = {}

    async def create_subprocess_exec(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", create_subprocess_exec)
    process.captured = captured
    return process


@pytest.mark.asyncio
async def test_exact_public_surface_query_and_single_action_remain_visible(
    tmp_path, monkeypatch
):
    process = install_process(
        monkeypatch,
        execution_responses([{"type": "text", "text": PROVIDER_SYNTHESIS}]),
    )
    provider = ClaudeClientWebResearchProvider(make_config(tmp_path))
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", provider)
    bridge.initialize()

    execution = bridge.execute_tool_typed(TOOL_JSON)

    assert execution.tool_result.status is ToolResultStatus.PARTIAL
    assert execution.tool_result.side_effect_state is SideEffectState.NONE
    output = execution.tool_result.structured_output
    assert output["query"] == QUERY
    assert output["findings"] == []
    assert output["sources"][0]["ref"] == "src_provider_bound_identity"
    assert output["sources"][0]["url"] == "https://provider.example/robotics-catalysts"
    assert output["sources"][0]["title"] == "Provider Robotics Catalyst Source"
    assert output["sources"][0]["provider_observation_ref"] == source_observation()["sources"][0]["provider_observation_ref"]
    assert "source_id" not in output["sources"][0]
    assert "sha256" not in output["sources"][0]
    assert PROVIDER_SYNTHESIS not in json.dumps(output)
    assert output["provenance"]["action_count"] == 1
    assert output["provenance"]["retry_count"] == 0
    assert output["provenance"]["fallback_count"] == 0
    assert output["provenance"]["structured_external_source_url_available"] is True
    assert output["provenance"]["raw_response_sha256"] == RAW_SHA256
    assert output["provenance"]["raw_response_classification"] == "EXECUTION_PROVENANCE_ONLY"
    assert "SOURCE_IDENTITY_ONLY_NO_SOURCE_BOUND_CONTENT" in output["limitations"]
    assert "external_result_truth=NOT_PROVEN" in output["limitations"]
    assert "external_freshness_truth=NOT_PROVEN" in output["limitations"]
    assert "search_index_completeness_truth=NOT_PROVEN" in output["limitations"]

    assert process.captured["args"] == (str(tmp_path / "bun"), "execution_boundary.ts")
    kwargs = process.captured["kwargs"]
    assert kwargs["cwd"] == str(tmp_path / "Claude_client")
    assert kwargs["env"]["CLAUDE_CLIENT_STDIO_PROVIDER_AUTHORITY_JSON"]
    commands = [json.loads(item) for item in process.writes]
    assert [command["type"] for command in commands] == [
        "ADMIT",
        "START",
        "EXECUTE",
        "SHUTDOWN",
    ]
    assert commands[0]["request"]["capability_id"] == "claude.web_search"
    assert commands[0]["request"]["arguments"] == {"query": QUERY}
    assert commands[2]["execution_attempt_id"] == "exec_attempt_test"
    assert provider.execution_count == 1
    assert provider.retry_count == 0
    assert provider.fallback_count == 0


@pytest.mark.asyncio
async def test_completed_search_without_valid_source_identity_fails_closed(
    tmp_path, monkeypatch
):
    mutations = (
        lambda observation: observation.pop("source_observation"),
        lambda observation: observation["source_observation"].update(
            {
                "source_identity_status": "BLOCKED_PROVIDER_DOES_NOT_EXPOSE_SOURCE_IDENTITY",
                "source_binding": "NONE",
                "sources": [],
                "reason": "provider results array contains no inspectable source identity",
            }
        ),
        lambda observation: observation["source_observation"]["sources"].__setitem__(
            0,
            {**observation["source_observation"]["sources"][0], "url": "ftp://example.com/source"},
        ),
        lambda observation: observation["source_observation"]["sources"][0].pop(
            "provider_observation_ref"
        ),
        lambda observation: observation["source_observation"]["sources"][0][
            "provider_observation_ref"
        ].update(
            {"raw_response_classification": "EXTERNAL_SOURCE_PROVENANCE"}
        ),
    )

    for mutation in mutations:
        responses = execution_responses([{"type": "text", "text": PROVIDER_SYNTHESIS}])
        mutation(responses[2])
        install_process(monkeypatch, responses)
        provider = ClaudeClientWebResearchProvider(make_config(tmp_path))
        bridge = RuntimeCapabilityBridge()
        bridge.register_provider("research", provider)
        bridge.initialize()

        execution = bridge.execute_tool_typed(TOOL_JSON)

        assert execution.tool_result.status is ToolResultStatus.ERROR
        assert execution.tool_result.error["code"] == "claude_client_source_identity_unavailable"
        assert execution.tool_result.structured_output == {}
        assert execution.tool_result.evidence_refs == ()
        assert bridge.manager.canonical_evidence == []


@pytest.mark.asyncio
async def test_provider_failure_is_typed_error_without_retry_or_fallback(
    tmp_path, monkeypatch
):
    process = install_process(monkeypatch, execution_responses([], ok=False))
    provider = ClaudeClientWebResearchProvider(make_config(tmp_path))

    outcome = await provider.execute(
        CapabilityRequest(
            "research.web.query", {"query": QUERY}, capability_request_id="req"
        )
    )

    assert outcome.status is ToolResultStatus.ERROR
    assert outcome.structured_output == {}
    assert outcome.error["provider_code"] == "provider_error"
    assert outcome.error["retry_count"] == 0
    assert outcome.side_effect_state is SideEffectState.UNKNOWN
    commands = [json.loads(item)["type"] for item in process.writes]
    assert commands.count("EXECUTE") == 1


@pytest.mark.asyncio
async def test_invalid_raw_digest_or_timestamp_fails_closed_without_synthetic_provenance(
    tmp_path, monkeypatch
):
    for field, value in (
        ("sha256", "not-a-sha256"),
        ("base64", base64.b64encode(b"different\n").decode("ascii")),
        ("observed_at_epoch_ms", None),
    ):
        responses = execution_responses([{"type": "text", "text": "observation"}])
        responses[2]["raw_response"][field] = value
        install_process(monkeypatch, responses)
        provider = ClaudeClientWebResearchProvider(make_config(tmp_path))

        outcome = await provider.execute(
            CapabilityRequest(
                "research.web.query", {"query": QUERY}, capability_request_id="req"
            )
        )

        assert outcome.status is ToolResultStatus.ERROR
        assert outcome.error["code"] == "claude_client_raw_evidence_invalid"
        assert outcome.structured_output == {}


@pytest.mark.asyncio
async def test_invalid_query_fails_closed_before_public_process_launch(
    tmp_path, monkeypatch
):
    process = install_process(monkeypatch, execution_responses([]))
    provider = ClaudeClientWebResearchProvider(make_config(tmp_path))

    outcome = await provider.execute(
        CapabilityRequest(
            "research.web.query", {"query": "x"}, capability_request_id="req"
        )
    )

    assert outcome.status is ToolResultStatus.ERROR
    assert outcome.error["code"] == "invalid_request"
    assert process.writes == []


def test_provider_declares_research_runtime_budget_with_lifecycle_grace(tmp_path):
    provider = ClaudeClientWebResearchProvider(
        make_config(tmp_path, timeout_seconds=150.0)
    )

    assert provider.capability_runtime_timeout_seconds == 155.0


@pytest.mark.asyncio
async def test_caller_timeout_argument_has_no_execution_authority(
    tmp_path, monkeypatch
):
    process = install_process(monkeypatch, execution_responses([]))
    provider = ClaudeClientWebResearchProvider(
        make_config(tmp_path, timeout_seconds=150.0)
    )

    outcome = await provider.execute(
        CapabilityRequest(
            "research.web.query",
            {"query": QUERY, "timeout": 999999},
            capability_request_id="req",
        )
    )

    assert outcome.status is ToolResultStatus.ERROR
    assert outcome.error["code"] == "invalid_request"
    assert process.writes == []
    assert provider.capability_runtime_timeout_seconds == 155.0


@pytest.mark.asyncio
async def test_timeout_is_typed_and_terminates_boundary(tmp_path, monkeypatch):
    process = install_process(monkeypatch, execution_responses([]), hang=True)
    provider = ClaudeClientWebResearchProvider(
        make_config(tmp_path, timeout_seconds=0.05)
    )

    outcome = await provider.execute(
        CapabilityRequest(
            "research.web.query", {"query": QUERY}, capability_request_id="req"
        )
    )

    assert outcome.status is ToolResultStatus.TIMEOUT
    assert outcome.error["code"] == "claude_client_timeout"
    assert process.terminated is True


def test_production_surface_contains_no_forbidden_provider_or_private_import():
    source = (
        Path(__file__).parents[2] / "julia_core" / "research" / "claude_client_web.py"
    )
    text = source.read_text(encoding="utf-8")
    assert "AsyncAnthropic" not in text
    assert "ANTHROPIC_API_KEY" not in text
    assert "web_provider" not in text
    assert "https://" not in text


@pytest.mark.asyncio
async def test_claude_client_evidence_reenters_julia_second_pass(monkeypatch, tmp_path):
    from julia_core.events import store as event_store_module

    monkeypatch.setattr(
        event_store_module,
        "_store",
        event_store_module.EventStore(str(tmp_path / "events")),
    )
    install_process(
        monkeypatch,
        execution_responses([{"type": "text", "text": PROVIDER_SYNTHESIS}]),
    )
    provider = ClaudeClientWebResearchProvider(make_config(tmp_path))
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", provider)
    bridge.initialize()
    monkeypatch.setattr(bridge_module, "_bridge", bridge)

    class ResearchCognitionInstrumentation:
        def __init__(self):
            self.calls = []

        def chat(self, messages, *, cognitive_mode=""):
            self.calls.append([dict(message) for message in messages])
            if len(self.calls) == 1:
                return f"```tool_call\n{TOOL_JSON}\n```"
            return "JULIA_FINAL_JUDGMENT_ONLY"

    cognition = ResearchCognitionInstrumentation()
    session = JuliaSession(provider=cognition)
    session.capability = bridge
    session.workflow_router.bridge = bridge

    reply = session.process(
        QUERY,
        [],
        conversation_id="claude-client-research",
        turn_id="claude-client-turn",
        modality="text",
    )

    assert reply == "JULIA_FINAL_JUDGMENT_ONLY"
    assert len(cognition.calls) == 2
    assert provider.execution_count == 1
    second_pass_system = str(cognition.calls[1][0]["content"])
    assert execution_evidence_visible(bridge)
    assert "latest robotics industry external catalysts" in second_pass_system
    assert "https://provider.example/robotics-catalysts" in second_pass_system
    assert "Provider Robotics Catalyst Source" in second_pass_system
    assert "src_provider_bound_identity" in second_pass_system
    assert "SOURCE_IDENTITY_ONLY_NO_SOURCE_BOUND_CONTENT" in second_pass_system
    assert "EXECUTION_PROVENANCE_ONLY" in second_pass_system
    assert PROVIDER_SYNTHESIS not in second_pass_system
    assert "https://must-not-become-a-source.example/path" not in second_pass_system
    assert f"claude-client:raw-response:{RAW_SHA256}" not in second_pass_system


def execution_evidence_visible(bridge: RuntimeCapabilityBridge) -> bool:
    return bool(bridge.manager.canonical_evidence)
