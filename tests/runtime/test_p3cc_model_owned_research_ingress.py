"""P3-CC I2-A — model-owned Research semantic ingress tests.

Proves the constitutional authority transfer:

    Julia cognition (model output) selects research.run_brief;
    user-text keywords are NOT authority.

Pairs:
- keywords present + model NO capability  → no Research composite execution;
- keywords ABSENT  + model research.run_brief → Research composite executes.

Also static zero-caller gates for the retired Runtime semantic routers.
"""

from __future__ import annotations

import ast
import json as _json
from pathlib import Path

import pytest

from julia_core.runtime.context_execution_runtime import CognitiveContextPackage
from julia_core.runtime.julia_session import ResearchTurnNotReady, JuliaSession

ROOT = Path(__file__).resolve().parents[2]


class _NoopEventStore:
    def append(self, event):
        pass


class _FakeRecorder:
    def record(self, *a, **k):
        pass

    def consolidate(self, *a, **k):
        pass


class _FakeAction:
    def start(self, *a, **k):
        pass

    def finish(self, *a, **k):
        pass


class _FakePersona:
    traits = {}
    identity = {}


class _ProviderSpy:
    def __init__(self):
        self.chat_calls = []
        self.stream_calls = []

    def chat(self, messages, cognitive_mode=""):
        self.chat_calls.append(list(messages))
        return "ok"

    async def stream_async(self, messages):
        self.stream_calls.append(list(messages))
        yield "ok"


class _FakeCapability:
    def __init__(self):
        self.tool_call = None

    def requires_tool(self, text):
        return False  # I2-A: never consulted as authority

    def detect_tool_call(self, reply):
        return self.tool_call


class _FakeContextOS:
    def __init__(self):
        self.initial_pkg = None

    def prepare(self, **kwargs):
        return self.initial_pkg


class _RecorderSameTurn:
    """Records whether the governed composite ingress was reached."""

    calls = []

    def __init__(self, *args, **kwargs):
        pass

    async def run(self, **kwargs):
        _RecorderSameTurn.calls.append(kwargs)
        from julia_core.runtime.research_continuation import (
            ResearchContinuationMaterial,
        )

        pkg = CognitiveContextPackage()
        pkg.capability_frame = {
            "manifest_entries": [],
            "non_admitted_diagnostics": [],
        }
        return ResearchContinuationMaterial(
            messages=[{"role": "assistant", "content": "research done"}],
            product=None,
            trace={"judgment_id": "j"},
            context_package=pkg,
        )


class _RealSession(JuliaSession):
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


def _package(*entries):
    pkg = CognitiveContextPackage()
    pkg.capability_frame = {
        "manifest_entries": [dict(e) for e in entries],
        "non_admitted_diagnostics": [],
    }
    return pkg


_ENTRY = {
    "capability_id": "file.read",
    "description": "read file",
    "input_schema": {},
    "output_schema": {},
    "side_effect_class": "read_only",
    "permission_requirements": ["file.read"],
    "idempotency_support": "none",
    "latency_cost_hints": {},
    "data_sensitivity": "local_user_files",
    "availability": "available",
    "schema_version": "1.0",
    "provenance": {"source": "capability:registry",
                   "definition_ref": "file.read",
                   "derived_at": "2026-09-09T00:00:00Z"},
}


def _session(capability, monkeypatch):
    monkeypatch.setattr(
        "julia_core.events.store.get_event_store", lambda: _NoopEventStore()
    )
    context_os = _FakeContextOS()
    context_os.initial_pkg = _package(_ENTRY)
    return _RealSession(context_os, capability)


def _run_stream(session, text):
    import asyncio

    async def consume():
        async for _ in session.process_stream(
            text, [], conversation_id="c", turn_id="t"
        ):
            pass

    asyncio.run(consume())


# ── Case B / mandatory pair (negative): keywords present, model silent ─────

def test_keywords_present_model_no_capability_no_research(monkeypatch):
    capability = _FakeCapability()
    capability.tool_call = None  # model emits no capability request
    session = _session(capability, monkeypatch)
    _RecorderSameTurn.calls = []

    import julia_core.runtime.research_continuation as rc
    monkeypatch.setattr(
        rc, "SameTurnResearchContinuation", _RecorderSameTurn
    )

    _run_stream(session, "我们聊聊市场研究这个概念")

    assert _RecorderSameTurn.calls == []  # composite never entered
    assert len(session.provider.stream_calls) == 1  # ordinary answer only


def test_negated_research_wording_model_silent_no_research(monkeypatch):
    capability = _FakeCapability()
    capability.tool_call = None
    session = _session(capability, monkeypatch)
    _RecorderSameTurn.calls = []

    import julia_core.runtime.research_continuation as rc
    monkeypatch.setattr(
        rc, "SameTurnResearchContinuation", _RecorderSameTurn
    )

    _run_stream(session, "不要研究市场")

    # No negation parser exists in Runtime anymore; the model's silence is
    # the only signal, and it means NO research execution.
    assert _RecorderSameTurn.calls == []
    assert len(session.provider.stream_calls) == 1


# ── Case A / mandatory pair (positive): keywords absent, model selects ─────

