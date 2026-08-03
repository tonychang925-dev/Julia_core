import json
import tempfile
import unittest
from pathlib import Path

from julia_core.evidence import EvidenceScanner, SemanticEvidenceIndex, SemanticEvidenceRetriever

ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_SOURCE = ROOT / "julia_core" / "evidence" / "semantic_index.py"
RETRIEVER_SOURCE = ROOT / "julia_core" / "evidence" / "retriever.py"


class G2SemanticRetrievalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs").mkdir()
        (self.root / "conversations").mkdir()
        (self.root / "tmp").mkdir()
        (self.root / "docs" / "ADR-015-persona-artifact-authority-boundary.md").write_text(
            "# ADR-015 Architecture Decision\n"
            "Identity persistence must be externalized from provider prompt text. "
            "Julia persona survives context independence, compact, and provider migration by authority boundary.\n",
            encoding="utf-8",
        )
        (self.root / "conversations" / "conversation_20260724.jsonl").write_text(
            json.dumps(
                {
                    "text": "Tony asked about prompt persona memory and why a giant prompt might save Julia. "
                    "The chat mentions system prompt many times."
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.root / "tmp" / "scratch_prompt_note.txt").write_text(
            "temporary scratch prompt persona prompt prompt prompt", encoding="utf-8"
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _retriever(self):
        catalog = EvidenceScanner().scan([str(self.root)])
        index = SemanticEvidenceIndex.from_catalog(catalog)
        return SemanticEvidenceRetriever(index)

    def test_g2001_semantic_query_finds_meaning_match(self):
        result = self._retriever().retrieve("为什么 Julia 不应该依赖 system prompt 保存人格", top_k=3)
        self.assertEqual(result.status, "FOUND")
        self.assertTrue(result.results)
        refs = [item.evidence_ref for item in result.results]
        self.assertTrue(any("ADR-015" in ref for ref in refs))

    def test_g2002_authority_can_rank_adr_above_chat_log(self):
        result = self._retriever().retrieve("为什么 Julia 不应该依赖 system prompt 保存人格", top_k=3)
        self.assertEqual(result.results[0].source_type, "architecture_decision")
        self.assertEqual(result.results[0].authority_level, "E3")
        self.assertIn("authority_E3", result.results[0].reason)

    def test_g2003_embedding_record_does_not_store_full_text(self):
        catalog = EvidenceScanner().scan([str(self.root)])
        index = SemanticEvidenceIndex.from_catalog(catalog)
        serialized = index.to_dict()
        first = serialized["records"][0]
        self.assertIn("evidence_ref", first)
        self.assertIn("embedding_id", first)
        self.assertIn("content_hash", first)
        self.assertIn("vector", first)
        self.assertNotIn("content", first)
        self.assertNotIn("text", first)
        self.assertNotIn("body", first)

    def test_g2004_trace_is_grounding_not_identity_update(self):
        result = self._retriever().retrieve("identity externalization context independence", top_k=2)
        trace = result.to_trace(used_for_context=True)
        self.assertTrue(trace["evidence"]["used"])
        self.assertTrue(trace["evidence"]["refs"])
        self.assertEqual(trace["evidence"]["retrieval_mode"], "semantic")
        self.assertFalse(trace["evidence"]["memory_updated"])
        self.assertFalse(trace["evidence"]["identity_updated"])
        self.assertFalse(trace["evidence"]["raw_dump_injected"])

    def test_g2005_semantic_retrieval_has_no_memory_identity_mutation_path(self):
        source = SEMANTIC_SOURCE.read_text(encoding="utf-8") + RETRIEVER_SOURCE.read_text(encoding="utf-8")
        forbidden = ["MemoryRef(", "memory_writer", "create_checkpoint", "mutate_persona", "persona_loader", "identity_updated = True"]
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
