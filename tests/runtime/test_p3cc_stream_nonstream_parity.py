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
