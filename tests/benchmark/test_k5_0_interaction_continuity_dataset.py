import json
import unittest
from pathlib import Path

DATASET = Path("artifacts/benchmark/interaction_continuity/interaction_continuity_dataset_v0_1.jsonl")
SCHEMA_DOC = Path("docs/benchmark/INTERACTION_CONTINUITY_DATASET_SCHEMA_v0_1.md")
PRINCIPLES = Path("docs/architecture/JULIA_CORE_PRINCIPLES.md")


class TestK50InteractionContinuityDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_dataset_and_schema_exist(self):
        self.assertTrue(DATASET.exists())
        self.assertTrue(SCHEMA_DOC.exists())
        self.assertGreaterEqual(len(self.records), 4)

    def test_required_categories_are_present(self):
        categories = {record["category"] for record in self.records}
        self.assertEqual(
            categories,
            {
                "identity_experience",
                "relationship_experience",
                "collaboration_experience",
                "correction_experience",
            },
        )

    def test_records_capture_behavior_tendency_not_identity_fact(self):
        for record in self.records:
            self.assertIn("trigger_event", record)
            self.assertIn("interaction_context", record)
            self.assertIn("behavior_change", record)
            self.assertIn("learned_tendency", record)
            self.assertIn("preferred_response_mode", record["learned_tendency"])
            self.assertIn("avoid_response_mode", record["learned_tendency"])
            self.assertIsInstance(record["example_turns"], list)
            self.assertGreater(record["confidence"], 0.0)
            payload = json.dumps(record, ensure_ascii=False)
            self.assertNotIn('"Tony是老公"', payload)
            self.assertNotIn('"Julia喜欢哲学"', payload)

    def test_boundary_flags_prevent_memory_identity_persona_mutation(self):
        for record in self.records:
            boundary = record["boundary"]
            self.assertTrue(boundary["not_memory"])
            self.assertTrue(boundary["not_identity"])
            self.assertTrue(boundary["not_persona_update"])
            self.assertTrue(boundary["requires_governance"])

    def test_principle_11_is_recorded(self):
        text = PRINCIPLES.read_text(encoding="utf-8")
        self.assertIn("Principle 11", text)
        self.assertIn("Experience Shapes Behavior, Not Identity", text)
        self.assertIn("Interaction experience may shape Julia's response tendencies", text)


if __name__ == "__main__":
    unittest.main()
