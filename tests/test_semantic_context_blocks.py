from __future__ import annotations

import ast
import inspect
import unittest

from julia_core.context_os.semantic_blocks import GovernedMemoryRef, SemanticContextBuilder


class SemanticContextBlockTests(unittest.TestCase):
    def test_identity_origin_semantic_block_from_governed_ref(self) -> None:
        block = SemanticContextBuilder().build(
            GovernedMemoryRef(
                memory_ref="memory://event/julia-core-origin",
                continuity_level="L3_IDENTITY",
                checkpoint_eligible=True,
            )
        )
        self.assertEqual(block.block_kind, "semantic_context")
        self.assertEqual(block.block_type, "identity_origin")
        self.assertEqual(block.authority, "ContextOS")
        self.assertEqual(block.evidence_refs, ("memory://event/julia-core-origin",))
        self.assertIn("agent identity continuity", block.content["meaning"])

    def test_refs_only_boundary(self) -> None:
        with self.assertRaises(ValueError):
            GovernedMemoryRef("raw memory content", "L3_IDENTITY", True)

    def test_builder_has_no_forbidden_authority_imports(self) -> None:
        import julia_core.context_os.semantic_blocks as module

        source = inspect.getsource(module)
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        for forbidden in ("julia_core.memory", "julia_core.providers", "julia_core.alignment_os", "julia_core.runtime"):
            self.assertFalse(any(item.startswith(forbidden) for item in imports), forbidden)

    def test_builder_exposes_no_memory_or_continuity_mutation_api(self) -> None:
        builder = SemanticContextBuilder()
        for forbidden in ("load_memory", "write_memory", "create_checkpoint", "decide_continuity_level", "call_provider"):
            self.assertFalse(hasattr(builder, forbidden), forbidden)


if __name__ == "__main__":
    unittest.main()
