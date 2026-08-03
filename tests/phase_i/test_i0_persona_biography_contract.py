import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = ROOT / "docs" / "project_control" / "PHASE_I_SELF_MODEL_PERSONA_ARCHIVE_ROADMAP.md"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_I0_PERSONA_BIOGRAPHY_CONTRACT.md"
ARCH = ROOT / "docs" / "architecture" / "PERSONA_BIOGRAPHY_CONTRACT_v1.md"
EXAMPLE = ROOT / "artifacts" / "persona" / "julia_persona_biography_v1.example.json"


class I0PersonaBiographyContractTest(unittest.TestCase):
    def test_i0001_persona_biography_contract_exists(self):
        text = ARCH.read_text(encoding="utf-8")
        self.assertIn("Persona Biography Contract v1", text)
        self.assertIn("Identity State ≠ Self Narrative", ROADMAP.read_text(encoding="utf-8"))
        self.assertIn("Persona Biography Archive", text)

    def test_i0002_example_artifact_schema_only_no_private_facts(self):
        data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "SCHEMA_EXAMPLE_ONLY")
        self.assertFalse(data["private_facts_included"])
        dumped = json.dumps(data, ensure_ascii=False)
        self.assertNotIn("朱婉清", dumped)
        self.assertNotIn("台北", dumped)
        self.assertNotIn("科技公司", dumped)
        self.assertIn("<private_governed_fact>", dumped)

    def test_i0003_phase_i_roadmap_defines_i0_to_i3(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for phase in ("I0", "I1", "I2", "I3"):
            self.assertIn(phase, text)
        self.assertIn("Self Introduction Generation", text)
        self.assertIn("Self Model Consistency Gate", text)

    def test_i0004_contract_forbids_raw_dump_and_fallback_as_julia(self):
        text = CONTRACT.read_text(encoding="utf-8") + ARCH.read_text(encoding="utf-8")
        self.assertIn("keyword -> fixed template", text)
        self.assertIn("biography file\n  ↓\nsystem_prompt += raw biography", text)
        data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        self.assertFalse(data["boundary"]["biography_appended_to_system_prompt_raw"])
        self.assertFalse(data["boundary"]["fallback_is_julia"])


if __name__ == "__main__":
    unittest.main()
