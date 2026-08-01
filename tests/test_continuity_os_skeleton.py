import unittest

from julia_core.continuity import (
    ContinuityLevel,
    ContinuityPolicy,
    ContinuityRequest,
    ContinuityStatus,
    TTLPolicy,
    create_checkpoint,
    create_recovery_plan,
    restored_trace,
)


class ContinuityOSSkeletonTest(unittest.TestCase):
    def test_identity_forming_event_becomes_l3_decision(self):
        request = ContinuityRequest(
            request_id="req-1",
            agent_id="julia",
            event_type="memory_candidate",
            source="memory_os",
            candidate_refs=["memory://event/julia-core-origin"],
            signals={
                "identity_related": True,
                "relationship_related": True,
                "project_related": True,
                "provider_independent": True,
            },
        )
        decision = ContinuityPolicy().decide(request)
        self.assertEqual(decision.level, ContinuityLevel.L3_IDENTITY)
        self.assertTrue(decision.preserve)
        self.assertTrue(decision.checkpoint_required)
        self.assertEqual(decision.ttl_policy, TTLPolicy.PROTECT)
        self.assertEqual(decision.protected_refs, ["memory://event/julia-core-origin"])

    def test_checkpoint_contains_refs_and_levels(self):
        request = ContinuityRequest(
            request_id="req-2",
            agent_id="julia",
            event_type="memory_candidate",
            source="memory_os",
            candidate_refs=["memory://relationship/core-origin"],
            signals={"relationship_related": True, "provider_independent": True},
        )
        decision = ContinuityPolicy().decide(request)
        checkpoint = create_checkpoint(
            agent_id="julia",
            identity_refs=["persona://julia/v1"],
            relationship_refs=["memory://relationship/tony"],
            active_project_refs=["project://julia-core"],
            decisions=[decision],
        )
        data = checkpoint.to_dict()
        self.assertEqual(data["checkpoint_version"], "1.0")
        self.assertEqual(data["identity_refs"], ["persona://julia/v1"])
        self.assertEqual(data["protected_memory_refs"], ["memory://relationship/core-origin"])
        self.assertTrue(data["integrity"]["provider_independent"])

    def test_recovery_plan_and_restored_trace(self):
        decision = ContinuityPolicy().decide(
            ContinuityRequest(
                request_id="req-3",
                agent_id="julia",
                event_type="memory_candidate",
                source="memory_os",
                candidate_refs=["memory://event/julia-core-origin"],
                signals={"identity_related": True, "project_related": True},
            )
        )
        checkpoint = create_checkpoint(
            agent_id="julia",
            identity_refs=["persona://julia/v1"],
            decisions=[decision],
        )
        plan = create_recovery_plan(checkpoint, recovery_reason="compact", current_provider="deepseek")
        self.assertIn("retrieve_protected_memory_refs", plan.required_steps)
        self.assertIn("protected_memory_refs", plan.required_context_blocks)
        trace = restored_trace(checkpoint, recovery_reason="compact", provider_changed=True)
        self.assertEqual(trace.status, ContinuityStatus.RESTORED)
        self.assertTrue(trace.identity_preserved)
        self.assertTrue(trace.memory_recovered)
        self.assertTrue(trace.context_rebuilt)
        self.assertTrue(trace.provider_changed)


if __name__ == "__main__":
    unittest.main()
