from __future__ import annotations

import ast
import inspect
import unittest
from dataclasses import dataclass

from julia_core.continuity.events import ContinuityEvent
from julia_core.runtime.continuity_hook import RuntimeContinuityHook
from julia_core.runtime.trace_pipeline import (
    AUTHORITY_CHAIN,
    ContinuityTracePipeline,
    RuntimeTraceContext,
    TRACE_VERSION,
)


@dataclass(frozen=True)
class FakeCheckpoint:
    checkpoint_id: str = "checkpoint://julia/latest"
    continuity_levels: dict[str, list[str]] | None = None

    def __post_init__(self) -> None:
        if self.continuity_levels is None:
            object.__setattr__(
                self,
                "continuity_levels",
                {
                    "L3_IDENTITY": ["persona://julia/v1"],
                    "L2_MEMORY": [],
                    "L1_SESSION": [],
                    "L0_EPHEMERAL": [],
                },
            )


class ContinuityTraceIntegrationTests(unittest.TestCase):
    def test_runtime_event_enters_trace(self) -> None:
        hook = RuntimeContinuityHook(checkpoint_lookup=lambda _agent_id: None)
        inspection = hook.check_state(event=ContinuityEvent.SESSION_START)

        trace = ContinuityTracePipeline().build_trace(
            runtime=RuntimeTraceContext(
                runtime_id="julia-runtime",
                session_id="session-123",
                event=ContinuityEvent.SESSION_START,
            ),
            continuity=inspection,
        ).to_dict()

        self.assertEqual(trace["trace_version"], TRACE_VERSION)
        self.assertEqual(trace["runtime"]["runtime_id"], "julia-runtime")
        self.assertEqual(trace["runtime"]["session_id"], "session-123")
        self.assertEqual(trace["runtime"]["event"], "SESSION_START")

    def test_continuity_result_enters_trace(self) -> None:
        hook = RuntimeContinuityHook(checkpoint_lookup=lambda _agent_id: FakeCheckpoint())
        inspection = hook.check_state(event=ContinuityEvent.SESSION_RESTART)

        trace = ContinuityTracePipeline().build_trace(
            runtime=RuntimeTraceContext(
                runtime_id="julia-runtime",
                session_id="session-456",
                event=ContinuityEvent.SESSION_RESTART,
            ),
            continuity=inspection,
        ).to_dict()

        self.assertTrue(trace["continuity"]["checked"])
        self.assertTrue(trace["continuity"]["checkpoint_found"])
        self.assertEqual(trace["continuity"]["checkpoint_id"], "checkpoint://julia/latest")
        self.assertEqual(trace["continuity"]["decision_level"], "L3_IDENTITY")
        self.assertEqual(trace["continuity"]["recovery_status"], "NOT_STARTED")

    def test_authority_chain_is_explicit_and_excludes_downstream_authorities(self) -> None:
        trace = ContinuityTracePipeline().build_trace(
            runtime=RuntimeTraceContext(
                runtime_id="julia-runtime",
                session_id="session-789",
                event=ContinuityEvent.PROVIDER_SWITCH,
            ),
            continuity={
                "checked": True,
                "checkpoint_found": True,
                "checkpoint_id": "checkpoint://julia/latest",
                "decision_level": "L3_IDENTITY",
                "recovery_status": "NOT_STARTED",
            },
        ).to_dict()

        self.assertEqual(trace["authority_chain"], list(AUTHORITY_CHAIN))
        self.assertIn("Runtime", trace["authority_chain"])
        self.assertIn("ContinuityHook", trace["authority_chain"])
        self.assertIn("ContinuityOS", trace["authority_chain"])
        for forbidden in ("Memory", "Context", "Provider", "LLM", "Alignment"):
            self.assertNotIn(forbidden, trace["authority_chain"])

    def test_trace_rejects_continuity_lifecycle_control_fields(self) -> None:
        trace = ContinuityTracePipeline().build_trace(
            runtime=RuntimeTraceContext(
                runtime_id="julia-runtime",
                session_id="session-negative",
                event=ContinuityEvent.RUNTIME_RECOVERY,
            ),
            continuity={
                "checked": True,
                "checkpoint_found": False,
                "decision_level": "NONE",
                "recovery_status": "NOT_REQUIRED",
                "shutdown": True,
                "request_shutdown": True,
                "provider_call": "forbidden",
            },
        ).to_dict()

        self.assertNotIn("shutdown", trace["continuity"])
        self.assertNotIn("request_shutdown", trace["continuity"])
        self.assertNotIn("provider_call", trace["continuity"])
        self.assertEqual(trace["continuity"]["recovery_status"], "NOT_REQUIRED")

    def test_trace_pipeline_has_no_downstream_dependency_imports(self) -> None:
        import julia_core.runtime.trace_pipeline as trace_pipeline_module

        source = inspect.getsource(trace_pipeline_module)
        tree = ast.parse(source)
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

        forbidden_prefixes = (
            "julia_core.memory",
            "julia_core.context_os",
            "julia_core.providers",
            "julia_core.alignment_os",
        )
        for module in imported_modules:
            self.assertFalse(
                module.startswith(forbidden_prefixes),
                f"E1.8.2 trace pipeline must not import downstream module: {module}",
            )


if __name__ == "__main__":
    unittest.main()
