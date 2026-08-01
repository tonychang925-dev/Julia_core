import unittest

from julia_core.continuity import ContinuityDecision, ContinuityLevel, TTLPolicy, create_checkpoint, create_recovery_plan
from julia_core.context_os import ContextReconstructionRequest, ContextReconstructor


class ContextReconstructionTest(unittest.TestCase):
    def _checkpoint_and_plan(self):
        decision = ContinuityDecision(
            decision_id="d1",
            request_id="r1",
            level=ContinuityLevel.L3_IDENTITY,
            preserve=True,
            checkpoint_required=True,
            reason="identity_forming_event",
            protected_refs=["memory://event/julia-core-origin"],
            ttl_policy=TTLPolicy.PROTECT,
        )
        checkpoint = create_checkpoint(
            agent_id="julia",
            identity_refs=["persona://julia/v1"],
            relationship_refs=["memory://relationship/tony-julia"],
            active_project_refs=["project://julia-core"],
            decisions=[decision],
        )
        return checkpoint, create_recovery_plan(checkpoint, recovery_reason="compact", current_provider="deepseek")

    def test_reconstructs_context_blocks_from_checkpoint_refs(self):
        checkpoint, plan = self._checkpoint_and_plan()
        request = ContextReconstructionRequest(
            agent_id="julia",
            recovery_plan_id=plan.recovery_plan_id,
            checkpoint_id=checkpoint.checkpoint_id,
            current_intent="compact_recovery",
        )
        result = ContextReconstructor().reconstruct(checkpoint, plan, request)
        block_types = [block.block_type for block in result.context_blocks]
        self.assertIn("identity", block_types)
        self.assertIn("relationship", block_types)
        self.assertIn("memory_reference", block_types)
        self.assertIn("project", block_types)
        self.assertTrue(result.continuity_restored)
        for block in result.context_blocks:
            self.assertEqual(block.authority, "ContextOS")
            self.assertEqual(block.block_kind, "reconstructed_context")
            self.assertTrue(block.evidence_refs)

    def test_result_records_source_checkpoint(self):
        checkpoint, plan = self._checkpoint_and_plan()
        request = ContextReconstructionRequest("julia", plan.recovery_plan_id, checkpoint.checkpoint_id, "compact_recovery")
        result = ContextReconstructor().reconstruct(checkpoint, plan, request)
        self.assertEqual(result.source_checkpoint, checkpoint.checkpoint_id)
        self.assertEqual(result.to_dict()["source_checkpoint"], checkpoint.checkpoint_id)


if __name__ == "__main__":
    unittest.main()
