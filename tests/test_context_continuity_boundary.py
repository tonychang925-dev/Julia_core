import unittest

from julia_core.continuity import ContinuityDecision, ContinuityLevel, TTLPolicy, create_checkpoint, create_recovery_plan
from julia_core.context_os import ContextRequirement, ContextPriority, ContextReconstructionRequest, ContextReconstructor


class ContextContinuityBoundaryTest(unittest.TestCase):
    def test_context_requirement_accepts_refs_only(self):
        with self.assertRaises(ValueError):
            ContextRequirement("memory_reference", "memory", ContextPriority.CRITICAL, ("raw 50000 token history dump",))

    def test_reconstruction_does_not_mutate_checkpoint(self):
        decision = ContinuityDecision(
            "d1", "r1", ContinuityLevel.L3_IDENTITY, True, True, "identity", ["memory://event/origin"], TTLPolicy.PROTECT
        )
        checkpoint = create_checkpoint(agent_id="julia", identity_refs=["persona://julia/v1"], decisions=[decision])
        before = checkpoint.to_dict()
        plan = create_recovery_plan(checkpoint, recovery_reason="compact")
        request = ContextReconstructionRequest("julia", plan.recovery_plan_id, checkpoint.checkpoint_id, "compact_recovery")
        ContextReconstructor().reconstruct(checkpoint, plan, request)
        self.assertEqual(before, checkpoint.to_dict())

    def test_reconstructor_does_not_expose_memory_write_or_provider_api(self):
        reconstructor = ContextReconstructor()
        for forbidden in ["write_memory", "save_memory", "call_llm", "generate", "update_continuity", "promote_identity"]:
            self.assertFalse(hasattr(reconstructor, forbidden))


if __name__ == "__main__":
    unittest.main()
