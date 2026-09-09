"""P3-CC I1b-3(+R1) — C-09 production alignment wiring + parity proofs.

R1 additions:
- capability_frame semantic is unambiguous: empty → proceed; non-empty →
  MUST be a governed manifest shape and ALWAYS goes through the accepted
  encoder (non-empty malformed frames fail closed).
- C2 execution-context projection moved to situation_frame; capability_frame
  for C2 is empty; all four execution values remain model-visible.
- dynamic provider-spy boundary tests (no vacuous assertions).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from julia_core.runtime.context_execution_runtime import (
    CognitiveContextPackage,
    ContextExecutionRuntime,
)
from julia_core.runtime.julia_session import (
    CapabilityAlignmentNotReady,
    JuliaSession,
)

ROOT = Path(__file__).resolve().parents[2]


def _session_source() -> str:
    return (ROOT / "julia_core" / "runtime" / "julia_session.py").read_text()


def _runtime_source() -> str:
    return (
        ROOT / "julia_core" / "runtime" / "context_execution_runtime.py"
    ).read_text()


def _entry(capability_id: str, availability: str = "available") -> dict:
    return {
        "capability_id": capability_id,
        "description": f"test {capability_id}",
        "input_schema": {"q": "query"},
        "output_schema": {},
        "side_effect_class": "read_only",
        "permission_requirements": ["file.read"],
        "idempotency_support": "none",
        "latency_cost_hints": {},
        "data_sensitivity": "test_observation",
        "availability": availability,
        "schema_version": "1.0",
        "provenance": {
            "source": "capability:registry",
            "definition_ref": capability_id,
            "derived_at": "2026-09-09T00:00:00Z",
        },
    }


def _package(*entries) -> CognitiveContextPackage:
    pkg = CognitiveContextPackage()
    pkg.capability_frame = {
        "manifest_entries": [dict(e) for e in entries],
        "non_admitted_diagnostics": [],
    }
    return pkg


class _ProviderSpy:
    def __init__(self):
        self.chat_calls: list[list[dict]] = []
        self.stream_calls: list[list[dict]] = []

    def chat(self, messages, cognitive_mode=""):
        self.chat_calls.append(list(messages))
        return "ok"

    async def stream_async(self, messages):
        self.stream_calls.append(list(messages))
        yield "ok"


class _SessionBoundaryHarness(JuliaSession):
    """Real JuliaSession subclass with only the provider replaced.

    Exercises the REAL JuliaSession alignment method through a genuine instance
    so method binding is real; the provider spy captures what would cross the
    provider boundary. No heavy services are initialized."""

    def __init__(self):
        # Deliberately skip JuliaSession.__init__ (no env services needed for
        # the capability-alignment boundary path).
        self.provider = _ProviderSpy()


def _harness_capability_block(provider_calls) -> str:
    for messages in provider_calls:
        for message in messages:
            content = str(message.get("content", ""))
            if content.startswith("[C-09 capability representation]"):
                return content
    return ""


def _align_via_session(harness, pkg, messages):
    """Drive the REAL session seam method on a real instance."""
    return harness._align_capability_messages(pkg, list(messages))


FILE_A = _entry("file.read")
MARKET_B = _entry("market.event.read", availability="registered")


# ── §31 direct Context OS capability render retired ────────────────────────

def test_to_messages_no_longer_renders_capability_frame():
    pkg = _package(FILE_A)
    messages = pkg.to_messages([], "hi")
    rendered = "\n".join(str(m) for m in messages)
    assert "[capability]" not in rendered
    assert "capability: file.read" not in rendered
    assert "manifest_entries" in pkg.capability_frame


def test_runtime_no_direct_capability_frame_render():
    assert 'self._render_frame("capability"' not in _runtime_source()


# ── §32/§33 C-09 injection via REAL session seam + provider spy ────────────

def test_real_seam_injects_encoder_block_once_and_spy_receives_it():
    harness = _SessionBoundaryHarness()
    pkg = _package(FILE_A)
    messages = [{"role": "system", "content": "[identity] test"},
                {"role": "user", "content": "hi"}]
    aligned = _align_via_session(harness, pkg, messages)
    # The exact call-site pattern used by JuliaSession provider boundaries.
    harness.provider.chat(aligned)
    blocks = [
        str(m.get("content"))
        for m in aligned
        if m.get("role") == "system"
        and str(m.get("content", "")).startswith("[C-09 capability representation]")
    ]
    assert len(blocks) == 1
    text = blocks[0]
    assert "capability: file.read" in text
    assert "side_effect_class: read_only" in text
    assert "availability: available" in text
    assert "provenance:" in text
    assert "available_tools" not in text
    assert "tool_manifest" not in text.lower()
    # Spy actually received the aligned block once.
    assert len(harness.provider.chat_calls) == 1
    assert "[C-09 capability representation]" in str(harness.provider.chat_calls[0])


# ── R1-B malformed capability_frame shapes fail closed ─────────────────────

def test_empty_capability_frame_proceeds_without_block():
    harness = _SessionBoundaryHarness()
    pkg = CognitiveContextPackage()  # capability_frame == {}
    messages = [{"role": "user", "content": "hi"}]
    aligned = _align_via_session(harness, pkg, messages)
    assert aligned == messages
    harness.provider.chat(aligned)
    assert _harness_capability_block(harness.provider.chat_calls) == ""


@pytest.mark.parametrize(
    "bad_frame",
    [
        {"non_admitted_diagnostics": []},  # claims manifest shape but no entries key
        {"foo": "bar"},
    ],
)
def test_non_empty_malformed_frame_fails_closed_no_provider_call(bad_frame):
    harness = _SessionBoundaryHarness()
    pkg = CognitiveContextPackage()
    pkg.capability_frame = bad_frame
    with pytest.raises(CapabilityAlignmentNotReady):
        _align_via_session(harness, pkg, [{"role": "user", "content": "hi"}])
    # No raw rendering, no tool_manifest fallback, no provider call.
    assert harness.provider.chat_calls == []


def test_non_mapping_capability_frame_fails_closed():
    harness = _SessionBoundaryHarness()
    pkg = CognitiveContextPackage()
    pkg.capability_frame = "not-a-mapping"  # type: ignore[assignment]
    with pytest.raises(CapabilityAlignmentNotReady):
        _align_via_session(harness, pkg, [{"role": "user", "content": "hi"}])
    assert harness.provider.chat_calls == []


def test_malformed_manifest_entry_fails_closed_no_provider_call():
    harness = _SessionBoundaryHarness()
    pkg = CognitiveContextPackage()
    pkg.capability_frame = {
        "manifest_entries": [{"capability_id": "file.read"}],
        "non_admitted_diagnostics": [],
    }
    with pytest.raises(CapabilityAlignmentNotReady):
        _align_via_session(harness, pkg, [{"role": "user", "content": "hi"}])
    assert harness.provider.chat_calls == []


# ── §12 empty valid manifest proceeds ──────────────────────────────────────

def test_empty_valid_manifest_injects_nothing():
    pkg = _package()
    messages = [{"role": "system", "content": "[identity] test"},
                {"role": "user", "content": "hi"}]
    aligned = _align_via_session(_SessionBoundaryHarness(), pkg, messages)
    assert aligned == messages


# ── R1-A C2 execution context preserved in situation frame ─────────────────

class _StubJudgmentBuilder:
    def __init__(self):
        pass

    def build(self, market_context, enrichment):
        from types import SimpleNamespace

        return SimpleNamespace(
            situation_frame={"mode": "c2_judgment"},
            evidence_frame={"normalized": True},
            control_frame={"kind": "research_judgment"},
            capability_frame={
                "research_capability_request_id": "req-1",
                "research_capability_call_id": "call-1",
                "tool_result_status": "succeeded",
                "correlation_id": "corr-1",
            },
            provenance={"market_event_id": "evt-1", "generation_id": "gen-1",
                        "source_trace_id": "trace-1"},
        )


def test_c2_execution_context_preserved_in_situation_frame(monkeypatch):
    import julia_core.research.judgment as judgment_module

    monkeypatch.setattr(
        judgment_module, "ResearchJudgmentContextBuilder", _StubJudgmentBuilder
    )
    runtime = ContextExecutionRuntime()
    pkg = runtime.project_research_judgment(
        market_context=object(), enrichment=object()
    )

    execution_context = pkg.situation_frame["capability_execution_context"]
    for key in (
        "research_capability_request_id",
        "research_capability_call_id",
        "tool_result_status",
        "correlation_id",
    ):
        assert key in execution_context, key
    assert execution_context["research_capability_request_id"] == "req-1"
    assert execution_context["correlation_id"] == "corr-1"

    # capability_frame is reserved for the governed C-08 manifest only.
    assert pkg.capability_frame == {}

    # Provider-facing non-capability messages still carry the execution
    # context and carry no generic capability / C-09 block (no manifest).
    messages = pkg.to_messages([], "Form Julia's judgment in JSON.")
    rendered = "\n".join(str(m) for m in messages)
    assert "research_capability_request_id" in rendered
    assert "correlation_id" in rendered
    assert "[capability]" not in rendered
    assert "[C-09 capability representation]" not in rendered


# ── §7 real-path sync/stream parity ────────────────────────────────────────

def test_sync_and_stream_boundary_share_identical_capability_block():
    sync_harness = _SessionBoundaryHarness()
    stream_harness = _SessionBoundaryHarness()
    pkg = _package(FILE_A, MARKET_B)
    base = [{"role": "system", "content": "[identity] test"},
            {"role": "user", "content": "question"}]

    # Real seam method on two real session instances (sync + stream paths both
    # consume the seam at the provider boundary).
    sync_input = sync_harness._align_capability_messages(pkg, list(base))
    stream_input = stream_harness._align_capability_messages(pkg, list(base))
    assert sync_input == stream_input
    block_sync = _harness_capability_block([sync_input])
    block_stream = _harness_capability_block([stream_input])
    assert block_sync == block_stream
    assert "capability: market.event.read" in block_sync


# ── §8 retry current-package real-seam proof ───────────────────────────────

def test_retry_current_package_b_encoded_not_stale_a():
    harness = _SessionBoundaryHarness()
    pkg_a = _package(FILE_A)
    pkg_b = _package(MARKET_B)
    messages = [{"role": "user", "content": "hi"}]

    # P0 attempt uses package A; retry uses package B (fresh Context OS
    # generation). Drive through the real seam exactly as the retry call site
    # does, then through the provider spy.
    p0_input = harness._align_capability_messages(pkg_a, list(messages))
    harness.provider.chat(p0_input)
    retry_input = harness._align_capability_messages(pkg_b, list(messages))
    harness.provider.chat(retry_input)

    assert len(harness.provider.chat_calls) == 2
    first = _harness_capability_block(harness.provider.chat_calls[:1])
    second = _harness_capability_block(harness.provider.chat_calls[1:])
    assert "capability: file.read" in first
    assert "capability: market.event.read" in second
    assert "capability: file.read" not in second  # stale A absent


# ── §9 tool-continuation current delta proof ───────────────────────────────

def test_tool_continuation_current_delta_package_encoded():
    harness = _SessionBoundaryHarness()
    parent = _package(FILE_A)
    delta = _package(MARKET_B)
    messages = [{"role": "user", "content": "continue"}]

    continuation_input = harness._align_capability_messages(delta, list(messages))
    harness.provider.chat(continuation_input)
    captured = _harness_capability_block(harness.provider.chat_calls)
    assert "capability: market.event.read" in captured
    assert "capability: file.read" not in captured  # stale parent absent
    assert parent.capability_frame != delta.capability_frame


# ── §10 research-final provider boundary proof ─────────────────────────────

def test_research_final_boundary_aligns_context_package():
    from julia_core.runtime.research_continuation import (
        ResearchContinuationMaterial,
    )

    harness = _SessionBoundaryHarness()
    material = ResearchContinuationMaterial(
        messages=[{"role": "user", "content": "final"}],
        product=None,
        trace={},
        context_package=_package(FILE_A),
    )
    # material.messages carry NO capability text (not smuggled).
    assert "[C-09" not in str(material.messages)
    # Exact research-final call-site pattern: align from context_package then
    # stream on the provider spy.
    aligned = harness._align_capability_messages(
        material.context_package, list(material.messages)
    )
    captured = _harness_capability_block([aligned])
    assert "capability: file.read" in captured


# ── §40 static AST audit: every provider call method aligns first ──────────

def test_static_audit_every_provider_call_method_contains_alignment():
    source = _session_source()
    tree = ast.parse(source)
    session_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "JuliaSession"
    )
    provider_call_methods = []
    for method in session_class.body:
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        has_provider_call = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("chat", "stream_async")
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "provider"
            for node in ast.walk(method)
        )
        if not has_provider_call:
            continue
        has_seam = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "_align_capability_messages"
            for node in ast.walk(method)
        )
        has_prepare = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_prepare_turn"
            for node in ast.walk(method)
        )
        assert has_seam or has_prepare, (
            f"provider call in {method.name} without alignment seam"
        )
        provider_call_methods.append(method.name)
    assert "process_stream" in provider_call_methods
    assert "_chat_impl" in provider_call_methods
    assert "form_preliminary_research_judgment" in provider_call_methods


def test_static_audit_research_failure_precedes_provider_call():
    source = _session_source()
    idx_failure = source.find("raise ResearchTurnNotReady(material.failure)")
    idx_stream_material = source.find("self.provider.stream_async(aligned)")
    assert idx_failure != -1
    assert idx_failure < idx_stream_material


def test_no_vacuous_or_true_assertions_in_this_file():
    source = Path(__file__).read_text()
    # Exclude this very self-check statement from the scan.
    marker = "def test_no_vacuous_or_true_assertions_in_this_file():"
    source = source.split(marker)[0]
    assert "or True" not in source


# ─────────────────────────────────────────────────────────────────────────────
# R2 — REAL PRODUCTION CONTROL-FLOW PROVIDER-BOUNDARY PROOFS
# These tests drive the actual JuliaSession control-flow methods
# (_chat_impl / process_stream) with controlled test doubles for external
# services. They NEVER hand-invoke the alignment seam as the proof.
# ─────────────────────────────────────────────────────────────────────────────

class _NoopEventStore:
    def append(self, event):
        pass


class _FakeRecorder:
    def __init__(self):
        self.records = []

    def record(self, *args, **kwargs):
        self.records.append(args)

    def consolidate(self, *args, **kwargs):
        pass


class _FakeAction:
    def start(self, *args, **kwargs):
        pass

    def finish(self, *args, **kwargs):
        pass


class _FakePersona:
    traits = {}
    identity = {}


class _FakeOutcome:
    def __init__(self, tool_result=None, evidence=()):
        self.authorization_decision = SimpleNamespace(decision="ALLOW")
        self.tool_result = tool_result or SimpleNamespace(
            status=SimpleNamespace(value="success"), structured_output={}
        )
        self.evidence = evidence
        self.capability_call = SimpleNamespace(call_id="call-1")


class _FakeCapability:
    def __init__(self):
        self.requires_tool_result = False
        self.tool_call = None
        self.outcome = None
        self.execute_calls = []

    def requires_tool(self, text):
        return self.requires_tool_result

    def detect_tool_call(self, reply):
        return self.tool_call

    def execute_tool_typed(self, tool_json, **kwargs):
        self.execute_calls.append(tool_json)
        return self.outcome

    async def execute_tool_typed_async(self, tool_json, **kwargs):
        self.execute_calls.append(tool_json)
        return self.outcome


class _FakeContextOS:
    """Controlled Context OS double returning scripted packages.

    The JuliaSession control-flow methods execute for real; only the Context OS
    package returns are scripted (prepare / retry / tool-result)."""

    def __init__(self):
        self.initial_pkg = None
        self.retry_pkg = None
        self.delta_pkg = None
        self.retry_calls = 0
        self.tool_result_calls = 0

    def prepare(self, **kwargs):
        return self.initial_pkg

    def project_retry_control(self, *, parent_package, reason, generation_id):
        self.retry_calls += 1
        return self.retry_pkg

    def project_tool_result(self, *, parent_package, tool_result, evidence=(), generation_id=""):
        self.tool_result_calls += 1
        return self.delta_pkg

    def project_authorization_outcome(self, **kwargs):
        return self.delta_pkg


class _RealSession(JuliaSession):
    """A REAL JuliaSession instance; __init__ injects test doubles only."""

    def __init__(self, context_os, capability):
        self.provider = _ProviderSpy()
        self.context_os = context_os
        self.capability = capability
        self.action = _FakeAction()
        self.recorder = _FakeRecorder()
        self.bootstrap = ""
        self.persona = _FakePersona()
        self.relationship = None
        self._session_state = {}


def _real_session(context_os, capability, monkeypatch):
    monkeypatch.setattr(
        "julia_core.events.store.get_event_store",
        lambda: _NoopEventStore(),
    )
    return _RealSession(context_os, capability)


def _c09_block(messages) -> str:
    for message in messages:
        content = str(message.get("content", ""))
        if content.startswith("[C-09 capability representation]"):
            return content
    return ""


def test_real_sync_initial_path(monkeypatch):
    capability = _FakeCapability()
    capability.requires_tool_result = False
    capability.tool_call = None
    context_os = _FakeContextOS()
    context_os.initial_pkg = _package(FILE_A)
    session = _real_session(context_os, capability, monkeypatch)

    session.process("hello", [], conversation_id="c1", turn_id="t1")

    assert len(session.provider.chat_calls) >= 1
    sync_initial = _c09_block(session.provider.chat_calls[0])
    assert sync_initial.count("[C-09 capability representation]") == 1
    assert "capability: file.read" in sync_initial
    assert "[capability]" not in str(session.provider.chat_calls[0])
    assert "available_tools" not in str(session.provider.chat_calls[0])


def test_real_stream_initial_path(monkeypatch):
    capability = _FakeCapability()
    context_os = _FakeContextOS()
    context_os.initial_pkg = _package(FILE_A)
    session = _real_session(context_os, capability, monkeypatch)

    chunks = []
    async def run():
        async for chunk in session.process_stream(
            "hello", [], conversation_id="c1", turn_id="t1"
        ):
            chunks.append(chunk)
    import asyncio
    asyncio.run(run())

    assert len(session.provider.stream_calls) >= 1
    stream_initial = _c09_block(session.provider.stream_calls[0])
    assert stream_initial.count("[C-09 capability representation]") == 1
    assert "capability: file.read" in stream_initial
    assert "[capability]" not in str(session.provider.stream_calls[0])
    assert len(chunks) >= 1


def test_real_sync_stream_parity(monkeypatch):
    sync_cap, stream_cap = _FakeCapability(), _FakeCapability()
    sync_ctx, stream_ctx = _FakeContextOS(), _FakeContextOS()
    pkg = _package(FILE_A, MARKET_B)
    sync_ctx.initial_pkg = pkg
    stream_ctx.initial_pkg = pkg
    sync_session = _real_session(sync_ctx, sync_cap, monkeypatch)
    stream_session = _real_session(stream_ctx, stream_cap, monkeypatch)

    sync_session.process("q", [], conversation_id="c", turn_id="t")
    async def consume():
        async for _ in stream_session.process_stream(
            "q", [], conversation_id="c", turn_id="t"
        ):
            pass
    import asyncio
    asyncio.run(consume())

    sync_block = _c09_block(sync_session.provider.chat_calls[0])
    stream_block = _c09_block(stream_session.provider.stream_calls[0])
    assert sync_block != ""
    assert sync_block == stream_block


def test_real_sync_retry_path(monkeypatch):
    capability = _FakeCapability()
    capability.requires_tool_result = True
    capability.tool_call = None  # first model pass emits no tool call
    context_os = _FakeContextOS()
    context_os.initial_pkg = _package(FILE_A)
    context_os.retry_pkg = _package(MARKET_B)  # retry package carries B
    session = _real_session(context_os, capability, monkeypatch)

    session.process("market", [], conversation_id="c", turn_id="t")

    assert len(session.provider.chat_calls) >= 2
    assert context_os.retry_calls >= 1
    first = _c09_block(session.provider.chat_calls[0])
    retry = _c09_block(session.provider.chat_calls[1])
    assert "capability: file.read" in first
    assert "capability: market.event.read" in retry
    assert "capability: file.read" not in retry  # stale A block absent


def test_real_sync_tool_continuation_path(monkeypatch):
    import json as _json

    capability = _FakeCapability()
    capability.requires_tool_result = False
    capability.tool_call = _json.dumps(
        {"name": "file.read", "arguments": {"path": "/tmp/x"}}
    )
    capability.outcome = _FakeOutcome()
    context_os = _FakeContextOS()
    context_os.initial_pkg = _package(FILE_A)
    context_os.delta_pkg = _package(MARKET_B)  # delta carries B
    session = _real_session(context_os, capability, monkeypatch)

    session.process("read", [], conversation_id="c", turn_id="t")

    assert len(capability.execute_calls) >= 1
    assert context_os.tool_result_calls >= 1
    assert len(session.provider.chat_calls) >= 2
    continuation = _c09_block(session.provider.chat_calls[1])
    assert "capability: market.event.read" in continuation
    assert "capability: file.read" not in continuation  # stale parent absent


def test_real_alignment_failure_at_provider_boundary(monkeypatch):
    capability = _FakeCapability()
    context_os = _FakeContextOS()
    context_os.initial_pkg = CognitiveContextPackage()
    context_os.initial_pkg.capability_frame = {
        "non_admitted_diagnostics": []
    }  # non-empty malformed frame
    session = _real_session(context_os, capability, monkeypatch)

    with pytest.raises(CapabilityAlignmentNotReady):
        session.process("hi", [], conversation_id="c", turn_id="t")
    assert session.provider.chat_calls == []
    assert session.provider.stream_calls == []


# ── R2: research final / failure REAL process_stream branches ──────────────

class _FakeSameTurnResearchContinuation:
    material = None

    def __init__(self, *args, **kwargs):
        pass

    async def run(self, **kwargs):
        return self.material


def _research_text() -> str:
    # Deterministic research ingress phrase (研究 + 市场) that reaches the
    # SameTurnResearchContinuation branch inside process_stream.
    return "请研究这个市场事件对行情的影响"


def test_real_research_final_branch_aligns_context_package(monkeypatch):
    import julia_core.runtime.research_continuation as rc

    from julia_core.runtime.research_continuation import (
        ResearchContinuationMaterial,
    )

    context_os = _FakeContextOS()
    context_os.initial_pkg = _package(FILE_A)
    session = _real_session(context_os, _FakeCapability(), monkeypatch)

    final_pkg = _package(MARKET_B)
    material = ResearchContinuationMaterial(
        messages=[{"role": "user", "content": "final"}],
        product=None,
        trace={"judgment_id": "j1"},
        context_package=final_pkg,
    )
    assert "[C-09" not in str(material.messages)
    _FakeSameTurnResearchContinuation.material = material
    monkeypatch.setattr(
        rc, "SameTurnResearchContinuation", _FakeSameTurnResearchContinuation
    )

    async def consume():
        async for _ in session.process_stream(
            _research_text(), [], conversation_id="c", turn_id="t"
        ):
            pass

    import asyncio
    asyncio.run(consume())

    assert len(session.provider.stream_calls) >= 1
    research_block = _c09_block(session.provider.stream_calls[0])
    assert "capability: market.event.read" in research_block
    assert "capability: file.read" not in research_block
    assert "[C-09" not in str(material.messages)


def test_real_research_failure_branch_no_model_call(monkeypatch):
    import julia_core.runtime.research_continuation as rc

    from julia_core.runtime.research_continuation import (
        ResearchContinuationMaterial,
    )

    context_os = _FakeContextOS()
    context_os.initial_pkg = _package(FILE_A)
    session = _real_session(context_os, _FakeCapability(), monkeypatch)

    _FakeSameTurnResearchContinuation.material = ResearchContinuationMaterial(
        messages=[],
        product=None,
        trace={},
        failure="research chain failed",
    )
    monkeypatch.setattr(
        rc, "SameTurnResearchContinuation", _FakeSameTurnResearchContinuation
    )

    async def consume():
        async for _ in session.process_stream(
            _research_text(), [], conversation_id="c", turn_id="t"
        ):
            pass

    import asyncio
    with pytest.raises(Exception) as excinfo:
        asyncio.run(consume())
    # Fail-closed: research failure stops cognition with the typed error.
    from julia_core.runtime.julia_session import ResearchTurnNotReady

    assert isinstance(excinfo.value, ResearchTurnNotReady)
    assert session.provider.stream_calls == []
    assert session.provider.chat_calls == []
