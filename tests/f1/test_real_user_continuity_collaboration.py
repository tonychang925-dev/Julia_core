from __future__ import annotations

import json
import unittest
from pathlib import Path

from tests.f1.evaluator import RealityEvaluator


class GoldenRealityResponder:
    def respond(self, case: dict) -> str:
        return " ".join(case["required_principles"]) + " evidence decision boundary next step reality baseline"


class F1RealityContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = json.loads(Path("tests/f1/fixtures/golden_reality_dataset_v1.json").read_text())
        cls.baseline = json.loads(Path("artifacts/reality/julia_reality_baseline_v1.json").read_text())

    def test_f1_golden_dataset_shape(self):
        self.assertEqual(len(self.dataset), 20)
        categories = {case["category"] for case in self.dataset}
        self.assertEqual(categories, {"identity", "architecture_decision", "long_project", "interaction_style"})
        self.assertEqual(self.baseline["baseline_id"], "julia_reality_baseline_v1")

    def test_f1_first_reality_interaction_run(self):
        evaluator = RealityEvaluator()
        responder = GoldenRealityResponder()
        scores = []
        for case in self.dataset:
            with self.subTest(case=case["id"]):
                response = responder.respond(case)
                evaluation = evaluator.evaluate(case, response)
                trace = {"reality_validation": evaluation.to_trace()}
                self.assertEqual(trace["reality_validation"]["baseline_version"], "julia_reality_baseline_v1")
                self.assertEqual(trace["reality_validation"]["status"], "PASS", trace)
                scores.append(trace["reality_validation"]["collaboration_continuity_score"])
        self.assertGreaterEqual(sum(scores) / len(scores), 0.90)

    def test_reality_failure_classification_rule_is_documented(self):
        contract = Path("docs/project_control/PHASE_CONTRACT_F1_REAL_USER_CONTINUITY_TEST.md").read_text()
        for token in ("Core Contract Failure", "Context Quality Failure", "Evaluation Failure", "Provider Capability Limitation"):
            self.assertIn(token, contract)
        self.assertIn("bad answer → add prompt", contract)

    def test_reality_evaluator_observation_only(self):
        source = Path("tests/f1/evaluator.py").read_text()
        for token in ("write_text", "create_checkpoint", "load_memory", "persona_loader", "provider.chat", "save"):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
