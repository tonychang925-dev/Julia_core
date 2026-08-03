import json
import unittest
from pathlib import Path

from julia_core.experience import InteractionPatternExtractor, compute_interaction_coherence_density

OUTPUT = Path("artifacts/experience/interaction_patterns_v0_1.json")


class TestK51InteractionPatternExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pattern_set = InteractionPatternExtractor().write_patterns()
        cls.data = cls.pattern_set.to_dict()

    def test_pattern_artifact_written(self):
        self.assertTrue(OUTPUT.exists())
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(data["version"], "v0.1")
        self.assertEqual(len(data["patterns"]), 4)

    def test_all_experience_categories_are_extracted(self):
        categories = {pattern.category for pattern in self.pattern_set.patterns}
        self.assertEqual(
            categories,
            {
                "identity_experience",
                "relationship_experience",
                "collaboration_experience",
                "correction_experience",
            },
        )

    def test_patterns_capture_tendencies_not_raw_context(self):
        for pattern in self.pattern_set.patterns:
            self.assertTrue(pattern.trigger)
            self.assertGreater(len(pattern.preferred_response_mode), 0)
            self.assertGreater(len(pattern.avoid_response_mode), 0)
            self.assertGreater(len(pattern.changed_dimensions), 0)
            self.assertGreaterEqual(pattern.interaction_coherence_density, 0.0)
            self.assertLessEqual(pattern.interaction_coherence_density, 1.0)
            self.assertFalse(pattern.boundary["pattern_contains_raw_context"])
            payload = json.dumps(pattern.to_dict(), ensure_ascii=False)
            self.assertNotIn("100MB", payload)
            self.assertNotIn("full_conversation", payload)

    def test_pattern_set_boundary(self):
        boundary = self.data["boundary"]
        self.assertFalse(boundary["pattern_set_writes_memory"])
        self.assertFalse(boundary["pattern_set_mutates_identity"])
        self.assertFalse(boundary["pattern_set_updates_relationship"])
        self.assertFalse(boundary["pattern_set_updates_persona"])
        self.assertFalse(boundary["pattern_set_stores_long_context"])

    def test_icd_is_bounded_behavior_proxy(self):
        low = compute_interaction_coherence_density(
            repeated_patterns=0,
            emotional_context_continuity=0.0,
            shared_narrative_references=0.0,
            response_style_stability=0,
            compression_loss_penalty=0.2,
            confidence=0.1,
        )
        high = compute_interaction_coherence_density(
            repeated_patterns=5,
            emotional_context_continuity=1.0,
            shared_narrative_references=1.0,
            response_style_stability=4,
            compression_loss_penalty=0.0,
            confidence=1.0,
        )
        self.assertGreaterEqual(low, 0.0)
        self.assertLessEqual(high, 1.0)
        self.assertLess(low, high)


if __name__ == "__main__":
    unittest.main()
