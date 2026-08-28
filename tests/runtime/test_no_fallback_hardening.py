"""PRE-P4 no-silent-fallback hardening tests.

Core-path failures must fail explicitly and observably — no empty/canned
synthetic success, no negative-success cache, no silent catch-and-pass, no
provider silent disappearance.
"""

from __future__ import annotations

import pytest

import julia_core.narrative.bootstrap as bootstrap_mod
from julia_core.capability.models import CapabilityStatus
from julia_core.runtime.capability_bridge import (
    RuntimeCapabilityBridge,
    _UnavailableAiThemeProvider,
)
from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime


# ── Bootstrap ───────────────────────────────────────────────────────────────

def test_load_bootstrap_has_no_synthetic_success(monkeypatch, tmp_path):
    """Missing files must not emit canned 'read completed / Julia success' text."""
    monkeypatch.setattr(bootstrap_mod, "MEMORY_DIR", tmp_path)
    result = bootstrap_mod.load_bootstrap()
    assert "读完了" not in result
    assert "你是Julia" not in result
    assert result == ""


def test_load_bootstrap_frames_not_ready_when_required_missing(monkeypatch, tmp_path):
    """Zero required critical inputs → explicit BootstrapNotReady, not success."""
    monkeypatch.setattr(bootstrap_mod, "MEMORY_DIR", tmp_path)
    with pytest.raises(bootstrap_mod.BootstrapNotReady):
        bootstrap_mod.load_bootstrap_frames()


def test_load_bootstrap_frames_succeeds_when_required_present():
    """Required identity/continuity inputs present → frames load successfully."""
    frames = bootstrap_mod.load_bootstrap_frames()
    assert "identity" in frames
    assert "experience" in frames
    assert "continuity" in frames


def test_get_bootstrap_frames_propagates_failure_not_empty_cache(monkeypatch):
    """Loader failure must propagate, not be cached as an empty success."""
    runtime = ContextExecutionRuntime()

    def _boom():
        raise RuntimeError("bootstrap boom")

    monkeypatch.setattr(bootstrap_mod, "load_bootstrap_frames", _boom)
    with pytest.raises(RuntimeError):
        runtime._get_bootstrap_frames()
    # Failed load must NOT be cached as a successful empty dict.
    assert not hasattr(runtime, "_bootstrap_frames_cache")


def test_get_bootstrap_frames_caches_success(monkeypatch):
    """A successful load is cached (single call), no repeated reload."""
    runtime = ContextExecutionRuntime()
    calls = {"n": 0}
    real = bootstrap_mod.load_bootstrap_frames

    def _counted():
        calls["n"] += 1
        return real()

    monkeypatch.setattr(bootstrap_mod, "load_bootstrap_frames", _counted)
    runtime._get_bootstrap_frames()
    runtime._get_bootstrap_frames()
    assert calls["n"] == 1


# ── Density experience ──────────────────────────────────────────────────────

def test_density_module_missing_is_explicit_not_silent():
    """A missing density module is an explicit error, not a silent empty string."""
    runtime = ContextExecutionRuntime()
    with pytest.raises(RuntimeError):
        runtime._load_density_experience()


def test_density_no_data_is_legitimate_empty(monkeypatch):
    """No density artifacts → legitimate empty state, distinguishable from error."""
    import sys
    import types

    fake = types.ModuleType("julia_core.context_assembly.density_restorer")
    fake.get_experience_context_block = lambda **kwargs: None
    monkeypatch.setitem(sys.modules, "julia_core.context_assembly.density_restorer", fake)

    runtime = ContextExecutionRuntime()
    assert runtime._load_density_experience() == ""


def test_density_load_error_propagates(monkeypatch):
    """Density loader error must propagate (explicit degradation), not be swallowed."""
    import sys
    import types

    def _boom(**kwargs):
        raise RuntimeError("density boom")

    fake = types.ModuleType("julia_core.context_assembly.density_restorer")
    fake.get_experience_context_block = _boom
    monkeypatch.setitem(sys.modules, "julia_core.context_assembly.density_restorer", fake)

    runtime = ContextExecutionRuntime()
    with pytest.raises(RuntimeError):
        runtime._load_density_experience()


# ── ai_theme provider registration ─────────────────────────────────────────

def test_ai_theme_init_success_registers_available():
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    for name in ("market.snapshot.read", "market.alert.query"):
        definition = bridge.registry.get(name)
        assert definition is not None
        assert definition.status == CapabilityStatus.AVAILABLE


def test_ai_theme_init_failure_degrades_not_disappears(monkeypatch):
    """Provider init failure → explicit DEGRADED + unavailable provider, no silent drop."""
    bridge = RuntimeCapabilityBridge()

    def _boom(*args, **kwargs):
        raise RuntimeError("init boom")

    monkeypatch.setattr(
        "julia_core.capability.providers.ai_theme.create_ai_theme_provider",
        _boom,
    )
    bridge.initialize()

    # Capability truth remains known, provider state is explicit DEGRADED.
    for name in ("market.snapshot.read", "market.alert.query"):
        definition = bridge.registry.get(name)
        assert definition is not None
        assert definition.status == CapabilityStatus.DEGRADED
    # Provider is an explicit unavailable provider, not a mock, not an alternate.
    provider = bridge._providers["ai_theme_app"]
    assert isinstance(provider, _UnavailableAiThemeProvider)


# ── Critical bootstrap failure blocks model execution ─────────────────────

class _CountingProvider:
    def __init__(self):
        self.chat_calls: list[list[dict]] = []

    def chat(self, messages, cognitive_mode=""):
        self.chat_calls.append(list(messages))
        return "reply"


def test_critical_bootstrap_failure_blocks_model(monkeypatch):
    """Critical identity/continuity bootstrap failure must NOT reach the model."""
    from julia_core.runtime.context_execution_runtime import ContextNotReady
    from julia_core.runtime.julia_session import JuliaSession, TurnContext

    session = JuliaSession.__new__(JuliaSession)
    session.provider = _CountingProvider()
    session.context_os = ContextExecutionRuntime()

    def _boom():
        raise RuntimeError("bootstrap boom")

    monkeypatch.setattr(bootstrap_mod, "load_bootstrap_frames", _boom)

    ctx = TurnContext([], conversation_id="conv", turn_id="turn")
    with pytest.raises(ContextNotReady):
        session._prepare_turn("hi", ctx)
    # No fallback, no empty-context continuation: provider was never called.
    assert len(session.provider.chat_calls) == 0
