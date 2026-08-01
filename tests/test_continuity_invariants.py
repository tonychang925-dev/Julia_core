import unittest

from julia_core.continuity import ContinuityPolicy, ContinuityRequest, create_checkpoint


class ContinuityInvariantsTest(unittest.TestCase):
    def test_continuity_policy_does_not_expose_memory_write_api(self):
        policy = ContinuityPolicy()
        self.assertFalse(hasattr(policy, "save_memory"))
        self.assertFalse(hasattr(policy, "write_memory"))
        self.assertFalse(hasattr(policy, "persist_memory"))

    def test_continuity_policy_does_not_expose_persona_mutation_api(self):
        policy = ContinuityPolicy()
        self.assertFalse(hasattr(policy, "update_persona"))
        self.assertFalse(hasattr(policy, "mutate_persona"))
        self.assertFalse(hasattr(policy, "set_identity"))

    def test_continuity_policy_does_not_call_provider(self):
        policy = ContinuityPolicy()
        self.assertFalse(hasattr(policy, "call_llm"))
        self.assertFalse(hasattr(policy, "generate"))
        self.assertFalse(hasattr(policy, "provider"))

    def test_checkpoint_rejects_raw_memory_content(self):
        decision = ContinuityPolicy().decide(
            ContinuityRequest(
                request_id="req-raw",
                agent_id="julia",
                event_type="memory_candidate",
                source="memory_os",
                candidate_refs=["raw conversation text without ref scheme"],
                signals={"identity_related": True, "project_related": True},
            )
        )
        with self.assertRaises(ValueError):
            create_checkpoint(agent_id="julia", identity_refs=["persona://julia/v1"], decisions=[decision])

    def test_checkpoint_accepts_refs_only(self):
        decision = ContinuityPolicy().decide(
            ContinuityRequest(
                request_id="req-ref",
                agent_id="julia",
                event_type="memory_candidate",
                source="memory_os",
                candidate_refs=["memory://event/julia-core-origin"],
                signals={"identity_related": True, "project_related": True},
            )
        )
        checkpoint = create_checkpoint(agent_id="julia", identity_refs=["persona://julia/v1"], decisions=[decision])
        self.assertIn("memory://event/julia-core-origin", checkpoint.protected_memory_refs)


if __name__ == "__main__":
    unittest.main()
