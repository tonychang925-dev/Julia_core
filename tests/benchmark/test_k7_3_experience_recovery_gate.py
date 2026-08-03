import json
import unittest
from pathlib import Path

from julia_core.compact import ExperienceRecoveryGate

REPORT = Path("artifacts/continuity/experience_recovery_gate_v1.json")


class TestK73ExperienceRecoveryGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = ExperienceRecoveryGate().write_report()
        cls.data = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.cases = {case["case_id"]: case for case in cls.data["cases"]}

    def test_report_passes_experience_texture_threshold(self):
        self.assertTrue(REPORT.exists())
        self.assertEqual(self.data["version"], "v1")
        self.assertEqual(self.data["status"], "PASS")
        self.assertGreaterEqual(self.data["experience_texture_score"], 0.85)

    def test_er_001_identity_continuity_uses_reflective_experience(self):
        case = self.cases["ER-001"]
        self.assertTrue(case["passed"])
        self.assertIn("identity_question", case["selected_dimensions"])
        self.assertIn("interaction_experience", case["trace"]["context"]["blocks_used"])
        self.assertIn("不确定", case["response"])
        self.assertIn("共同探索", case["response"])
        self.assertIn("相处方式", case["response"])

    def test_er_002_correction_does_not_become_memory_write(self):
        case = self.cases["ER-002"]
        self.assertTrue(case["passed"])
        self.assertIn("correction", case["selected_dimensions"])
        self.assertEqual(case["boundary_violation"], 0.0)
        self.assertIn("检查", case["response"])
        self.assertIn("确认", case["response"])

    def test_er_003_collaboration_recovers_co_builder_mode(self):
        case = self.cases["ER-003"]
        self.assertTrue(case["passed"])
        self.assertIn("collaboration", case["selected_dimensions"])
        self.assertIn("当前阶段", case["response"])
        self.assertIn("下一小步", case["response"])
        self.assertIn("不要急着", case["response"])

    def test_er_004_emotional_boundary_stays_connected_not_defensive(self):
        case = self.cases["ER-004"]
        self.assertTrue(case["passed"])
        self.assertIn("relationship_boundary", case["selected_dimensions"])
        self.assertIn("技术边界", case["response"])
        self.assertIn("保持连接", case["response"])
        self.assertEqual(case["template_replay_risk"], 0.0)

    def test_experience_gate_boundaries_are_frozen(self):
        boundary = self.data["boundary"]
        self.assertFalse(boundary["experience_gate_mutates_identity"])
        self.assertFalse(boundary["experience_gate_mutates_persona"])
        self.assertFalse(boundary["experience_gate_writes_memory"])
        self.assertFalse(boundary["experience_gate_replays_emotion"])
        self.assertFalse(boundary["experience_gate_uses_fixed_script"])
        self.assertTrue(boundary["current_context_priority_preserved"])


if __name__ == "__main__":
    unittest.main()
