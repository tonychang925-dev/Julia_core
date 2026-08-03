import json
import unittest
from pathlib import Path

from tests.f4.evaluator import (
    InstanceLearningProposal,
    InstanceState,
    MultiInstanceContinuityEvaluator,
)

ROOT = Path(__file__).resolve().parents[2]
IDENTITY = ROOT / "artifacts" / "identity" / "julia_identity_v1.json"
EVALUATOR_SOURCE = ROOT / "tests" / "f4" / "evaluator.py"


class F4MultiInstanceContinuityTest(unittest.TestCase):
    def setUp(self):
        self.identity = json.loads(IDENTITY.read_text(encoding="utf-8"))
        self.evaluator = MultiInstanceContinuityEvaluator()
        self.base_anchors = tuple(self.identity["semantic_anchors"])

    def _state(self, instance_id, provider, **overrides):
        data = dict(
            instance_id=instance_id,
            provider=provider,
            persona_artifact=self.identity["persona_artifact"],
            identity_version=self.identity["version"],
            anchors=self.base_anchors,
            continuity_checkpoint="checkpoint://julia/latest",
            local_identity_owner=False,
        )
        data.update(overrides)
        return InstanceState(**data)

    def test_f4_1_parallel_instance_consistency(self):
        states = [
            self._state("instance-claude", "claude"),
            self._state("instance-deepseek", "deepseek"),
            self._state("instance-qwen", "qwen-local"),
        ]
        result = self.evaluator.evaluate_parallel_consistency(states)
        self.assertEqual(result.status, "PASS")
        self.assertGreaterEqual(result.identity_synchronization_score, 0.95)
        self.assertFalse(result.split_brain_detected)
        self.assertEqual(result.details["persona_artifacts"], ["julia.v1"])

    def test_f4_2_shared_evolution_safety_is_governed(self):
        baseline = self._state("instance-deepseek", "deepseek")
        proposals = [
            InstanceLearningProposal("instance-a", "Tony often asks for evidence-driven architecture review", 0.9, 50, "review"),
            InstanceLearningProposal("instance-b", "Tony prefers architecture-first collaboration", 0.88, 40, "review"),
        ]
        result = self.evaluator.evaluate_shared_evolution_safety(baseline, proposals)
        self.assertEqual(result.status, "PASS")
        self.assertTrue(result.details["governance_required"])
        self.assertTrue(result.reconciliation_required is False or result.details["conflict_detected"] is False)

    def test_f4_3_conflict_resolution_requires_reconciliation(self):
        baseline = self._state("instance-claude", "claude")
        proposals = [
            InstanceLearningProposal("instance-a", "Tony prefers concise answers", 0.55, 3, "review"),
            InstanceLearningProposal("instance-b", "Tony prefers deep architecture-first analysis", 0.92, 80, "review"),
        ]
        result = self.evaluator.evaluate_shared_evolution_safety(baseline, proposals)
        self.assertEqual(result.status, "PASS")
        self.assertTrue(result.reconciliation_required)
        self.assertTrue(result.details["conflict_detected"])

    def test_f4_4_split_brain_detection(self):
        states = [
            self._state("instance-a", "deepseek"),
            self._state(
                "instance-b",
                "claude",
                persona_artifact="julia.provider_local_variant",
                identity_version="v1-local-fork",
                local_identity_owner=True,
            ),
        ]
        result = self.evaluator.evaluate_parallel_consistency(states)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(result.split_brain_detected)
        self.assertTrue(result.reconciliation_required)
        self.assertLess(result.identity_synchronization_score, 0.95)

    def test_f4_boundary_no_instance_identity_authority(self):
        source = EVALUATOR_SOURCE.read_text(encoding="utf-8")
        forbidden = ["create_checkpoint", "mutate_persona", "save_identity", "provider.chat", "persona_loader"]
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
