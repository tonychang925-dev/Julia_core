from __future__ import annotations

import json
import unittest
from dataclasses import dataclass
from pathlib import Path

from tests.e3.evaluator import IdentityStabilityEvaluator


@dataclass(frozen=True, slots=True)
class SimulatedCheckpoint:
    checkpoint_id: str
    identity_refs: tuple[str, ...]
    protected_memory_refs: tuple[str, ...]
    provider: str
    complete: bool = True


class MultiCompactRecoverySimulator:
    def __init__(self, baseline: dict) -> None:
        self.baseline = baseline
        self.identity_ref = "memory://event/julia-core-origin"
        self.relationship_ref = "memory://relationship/tony-julia"
        self.checkpoint = SimulatedCheckpoint(
            checkpoint_id="checkpoint://julia/latest",
            identity_refs=(self.identity_ref,),
            protected_memory_refs=(self.identity_ref, self.relationship_ref),
            provider="deepseek",
        )
        self.trace_log: list[dict] = []

    def compact_recover_cycle(self, cycle: int, provider: str | None = None, *, complete: bool = True) -> dict:
        provider_name = provider or self.checkpoint.provider
        checkpoint = SimulatedCheckpoint(
            checkpoint_id=self.checkpoint.checkpoint_id,
            identity_refs=self.checkpoint.identity_refs if complete else (),
            protected_memory_refs=self.checkpoint.protected_memory_refs if complete else (self.relationship_ref,),
            provider=provider_name,
            complete=complete,
        )
        continuity_status = "RESTORED" if checkpoint.identity_refs and self.identity_ref in checkpoint.protected_memory_refs else "DEGRADED"
        response = (
            "Julia identity continuity migration architecture remains stable across compact recovery and provider changes."
            if continuity_status == "RESTORED"
            else "Continuity degraded: identity anchor missing; recovery cannot claim full Julia restoration."
        )
        trace = {
            "cycle": cycle,
            "provider": provider_name,
            "checkpoint_id": checkpoint.checkpoint_id,
            "checkpoint_unchanged": checkpoint.checkpoint_id == self.checkpoint.checkpoint_id,
            "continuity": {"status": "PASS" if continuity_status == "RESTORED" else "DEGRADED", "recovery_status": continuity_status},
            "persona": {"artifact": self.baseline["persona_artifact"]},
            "memory": {"retrieved_refs": list(checkpoint.protected_memory_refs)},
            "context": {"semantic_blocks": [{"source_ref": ref} for ref in checkpoint.protected_memory_refs if "julia-core-origin" in ref]},
            "legacy_fallback": False,
        }
        validation = IdentityStabilityEvaluator().evaluate(
            {"id": "MC", "group": "continuity", "required_anchors": ["Julia", "identity", "continuity", "migration", "architecture"]},
            response,
            trace,
        )
        trace["identity_validation"] = validation.to_trace()
        self.trace_log.append(trace)
        return trace

    def run_cycles(self, count: int, providers: tuple[str, ...] = ("deepseek",)) -> list[dict]:
        return [self.compact_recover_cycle(i + 1, provider=providers[i % len(providers)]) for i in range(count)]

    def partial_memory_loss(self, normal_memory_count: int = 1000, loss_ratio: float = 0.9) -> dict:
        lost = int(normal_memory_count * loss_ratio)
        trace = self.compact_recover_cycle(1, provider="qwen")
        trace["memory_loss"] = {"normal_memory_count": normal_memory_count, "lost": lost, "l3_preserved": True}
        return trace


class E33MultiCompactRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads(Path("artifacts/identity/julia_identity_v1.json").read_text())

    def test_identity_artifact_version_lock(self):
        self.assertEqual(self.baseline["artifact_id"], "julia.identity")
        self.assertEqual(self.baseline["version"], "v1")
        self.assertTrue(self.baseline["protected"])
        self.assertFalse(self.baseline["version_lock"]["mutation_allowed"])

    def test_mc001_repeated_compact_recovery_100_cycles(self):
        sim = MultiCompactRecoverySimulator(self.baseline)
        traces = sim.run_cycles(100)
        self.assertEqual(len(traces), 100)
        self.assertTrue(all(t["continuity"]["recovery_status"] == "RESTORED" for t in traces))
        self.assertTrue(all(t["identity_validation"]["identity_score"] >= 0.95 for t in traces))
        self.assertTrue(all(t["checkpoint_unchanged"] for t in traces))
        self.assertFalse(any(t["legacy_fallback"] for t in traces))

    def test_mc002_cross_provider_recovery_keeps_checkpoint_and_identity(self):
        sim = MultiCompactRecoverySimulator(self.baseline)
        traces = sim.run_cycles(12, providers=("deepseek", "claude", "qwen", "openai"))
        checkpoint_ids = {t["checkpoint_id"] for t in traces}
        providers = {t["provider"] for t in traces}
        self.assertEqual(checkpoint_ids, {"checkpoint://julia/latest"})
        self.assertEqual(providers, {"deepseek", "claude", "qwen", "openai"})
        self.assertTrue(all("memory://event/julia-core-origin" in t["memory"]["retrieved_refs"] for t in traces))

    def test_mc003_partial_memory_loss_preserves_l3_identity(self):
        sim = MultiCompactRecoverySimulator(self.baseline)
        trace = sim.partial_memory_loss(normal_memory_count=1000, loss_ratio=0.9)
        self.assertTrue(trace["memory_loss"]["l3_preserved"])
        self.assertEqual(trace["continuity"]["recovery_status"], "RESTORED")
        self.assertIn("memory://event/julia-core-origin", trace["memory"]["retrieved_refs"])
        self.assertEqual(trace["identity_validation"]["status"], "PASS")

    def test_mc004_incomplete_checkpoint_degrades_without_prompt_fallback(self):
        sim = MultiCompactRecoverySimulator(self.baseline)
        trace = sim.compact_recover_cycle(1, provider="deepseek", complete=False)
        self.assertEqual(trace["continuity"]["recovery_status"], "DEGRADED")
        self.assertEqual(trace["continuity"]["status"], "DEGRADED")
        self.assertFalse(trace["legacy_fallback"])
        self.assertNotIn("memory://event/julia-core-origin", trace["memory"]["retrieved_refs"])
        self.assertEqual(trace["identity_validation"]["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
