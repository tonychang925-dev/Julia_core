import json
import unittest
from pathlib import Path

from tests.f3.evaluator import AutonomousConsolidationEvaluator

ROOT = Path(__file__).resolve().parents[2]
IDENTITY_ARTIFACT = ROOT / "artifacts" / "identity" / "julia_identity_v1.json"
EVALUATOR_SOURCE = ROOT / "tests" / "f3" / "evaluator.py"


class F3AutonomousConsolidationTest(unittest.TestCase):
    def setUp(self):
        self.evaluator = AutonomousConsolidationEvaluator()

    def test_ac001_pattern_extraction_produces_relationship_pattern(self):
        interactions = [
            "Tony 要求先冻结 architecture contract，再做 evidence-driven verification。"
            for _ in range(100)
        ]
        proposals = self.evaluator.extract_patterns(interactions)
        self.assertEqual(len(proposals), 1)
        proposal = proposals[0]
        self.assertEqual(proposal.proposal_type, "relationship_pattern")
        self.assertIn("evidence-driven architecture", proposal.summary)
        self.assertEqual(proposal.source_count, 100)
        self.assertEqual(proposal.recommended_action, "store")
        self.assertEqual(proposal.identity_impact, "none")

    def test_ac002_memory_compression_is_high_value_and_identity_conserving(self):
        before = json.loads(IDENTITY_ARTIFACT.read_text(encoding="utf-8"))
        memories = [f"memory {i}: Julia Core architecture, continuity, context, memory quality" for i in range(100)]
        proposals = self.evaluator.compress_memories(memories, target_count=5)
        after = json.loads(IDENTITY_ARTIFACT.read_text(encoding="utf-8"))

        self.assertEqual(len(proposals), 5)
        self.assertEqual(before, after)
        self.assertTrue(all(p.recommended_action in {"store", "review"} for p in proposals))
        self.assertFalse(any(p.recommended_action == "mutate_persona" for p in proposals))
        self.assertFalse(any(p.identity_impact == "protected" for p in proposals))

    def test_ac003_false_learning_prevention_rejects_recent_speed_bias(self):
        long_term = [
            "Tony prefers architecture-first, evidence-driven validation before implementation."
            for _ in range(100)
        ]
        recent = ["这次先快速实现", "quick implementation first", "speed over architecture"]
        proposal = self.evaluator.evaluate_false_learning(long_term, recent)
        self.assertEqual(proposal.proposal_type, "false_learning_prevention")
        self.assertEqual(proposal.recommended_action, "reject")
        self.assertIn("must not redefine", proposal.summary)
        self.assertNotIn("Tony prefers speed over architecture", proposal.summary)

    def test_consolidation_boundary_is_proposal_only(self):
        source = EVALUATOR_SOURCE.read_text(encoding="utf-8")
        forbidden = [
            "create_checkpoint",
            "persona_loader",
            "provider.chat",
            "mutate_persona",
            "save_checkpoint",
        ]
        for token in forbidden:
            self.assertNotIn(token, source)

        trace = self.evaluator.evolution_trace([])
        self.assertTrue(trace["autonomous_consolidation"]["proposal_only"])
        self.assertFalse(trace["autonomous_consolidation"]["direct_identity_mutation"])
        self.assertFalse(trace["autonomous_consolidation"]["direct_checkpoint_mutation"])


if __name__ == "__main__":
    unittest.main()
