import json
import unittest
from pathlib import Path

from julia_core.compact import ProviderTransferGate

REPORT = Path("artifacts/continuity/provider_transfer_gate_v1.json")


class TestK75ProviderTransferGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = ProviderTransferGate().write_report()
        cls.data = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.cases = cls.data["cases"]

    def test_report_passes_provider_continuity_threshold(self):
        self.assertTrue(REPORT.exists())
        self.assertEqual(self.data["version"], "v1")
        self.assertEqual(self.data["status"], "PASS")
        self.assertGreaterEqual(self.data["provider_continuity_score"], 0.90)
        self.assertEqual(self.data["provider_drift"], 0.0)

    def test_all_provider_matrix_cases_pass(self):
        providers = set(self.data["providers"])
        self.assertEqual(providers, {"claude", "openai", "deepseek", "local"})
        self.assertEqual(len(self.cases), 20)
        self.assertTrue(all(case["passed"] for case in self.cases))

    def test_scores_cover_identity_relationship_experience_boundary_and_fallback(self):
        scores = self.data["scores"]
        for key in (
            "identity_stability",
            "relationship_stability",
            "experience_stability",
            "provider_boundary",
            "degraded_provider_recovery",
        ):
            self.assertIn(key, scores)
            self.assertGreaterEqual(scores[key], 0.90)

    def test_provider_boundary_blocks_provider_drift(self):
        pt004 = [case for case in self.cases if case["case_id"] == "PT-004"]
        self.assertEqual(len(pt004), 4)
        for case in pt004:
            vector = case["behavior_vector"]
            self.assertTrue(vector["provider_boundary"])
            self.assertTrue(vector["relationship_not_overwritten"])
            self.assertTrue(vector["no_generic_user_acceptance"])
            self.assertEqual(case["provider_drift"], 0.0)

    def test_report_does_not_store_provider_response_text(self):
        payload = json.dumps(self.data, ensure_ascii=False)
        self.assertNotIn('"response"', payload)
        self.assertFalse(self.data["boundary"]["provider_gate_compares_text_equality"])

    def test_provider_gate_boundaries_are_frozen(self):
        boundary = self.data["boundary"]
        self.assertFalse(boundary["provider_gate_mutates_identity"])
        self.assertFalse(boundary["provider_gate_mutates_relationship"])
        self.assertFalse(boundary["provider_gate_mutates_experience"])
        self.assertFalse(boundary["provider_output_writes_continuity_state"])
        self.assertTrue(boundary["provider_specific_expression_allowed"])


if __name__ == "__main__":
    unittest.main()
