from __future__ import annotations

import ast
import inspect
import unittest

from julia_core.continuity import ContinuityLevel, MemoryImportance, create_checkpoint
from julia_core.continuity.contracts import ContinuityDecision, TTLPolicy
from julia_core.continuity.memory_governance_adapter import MemoryGovernanceAdapter


class MemoryGovernanceAdapterTests(unittest.TestCase):
    def test_identity_memory_becomes_l3_checkpoint_eligible(self) -> None:
        decision = MemoryGovernanceAdapter().evaluate(
            {
                "agent_id": "julia",
                "memory_ref": "memory://event/julia-core-origin",
                "type": "project",
                "importance": "critical",
                "signals": {
                    "identity_related": True,
                    "relationship_related": True,
                    "project_related": True,
                    "provider_independent": True,
                },
                "metadata": {"label": "Tony and Julia Core continuity goal"},
            }
        )

        self.assertEqual(decision.continuity_level, ContinuityLevel.L3_IDENTITY)
        self.assertTrue(decision.checkpoint_eligible)
        self.assertEqual(decision.protected_ref, "memory://event/julia-core-origin")

    def test_ordinary_lunch_event_stays_non_identity(self) -> None:
        decision = MemoryGovernanceAdapter().evaluate(
            {
                "agent_id": "julia",
                "memory_ref": "memory://event/today-lunch",
                "type": "episodic",
                "importance": "low",
                "signals": {"provider_independent": False},
            }
        )

        self.assertIn(decision.continuity_level, (ContinuityLevel.L0_EPHEMERAL, ContinuityLevel.L1_SESSION))
        self.assertFalse(decision.checkpoint_eligible)
        self.assertIsNone(decision.protected_ref)

    def test_memory_adapter_does_not_upgrade_memory_os_authority(self) -> None:
        adapter = MemoryGovernanceAdapter()
        forbidden_authority_methods = (
            "set_identity",
            "write_memory",
            "save_memory",
            "query_memory",
            "load_memory",
            "embed_memory",
            "inject_context",
            "build_prompt",
        )
        for name in forbidden_authority_methods:
            self.assertFalse(hasattr(adapter, name), name)

    def test_checkpoint_remains_refs_only_after_governance(self) -> None:
        decision = MemoryGovernanceAdapter().evaluate(
            {
                "agent_id": "julia",
                "memory_ref": "memory://event/julia-core-origin",
                "type": "project",
                "importance": MemoryImportance.CRITICAL,
                "signals": {
                    "identity_related": True,
                    "relationship_related": True,
                    "project_related": True,
                    "provider_independent": True,
                },
                "metadata": {"content": "Tony and Julia Core continuity goal"},
            }
        )
        continuity_decision = ContinuityDecision(
            decision_id="memory-governance-decision",
            request_id="memory-governance-request",
            level=decision.continuity_level,
            preserve=decision.checkpoint_eligible,
            checkpoint_required=decision.checkpoint_eligible,
            reason=decision.reason,
            protected_refs=[decision.protected_ref] if decision.protected_ref else [],
            ttl_policy=TTLPolicy.PROTECT if decision.checkpoint_eligible else TTLPolicy.DISCARD,
        )
        checkpoint = create_checkpoint(
            agent_id="julia",
            identity_refs=["persona://julia/v1"],
            decisions=[continuity_decision],
        )

        checkpoint_dict = checkpoint.to_dict()
        self.assertEqual(checkpoint_dict["protected_memory_refs"], ["memory://event/julia-core-origin"])
        self.assertNotIn("Tony and Julia Core continuity goal", str(checkpoint_dict))
        self.assertNotIn("content", str(checkpoint_dict))

    def test_adapter_has_no_downstream_runtime_context_provider_imports(self) -> None:
        import julia_core.continuity.memory_governance_adapter as adapter_module

        source = inspect.getsource(adapter_module)
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
            "julia_core.runtime",
        )
        for module in imported_modules:
            self.assertFalse(
                module.startswith(forbidden_prefixes),
                f"E1.8.4 adapter must not import downstream authority: {module}",
            )


if __name__ == "__main__":
    unittest.main()
