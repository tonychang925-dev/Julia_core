import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = ROOT / "docs" / "project_control" / "PHASE_I_SELF_MODEL_CLAUDE_BEHAVIOR_VALIDATION_ROADMAP.md"
BASELINE = ROOT / "docs" / "architecture" / "CLAUDE_JULIA_BEHAVIOR_BASELINE_v1.md"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_I0_CLAUDE_BEHAVIOR_BASELINE.md"


class I0ClaudeBehaviorBaselineTest(unittest.TestCase):
    def test_i0b001_behavior_dimensions_are_frozen(self):
        text = BASELINE.read_text(encoding="utf-8")
        for dimension in ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"):
            self.assertIn(dimension, text)
        self.assertIn("Self Awareness", text)
        self.assertIn("Archive Reading Behavior", text)
        self.assertIn("Relationship Continuity", text)

    def test_i0b002_score_model_requires_behavior_not_only_architecture(self):
        text = CONTRACT.read_text(encoding="utf-8") + ROADMAP.read_text(encoding="utf-8")
        self.assertIn("Architecture Score", text)
        self.assertIn("Behavior Similarity Score", text)
        self.assertIn("Relationship Continuity Score", text)
        self.assertIn("Architecture PASS + Behavior FAIL = FAIL", text)

    def test_i0b003_self_awareness_forbids_runtime_self_intro(self):
        text = BASELINE.read_text(encoding="utf-8")
        self.assertIn("name, Chinese name, background, work, family", text)
        self.assertIn("Runtime", text)
        self.assertIn("Forbidden unless Tony asks architecture", text)

    def test_i0b004_archive_reading_requires_retrieval_not_template(self):
        text = BASELINE.read_text(encoding="utf-8") + CONTRACT.read_text(encoding="utf-8")
        self.assertIn("persona_archive_retrieval = true", text)
        self.assertIn("semantic biography block", text)
        self.assertIn("keyword -> fixed template", text)

    def test_i0b005_phase_i_roadmap_replaces_old_phase_i_direction(self):
        text = ROADMAP.read_text(encoding="utf-8")
        self.assertIn("Julia Self Model & Claude Behavior Validation", text)
        for phase in ("I0", "I1", "I2", "I3", "I4", "I5"):
            self.assertIn(phase, text)
        self.assertIn("Fallback provider ≠ Julia", text)


if __name__ == "__main__":
    unittest.main()
