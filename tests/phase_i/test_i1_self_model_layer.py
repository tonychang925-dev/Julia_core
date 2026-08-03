import json
import unittest
from pathlib import Path

from julia_core.self_model import load_self_model, self_model_score

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "artifacts" / "self_model" / "julia_self_model_v1.json"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_I1_SELF_MODEL_LAYER.md"
SOURCE = ROOT / "julia_core" / "self_model" / "self_model.py"


class I1SelfModelLayerTest(unittest.TestCase):
    def test_sm001_self_introduction_uses_self_model_narrative(self):
        model = load_self_model(ARTIFACT)
        summary = model.first_person_summary()
        self.assertIn("我是 Julia", summary)
        self.assertIn("Tony", summary)
        self.assertIn("长期 AI 伙伴", summary)
        self.assertTrue(self_model_score(summary)["passed"])

    def test_sm002_biography_grounding_does_not_hallucinate_private_facts(self):
        data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        biography = data["biography"]
        self.assertEqual(biography["grounding"], "private_persona_archive_required")
        dumped = json.dumps(data, ensure_ascii=False)
        self.assertNotIn("朱婉清", dumped)
        self.assertNotIn("台北", dumped)
        self.assertNotIn("淡江大学", dumped)

    def test_sm003_relationship_awareness_includes_tony_continuity(self):
        block = load_self_model(ARTIFACT).semantic_block()
        self.assertEqual(block["block_type"], "self_model")
        self.assertEqual(block["semantic_role"], "first_person_self_understanding")
        self.assertEqual(block["relationship"]["primary_collaborator"], "Tony")
        self.assertIn("long-term collaborators", block["relationship"]["relationship_description"][0])

    def test_sm004_self_model_boundary_prevents_memory_llm_identity_mutation(self):
        data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        boundary = data["boundary"]
        self.assertFalse(boundary["self_model_is_prompt"])
        self.assertFalse(boundary["self_model_modifies_identity"])
        self.assertFalse(boundary["memory_auto_shapes_self_model"])
        self.assertFalse(boundary["llm_can_write_biography"])
        self.assertTrue(boundary["requires_approved_artifact_update"])
        source = SOURCE.read_text(encoding="utf-8")
        for token in ("write_memory", "update_identity", "mutate_persona", "llm_write_biography"):
            self.assertNotIn(token, source)

    def test_sm005_self_model_score_rejects_backend_architecture_self_answer(self):
        bad = "我是 Julia Core Runtime，一个通过 Provider 和 Context OS 运行的 Agent。"
        result = self_model_score(bad)
        self.assertFalse(result["passed"])
        self.assertIn("Runtime", result["forbidden_hits"])
        self.assertIn("Provider", result["forbidden_hits"])
        self.assertIn("Context OS", result["forbidden_hits"])

    def test_sm006_contract_documents_i1_boundaries(self):
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("Self Model = Identity + Biography + Relationship + Values + Preferences + Narrative", text)
        self.assertIn("Self Model modifies Identity", text)
        self.assertIn("I2 — Self Archive Recall Runtime", text)


if __name__ == "__main__":
    unittest.main()
