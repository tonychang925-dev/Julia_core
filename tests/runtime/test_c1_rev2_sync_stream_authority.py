"""C1-R2.6 Sync / stream authority parity contracts.

Protected contracts: C-00 / C-03 / C-08 / C-12 / REV2 R2-I01/R2-I08
Expected baseline: PASS for shared public API shape and sync capability
lifecycle behavior; XFAIL for stream capability authority parity gaps.
Known gaps: A-05 and D-01 from conformance audit
Resolving phase: R2-P4 / R2-P7

TC-ID: C1-R2.6-PARITY-001 sync and stream expose the same turn boundary inputs
TC-ID: C1-R2.6-PARITY-002 sync capability calls re-enter through Context OS
TC-ID: C1-R2.6-PARITY-003 stream must not bypass capability authorization/execution
TC-ID: C1-R2.6-PARITY-004 stream tool output must re-enter through Context OS
TC-ID: C1-R2.6-PARITY-005 parity does not freeze chunking/provider class names
TC-ID: C1-R2.6-PARITY-006 provider-native streaming tool protocol needs source audit

Parity here means same cognitive authority / authorization / execution /
Context OS re-entry / failure semantics. It does not mean identical chunking,
buffering, provider API, token timing, or a mandated executor class name.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

import pytest

from julia_core.capability.manager import CapabilityExecution
from julia_core.capability.models import (
    CapabilityCall,
    Evidence,
    EvidenceSourceType,
    ToolResult,
    ToolResultStatus,
)
from julia_core.capability.policy import AuthorizationDecision, AuthorizationStatus
from julia_core.runtime.julia_session import JuliaSession


ROOT = Path(__file__).resolve().parents[2]


class FakeProvider:
    def __init__(self):
        self.chat_calls: list[list[dict[str, Any]]] = []
        self.stream_calls: list[list[dict[str, Any]]] = []

    def chat(self, messages, cognitive_mode=""):
        self.chat_calls.append(list(messages))
        if len(self.chat_calls) == 1:
            return '```tool_call\n{"name":"read_file","arguments":{"path":"/Users/admin/julia_core/README.md"}}\n```'
        return "final answer after context projection"

    async def stream_async(self, messages):
        self.stream_calls.append(list(messages))
        yield '```tool_call\n{"name":"read_file","arguments":{"path":"/Users/admin/julia_core/README.md"}}\n```'


class FakeCapability:
    def __init__(self):
        self.requires_tool_calls: list[str] = []
        self.detect_tool_call_inputs: list[str] = []
        self.execute_tool_typed_calls: list[str] = []
        self.outcome = self._build_outcome()

    @staticmethod
    def _build_outcome() -> CapabilityExecution:
        call = CapabilityCall(capability_call_id="call-1", capability_request_id="req-1")
        evidence = Evidence(
            evidence_id="ev-1",
            source_type=EvidenceSourceType.TOOL_OBSERVATION,
            source_ref="capability:file.read:provider:local",
            observed_at="2026-08-27T00:00:00Z",
            content_ref="tool_result:call-1:structured_output",
        )
        result = ToolResult(
            capability_call_id="call-1",
            status=ToolResultStatus.SUCCESS,
            structured_output={"content": "tool observation"},
            evidence_refs=("ev-1",),
        )
        return CapabilityExecution(
            AuthorizationDecision(decision=AuthorizationStatus.ALLOW, scope="file.read", reason="allow"),
            call,
            result,
            (evidence,),
        )

    def requires_tool(self, text: str) -> bool:
        self.requires_tool_calls.append(text)
        return False

    def detect_tool_call(self, reply: str) -> str | None:
        self.detect_tool_call_inputs.append(reply)
        if "tool_call" in reply:
            return '{"name":"read_file","arguments":{"path":"/Users/admin/julia_core/README.md"}}'
        return None

    def execute_tool_typed(self, tool_json: str) -> CapabilityExecution:
        self.execute_tool_typed_calls.append(tool_json)
        return self.outcome


class FakeContextOS:
    def __init__(self):
        self.project_tool_result_calls: list[dict[str, Any]] = []

    def project_tool_result(self, *, parent_package=None, tool_result=None, evidence=(), generation_id=""):
        self.project_tool_result_calls.append({
            "parent_package": parent_package,
            "tool_result": tool_result,
            "evidence": evidence,
            "generation_id": generation_id,
        })

        class DeltaPackage:
            active_tail_messages: list[dict[str, Any]] = []

            def to_messages(self, history, user_text):
                content = ""
                if tool_result is not None and hasattr(tool_result, "structured_output"):
                    content = str(tool_result.structured_output.get("content", ""))
                return [{"role": "system", "content": f"[evidence]\ntool_result: {content}"}, {"role": "user", "content": user_text}]

        return DeltaPackage()


class FakeAction:
    def __init__(self):
        self.started: list[dict[str, Any]] = []
        self.finished: list[dict[str, Any]] = []

    def start(self, name, description="", correlation_id=""):
        self.started.append({"name": name, "description": description, "correlation_id": correlation_id})

    def finish(self, status, correlation_id=""):
        self.finished.append({"status": status, "correlation_id": correlation_id})


class FakeRecorder:
    def __init__(self):
        self.records: list[tuple[str, str]] = []

    def record(self, speaker, text, topic=""):
        self.records.append((speaker, text))


def _minimal_session(monkeypatch) -> JuliaSession:
    session = JuliaSession.__new__(JuliaSession)
    session.provider = FakeProvider()
    session.capability = FakeCapability()
    session.context_os = FakeContextOS()
    session.action = FakeAction()
    session.recorder = FakeRecorder()

    class FakePackage:
        package_id = "ctxpkg_sync_stream_parity"
        active_tail_messages: list[dict[str, Any]] = []

    def fake_prepare_turn(self, text, ctx):
        ctx._last_package = FakePackage()
        return [{"role": "user", "content": text}]

    def fake_update_state(self, text, reply, ctx):
        return None

    monkeypatch.setattr(JuliaSession, "_prepare_turn", fake_prepare_turn)
    monkeypatch.setattr(JuliaSession, "_update_conversation_state", fake_update_state)
    return session


def test_sync_and_stream_public_turn_boundaries_have_same_authority_inputs():
    """TC-ID: C1-R2.6-PARITY-001. Transport mode must not change turn authority inputs."""
    sync_sig = inspect.signature(JuliaSession.process)
    stream_sig = inspect.signature(JuliaSession.process_stream)

    for name in ["text", "history", "conversation_id", "turn_id", "modality", "interaction"]:
        assert name in sync_sig.parameters
        assert name in stream_sig.parameters
        assert sync_sig.parameters[name].default == stream_sig.parameters[name].default


def test_sync_path_executes_tool_and_reenters_through_context_os(monkeypatch):
    """TC-ID: C1-R2.6-PARITY-002. Existing sync lifecycle executes and projects tool result."""
    session = _minimal_session(monkeypatch)

    reply = session.process("read the fixture file", [], conversation_id="conv", turn_id="turn")

    carrier = session.capability.outcome
    assert reply == "final answer after context projection"
    assert len(session.provider.chat_calls) == 2
    assert len(session.capability.detect_tool_call_inputs) >= 1
    assert len(session.capability.execute_tool_typed_calls) == 1
    assert len(session.context_os.project_tool_result_calls) == 1
    dispatched = session.context_os.project_tool_result_calls[0]
    assert dispatched["tool_result"] is carrier.tool_result
    assert dispatched["evidence"] == carrier.evidence


@pytest.mark.xfail(
    strict=True,
    reason="A-05/C-08: process_stream currently streams provider deltas without capability authorization/execution lifecycle; pending R2-P4",
)
@pytest.mark.asyncio
async def test_stream_path_executes_cognitively_requested_tool_like_sync(monkeypatch):
    """TC-ID: C1-R2.6-PARITY-003. Stream must not emit tool call text without runtime execution."""
    session = _minimal_session(monkeypatch)

    chunks = []
    async for chunk in session.process_stream("read the fixture file", [], conversation_id="conv", turn_id="turn"):
        chunks.append(chunk)

    assert len(session.capability.detect_tool_call_inputs) >= 1
    assert len(session.capability.execute_tool_calls) == 1
    assert not any("tool_call" in chunk for chunk in chunks)


@pytest.mark.xfail(
    strict=True,
    reason="A-05/C-03+C-08: stream path has no ToolResult → Context OS re-entry after streamed tool request; pending R2-P4",
)
@pytest.mark.asyncio
async def test_stream_tool_result_reenters_through_context_os_before_continuation(monkeypatch):
    """TC-ID: C1-R2.6-PARITY-004. Stream tool observations must use Context OS projection."""
    session = _minimal_session(monkeypatch)

    async for _ in session.process_stream("read the fixture file", [], conversation_id="conv", turn_id="turn"):
        pass

    assert len(session.context_os.project_tool_result_calls) == 1
    assert session.context_os.project_tool_result_calls[0]["tool_result"] == "tool observation"


def test_parity_contract_does_not_require_identical_chunking_or_executor_class():
    """TC-ID: C1-R2.6-PARITY-005. R2.6 freezes semantics, not a class name or token timing."""
    forbidden_mandatory_terms = {
        "must_use_same_chunks",
        "identical_token_timing",
        "CognitiveTurnExecutor is canonical ontology",
    }
    test_source = (ROOT / "tests" / "runtime" / "test_c1_rev2_sync_stream_authority.py").read_text()
    assert forbidden_mandatory_terms.isdisjoint(test_source.splitlines())


def test_active_provider_source_pending_before_freezing_native_stream_tool_events():
    """TC-ID: C1-R2.6-PARITY-006. Provider-native streaming protocol requires source audit."""
    provider_path = ROOT / "providers" / "llm" / "deepseek_provider.py"
    if not provider_path.exists():
        pytest.skip(
            "PENDING D-01/D-03: active provider source is outside Julia_core truth scope; "
            "native structured streaming tool semantics cannot be frozen"
        )

    source = provider_path.read_text(encoding="utf-8")
    assert "stream_async" in source
    assert "provider" in source.lower()
