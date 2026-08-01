import unittest

from julia_core.continuity import (
    MemoryContinuityBinder,
    MemoryImportance,
    ContinuityDecision,
    TTLPolicy,
    create_checkpoint,
    create_recovery_plan,
    request_from_memory_ref,
    restored_trace,
)
from julia_core.context_os import ContextReconstructionRequest, ContextReconstructor
from julia_core.continuity import ContinuityLevel, ContinuityStatus


class CompactSurvivalHarness:
    def __init__(self):
        self.session_state = {
            "conversation_history": [
                "Tony created Julia Core to achieve cross-model continuity.",
                "Julia identity should not depend on Claude compact windows.",
            ],
            "temporary_context": ["current debugging details", "provider-specific formatting"],
            "provider": "deepseek",
        }
        self.provider_calls = 0

    def build_identity_state(self):
        request = request_from_memory_ref(
            agent_id="julia",
            memory_ref="memory://event/julia-core-origin",
            memory_type="project",
            importance=MemoryImportance.CRITICAL,
            signals={
                "identity_related": True,
                "relationship_related": True,
                "project_related": True,
                "recurring": True,
                "provider_independent": True,
            },
        )
        eligibility = MemoryContinuityBinder().decide(request)
        protected = MemoryContinuityBinder().protect(eligibility)
        decision = ContinuityDecision(
            decision_id="compact-survival-decision",
            request_id=request.request_id,
            level=protected.level,
            preserve=True,
            checkpoint_required=True,
            reason=protected.reason,
            protected_refs=[protected.ref],
            ttl_policy=TTLPolicy.PROTECT,
        )
        checkpoint = create_checkpoint(
            agent_id="julia",
            identity_refs=["persona://julia/v1"],
            relationship_refs=["memory://relationship/tony-julia"],
            active_project_refs=["project://julia-core"],
            decisions=[decision],
            checkpoint_id="continuity://checkpoint/julia/compact-survival-test",
        )
        return eligibility, checkpoint

    def compact(self):
        self.session_state["conversation_history"] = []
        self.session_state["temporary_context"] = []

    def recover(self, checkpoint, *, provider="mock-provider"):
        old_provider = self.session_state["provider"]
        self.session_state["provider"] = provider
        plan = create_recovery_plan(checkpoint, recovery_reason="compact", current_provider=provider)
        request = ContextReconstructionRequest(
            agent_id="julia",
            recovery_plan_id=plan.recovery_plan_id,
            checkpoint_id=checkpoint.checkpoint_id,
            current_intent="compact_recovery",
        )
        context = ContextReconstructor().reconstruct(checkpoint, plan, request)
        trace = restored_trace(checkpoint, recovery_reason="compact", provider_changed=(old_provider != provider))
        return plan, context, trace

    def call_provider(self):
        self.provider_calls += 1
        raise AssertionError("Compact survival proof must not call provider")


class CompactSurvivalTest(unittest.TestCase):
    def test_compact_survival_end_to_end_architecture_proof(self):
        harness = CompactSurvivalHarness()

        eligibility, checkpoint = harness.build_identity_state()
        self.assertTrue(eligibility.eligible)
        self.assertEqual(eligibility.level, ContinuityLevel.L3_IDENTITY)
        self.assertEqual(checkpoint.identity_refs, ["persona://julia/v1"])
        self.assertEqual(checkpoint.protected_memory_refs, ["memory://event/julia-core-origin"])
        self.assertNotIn("Tony created Julia Core", str(checkpoint.to_dict()))

        harness.compact()
        self.assertEqual(harness.session_state["conversation_history"], [])
        self.assertEqual(harness.session_state["temporary_context"], [])

        plan, context, trace = harness.recover(checkpoint, provider="mock-provider")
        self.assertIn("retrieve_protected_memory_refs", plan.required_steps)
        self.assertTrue(context.continuity_restored)
        self.assertIn("identity", [block.block_type for block in context.context_blocks])
        self.assertIn("memory_reference", [block.block_type for block in context.context_blocks])
        self.assertEqual(trace.status, ContinuityStatus.RESTORED)
        self.assertTrue(trace.identity_preserved)
        self.assertTrue(trace.memory_recovered)
        self.assertTrue(trace.context_rebuilt)
        self.assertTrue(trace.provider_changed)
        self.assertEqual(harness.provider_calls, 0)

    def test_provider_switch_does_not_change_continuity_checkpoint(self):
        harness = CompactSurvivalHarness()
        _eligibility, checkpoint = harness.build_identity_state()
        before = checkpoint.to_dict()
        harness.compact()
        harness.recover(checkpoint, provider="mock-provider")
        self.assertEqual(before, checkpoint.to_dict())


if __name__ == "__main__":
    unittest.main()
