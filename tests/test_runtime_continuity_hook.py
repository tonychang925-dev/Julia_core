from __future__ import annotations

import ast
import inspect
import unittest
from dataclasses import dataclass

from julia_core.continuity.events import ContinuityEvent
from julia_core.runtime.continuity_hook import RuntimeContinuityHook


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


class RuntimeContinuityHookTests(unittest.TestCase):
    def test_runtime_calls_continuity_hook_and_gets_trace(self) -> None:
        hook = RuntimeContinuityHook(
            checkpoint_lookup=lambda agent_id: FakeCheckpoint()
            if agent_id == "julia"
            else None
        )

        inspection = hook.inspect(
            {
                "agent_id": "julia",
                "event": ContinuityEvent.SESSION_START,
                "runtime_state": {"state": "running"},
            }
        )
        trace = hook.create_trace(inspection)

        self.assertTrue(trace["continuity"]["checked"])
        self.assertTrue(trace["continuity"]["checkpoint_found"])
        self.assertEqual(trace["continuity"]["checkpoint_id"], "checkpoint://julia/latest")
        self.assertEqual(trace["continuity"]["decision_level"], "L3_IDENTITY")
        self.assertEqual(trace["runtime"]["event"], "SESSION_START")

    def test_checkpoint_missing_is_normal_for_first_session_start(self) -> None:
        hook = RuntimeContinuityHook(checkpoint_lookup=lambda _agent_id: None)

        inspection = hook.check_state(event=ContinuityEvent.SESSION_START)
        trace = hook.create_trace(inspection)

        self.assertTrue(trace["continuity"]["checked"])
        self.assertFalse(trace["continuity"]["checkpoint_found"])
        self.assertEqual(trace["continuity"]["decision_level"], "NONE")
        self.assertEqual(trace["continuity"]["recovery_status"], "NOT_REQUIRED")

    def test_continuity_hook_has_no_runtime_lifecycle_authority(self) -> None:
        hook = RuntimeContinuityHook()

        forbidden_lifecycle_controls = (
            "request_shutdown",
            "shutdown",
            "start",
            "stop",
            "restart",
            "initialize",
            "invoke_provider",
        )
        for name in forbidden_lifecycle_controls:
            self.assertFalse(hasattr(hook, name), name)

    def test_continuity_hook_has_no_downstream_dependency_imports(self) -> None:
        import julia_core.runtime.continuity_hook as continuity_hook_module

        source = inspect.getsource(continuity_hook_module)
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
                f"E1.8.1 hook must not import downstream module: {module}",
            )


if __name__ == "__main__":
    unittest.main()
