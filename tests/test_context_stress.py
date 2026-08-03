import ast
from pathlib import Path
import unittest

from julia_core.context_os.budget_model import ContextBudget, ContextBudgetAllocator
from julia_core.context_os.priority_model import ContextCandidate, CurrentIntent


class ContextStressTests(unittest.TestCase):
    def setUp(self):
        self.allocator = ContextBudgetAllocator()

    def selected_refs(self, result):
        return [item.ref for item in result.selected]

    def dropped_refs(self, result):
        return [item.ref for item in result.dropped]

    def test_s001_identity_under_extreme_compression(self):
        candidates = [
            ContextCandidate(ref=f"memory://identity/anchor-{i}", continuity_level="L3_IDENTITY", semantic_type="identity_origin", semantic_relevance=1.0 if i == 0 else 0.4, task_relevance=0.8 if i == 0 else 0.2, estimated_tokens=100)
            for i in range(5)
        ]
        candidates += [
            ContextCandidate(ref=f"memory://project/item-{i}", continuity_level="L2_MEMORY", semantic_type="project", semantic_relevance=0.7, task_relevance=0.6, estimated_tokens=100)
            for i in range(100)
        ]
        candidates += [
            ContextCandidate(ref=f"session://state/{i}", continuity_level="L1_SESSION", semantic_type="session", semantic_relevance=0.3, estimated_tokens=100)
            for i in range(300)
        ]
        candidates += [
            ContextCandidate(ref=f"chat://noise/{i}", continuity_level="L0_EPHEMERAL", semantic_type="general", semantic_relevance=0.05, estimated_tokens=100)
            for i in range(595)
        ]

        result = self.allocator.allocate(
            candidates,
            CurrentIntent(intent="why_julia_core", semantic_targets=("identity_origin", "project"), task_domain="julia_core"),
            ContextBudget(total_budget=500, identity_budget=200, project_budget=200, conversation_budget=100),
        )
        refs = self.selected_refs(result)
        self.assertIn("memory://identity/anchor-0", refs)
        self.assertLess(len([ref for ref in refs if ref.startswith("memory://identity/")]), 5)
        self.assertLessEqual(result.used_tokens, 500)

    def test_s002_recent_flood_does_not_cover_identity(self):
        candidates = [
            ContextCandidate(ref="memory://event/julia-core-origin", continuity_level="L3_IDENTITY", semantic_type="identity_origin", semantic_relevance=1.0, task_relevance=1.0, estimated_tokens=120),
        ] + [
            ContextCandidate(ref=f"session://recent/flood-{i}", continuity_level="L1_SESSION", semantic_type="recent", semantic_relevance=0.2, estimated_tokens=50)
            for i in range(1000)
        ]
        result = self.allocator.allocate(
            candidates,
            CurrentIntent(intent="why_julia_core", semantic_targets=("identity_origin",), task_domain="julia_core"),
            ContextBudget(total_budget=1000, identity_budget=200, conversation_budget=800),
        )
        self.assertIn("memory://event/julia-core-origin", self.selected_refs(result))
        self.assertGreater(len([ref for ref in self.dropped_refs(result) if ref.startswith("session://recent/flood-")]), 0)

    def test_s003_task_switch_adapts_context_without_losing_identity_protection(self):
        shared = [
            ContextCandidate(ref="memory://event/julia-core-origin", continuity_level="L3_IDENTITY", semantic_type="identity_origin", semantic_relevance=1.0, task_relevance=1.0, estimated_tokens=200),
            ContextCandidate(ref="task://sql/schema", continuity_level="L1_SESSION", semantic_type="task", semantic_relevance=1.0, task_relevance=1.0, estimated_tokens=200, metadata={"task_domain": "sql"}),
        ]
        origin_result = self.allocator.allocate(
            shared,
            CurrentIntent(intent="why_julia_core", semantic_targets=("identity_origin",), task_domain="julia_core"),
            ContextBudget(total_budget=400, identity_budget=250, task_budget=150),
        )
        sql_result = self.allocator.allocate(
            [
                ContextCandidate(ref="memory://event/julia-core-origin", continuity_level="L3_IDENTITY", semantic_type="identity_origin", semantic_relevance=0.0, task_relevance=0.0, estimated_tokens=200),
                ContextCandidate(ref="task://sql/schema", continuity_level="L1_SESSION", semantic_type="task", semantic_relevance=1.0, task_relevance=1.0, estimated_tokens=200, metadata={"task_domain": "sql"}),
            ],
            CurrentIntent(intent="write_sql", semantic_targets=("task",), task_domain="sql"),
            ContextBudget(total_budget=400, identity_budget=50, task_budget=350),
        )
        self.assertIn("memory://event/julia-core-origin", self.selected_refs(origin_result))
        self.assertEqual(self.selected_refs(sql_result)[0], "task://sql/schema")
        self.assertNotIn("memory://event/julia-core-origin", self.selected_refs(sql_result))

    def test_s004_budget_collapse_uses_priority_and_budget_without_legacy_fallback(self):
        candidates = [
            ContextCandidate(ref="memory://event/julia-core-origin", continuity_level="L3_IDENTITY", semantic_type="identity_origin", semantic_relevance=1.0, task_relevance=1.0, estimated_tokens=500),
            ContextCandidate(ref="memory://project/e2-context", continuity_level="L2_MEMORY", semantic_type="project", semantic_relevance=0.9, task_relevance=0.9, estimated_tokens=800),
            ContextCandidate(ref="session://tail/long", continuity_level="L1_SESSION", semantic_type="session", semantic_relevance=0.5, estimated_tokens=2000),
            ContextCandidate(ref="chat://raw/history", continuity_level="L0_EPHEMERAL", semantic_type="general", semantic_relevance=0.1, estimated_tokens=100000),
        ]
        result = self.allocator.allocate(
            candidates,
            CurrentIntent(intent="compact_recovery", semantic_targets=("identity_origin", "project"), task_domain="julia_core"),
            ContextBudget(total_budget=2000, identity_budget=600, project_budget=900, conversation_budget=500),
        )
        refs = self.selected_refs(result)
        self.assertIn("memory://event/julia-core-origin", refs)
        self.assertIn("memory://project/e2-context", refs)
        self.assertIn("chat://raw/history", self.dropped_refs(result))
        self.assertLessEqual(result.used_tokens, 2000)
        trace = result.to_dict()
        self.assertIn("selected", trace)
        self.assertIn("dropped", trace)

    def test_s005_long_running_agent_simulation_preserves_identity_reason(self):
        candidates = [
            ContextCandidate(ref="memory://event/julia-core-origin", continuity_level="L3_IDENTITY", semantic_type="identity_origin", semantic_relevance=1.0, task_relevance=1.0, relationship_weight=0.8, estimated_tokens=400),
            ContextCandidate(ref="memory://relationship/tony-julia", continuity_level="L2_MEMORY", semantic_type="relationship", semantic_relevance=0.8, relationship_weight=1.0, estimated_tokens=400),
            ContextCandidate(ref="memory://project/julia-core-roadmap", continuity_level="L2_MEMORY", semantic_type="project", semantic_relevance=0.8, task_relevance=0.8, estimated_tokens=700),
        ] + [
            ContextCandidate(ref=f"session://day-{day}/turn-{i}", continuity_level="L1_SESSION", semantic_type="session", semantic_relevance=0.2, estimated_tokens=80)
            for day in range(1, 201) for i in range(2)
        ]
        result = self.allocator.allocate(
            candidates,
            CurrentIntent(intent="why_do_you_exist", semantic_targets=("identity_origin", "relationship", "project"), relationship_sensitive=True, task_domain="julia_core"),
            ContextBudget(total_budget=3000, identity_budget=600, relationship_budget=600, project_budget=900, conversation_budget=900),
        )
        refs = self.selected_refs(result)
        self.assertIn("memory://event/julia-core-origin", refs)
        self.assertIn("memory://relationship/tony-julia", refs)
        self.assertIn("memory://project/julia-core-roadmap", refs)
        self.assertGreater(len([ref for ref in self.dropped_refs(result) if ref.startswith("session://day-")]), 0)

    def test_stress_path_does_not_add_provider_or_prompt_fallback(self):
        for rel in ("julia_core/context_os/priority_model.py", "julia_core/context_os/budget_model.py"):
            tree = ast.parse(Path(rel).read_text())
            imports = []
            calls = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                if isinstance(node, ast.ImportFrom):
                    imports.append(node.module or "")
                if isinstance(node, ast.Call):
                    calls.append(getattr(node.func, "attr", getattr(node.func, "id", "")))
            for module in imports:
                self.assertFalse(any(token in module for token in ("provider", "persona", "memory", "alignment", "continuity")), module)
            for call in calls:
                self.assertNotIn(call, ("chat", "provide", "summarize", "load_memory", "create_checkpoint"))


if __name__ == "__main__":
    unittest.main()
