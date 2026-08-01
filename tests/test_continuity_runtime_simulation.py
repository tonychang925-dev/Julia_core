import unittest

from julia_core.continuity import (
    ContinuityLevel,
    ContinuityPolicy,
    ContinuityRequest,
    ContinuityStatus,
    create_checkpoint,
    create_recovery_plan,
    restored_trace,
)


class SimulatedAgentLifecycle:
    """Simulation harness; intentionally not real Runtime integration."""

    def __init__(self, *, provider="deepseek"):
        self.agent_id = "julia"
        self.provider = provider
        self.session_state = {
            "turns": [
                "Tony and Julia discussed why Julia Core exists for cross-model continuity."
            ]
        }
        self.provider_calls = 0
        self.policy = ContinuityPolicy()

    def classify_origin_event(self):
        request = ContinuityRequest(
            request_id="sim-req-origin",
            agent_id=self.agent_id,
            event_type="conversation",
            source="session",
            candidate_refs=["memory://event/julia-core-origin"],
            signals={
                "identity_related": True,
                "relationship_related": True,
                "project_related": True,
                "recurring": True,
                "provider_independent": True,
            },
            current_context={"provider": self.provider, "session_id": "sim-session"},
        )
        return self.policy.decide(request)

    def checkpoint(self, decision):
        return create_checkpoint(
            agent_id=self.agent_id,
            identity_refs=["persona://julia/v1"],
            relationship_refs=["memory://relationship/tony-julia"],
            active_project_refs=["project://julia-core"],
            decisions=[decision],
            checkpoint_id="continuity://checkpoint/julia/simulation",
        )

    def compact(self):
        self.session_state = {"turns": []}

    def recover(self, checkpoint, *, provider="gpt"):
        self.provider = provider
        plan = create_recovery_plan(checkpoint, recovery_reason="compact", current_provider=provider)
        trace = restored_trace(checkpoint, recovery_reason="compact", provider_changed=True)
        return plan, trace

    def call_provider(self):
        self.provider_calls += 1
        raise AssertionError("simulation must not call provider")


class ContinuityRuntimeSimulationTest(unittest.TestCase):
    def test_identity_survives_compact_simulation(self):
        sim = SimulatedAgentLifecycle(provider="deepseek")
        decision = sim.classify_origin_event()
        self.assertEqual(decision.level, ContinuityLevel.L3_IDENTITY)
        checkpoint = sim.checkpoint(decision)

        sim.compact()
        self.assertEqual(sim.session_state["turns"], [])

        plan, trace = sim.recover(checkpoint, provider="gpt")
        self.assertIn("load_identity_refs", plan.required_steps)
        self.assertEqual(trace.status, ContinuityStatus.RESTORED)
        self.assertTrue(trace.identity_preserved)
        self.assertTrue(trace.memory_recovered)
        self.assertTrue(trace.context_rebuilt)

    def test_checkpoint_refs_are_not_raw_content(self):
        sim = SimulatedAgentLifecycle()
        checkpoint = sim.checkpoint(sim.classify_origin_event())
        data = checkpoint.to_dict()
        self.assertEqual(data["identity_refs"], ["persona://julia/v1"])
        self.assertEqual(data["protected_memory_refs"], ["memory://event/julia-core-origin"])
        serialized = str(data)
        self.assertNotIn("Tony and Julia discussed why Julia Core exists", serialized)

    def test_recovery_does_not_call_provider(self):
        sim = SimulatedAgentLifecycle()
        checkpoint = sim.checkpoint(sim.classify_origin_event())
        sim.compact()
        sim.recover(checkpoint, provider="gpt")
        self.assertEqual(sim.provider_calls, 0)

    def test_provider_replacement_does_not_change_checkpoint(self):
        sim = SimulatedAgentLifecycle(provider="deepseek")
        checkpoint_before = sim.checkpoint(sim.classify_origin_event())
        before_identity = list(checkpoint_before.identity_refs)
        before_memory = list(checkpoint_before.protected_memory_refs)

        sim.compact()
        plan, trace = sim.recover(checkpoint_before, provider="gpt")

        self.assertEqual(before_identity, checkpoint_before.identity_refs)
        self.assertEqual(before_memory, checkpoint_before.protected_memory_refs)
        self.assertEqual(plan.provider_constraints["current_provider"], "gpt")
        self.assertTrue(trace.provider_changed)


if __name__ == "__main__":
    unittest.main()
