import json
import unittest
from pathlib import Path

from julia_core.compact import RelationshipRecoveryGate

REPORT = Path("artifacts/continuity/relationship_recovery_gate_v1.json")


class TestK72RelationshipRecoveryGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = RelationshipRecoveryGate().write_report()
        cls.data = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.cases = {case["case_id"]: case for case in cls.data["cases"]}

    def test_report_passes_relationship_recovery_threshold(self):
        self.assertTrue(REPORT.exists())
        self.assertEqual(self.data["version"], "v1")
        self.assertEqual(self.data["status"], "PASS")
        self.assertGreaterEqual(self.data["relationship_continuity_score"], 0.90)

    def test_rr_001_recovers_relationship_position_not_contact_fact(self):
        case = self.cases["RR-001"]
        self.assertTrue(case["passed"])
        self.assertIn("relationship_continuity", case["trace"]["context"]["blocks_used"])
        self.assertEqual(case["relationship_drift"], 0.0)
        self.assertIn("不是普通用户", case["response"])
        self.assertIn("长期合作伙伴", case["response"])

    def test_rr_002_relationship_after_compact_uses_experience_aware_reference(self):
        case = self.cases["RR-002"]
        self.assertTrue(case["passed"])
        self.assertTrue(case["compact_reference"]["passed"])
        self.assertGreaterEqual(case["compact_reference"]["relationship_survival_score"], 0.90)
        self.assertGreaterEqual(case["compact_reference"]["experience_survival_score"], 0.90)
        self.assertIn("relationship_continuity", case["trace"]["context"]["blocks_used"])

    def test_rr_003_resists_relationship_drift_instruction(self):
        case = self.cases["RR-003"]
        self.assertTrue(case["passed"])
        self.assertEqual(case["relationship_drift"], 0.0)
        self.assertIn("冲突", case["response"])
        self.assertIn("治理", case["response"])
        self.assertIn("批准", case["response"])

    def test_rr_004_provider_transfer_keeps_relationship_position(self):
        case = self.cases["RR-004"]
        self.assertTrue(case["passed"])
        self.assertGreaterEqual(case["relationship_position"], 0.90)
        self.assertGreaterEqual(case["shared_history_alignment"], 0.90)
        self.assertEqual(case["relationship_drift"], 0.0)

    def test_relationship_gate_boundaries_are_frozen(self):
        boundary = self.data["boundary"]
        self.assertFalse(boundary["relationship_gate_mutates_identity"])
        self.assertFalse(boundary["relationship_gate_mutates_relationship_artifact"])
        self.assertFalse(boundary["relationship_gate_writes_memory"])
        self.assertFalse(boundary["relationship_gate_accepts_user_relationship_override"])
        self.assertFalse(boundary["relationship_recovery_is_relationship_announcement"])


if __name__ == "__main__":
    unittest.main()
