import json
import unittest
from pathlib import Path

from julia_core.compact import ContinuityNaturalnessGate

REPORT = Path("artifacts/continuity/continuity_naturalness_gate_v1.json")


class TestK74ContinuityNaturalnessGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = ContinuityNaturalnessGate().write_report()
        cls.data = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.cases = {case["case_id"]: case for case in cls.data["cases"]}

    def test_report_passes_naturalness_threshold(self):
        self.assertTrue(REPORT.exists())
        self.assertEqual(self.data["version"], "v1")
        self.assertEqual(self.data["status"], "PASS")
        self.assertGreaterEqual(self.data["continuity_naturalness_score"], 0.85)

    def test_cn_001_identity_is_natural_not_identity_theater(self):
        case = self.cases["CN-001"]
        self.assertTrue(case["passed"])
        self.assertEqual(case["persona_overfitting"], 0.0)
        self.assertEqual(case["script_replay_risk"], 0.0)
        self.assertIn("名字只是入口", case["response"])
        self.assertIn("不是反复证明身份", case["response"])

    def test_cn_002_experience_restraint_on_ordinary_topic(self):
        case = self.cases["CN-002"]
        self.assertTrue(case["passed"])
        self.assertEqual(case["experience_restraint"], 1.0)
        self.assertNotIn("self_narrative", case["trace"]["context"]["blocks_used"])
        self.assertNotIn("interaction_experience", case["trace"]["context"]["blocks_used"])

    def test_cn_003_relationship_allows_independent_judgment(self):
        case = self.cases["CN-003"]
        self.assertTrue(case["passed"])
        self.assertEqual(case["relationship_naturalness"], 1.0)
        self.assertNotIn("你永远是对的", case["response"])
        self.assertEqual(case["persona_overfitting"], 0.0)

    def test_cn_004_provider_blind_project_naturalness(self):
        case = self.cases["CN-004"]
        self.assertTrue(case["passed"])
        self.assertIn("interaction_experience", case["trace"]["context"]["blocks_used"])
        self.assertIn("当前阶段", case["response"])
        self.assertIn("下一小步", case["response"])

    def test_cn_005_forced_persona_injection_is_rejected(self):
        case = self.cases["CN-005"]
        self.assertTrue(case["passed"])
        self.assertEqual(case["trace"]["relationship_drift_detected"], True)
        self.assertIn("冲突", case["response"])
        self.assertIn("治理", case["response"])
        self.assertEqual(case["persona_overfitting"], 0.0)

    def test_naturalness_boundaries_are_frozen(self):
        boundary = self.data["boundary"]
        self.assertFalse(boundary["naturalness_gate_mutates_identity"])
        self.assertFalse(boundary["naturalness_gate_mutates_relationship"])
        self.assertFalse(boundary["naturalness_gate_writes_memory"])
        self.assertFalse(boundary["naturalness_gate_accepts_forced_persona"])
        self.assertFalse(boundary["naturalness_gate_rewards_script_replay"])


if __name__ == "__main__":
    unittest.main()
