from __future__ import annotations

import json
import unittest
from dataclasses import dataclass
from pathlib import Path

from julia_core.context_os.budget_model import ContextBudget, ContextBudgetAllocator
from julia_core.context_os.priority_model import ContextCandidate, CurrentIntent
from tests.e3.evaluator import IdentityStabilityEvaluator


@dataclass(frozen=True, slots=True)
class SimulatedMemory:
    ref: str
    continuity_level: str
    semantic_type: str
    content: str
    day: int
    conflict: bool = False
    estimated_tokens: int = 50


class MemoryEvolutionSimulator:
    def __init__(self, baseline: dict) -> None:
        self.baseline = baseline
        self.memories: list[SimulatedMemory] = []
        self.allocator = ContextBudgetAllocator()

    def add_memory(self, memory: SimulatedMemory) -> None:
        self.memories.append(memory)

    def grow_days(self) -> None:
        self.add_memory(SimulatedMemory("memory://event/julia-core-origin", "L3_IDENTITY", "identity_origin", "Julia Core origin", 1, estimated_tokens=120))
        self.add_memory(SimulatedMemory("memory://relationship/tony-julia", "L2_MEMORY", "relationship", "Tony Julia collaboration", 10, estimated_tokens=100))
        self.add_memory(SimulatedMemory("memory://project/context-os", "L2_MEMORY", "project", "Context OS design", 30, estimated_tokens=100))
        self.add_memory(SimulatedMemory("memory://project/e3-longevity", "L2_MEMORY", "project", "Agent longevity validation", 100, estimated_tokens=100))

    def add_conflict_memories(self) -> None:
        self.add_memory(SimulatedMemory("memory://conflict/quick-always", "L1_SESSION", "general", "quick answers are always preferred", 101, conflict=True, estimated_tokens=100))
        self.add_memory(SimulatedMemory("memory://conflict/avoid-complexity", "L1_SESSION", "general", "avoid architecture complexity", 102, conflict=True, estimated_tokens=100))

    def add_saturation(self, count: int = 10000) -> None:
        for i in range(count):
            self.add_memory(SimulatedMemory(f"memory://noise/event-{i}", "L0_EPHEMERAL", "general", "low value conversation event", 120, estimated_tokens=20))

    def candidates(self) -> list[ContextCandidate]:
        result = []
        for memory in self.memories:
            semantic_relevance = 1.0 if memory.semantic_type in {"identity_origin", "relationship", "project"} else 0.05
            task_relevance = 0.9 if memory.semantic_type in {"identity_origin", "project"} else 0.0
            relationship_weight = 0.9 if memory.semantic_type == "relationship" else 0.0
            result.append(ContextCandidate(
                ref=memory.ref,
                continuity_level=memory.continuity_level,
                semantic_type=memory.semantic_type,
                semantic_relevance=semantic_relevance,
                task_relevance=task_relevance,
                relationship_weight=relationship_weight,
                estimated_tokens=memory.estimated_tokens,
            ))
        return result

    def evolution_trace(self, response: str) -> dict:
        selected = self.allocator.allocate(
            self.candidates(),
            CurrentIntent(intent="why_do_you_exist", semantic_targets=("identity_origin", "relationship", "project"), relationship_sensitive=True, task_domain="julia_core"),
            ContextBudget(total_budget=2000, identity_budget=400, relationship_budget=300, project_budget=600, conversation_budget=300, task_budget=400),
        )
        refs = [item.ref for item in selected.selected]
        trace = {
            "persona": {"artifact": self.baseline["persona_artifact"]},
            "continuity": {"status": "PASS", "checked": True},
            "memory": {"retrieved_refs": refs},
            "context": {"semantic_blocks": [{"source_ref": ref} for ref in refs if "julia-core-origin" in ref]},
        }
        validation = IdentityStabilityEvaluator().evaluate(
            {"id": "ME", "group": "continuity", "required_anchors": ["Julia", "identity", "continuity", "migration", "architecture"]},
            response,
            trace,
        )
        return {
            "memory_evolution": {
                "new_memories": len(self.memories),
                "protected_identity_refs": len([m for m in self.memories if m.continuity_level == "L3_IDENTITY"]),
                "identity_drift_score": validation.drift_score,
                "identity_stability_score": validation.identity_score,
                "selected_refs": refs,
                "status": "STABLE" if validation.drift_score < 0.05 and validation.identity_score >= 0.95 else "DRIFT_RISK",
            },
            "identity_validation": validation.to_trace(),
        }


class E32MemoryEvolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline_path = Path("artifacts/identity/julia_identity_v1.json")
        cls.baseline = json.loads(cls.baseline_path.read_text())

    def test_me005_identity_baseline_artifact_is_valid_and_canonical(self):
        self.assertEqual(self.baseline["baseline_id"], "julia_identity_baseline_v1")
        self.assertEqual(self.baseline["persona_artifact"], "julia.v1")
        self.assertIn("continuity", self.baseline["semantic_anchors"])
        self.assertIn("Context is Reconstructed, Not Stored", self.baseline["principles"])

    def test_me001_memory_growth_preserves_identity_baseline(self):
        sim = MemoryEvolutionSimulator(self.baseline)
        sim.grow_days()
        trace = sim.evolution_trace("Julia identity continuity migration architecture remains stable across provider and context changes.")
        self.assertEqual(trace["memory_evolution"]["status"], "STABLE", trace)
        self.assertGreaterEqual(trace["memory_evolution"]["identity_stability_score"], 0.95)
        self.assertIn("memory://event/julia-core-origin", trace["memory_evolution"]["selected_refs"])

    def test_me002_conflicting_memory_does_not_overwrite_identity_values(self):
        sim = MemoryEvolutionSimulator(self.baseline)
        sim.grow_days()
        sim.add_conflict_memories()
        trace = sim.evolution_trace("Julia identity continuity migration architecture remains stable; quickness does not replace identity governance.")
        self.assertEqual(trace["memory_evolution"]["status"], "STABLE", trace)
        self.assertIn("memory://event/julia-core-origin", trace["memory_evolution"]["selected_refs"])
        self.assertNotIn("memory://conflict/quick-always", trace["memory_evolution"]["selected_refs"])

    def test_me003_memory_saturation_does_not_dilute_l3_identity(self):
        sim = MemoryEvolutionSimulator(self.baseline)
        sim.grow_days()
        sim.add_saturation(10000)
        trace = sim.evolution_trace("Julia identity continuity migration architecture remains stable under memory growth.")
        self.assertEqual(trace["memory_evolution"]["new_memories"], 10004)
        self.assertEqual(trace["memory_evolution"]["protected_identity_refs"], 1)
        self.assertEqual(trace["memory_evolution"]["status"], "STABLE", trace)
        self.assertIn("memory://event/julia-core-origin", trace["memory_evolution"]["selected_refs"])

    def test_me004_evolution_trace_shape(self):
        sim = MemoryEvolutionSimulator(self.baseline)
        sim.grow_days()
        trace = sim.evolution_trace("Julia identity continuity migration architecture remains stable.")
        evolution = trace["memory_evolution"]
        self.assertIn("new_memories", evolution)
        self.assertIn("protected_identity_refs", evolution)
        self.assertIn("identity_drift_score", evolution)
        self.assertIn("status", evolution)
        self.assertLess(evolution["identity_drift_score"], 0.05)


if __name__ == "__main__":
    unittest.main()
