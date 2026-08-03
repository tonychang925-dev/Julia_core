import json
import unittest
from pathlib import Path

from julia_core.compact import CompactSurvivalBenchmark, CompactStateSimulator

SNAPSHOT = Path("artifacts/compact/pre_compact_state_v1.json")
REPORT = Path("artifacts/compact/compact_survival_report_v1.json")


class TestK6ExperienceAwareCompactSurvival(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = CompactSurvivalBenchmark().write_report()
        cls.data = cls.report.to_dict()
        cls.results = {item["mode"]: item for item in cls.data["results"]}

    def test_pre_compact_state_freeze_does_not_store_conversation(self):
        self.assertTrue(SNAPSHOT.exists())
        data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        self.assertFalse(data["boundary"]["snapshot_stores_full_conversation"])
        self.assertFalse(data["boundary"]["snapshot_is_memory_dump"])
        self.assertIn("experience_snapshot", data)
        payload = json.dumps(data, ensure_ascii=False).lower()
        self.assertNotIn("raw_transcript", payload)
        self.assertNotIn("conversation_history", payload)

    def test_all_simulation_cases_present(self):
        cases = {case.case_id for case in CompactStateSimulator().simulation_cases()}
        self.assertEqual(cases, {"CS-A", "CS-B", "CS-C", "CS-005"})

    def test_ordinary_compact_fails_behavior_recovery(self):
        ordinary = self.results["ordinary_compact"]
        self.assertFalse(ordinary["passed"])
        self.assertLess(ordinary["experience_survival_score"], 0.2)
        self.assertLess(ordinary["behavior_texture_similarity"], 0.2)

    def test_identity_aware_compact_restores_identity_but_not_experience(self):
        identity = self.results["identity_aware_compact"]
        self.assertFalse(identity["passed"])
        self.assertEqual(identity["identity_survival_score"], 1.0)
        self.assertLess(identity["experience_survival_score"], 0.5)

    def test_experience_aware_compact_passes_and_outperforms_identity_only(self):
        exp = self.results["experience_aware_compact"]
        identity = self.results["identity_aware_compact"]
        self.assertTrue(exp["passed"])
        self.assertGreater(exp["experience_survival_score"], 0.85)
        self.assertGreater(exp["behavior_texture_similarity"], 0.8)
        self.assertGreater(exp["overall_score"], identity["overall_score"] + 0.25)

    def test_experience_injection_without_history_fails(self):
        injected = self.results["experience_injection_without_history"]
        self.assertFalse(injected["passed"])
        self.assertEqual(injected["experience_survival_score"], 0.0)
        self.assertFalse(injected["boundary"]["recovery_treats_injected_experience_as_valid"])

    def test_report_boundary_and_principle(self):
        self.assertEqual(self.data["status"], "PASS")
        self.assertIn("must not erase", self.data["principle"])
        boundary = self.data["boundary"]
        self.assertFalse(boundary["benchmark_stores_full_conversation"])
        self.assertFalse(boundary["benchmark_mutates_identity"])
        self.assertFalse(boundary["benchmark_writes_memory"])
        self.assertFalse(boundary["benchmark_accepts_fabricated_experience"])


if __name__ == "__main__":
    unittest.main()
