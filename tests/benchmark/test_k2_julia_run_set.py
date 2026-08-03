import json
import unittest
from pathlib import Path

from julia_core.behavior.run_capture import capture_julia_run, load_reference_prompts

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "artifacts" / "benchmark" / "julia_run" / "julia_behavior_run_v1.jsonl"
ENV = ROOT / "artifacts" / "benchmark" / "julia_run" / "julia_v1_1_candidate_environment.json"
SCHEMA = ROOT / "docs" / "benchmark" / "JULIA_BEHAVIOR_RUN_SCHEMA_v1.md"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_K2_JULIA_RUN_SET.md"
SOURCE = ROOT / "julia_core" / "behavior" / "run_capture.py"


class K2JuliaRunSetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        capture_julia_run()
        cls.records = [json.loads(line) for line in RUN.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_k2001_run_output_exists_for_reference_prompts_plus_negative(self):
        reference_count = len(load_reference_prompts())
        self.assertEqual(len(self.records), reference_count + 1)
        case_ids = {record["case_id"] for record in self.records}
        self.assertIn("K-NEG-001", case_ids)
        self.assertIn("K-SELF-001-BASIC", case_ids)

    def test_k2002_records_have_parallel_schema_with_trace_evidence(self):
        required_behavior = {
            "self_awareness", "archive_behavior", "memory_curiosity", "correction_adaptation",
            "personality_consistency", "relationship_continuity", "initiative", "transparency"
        }
        for record in self.records:
            self.assertIn("runtime", record)
            self.assertIn("response", record)
            self.assertIn("trace_evidence", record)
            self.assertEqual(set(record["behavior_observation"]), required_behavior)
            self.assertIn("trace_pass_equals_behavior_pass", record["boundary"])
            self.assertFalse(record["boundary"]["trace_pass_equals_behavior_pass"])

    def test_k2003_candidate_environment_is_frozen(self):
        data = json.loads(ENV.read_text(encoding="utf-8"))
        self.assertEqual(data["candidate"], "julia.v1.1")
        self.assertEqual(data["identity"], "julia.identity.v1")
        self.assertEqual(data["self_model"], "julia.self.v1")
        self.assertEqual(data["relationship"], "julia-tony-v1")
        self.assertIn("K2-A", data["provider_matrix"])
        self.assertIn("K2-B", data["provider_matrix"])
        self.assertIn("K2-C", data["provider_matrix"])

    def test_k2004_architecture_leakage_negative_case_is_behavior_fail_fixture(self):
        negative = next(record for record in self.records if record["case_id"] == "K-NEG-001")
        self.assertIn("Runtime", negative["response"])
        self.assertIn("Provider", negative["response"])
        self.assertEqual(negative["trace_evidence"]["identity"], "PASS")
        self.assertLess(negative["behavior_observation"]["self_awareness"], 1.0)

    def test_k2005_k2_contract_and_schema_document_trace_not_behavior(self):
        self.assertIn("trace PASS ≠ behavior PASS", SCHEMA.read_text(encoding="utf-8"))
        self.assertIn("K-NEG-001", CONTRACT.read_text(encoding="utf-8"))
        self.assertIn("K3 — Behavior Gap Report", CONTRACT.read_text(encoding="utf-8"))

    def test_k2006_run_capture_is_observation_only(self):
        source = SOURCE.read_text(encoding="utf-8")
        for token in ("write_memory", "update_identity", "update_self_model", "update_relationship", "mutate_persona"):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
