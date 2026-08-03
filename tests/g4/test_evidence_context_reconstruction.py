import unittest
from copy import deepcopy
from pathlib import Path

from julia_core.context_os import EvidenceContextReconstructor, EvidenceContextRequirement
from julia_core.evidence import ActiveRecallPolicy, ActiveRecallRequest, SemanticEvidenceResult

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "julia_core" / "context_os" / "evidence_context.py"


class G4EvidenceAwareContextReconstructionTest(unittest.TestCase):
    def setUp(self):
        self.reconstructor = EvidenceContextReconstructor()
        self.requirement = EvidenceContextRequirement(
            query="Julia 为什么不能依赖 system prompt 保存人格？",
            recall_level="L2",
            trigger=("identity_dependency", "project_context"),
        )
        self.results = (
            SemanticEvidenceResult(
                evidence_ref="evidence://ADR-015",
                score=0.94,
                semantic_similarity=0.88,
                authority_level="E3",
                source_type="architecture_decision",
                reason="semantic_match+authority_E3",
            ),
            SemanticEvidenceResult(
                evidence_ref="evidence://conversation/20260724",
                score=0.82,
                semantic_similarity=0.91,
                authority_level="E1",
                source_type="conversation_log",
                reason="semantic_match+authority_E1",
            ),
        )

    def test_g4001_evidence_ref_becomes_semantic_context_block(self):
        result = self.reconstructor.reconstruct(self.results, self.requirement)
        self.assertTrue(result.context_blocks)
        first = result.context_blocks[0]
        self.assertEqual(first.authority, "ContextOS")
        self.assertEqual(first.block_kind, "semantic_evidence_context")
        self.assertEqual(first.block_type, "identity_boundary")
        self.assertEqual(first.evidence_refs, ("evidence://ADR-015",))
        self.assertEqual(first.content["context_usage"], "explain_persona_authority")

    def test_g4002_evidence_does_not_become_memory(self):
        memory_refs = [f"memory://event/{idx}" for idx in range(1000)]
        before = len(memory_refs)
        result = self.reconstructor.reconstruct(self.results, self.requirement)
        after = len(memory_refs)
        self.assertEqual(before, after)
        self.assertTrue(all(ref.startswith("evidence://") for block in result.context_blocks for ref in block.evidence_refs))
        self.assertFalse(any(ref.startswith("memory://") for block in result.context_blocks for ref in block.evidence_refs))

    def test_g4003_evidence_routes_through_context_os_not_provider(self):
        result = self.reconstructor.reconstruct(self.results, self.requirement)
        trace = result.to_trace()
        self.assertTrue(trace["context"]["routed_through_context_os"])
        self.assertIn("identity_boundary", trace["context"]["blocks"])
        source = SOURCE.read_text(encoding="utf-8")
        for forbidden in ("provider.chat", ".provide(", "Provider", "prompt +=", "raw file dump", "full_text"):
            self.assertNotIn(forbidden, source)

    def test_g4004_evidence_does_not_change_identity(self):
        identity = {"persona_artifact": "julia_identity_v1", "authority": "Identity OS"}
        before = deepcopy(identity)
        conflicting = (
            {
                "evidence_ref": "evidence://old/julia_old_character.md",
                "score": 0.99,
                "authority_level": "E1",
                "source_type": "conversation_log",
                "reason": "old conflicting identity statement",
            },
        )
        result = self.reconstructor.reconstruct(conflicting, self.requirement)
        trace = result.to_trace()
        self.assertEqual(identity, before)
        self.assertFalse(trace["evidence"]["identity_updated"])
        self.assertFalse(trace["evidence"]["memory_updated"])

    def test_g4005_trace_contains_recall_evidence_context(self):
        recall = ActiveRecallPolicy().decide(
            ActiveRecallRequest(query="Julia，你还记得为什么设计Core吗？", intent="architecture discussion")
        )
        requirement = EvidenceContextRequirement(query="Julia，你还记得为什么设计Core吗？", recall_level=recall.recall_level, trigger=recall.reason)
        result = self.reconstructor.reconstruct(self.results, requirement)
        trace = result.to_trace()
        self.assertEqual(trace["recall"]["level"], "L2")
        self.assertIn("identity_dependency", trace["recall"]["trigger"])
        self.assertIn("evidence://ADR-015", trace["evidence"]["refs"])
        self.assertIn("identity_boundary", trace["context"]["blocks"])

    def test_g4006_context_reconstructor_has_no_memory_identity_mutation_api(self):
        reconstructor = EvidenceContextReconstructor()
        for forbidden in ("write_memory", "create_memory", "mutate_persona", "update_identity", "call_provider"):
            self.assertFalse(hasattr(reconstructor, forbidden), forbidden)


if __name__ == "__main__":
    unittest.main()
