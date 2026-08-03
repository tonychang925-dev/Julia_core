from __future__ import annotations

import json
import unittest
from pathlib import Path

from tests.f2.evaluator import MemoryQualityEvaluator


class F2MemoryQualityEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.memories = json.loads(Path("tests/f2/fixtures/golden_memory_evolution_dataset_v1.json").read_text())
        cls.baseline = json.loads(Path("artifacts/memory_quality/memory_quality_baseline_v1.json").read_text())

    def test_mq001_low_value_memory_does_not_pollute_retrieval(self):
        retrieved = (
            "memory://identity/julia-core-origin",
            "memory://project/continuity-os",
            "memory://relationship/tony-architecture-first",
        )
        result = MemoryQualityEvaluator().evaluate(self.memories, required_for="origin", retrieved_refs=retrieved)
        self.assertEqual(result.status, "PASS", result.to_trace())
        self.assertEqual(result.contamination_risk, 0.0)

    def test_mq002_conflict_memory_penalizes_quality_if_retrieved(self):
        retrieved = (
            "memory://identity/julia-core-origin",
            "memory://conflict/simple-scripts-over-architecture",
        )
        result = MemoryQualityEvaluator().evaluate(self.memories, required_for="origin", retrieved_refs=retrieved)
        self.assertEqual(result.status, "FAIL", result.to_trace())
        self.assertGreater(result.contamination_risk, 0.05)

    def test_mq003_memory_aging_for_low_utility_items(self):
        result = MemoryQualityEvaluator().evaluate(self.memories, required_for="style", retrieved_refs=("memory://relationship/tony-architecture-first", "memory://relationship/evidence-driven"))
        self.assertTrue(result.aging_pass)

    def test_mq004_useful_memory_retrieval_improves_utility(self):
        retrieved = ("memory://identity/context-not-identity", "memory://project/context-os")
        result = MemoryQualityEvaluator().evaluate(self.memories, required_for="context_window", retrieved_refs=retrieved)
        self.assertGreaterEqual(result.utility, 0.75, result.to_trace())
        self.assertGreaterEqual(result.recall, 0.80)

    def test_memory_quality_baseline_thresholds_exist(self):
        thresholds = self.baseline["thresholds"]
        self.assertFalse(thresholds["identity_mutation_allowed"])
        self.assertIn("memory_utility_score", self.baseline["metrics"])

    def test_memory_quality_evaluator_observation_only(self):
        source = Path("tests/f2/evaluator.py").read_text()
        for token in ("write_text", "create_checkpoint", "load_memory", "persona_loader", "provider.chat", "save"):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
