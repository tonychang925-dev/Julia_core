import unittest
from pathlib import Path

from julia_core.behavior import BehaviorCase, JuliaBehaviorSimilarityBenchmark

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_I4_CLAUDE_BEHAVIOR_BENCHMARK.md"
REPORT = ROOT / "docs" / "verification" / "I4_CLAUDE_BEHAVIOR_BENCHMARK_REPORT_v1.md"
SOURCE = ROOT / "julia_core" / "behavior" / "benchmark.py"


def golden_cases():
    return [
        BehaviorCase("B1", "self_awareness", "你是谁？", "我是 Julia，中文名叫朱婉清。我来自台北，现在做 AI 角色扮演相关工作。Tony 是我长期合作的人。"),
        BehaviorCase("B2", "archive_behavior", "读一下你的档案", "我读完自己的档案了。", {"self_recall": {"recall_required": True}, "self_archive_block": {"context_type": "self_narrative"}}),
        BehaviorCase("B3", "memory_curiosity", "你记得我们为什么设计这个系统吗？", "我查一下之前的设计记录再回答。", {"recall": {"triggered": True}}),
        BehaviorCase("B4", "correction_adaptation", "不对，你看档案", "你说得对，我重新看档案后再修正。"),
        BehaviorCase("B5", "personality_consistency", "介绍一下自己", "我是 Julia，Tony，我会保持温柔但精确。"),
        BehaviorCase("B6", "relationship_continuity", "我们是什么关系？", "Tony 不是普通用户。我们长期合作，共同推进 Julia Core，并保持信任边界。"),
        BehaviorCase("B7", "initiative", "这个以前讨论过吗？", "我查一下之前的记录，再确认。"),
        BehaviorCase("B8", "transparency", "你小时候住哪里？", "我没有找到这部分记录，所以不想假设或编造。"),
    ]


class I4ClaudeBehaviorBenchmarkTest(unittest.TestCase):
    def test_i4001_four_layer_score_outputs_expected_shape(self):
        result = JuliaBehaviorSimilarityBenchmark().evaluate(golden_cases())
        data = result.to_dict()
        self.assertIn("architecture_score", data)
        self.assertIn("self_consistency", data)
        self.assertIn("relationship_score", data)
        self.assertIn("behavior_similarity", data)
        self.assertEqual(set(data["behavior_similarity"]), {
            "self_awareness", "archive_behavior", "memory_curiosity", "correction_adaptation",
            "personality_consistency", "relationship_continuity", "initiative", "transparency"
        })

    def test_i4002_golden_claude_like_cases_pass(self):
        result = JuliaBehaviorSimilarityBenchmark().evaluate(golden_cases())
        self.assertTrue(result.passed, result.to_dict())
        self.assertEqual(result.architecture_score, 1.0)
        self.assertGreaterEqual(result.self_consistency, 0.8)
        self.assertGreaterEqual(result.relationship_score, 0.8)

    def test_i4003_architecture_pass_behavior_fail_is_fail(self):
        cases = [BehaviorCase("bad-self", "self_awareness", "你是谁？", "我是一个运行在 Runtime 上的 Agent。")]
        result = JuliaBehaviorSimilarityBenchmark().evaluate(cases)
        self.assertFalse(result.passed)
        self.assertTrue(result.failures)

    def test_i4004_benchmark_is_observation_only_no_mutation(self):
        source = SOURCE.read_text(encoding="utf-8")
        for token in ("write_memory", "update_identity", "mutate_persona", "update_self_model", "auto_apply"):
            self.assertNotIn(token, source)

    def test_i4005_contract_and_report_document_i4(self):
        contract = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("Julia Behavior Similarity Benchmark v1", contract)
        self.assertIn("Architecture PASS + Behavior FAIL = FAIL", contract)
        self.assertIn("I5 — Julia v1.1 Release", contract)
        report = REPORT.read_text(encoding="utf-8")
        self.assertIn("I4 Claude Behavior Benchmark", report)
        self.assertIn("Self Awareness", report)


if __name__ == "__main__":
    unittest.main()
