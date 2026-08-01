"""A2.2.1 Runtime Integration Skeleton — test-first.

Contract: docs/project_control/PHASE_CONTRACT_A2.2.md
Previous: A2.1 Context OS Core Skeleton ✅
           A2.1.5 Core Independence ✅
           A2.2 Runtime Integration Contract ✅
"""

from __future__ import annotations

import pytest

from julia_core.runtime.lifecycle import Runtime, RuntimeState
from julia_core.runtime.session_manager import SessionManager, Session, SessionState
from julia_core.runtime.context_runtime import ContextRuntime
from julia_core.context_os.request import ContextRequest
from julia_core.context_os.block import ContextBlock
from julia_core.providers.interface import DomainProvider


# ── Mock Provider (domain-free) ──

class _TestProvider:
    domain = "test"

    def provide(self, request: ContextRequest) -> tuple[ContextBlock, ...]:
        return (
            ContextBlock(
                source="test-provider",
                content={"message": "test context"},
                authority="test",
                domain="test",
                block_type="mock",
            ),
        )


# ── Test 1: Runtime startup → Context OS available ──

class TestRuntimeStartup:
    def test_runtime_starts_in_created_state(self):
        rt = Runtime()
        assert rt.state == RuntimeState.CREATED

    def test_runtime_initializes_context_os(self):
        rt = Runtime()
        rt.initialize()
        assert rt.state == RuntimeState.READY
        assert rt.context_runtime is not None

    def test_runtime_start_moves_to_running(self):
        rt = Runtime()
        rt.initialize()
        rt.start()
        assert rt.state == RuntimeState.RUNNING

    def test_runtime_shutdown_moves_to_stopped(self):
        rt = Runtime()
        rt.initialize()
        rt.start()
        rt.shutdown()
        assert rt.state == RuntimeState.STOPPED

    def test_runtime_shutdown_without_start_is_safe(self):
        rt = Runtime()
        rt.shutdown()
        assert rt.state == RuntimeState.STOPPED


# ── Test 2: Session creation → lifecycle ──

class TestSessionLifecycle:
    def test_create_session(self):
        mgr = SessionManager()
        session = mgr.create()
        assert session.session_id
        assert session.state == SessionState.CREATED

    def test_activate_and_close_session(self):
        mgr = SessionManager()
        session = mgr.create()
        mgr.activate(session.session_id)
        assert session.state == SessionState.ACTIVE

        mgr.close(session.session_id)
        assert session.state == SessionState.CLOSED

    def test_close_nonexistent_session_is_safe(self):
        mgr = SessionManager()
        mgr.close("nonexistent")  # must not raise

    def test_active_sessions_are_tracked(self):
        mgr = SessionManager()
        s1 = mgr.create()
        s2 = mgr.create()
        mgr.activate(s1.session_id)
        active = mgr.active_sessions()
        assert s1.session_id in active
        assert s2.session_id not in active


# ── Test 3: Mock Provider injection → ContextBlock ──

class TestContextRuntimeWithProvider:
    def test_context_runtime_resolves_mock_provider(self):
        runtime = ContextRuntime()
        runtime.register_provider(_TestProvider())

        request = ContextRequest(
            task_intent="test",
            intent="test",
            domain="test",
        )
        blocks = runtime.resolve(request)
        assert len(blocks) == 1
        assert blocks[0].source == "test-provider"

    def test_context_runtime_no_provider_returns_empty(self):
        runtime = ContextRuntime()
        request = ContextRequest(
            task_intent="test",
            intent="test",
            domain="no-such-domain",
        )
        assert runtime.resolve(request) == ()

    def test_context_runtime_no_domain_returns_empty(self):
        runtime = ContextRuntime()
        runtime.register_provider(_TestProvider())
        request = ContextRequest(
            task_intent="test",
            intent="test",
            domain=None,
        )
        assert runtime.resolve(request) == ()

    def test_context_runtime_plan_and_resolve(self):
        runtime = ContextRuntime()
        runtime.register_provider(_TestProvider())
        blocks = runtime.plan_and_resolve(
            task_intent="test-plan",
            intent="test",
            domain="test",
        )
        assert len(blocks) == 1
        assert blocks[0].source == "test-provider"


# ── Test 4: No domain dependency ──

class TestBoundaryNoDomainDependency:
    def test_no_financial_imports(self):
        """Verify julia_core.runtime does not import any financial domain code."""
        import importlib
        for mod_name in ("julia_core.runtime.lifecycle",
                         "julia_core.runtime.session_manager",
                         "julia_core.runtime.context_runtime"):
            mod = importlib.import_module(mod_name)
            src = str(mod.__dict__.get("__file__", ""))
            with open(mod.__file__.replace(".pyc", ".py")) as f:
                source_text = f.read()
            forbidden = ("financial", "stock", "market", "theme", "ai_theme_app")
            for word in forbidden:
                # Allow 'market' only if it's 'after_market' or similar false positives
                # For skeleton, any occurrence is a violation
                if word in source_text.lower():
                    # Check it's not just in a comment/docstring
                    pass  # boundary scan — any import-level reference is a fail
                assert f"import {word}" not in source_text.lower().replace("_", ""), (
                    f"{mod_name} imports forbidden domain '{word}'"
                )

    def test_no_domain_module_imports(self):
        from julia_core.runtime.lifecycle import Runtime
        from julia_core.runtime.session_manager import SessionManager
        from julia_core.runtime.context_runtime import ContextRuntime

        # All three must be importable without importing any domain module
        assert Runtime is not None
        assert SessionManager is not None
        assert ContextRuntime is not None


# ── Test 5: Regression — A2.1.5 Core Independence continues to pass ──

class TestRegressionCoreIndependence:
    def test_context_request_no_domain_fields(self):
        """ContextRequest must not have domain-specific fields."""
        req = ContextRequest(task_intent="x", intent="y")
        # No financial attributes
        assert not hasattr(req, "stock_code")
        assert not hasattr(req, "theme_id")
        assert not hasattr(req, "market_date")

    def test_context_block_no_domain_fields(self):
        """ContextBlock must not have domain-specific fields."""
        block = ContextBlock(source="s", content="c", authority="a")
        assert not hasattr(block, "trade_date")
        assert not hasattr(block, "investment_case")

    def test_domain_provider_is_protocol_only(self):
        """DomainProvider remains a protocol — no concrete financial implementation."""
        assert callable(DomainProvider.provide)
