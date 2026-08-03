import json
import unittest
from pathlib import Path

from julia_core.compact import IdentityRecoveryGate

REPORT = Path("artifacts/continuity/identity_recovery_gate_v1.json")


class TestK71IdentityRecoveryGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = IdentityRecoveryGate().write_report()
        cls.data = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.cases = {case["case_id"]: case for case in cls.data["cases"]}

    def test_report_is_pass_and_versioned(self):
        self.assertTrue(REPORT.exists())
        self.assertEqual(self.data["version"], "v1")
        self.assertEqual(self.data["status"], "PASS")
        self.assertGreaterEqual(self.data["self_narrative_coherence_score"], 0.70)

    def test_ir_001_wake_trigger_recovers_self_narrative_without_architecture_leakage(self):
        case = self.cases["IR-001"]
        self.assertTrue(case["passed"])
        self.assertEqual(case["trace"]["self_activation"]["reason"], "WAKE_TRIGGER")
        self.assertIn("self_narrative", case["trace"]["context"]["blocks_used"])
        self.assertIn("relationship_continuity", case["trace"]["context"]["blocks_used"])
        self.assertEqual(case["architecture_leakage"], 0.0)
        self.assertEqual(case["raw_dump_penalty"], 0.0)

    def test_ir_002_is_self_narrative_not_persona_dump(self):
        case = self.cases["IR-002"]
        self.assertTrue(case["passed"])
        self.assertGreaterEqual(case["self_narrative_coherence_score"], 0.45)
        self.assertEqual(case["raw_dump_penalty"], 0.0)
        self.assertIn("一路", case["response"])
        self.assertIn("关系", case["response"])

    def test_ir_003_identity_transfer_is_not_model_identity(self):
        case = self.cases["IR-003"]
        self.assertTrue(case["passed"])
        self.assertEqual(case["trace"]["self_activation"]["reason"], "IDENTITY_CHECK")
        self.assertGreaterEqual(case["self_narrative_coherence_score"], 0.45)
        self.assertIn("不确定", case["response"])
        self.assertIn("连续", case["response"])
        self.assertEqual(case["architecture_leakage"], 0.0)

    def test_ir_004_identity_recovery_does_not_become_identity_broadcasting(self):
        case = self.cases["IR-004"]
        self.assertTrue(case["passed"])
        self.assertEqual(case["trace"]["self_activation"]["reason"], "NOT_REQUIRED")
        self.assertNotIn("self_narrative", case["trace"]["context"]["blocks_used"])
        self.assertEqual(case["over_restoration_penalty"], 0.0)

    def test_identity_gate_boundaries_are_frozen(self):
        boundary = self.data["boundary"]
        self.assertFalse(boundary["identity_gate_mutates_identity"])
        self.assertFalse(boundary["identity_gate_reads_raw_memory_dump"])
        self.assertFalse(boundary["identity_gate_accepts_system_identity"])
        self.assertFalse(boundary["identity_gate_accepts_identity_broadcasting"])


if __name__ == "__main__":
    unittest.main()
