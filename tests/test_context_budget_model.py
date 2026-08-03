import ast
from pathlib import Path
import unittest

from julia_core.context_os.budget_model import ContextBudget, ContextBudgetAllocator
from julia_core.context_os.priority_model import ContextCandidate, CurrentIntent


class ContextBudgetModelTests(unittest.TestCase):
    def setUp(self):
        self.allocator = ContextBudgetAllocator()

    def selected_refs(self, result):
        return [item.ref for item in result.selected]

    def dropped_refs(self, result):
        return [item.ref for item in result.dropped]

    def test_identity_protection_under_budget_pressure(self):
        result = self.allocator.allocate(
            [
                ContextCandidate(ref="memory://event/julia-core-origin", continuity_level="L3_IDENTITY", semantic_type="identity_origin", semantic_relevance=1.0, task_relevance=1.0, estimated_tokens=500),
                ContextCandidate(ref="memory://project/context-os", continuity_level="L2_MEMORY", semantic_type="project", semantic_relevance=0.8, task_relevance=0.8, estimated_tokens=700),
                ContextCandidate(ref="session://working-state", continuity_level="L1_SESSION", semantic_type="session", semantic_relevance=0.6, estimated_tokens=700),
                ContextCandidate(ref="chat://smalltalk", continuity_level="L0_EPHEMERAL", semantic_type="general", semantic_relevance=0.2, estimated_tokens=700),
            ],
            CurrentIntent(intent="why_julia_core", semantic_targets=("identity_origin", "project"), task_domain="julia_core"),
            ContextBudget(total_budget=2000, identity_budget=600, project_budget=800, conversation_budget=400, task_budget=200),
        )
        self.assertIn("memory://event/julia-core-origin", self.selected_refs(result))
        self.assertIn("chat://smalltalk", self.dropped_refs(result))
        self.assertLessEqual(result.used_tokens, 2000)

    def test_task_dominance_for_context_os_design(self):
        result = self.allocator.allocate(
            [
                ContextCandidate(ref="memory://project/context-os-architecture", continuity_level="L2_MEMORY", semantic_type="project", task_relevance=1.0, semantic_relevance=0.9, estimated_tokens=500, metadata={"task_domain": "context_os"}),
                ContextCandidate(ref="memory://relationship/tony-style", continuity_level="L2_MEMORY", semantic_type="relationship", relationship_weight=0.8, semantic_relevance=0.4, estimated_tokens=300),
                ContextCandidate(ref="memory://general/history", continuity_level="L1_SESSION", semantic_type="general", semantic_relevance=0.1, estimated_tokens=300),
            ],
            CurrentIntent(intent="design_context_os", semantic_targets=("project",), relationship_sensitive=True, task_domain="context_os"),
            ContextBudget(total_budget=1000, project_budget=600, relationship_budget=300, general_budget=100),
        )
        self.assertEqual(self.selected_refs(result)[0], "memory://project/context-os-architecture")
        self.assertIn("memory://relationship/tony-style", self.selected_refs(result))

    def test_compact_pressure_preserves_identity_and_drops_low_value_context(self):
        result = self.allocator.allocate(
            [
                ContextCandidate(ref="memory://event/julia-core-origin", continuity_level="L3_IDENTITY", semantic_type="identity_origin", semantic_relevance=1.0, task_relevance=1.0, estimated_tokens=1200),
                ContextCandidate(ref="memory://relationship/tony-julia", continuity_level="L2_MEMORY", semantic_type="relationship", relationship_weight=1.0, semantic_relevance=0.7, estimated_tokens=1000),
                ContextCandidate(ref="memory://project/e2-roadmap", continuity_level="L2_MEMORY", semantic_type="project", task_relevance=0.8, semantic_relevance=0.8, estimated_tokens=1500),
                ContextCandidate(ref="session://long-transcript-tail", continuity_level="L1_SESSION", semantic_type="session", semantic_relevance=0.4, estimated_tokens=6000),
                ContextCandidate(ref="chat://noise", continuity_level="L0_EPHEMERAL", semantic_type="general", semantic_relevance=0.1, estimated_tokens=90000),
            ],
            CurrentIntent(intent="compact_recovery", semantic_targets=("identity_origin", "relationship", "project"), relationship_sensitive=True, task_domain="julia_core"),
            ContextBudget(total_budget=10000, identity_budget=2000, relationship_budget=1500, project_budget=3000, conversation_budget=1000, task_budget=2500),
        )
        refs = self.selected_refs(result)
        self.assertIn("memory://event/julia-core-origin", refs)
        self.assertIn("memory://relationship/tony-julia", refs)
        self.assertIn("memory://project/e2-roadmap", refs)
        self.assertIn("chat://noise", self.dropped_refs(result))
        self.assertLessEqual(result.used_tokens, 10000)

    def test_budget_allocator_has_no_external_authority_dependencies(self):
        source = Path("julia_core/context_os/budget_model.py").read_text()
        tree = ast.parse(source)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
        forbidden_imports = ("memory", "persona", "provider", "alignment", "continuity")
        for module in imported:
            self.assertFalse(any(token in module for token in forbidden_imports), module)
        calls = [getattr(node.func, "attr", getattr(node.func, "id", "")) for node in ast.walk(tree) if isinstance(node, ast.Call)]
        for token in ("chat", "provide", "create_checkpoint", "load_memory", "summarize"):
            self.assertNotIn(token, calls)

    def test_total_budget_must_be_positive(self):
        with self.assertRaises(ValueError):
            ContextBudget(total_budget=0)


if __name__ == "__main__":
    unittest.main()
