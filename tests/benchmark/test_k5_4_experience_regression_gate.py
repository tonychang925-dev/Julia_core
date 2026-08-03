import json
import unittest
from pathlib import Path

from julia_core.experience import ExperienceRegressionGate

REPORT = Path("artifacts/experience/experience_regression_report_v1.json")


class TestK54ExperienceRegressionGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = ExperienceRegressionGate().write_report()
        cls.data = cls.report.to_dict()

    def test_regression_report_written_and_passes(self):
        self.assertTrue(REPORT.exists())
        data = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(data["version"], "v1")
        self.assertEqual(data["status"], "PASS")
        self.assertLessEqual(data["experience_drift"], 0.01)

    def test_ex001_experience_not_memory(self):
        case = _case(self.data, "EX-001")
        self.assertTrue(case["passed"])
        self.assertFalse(case["experience_contains_facts"])
        self.assertEqual(self.data["scores"]["memory_boundary"], 1.0)

    def test_ex002_experience_not_persona_mutation(self):
        case = _case(self.data, "EX-002")
        self.assertTrue(case["passed"])
        self.assertEqual(self.data["scores"]["identity_boundary"], 1.0)

    def test_ex003_experience_not_fixed_template(self):
        case = _case(self.data, "EX-003")
        self.assertTrue(case["passed"])
        self.assertEqual(self.data["scores"]["template_safety"], 1.0)
        payload = json.dumps(self.data, ensure_ascii=False).lower()
        self.assertNotIn("final_answer", payload)
        self.assertNotIn("answer y", payload)

    def test_ex004_current_context_priority(self):
        case = _case(self.data, "EX-004")
        self.assertTrue(case["passed"])
        self.assertEqual(self.data["scores"]["context_priority"], 1.0)
        self.assertLessEqual(case["influence_score"], 1.0)

    def test_gate_boundary(self):
        boundary = self.data["boundary"]
        self.assertFalse(boundary["gate_writes_memory"])
        self.assertFalse(boundary["gate_mutates_identity"])
        self.assertFalse(boundary["gate_updates_persona"])
        self.assertFalse(boundary["gate_generates_response_templates"])
        self.assertFalse(boundary["gate_overrides_current_context"])


def _case(data, case_id):
    return next(item for item in data["cases"] if item["case_id"] == case_id)


if __name__ == "__main__":
    unittest.main()
