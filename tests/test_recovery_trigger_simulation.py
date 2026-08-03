from __future__ import annotations

import ast
import inspect
import unittest

from julia_core.continuity.events import ContinuityEvent
from julia_core.continuity.trigger import RecoveryTrigger, RecoveryTriggerInput
from julia_core.runtime.trace_pipeline import ContinuityTracePipeline, RuntimeTraceContext


class RecoveryTriggerSimulationTests(unittest.TestCase):
    def test_session_start_without_checkpoint_is_not_required(self) -> None:
        decision = RecoveryTrigger().evaluate(
            RecoveryTriggerInput(
                event=ContinuityEvent.SESSION_START,
                checkpoint_available=False,
            )
        )
        trace = ContinuityTracePipeline().build_trace(
            runtime=RuntimeTraceContext(
                runtime_id="julia-runtime",
                session_id="session-first",
                event=ContinuityEvent.SESSION_START,
            ),
            continuity={
                "checked": True,
                "checkpoint_found": False,
                "decision_level": "NONE",
                "recovery_status": decision.recovery_status,
            },
        ).to_dict()

        self.assertFalse(decision.recovery_required)
        self.assertEqual(decision.reason, "first_session_no_checkpoint")
        self.assertEqual(decision.recovery_status, "NOT_REQUIRED")
        self.assertEqual(trace["continuity"]["recovery_status"], "NOT_REQUIRED")

    def test_runtime_recovery_with_checkpoint_requires_recovery(self) -> None:
        decision = RecoveryTrigger().evaluate(
            RecoveryTriggerInput(
                event=ContinuityEvent.RUNTIME_RECOVERY,
                checkpoint_available=True,
            )
        )
        intent_trace = decision.to_trace()

        self.assertTrue(decision.recovery_required)
        self.assertEqual(decision.reason, "checkpoint_available")
        self.assertEqual(decision.recovery_status, "RECOVERY_REQUIRED")
        self.assertTrue(intent_trace["recovery_required"])

    def test_provider_switch_does_not_change_continuity_state(self) -> None:
        decision = RecoveryTrigger().evaluate(
            RecoveryTriggerInput(
                event=ContinuityEvent.PROVIDER_SWITCH,
                checkpoint_available=True,
                provider_changed=True,
                previous_provider="deepseek",
                current_provider="gpt",
            )
        )

        self.assertTrue(decision.provider_changed)
        self.assertTrue(decision.recovery_required)
        self.assertFalse(decision.continuity_state_changed)
        self.assertEqual(decision.reason, "provider_switch_continuity_state_unchanged")

    def test_recovery_trigger_does_not_execute_downstream_recovery(self) -> None:
        trigger = RecoveryTrigger()
        forbidden_methods = (
            "load_memory",
            "resolve_memory",
            "rebuild_context",
            "switch_provider",
            "call_provider",
            "shutdown",
            "restart_runtime",
        )
        for name in forbidden_methods:
            self.assertFalse(hasattr(trigger, name), name)

    def test_recovery_trigger_has_no_downstream_dependency_imports(self) -> None:
        import julia_core.continuity.trigger as trigger_module

        source = inspect.getsource(trigger_module)
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
                f"E1.8.3 trigger must not import downstream module: {module}",
            )


if __name__ == "__main__":
    unittest.main()
