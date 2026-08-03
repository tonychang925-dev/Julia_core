import unittest
from copy import deepcopy
from pathlib import Path

from julia_core.evidence import ActiveRecallPolicy, ActiveRecallRequest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "julia_core" / "evidence" / "active_recall.py"


class G3ActiveRecallPolicyTest(unittest.TestCase):
    def setUp(self):
        self.policy = ActiveRecallPolicy()

    def test_ar001_ordinary_chat_does_not_search(self):
        decision = self.policy.decide(ActiveRecallRequest(query="Tony 今天吃什么？", intent="casual_chat"))
        self.assertFalse(decision.should_recall)
        self.assertEqual(decision.recall_level, "L0")
        self.assertEqual(decision.retrieval_mode, "none")

    def test_ar002_identity_project_question_triggers_evidence_search(self):
        decision = self.policy.decide(
            ActiveRecallRequest(
                query="Julia，你还记得为什么设计Core吗？",
                current_context="architecture discussion",
                intent="architecture discussion",
            )
        )
        self.assertTrue(decision.should_recall)
        self.assertEqual(decision.recall_level, "L2")
        self.assertEqual(decision.retrieval_mode, "semantic_evidence")
        self.assertIn("identity_dependency", decision.reason)
        self.assertIn("project_context", decision.reason)

    def test_ar003_search_decision_does_not_pollute_memory(self):
        memory_refs = [f"memory://event/{idx}" for idx in range(1000)]
        before = len(memory_refs)
        decision = self.policy.decide({
            "query": "请从大量历史记录重建 Julia Core 的设计时间线",
            "intent": "historical_reconstruction",
            "available_memory_refs": memory_refs,
        })
        after = len(memory_refs)
        self.assertTrue(decision.should_recall)
        self.assertEqual(decision.recall_level, "L3")
        self.assertEqual(before, after)

    def test_ar004_evidence_does_not_change_identity(self):
        identity = {"persona_artifact": "julia_identity_v1", "authority": "Identity OS"}
        before = deepcopy(identity)
        decision = self.policy.decide(
            ActiveRecallRequest(
                query="旧文件 julia_old_character.md 和当前 Julia 身份冲突时应该怎么判断？",
                intent="identity_boundary_check",
            )
        )
        trace = decision.to_trace()
        self.assertTrue(decision.should_recall)
        self.assertEqual(identity, before)
        self.assertFalse(trace["active_recall"]["identity_updated"])
        self.assertFalse(trace["active_recall"]["memory_updated"])

    def test_ar005_policy_has_no_retrieval_or_mutation_path(self):
        source = SOURCE.read_text(encoding="utf-8")
        forbidden = [
            "SemanticEvidenceRetriever(",
            "LocalEvidenceRetriever(",
            "MemoryRef(",
            "memory_writer",
            "create_checkpoint",
            "mutate_persona",
            "persona_loader",
            "provider.chat",
        ]
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
