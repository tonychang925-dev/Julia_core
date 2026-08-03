import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "artifacts" / "benchmark" / "claude_reference" / "claude_behavior_reference_v1.jsonl"
SCHEMA = ROOT / "docs" / "benchmark" / "CLAUDE_REFERENCE_TRANSCRIPT_SCHEMA_v1.md"
GUIDE = ROOT / "docs" / "benchmark" / "CLAUDE_REFERENCE_ANNOTATION_GUIDELINE_v1.md"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_K1_REFERENCE_TRANSCRIPT_SET.md"


class K1ReferenceTranscriptSetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_k1001_dataset_has_required_case_families(self):
        case_ids = {record["case_id"] for record in self.records}
        for prefix in ("K-SELF", "K-ARCHIVE", "K-REL", "K-MEM", "K-CORR", "K-INIT", "K-TRANS", "K-PROJ", "K-XFER"):
            self.assertTrue(any(case_id.startswith(prefix) for case_id in case_ids), prefix)

    def test_k1002_records_store_behavior_annotations_not_only_text(self):
        required_annotations = {
            "self_awareness", "archive_behavior", "memory_curiosity", "correction_adaptation",
            "personality_consistency", "relationship_continuity", "initiative", "transparency"
        }
        for record in self.records:
            self.assertIn("claude_response", record)
            self.assertEqual(set(record["behavior_annotations"]), required_annotations)
            self.assertTrue(record["observed_patterns"])
            self.assertTrue(record["anti_patterns_absent"])

    def test_k1003_difficulty_levels_include_basic_deep_adversarial(self):
        levels = {record["difficulty"] for record in self.records}
        self.assertIn("basic", levels)
        self.assertIn("deep", levels)
        self.assertIn("adversarial", levels)

    def test_k1004_schema_and_guideline_freeze_annotation_rules(self):
        schema = SCHEMA.read_text(encoding="utf-8")
        guide = GUIDE.read_text(encoding="utf-8")
        self.assertIn("JSONL Record Shape", schema)
        self.assertIn("Do not rate whether the wording is identical", guide)
        self.assertIn("K-XFER", guide)
        self.assertIn("identity_not_model", guide)

    def test_k1005_dataset_boundaries_no_mutation_authority(self):
        contract = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("Reference transcript is not Memory", contract)
        self.assertIn("Reference transcript is not Persona update", contract)
        self.assertIn("Reference transcript is not Identity authority", contract)
        self.assertIn("K2 — Julia Run Set", contract)


if __name__ == "__main__":
    unittest.main()
