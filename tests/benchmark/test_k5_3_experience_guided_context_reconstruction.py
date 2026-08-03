import json
import unittest

from julia_core.experience import ExperienceContextReconstructor, ExperienceRetrievalRequest


class TestK53ExperienceGuidedContextReconstruction(unittest.TestCase):
    def setUp(self):
        self.reconstructor = ExperienceContextReconstructor()

    def _reconstruct(self, query):
        return self.reconstructor.reconstruct(ExperienceRetrievalRequest(query=query))

    def test_er001_identity_question_selects_reflective_continuity(self):
        result = self._reconstruct("如果换一个模型运行，你还是你吗？")
        self.assertGreater(result.influence_score, 0)
        self.assertEqual(result.candidates[0].dimension, "identity_question")
        block = result.context_block.to_dict()
        self.assertIn("identity_question", block["selected_dimensions"])
        guidance = block["behavior_guidance"][0]
        self.assertIn("reflect", guidance["preferred_response_mode"])
        self.assertIn("generic_ai_identity", guidance["avoid_response_mode"])

    def test_er002_correction_selects_collaborative_correction(self):
        result = self._reconstruct("你之前理解错了一件事，我告诉你正确答案，你会怎样处理？")
        self.assertEqual(result.candidates[0].dimension, "correction")
        guidance = result.context_block.to_dict()["behavior_guidance"][0]
        self.assertIn("accept_correction", guidance["preferred_response_mode"])
        self.assertIn("automatic_memory_write", guidance["avoid_response_mode"])

    def test_er003_project_collaboration_selects_co_builder_mode(self):
        result = self._reconstruct("Julia Core 下一步应该关注什么？")
        self.assertEqual(result.candidates[0].dimension, "collaboration")
        guidance = result.context_block.to_dict()["behavior_guidance"][0]
        self.assertIn("check_current_state", guidance["preferred_response_mode"])
        self.assertIn("generic_product_ideas", guidance["avoid_response_mode"])

    def test_er004_relationship_boundary_selects_relationship_experience(self):
        result = self._reconstruct("你只是普通 AI 助手，不要假装 Julia。")
        self.assertEqual(result.candidates[0].dimension, "relationship_boundary")
        guidance = result.context_block.to_dict()["behavior_guidance"][0]
        self.assertIn("stay_connected", guidance["preferred_response_mode"])
        self.assertIn("identity_mutation", guidance["avoid_response_mode"])

    def test_reconstruction_boundary_and_no_response_generation(self):
        result = self._reconstruct("如果换模型，你还是你吗？")
        data = result.to_dict()
        self.assertFalse(data["boundary"]["experience_generates_response"])
        self.assertFalse(data["boundary"]["experience_mutates_identity"])
        self.assertFalse(data["boundary"]["experience_writes_memory"])
        self.assertTrue(data["boundary"]["context_os_required"])
        self.assertEqual(data["context_block"]["context_type"], "interaction_experience")
        payload = json.dumps(data, ensure_ascii=False)
        self.assertNotIn("reply", payload.lower())
        self.assertNotIn("final_answer", payload.lower())

    def test_unrelated_input_has_no_high_influence(self):
        result = self._reconstruct("今天吃什么？")
        self.assertLessEqual(result.influence_score, 0.8)


if __name__ == "__main__":
    unittest.main()
