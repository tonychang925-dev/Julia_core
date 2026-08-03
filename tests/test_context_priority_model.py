import ast
from pathlib import Path
import unittest

from julia_core.context_os.priority_model import ContextCandidate, ContextPriorityResolver, CurrentIntent


class ContextPriorityModelTests(unittest.TestCase):
    def setUp(self):
        self.resolver = ContextPriorityResolver()

    def refs(self, result):
        return [item.ref for item in result.ranked_candidates]

    def test_julia_core_origin_beats_recent_chat_for_origin_question(self):
        result = self.resolver.rank(
            [
                ContextCandidate(
                    ref="memory://event/julia-core-origin",
                    continuity_level="L3_IDENTITY",
                    semantic_type="identity_origin",
                    semantic_relevance=1.0,
                    task_relevance=0.9,
                    relationship_weight=0.7,
                    estimated_tokens=80,
                ),
                ContextCandidate(
                    ref="session://recent/chat",
                    continuity_level="L1_SESSION",
                    semantic_type="recent",
                    semantic_relevance=0.3,
                    task_relevance=0.4,
                    estimated_tokens=20,
                ),
            ],
            CurrentIntent(intent="why_julia_core", semantic_targets=("identity_origin",), task_domain="julia_core"),
        )
        self.assertEqual(self.refs(result)[0], "memory://event/julia-core-origin")

    def test_context_os_design_prioritizes_architecture_memory(self):
        result = self.resolver.rank(
            [
                ContextCandidate(
                    ref="memory://project/context-os-architecture",
                    continuity_level="L2_MEMORY",
                    semantic_type="project",
                    task_relevance=1.0,
                    semantic_relevance=0.9,
                    estimated_tokens=120,
                    metadata={"task_domain": "context_os"},
                ),
                ContextCandidate(
                    ref="memory://relationship/tony-style",
                    continuity_level="L2_MEMORY",
                    semantic_type="relationship",
                    relationship_weight=0.8,
                    semantic_relevance=0.4,
                    estimated_tokens=60,
                ),
                ContextCandidate(
                    ref="memory://general/history",
                    continuity_level="L1_SESSION",
                    semantic_type="general",
                    semantic_relevance=0.1,
                    estimated_tokens=50,
                ),
            ],
            CurrentIntent(intent="design_context_os", semantic_targets=("project",), relationship_sensitive=True, task_domain="context_os"),
        )
        self.assertEqual(self.refs(result)[0], "memory://project/context-os-architecture")
        self.assertLess(self.refs(result).index("memory://relationship/tony-style"), self.refs(result).index("memory://general/history"))

    def test_recent_context_can_beat_irrelevant_l3_identity_for_lunch_question(self):
        result = self.resolver.rank(
            [
                ContextCandidate(
                    ref="memory://event/julia-core-origin",
                    continuity_level="L3_IDENTITY",
                    semantic_type="identity_origin",
                    semantic_relevance=0.0,
                    task_relevance=0.0,
                    relationship_weight=0.0,
                    required=False,
                    estimated_tokens=80,
                ),
                ContextCandidate(
                    ref="session://today/lunch",
                    continuity_level="L1_SESSION",
                    semantic_type="recent",
                    semantic_relevance=1.0,
                    task_relevance=1.0,
                    estimated_tokens=20,
                ),
            ],
            CurrentIntent(intent="today_lunch", semantic_targets=("recent",), task_domain="daily"),
        )
        self.assertEqual(self.refs(result)[0], "session://today/lunch")

    def test_context_priority_is_not_memory_importance_authority(self):
        source = Path("julia_core/context_os/priority_model.py").read_text()
        tree = ast.parse(source)
        imported_modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")
        forbidden_imports = ("memory", "persona", "provider", "alignment", "continuity")
        for module in imported_modules:
            self.assertFalse(any(token in module for token in forbidden_imports), module)
        forbidden_calls = ("create_checkpoint", "load_memory", "chat", "provide")
        call_names = [getattr(node.func, "attr", getattr(node.func, "id", "")) for node in ast.walk(tree) if isinstance(node, ast.Call)]
        for token in forbidden_calls:
            self.assertNotIn(token, call_names)

    def test_candidate_accepts_refs_only(self):
        with self.assertRaises(ValueError):
            ContextCandidate(ref="raw text", continuity_level="L1_SESSION", semantic_type="general")


if __name__ == "__main__":
    unittest.main()
