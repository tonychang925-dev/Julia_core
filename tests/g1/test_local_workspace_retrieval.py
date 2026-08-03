import json
import tempfile
import unittest
from pathlib import Path

from julia_core.evidence.local_retrieval import EvidenceScanner, LocalEvidenceRetriever, RetrievalRequest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "julia_core" / "evidence" / "local_retrieval.py"


class G1LocalWorkspaceRetrievalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs").mkdir()
        (self.root / "conversations").mkdir()
        (self.root / "code").mkdir()
        (self.root / "docs" / "ADR-009.md").write_text(
            "# ADR-009 Continuity OS\nJulia Core added Continuity OS because identity must survive compact and provider migration.\n",
            encoding="utf-8",
        )
        (self.root / "conversations" / "20260724.jsonl").write_text(
            json.dumps({"text": "Tony and Julia discussed why Continuity OS protects identity."}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (self.root / "facts.json").write_text(json.dumps({"topic": "Julia Core identity"}), encoding="utf-8")
        (self.root / "notes.txt").write_text("Context is reconstructed, not stored.", encoding="utf-8")
        (self.root / "code" / "continuity.py").write_text("class ContinuityOS: pass\n", encoding="utf-8")
        (self.root / "ignored.bin").write_bytes(b"ignore")

    def tearDown(self):
        self.tmp.cleanup()

    def test_g1001_evidence_scanner_catalogs_supported_files(self):
        entries = EvidenceScanner().scan([str(self.root)])
        file_types = {entry.file_type for entry in entries}
        self.assertEqual(file_types, {".md", ".json", ".jsonl", ".txt", ".py"})
        self.assertTrue(all(entry.evidence_id.startswith("evidence://file/") for entry in entries))

    def test_g1002_retrieval_returns_evidence_refs(self):
        request = RetrievalRequest(
            query="why Continuity OS identity provider migration",
            intent="historical_event_lookup",
            allowed_roots=(str(self.root),),
            max_results=3,
        )
        result = LocalEvidenceRetriever().retrieve(request)
        self.assertEqual(result.status, "FOUND")
        self.assertGreaterEqual(len(result.evidence_refs), 1)
        self.assertTrue(result.evidence_refs[0].ref.startswith("evidence://file/"))
        self.assertIn("Continuity OS", result.evidence_refs[0].snippet)

    def test_g1003_evidence_trace_is_auditable_and_no_raw_dump(self):
        request = RetrievalRequest(
            query="Context reconstructed stored",
            intent="architecture_lookup",
            allowed_roots=(str(self.root),),
        )
        result = LocalEvidenceRetriever().retrieve(request)
        trace = result.to_trace(used_for_context=True)
        self.assertTrue(trace["evidence"]["retrieved"])
        self.assertTrue(trace["evidence"]["used_for_context"])
        self.assertFalse(trace["evidence"]["raw_dump_injected"])
        self.assertGreaterEqual(trace["evidence"]["source_count"], 1)

    def test_g1004_boundary_no_identity_memory_provider_authority(self):
        source = SOURCE.read_text(encoding="utf-8")
        forbidden = [
            "create_checkpoint",
            "mutate_persona",
            "persona_loader",
            "provider.chat",
            "MemoryRef(",
            "system_prompt",
        ]
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_g1005_no_memory_pollution(self):
        request = RetrievalRequest(
            query="Julia Core identity",
            intent="historical_event_lookup",
            allowed_roots=(str(self.root),),
        )
        result = LocalEvidenceRetriever().retrieve(request)
        self.assertTrue(result.evidence_refs)
        self.assertTrue(all("evidence://" in ref.ref for ref in result.evidence_refs))
        self.assertFalse(any("memory://" in ref.ref for ref in result.evidence_refs))


if __name__ == "__main__":
    unittest.main()
