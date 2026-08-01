import unittest

from julia_core.continuity import (
    ContinuityLevel,
    MemoryContinuityBinder,
    MemoryImportance,
    create_checkpoint,
    request_from_memory_ref,
)
from julia_core.continuity.contracts import ContinuityDecision, TTLPolicy


class MemoryContinuityBindingTest(unittest.TestCase):
    def test_identity_forming_memory_ref_becomes_l3_eligible(self):
        binder = MemoryContinuityBinder()
        request = request_from_memory_ref(
            agent_id="julia",
            memory_ref="memory://event/julia-core-origin",
            memory_type="project",
            importance=MemoryImportance.CRITICAL,
            signals={
                "identity_related": True,
                "relationship_related": True,
                "project_related": True,
                "provider_independent": True,
            },
        )
        decision = binder.decide(request)
        protected = binder.protect(decision)
        self.assertTrue(decision.eligible)
        self.assertEqual(decision.level, ContinuityLevel.L3_IDENTITY)
        self.assertEqual(protected.ref, "memory://event/julia-core-origin")

    def test_ordinary_lunch_memory_does_not_become_l3(self):
        binder = MemoryContinuityBinder()
        request = request_from_memory_ref(
            agent_id="julia",
            memory_ref="memory://lunch/today",
            memory_type="episodic",
            importance=MemoryImportance.LOW,
            signals={"provider_independent": False},
        )
        decision = binder.decide(request)
        self.assertFalse(decision.eligible)
        self.assertNotEqual(decision.level, ContinuityLevel.L3_IDENTITY)
        self.assertIsNone(binder.protect(decision))

    def test_checkpoint_uses_protected_refs_only(self):
        binder = MemoryContinuityBinder()
        request = request_from_memory_ref(
            agent_id="julia",
            memory_ref="memory://event/julia-core-origin",
            memory_type="project",
            importance=MemoryImportance.CRITICAL,
            signals={"identity_related": True, "project_related": True, "provider_independent": True},
        )
        eligibility = binder.decide(request)
        protected = binder.protect(eligibility)
        continuity_decision = ContinuityDecision(
            decision_id="decision-from-protected-ref",
            request_id=request.request_id,
            level=protected.level,
            preserve=True,
            checkpoint_required=True,
            reason=protected.reason,
            protected_refs=[protected.ref],
            ttl_policy=TTLPolicy.PROTECT,
        )
        checkpoint = create_checkpoint(agent_id="julia", identity_refs=["persona://julia/v1"], decisions=[continuity_decision])
        self.assertEqual(checkpoint.protected_memory_refs, ["memory://event/julia-core-origin"])
        self.assertNotIn("Tony said", str(checkpoint.to_dict()))

    def test_binding_accepts_refs_only(self):
        binder = MemoryContinuityBinder()
        request = request_from_memory_ref(
            agent_id="julia",
            memory_ref="raw memory content",
            memory_type="project",
        )
        with self.assertRaises(ValueError):
            binder.decide(request)


if __name__ == "__main__":
    unittest.main()
