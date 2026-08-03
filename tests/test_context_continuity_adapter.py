from __future__ import annotations

import ast
import inspect
import unittest

from julia_core.continuity import ContinuityDecision, ContinuityLevel, TTLPolicy, create_checkpoint, create_recovery_plan
from julia_core.context_os.block import ContextBlock
from julia_core.context_os.continuity_adapter import ContextContinuityAdapter, ContextContinuityRequest


class ContextContinuityAdapterTests(unittest.TestCase):
    def _checkpoint_and_plan(self):
        decision = ContinuityDecision(
            decision_id="d-context",
            request_id="r-context",
            level=ContinuityLevel.L3_IDENTITY,
            preserve=True,
            checkpoint_required=True,
            reason="identity",
            protected_refs=["memory://event/julia-core-origin"],
            ttl_policy=TTLPolicy.PROTECT,
        )
        checkpoint = create_checkpoint(
            agent_id="julia",
            identity_refs=["persona://julia/v1"],
            relationship_refs=["memory://relationship/tony-julia"],
            active_project_refs=["project://julia-core"],
            decisions=[decision],
        )
        return checkpoint, create_recovery_plan(checkpoint, recovery_reason="compact")

    def test_identity_recovery_requires_identity_context(self) -> None:
        checkpoint, plan = self._checkpoint_and_plan()
        result = ContextContinuityAdapter().build_requirements(
            ContextContinuityRequest(
                checkpoint_id=checkpoint.checkpoint_id,
                required_continuity_level="L3_IDENTITY",
                recovery_plan=plan,
            )
        )
        requirement_types = [req.required_type for req in result.context_requirements]

        self.assertIn("identity_anchor", requirement_types)
        self.assertIn("protected_memory_refs", requirement_types)
        self.assertIn("relationship_state", requirement_types)
        self.assertEqual(result.checkpoint_id, checkpoint.checkpoint_id)

    def test_context_adapter_does_not_modify_continuity_checkpoint(self) -> None:
        checkpoint, plan = self._checkpoint_and_plan()
        before = checkpoint.to_dict()
        ContextContinuityAdapter().build_requirements(
            ContextContinuityRequest(
                checkpoint_id=checkpoint.checkpoint_id,
                required_continuity_level="L3_IDENTITY",
                recovery_plan=plan,
            )
        )
        self.assertEqual(before, checkpoint.to_dict())
        adapter = ContextContinuityAdapter()
        for forbidden in ("update_checkpoint", "create_checkpoint", "promote_identity", "write_continuity"):
            self.assertFalse(hasattr(adapter, forbidden), forbidden)

    def test_context_block_is_not_memory_ref_generator(self) -> None:
        block = ContextBlock(
            source="continuity_reconstruction",
            content={"requirement": "identity_anchor", "refs": ["persona://julia/v1"]},
            authority="ContextOS",
            block_type="identity",
            block_kind="reconstructed_context",
            evidence_refs=("persona://julia/v1",),
        )

        self.assertFalse(hasattr(block, "memory_ref"))
        self.assertFalse(hasattr(block, "to_memory_ref"))
        self.assertEqual(block.block_kind, "reconstructed_context")

    def test_adapter_exposes_no_provider_or_retrieval_api(self) -> None:
        adapter = ContextContinuityAdapter()
        for forbidden in (
            "call_provider",
            "invoke_provider",
            "generate",
            "restore_prompt",
            "load_memory",
            "query_memory",
            "reconstruct",
        ):
            self.assertFalse(hasattr(adapter, forbidden), forbidden)

    def test_adapter_has_no_memory_provider_alignment_runtime_imports(self) -> None:
        import julia_core.context_os.continuity_adapter as adapter_module

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
            "julia_core.providers",
            "julia_core.alignment_os",
            "julia_core.runtime",
        )
        for module in imported_modules:
            self.assertFalse(
                module.startswith(forbidden_prefixes),
                f"E1.8.5 adapter must not import downstream authority: {module}",
            )


if __name__ == "__main__":
    unittest.main()