def test_neutral_text_model_selects_research_run_brief(monkeypatch):
    capability = _FakeCapability()
    capability.tool_call = _json.dumps({
        "name": "research.run_brief",
        "arguments": {"query": "帮我把这件事搞清楚"},
    })
    session = _session(capability, monkeypatch)
    _RecorderSameTurn.calls = []

    import julia_core.runtime.research_continuation as rc
    monkeypatch.setattr(
        rc, "SameTurnResearchContinuation", _RecorderSameTurn
    )

    # Deliberately neutral user text with NONE of the old research keywords.
    _run_stream(session, "帮我把这件事搞清楚")

    assert len(_RecorderSameTurn.calls) == 1
    request_kwargs = _RecorderSameTurn.calls[0]
    assert "governed_research_request" in request_kwargs
    assert request_kwargs["governed_research_request"].find(
        "research.run_brief"
    ) != -1


def test_malformed_research_request_fails_closed_before_subcalls(monkeypatch):
    """Case D: malformed high-level request must not reach internal resolve."""
    from julia_core.runtime.research_continuation import (
        SameTurnResearchContinuation,
    )

    capability = _FakeCapability()
    capability.tool_call = _json.dumps({"name": "not.research", "arguments": {}})
    session = _session(capability, monkeypatch)

    with pytest.raises(Exception):
        _run_stream(session, "随便聊聊")
    # No SameTurn ingress (name mismatch caught during conversion before any
    # internal execution) — the typed ValueError propagates and nothing runs.
    assert len(session.provider.stream_calls) == 1  # initial pass only


# ── static zero-caller gates ────────────────────────────────────────────────

def test_static_zero_caller_research_text_router():
    source = (
        ROOT / "julia_core" / "runtime" / "julia_session.py"
    ).read_text()
    tree = ast.parse(source)
    session_class = next(
        n for n in tree.body
        if isinstance(n, ast.ClassDef) and n.name == "JuliaSession"
    )
    method_names = {
        m.name for m in session_class.body
        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "_build_research_desk_resolver_call" not in method_names
    assert "_research_intent_is_negated_only" not in method_names
    assert "requires_tool" not in method_names


def test_static_no_user_text_semantic_gate_in_session():
    source = (
        ROOT / "julia_core" / "runtime" / "julia_session.py"
    ).read_text()
    assert "requires_tool(text)" not in source
    assert "_build_research_desk_resolver_call(text)" not in source


# ── I2-A-R1: high-level authorization precedes internal sub-calls ──────────

def test_high_level_denied_blocks_internal_resolve(monkeypatch):
    """R1: a denied research.run_brief high-level request must fail closed
    BEFORE any internal market.event.resolve/read/enrich sub-call executes."""
    from types import SimpleNamespace

    from julia_core.capability.models import CapabilityStatus, SideEffectClass
    from julia_core.runtime.research_continuation import (
        ResearchHighLevelDenied,
        SameTurnResearchContinuation,
    )

    sub_execute_calls = []

    class _DenyPolicy:
        def check(self, scope):
            return SimpleNamespace(decision="DENY")

    class _DenyCapability:
        registry = None
        policy = _DenyPolicy()

        async def execute_capability_request_async(self, *a, **k):
            sub_execute_calls.append(a)

    definition = SimpleNamespace(
        name="research.run_brief",
        permission_scope="research.run_brief",
        status=CapabilityStatus.AVAILABLE,
        side_effect_class=SideEffectClass.READ_ONLY,
    )

    class _Registry:
        def get(self, name):
            if name == "research.run_brief":
                return definition
            return None

    capability = _DenyCapability()
    capability.registry = _Registry()

    session = SimpleNamespace(capability=capability)
    continuation = SameTurnResearchContinuation(session)

    turn_context = SimpleNamespace(
        conversation_id="c", turn_id="t", turn_count=1,
        correlation_id="corr",
    )

    import asyncio

    with pytest.raises(ResearchHighLevelDenied):
        asyncio.run(continuation.run(
            governed_research_request=_json.dumps({
                "name": "research.run_brief",
                "arguments": {"query": "查证某事"},
            }),
            turn_context=turn_context,
            parent_package=CognitiveContextPackage(),
            research_product_hook=None,
            product_sink=None,
        ))

    # Denied high-level request → ZERO internal sub-capability execution.
    assert sub_execute_calls == []


def test_high_level_missing_definition_blocks_internal_resolve():
    from types import SimpleNamespace

    from julia_core.runtime.research_continuation import (
        ResearchHighLevelDenied,
        SameTurnResearchContinuation,
    )

    class _EmptyRegistry:
        def get(self, name):
            return None

    class _EmptyCapability:
        registry = _EmptyRegistry()
        policy = None

    session = SimpleNamespace(capability=_EmptyCapability())
    continuation = SameTurnResearchContinuation(session)

    import asyncio

    with pytest.raises(ResearchHighLevelDenied):
        asyncio.run(continuation.run(
            governed_research_request=_json.dumps({
                "name": "research.run_brief",
                "arguments": {"query": "x"},
            }),
            turn_context=SimpleNamespace(
                conversation_id="c", turn_id="t", turn_count=1,
                correlation_id="corr",
            ),
            parent_package=CognitiveContextPackage(),
            research_product_hook=None,
            product_sink=None,
        ))
