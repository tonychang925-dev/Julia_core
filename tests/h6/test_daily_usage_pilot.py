import unittest
from pathlib import Path

from julia_core.observer import (
    ContinuityObservation,
    DailyRelationshipSnapshot,
    EvidenceObservation,
    HumanFrictionObservation,
    InteractionObservation,
    MemoryObservation,
    PilotObservationRecord,
    VoiceObservation,
    daily_relationship_snapshot,
)

ROOT = Path(__file__).resolve().parents[2]
OBSERVER = ROOT / "julia_core" / "observer" / "pilot_observer.py"
CONTRACT = ROOT / "docs" / "project_control" / "PHASE_CONTRACT_H6_1_DAILY_USAGE_PILOT.md"
REPORT = ROOT / "docs" / "verification" / "H6_1_DAILY_USAGE_PILOT_REPORT_v1.md"
FEATURE = ROOT / "docs" / "project_control" / "FEATURE_SPEC_H6_1.md"
ROADMAP = ROOT / "docs" / "project_control" / "PHASE_H_JULIA_HUMAN_INTERFACE_LAYER_ROADMAP.md"


def record(
    session,
    *,
    continuity=True,
    evidence=False,
    evidence_success=False,
    memory_useful=None,
    voice=False,
    corrections=0,
    repeat=0,
    wrong=0,
):
    return PilotObservationRecord(
        session=session,
        timestamp="2026-08-02T00:00:00+00:00",
        interaction=InteractionObservation(duration_ms=1000, turns=1),
        continuity=ContinuityObservation(checkpoint_used=continuity, reconstruction_required=evidence),
        memory=MemoryObservation(memory_hit=memory_useful is not None, useful=memory_useful),
        evidence=EvidenceObservation(retrieval_triggered=evidence, successful=evidence_success, refs=("evidence://ADR-017",) if evidence_success else ()),
        voice=VoiceObservation(input=voice, output=voice),
        human=HumanFrictionObservation(correction_count=corrections, repetition_required=repeat, wrong_assumption_count=wrong),
    )


class H61DailyUsagePilotTest(unittest.TestCase):
    def test_h6101_daily_snapshot_summarizes_real_usage_metrics(self):
        snapshot = daily_relationship_snapshot(
            [
                record("s1", continuity=True, evidence=True, evidence_success=True, memory_useful=True, voice=True),
                record("s1", continuity=True, evidence=False, memory_useful=False, corrections=1),
                record("s2", continuity=False, evidence=True, evidence_success=False, repeat=1, wrong=1),
            ],
            date="2026-08-02",
            topics=("Julia Core", "AI architecture", "stock agent"),
        )
        self.assertIsInstance(snapshot, DailyRelationshipSnapshot)
        self.assertEqual(snapshot.sessions, 2)
        self.assertEqual(snapshot.turns, 3)
        self.assertEqual(snapshot.continuity_success, 0.6667)
        self.assertEqual(snapshot.repeated_explanation_rate, 0.3333)
        self.assertEqual(snapshot.memory_usefulness, 0.5)
        self.assertEqual(snapshot.evidence_success_rate, 0.5)
        self.assertEqual(snapshot.manual_corrections, 1)
        self.assertEqual(snapshot.human_friction_score, 3)
        self.assertEqual(snapshot.voice_usage_ratio, 0.3333)

    def test_h6102_daily_snapshot_is_not_memory_or_identity(self):
        snapshot = daily_relationship_snapshot([record("s1")], date="2026-08-02", topics=("Julia Core",))
        self.assertFalse(snapshot.boundary["snapshot_writes_memory"])
        self.assertFalse(snapshot.boundary["snapshot_mutates_identity"])
        self.assertFalse(snapshot.boundary["snapshot_updates_persona"])
        self.assertFalse(snapshot.boundary["snapshot_is_memory"])
        as_dict = snapshot.to_dict()
        self.assertIn("topics", as_dict)
        self.assertNotIn("memory_ref", as_dict)
        self.assertNotIn("identity_updated", as_dict)

    def test_h6103_empty_daily_snapshot_is_stable(self):
        snapshot = daily_relationship_snapshot([], date="2026-08-02", topics=("Julia Core",))
        self.assertEqual(snapshot.sessions, 0)
        self.assertEqual(snapshot.turns, 0)
        self.assertEqual(snapshot.continuity_success, 0.0)
        self.assertEqual(snapshot.human_friction_score, 0)
        self.assertEqual(snapshot.topics, ("Julia Core",))

    def test_h6104_h6_pilot_forbids_auto_evolution_shortcut(self):
        source = OBSERVER.read_text(encoding="utf-8")
        forbidden = [
            "write_memory",
            "create_memory",
            "MemoryRef(",
            "mutate_persona",
            "update_identity",
            "identity_updated",
            "persona_updated",
        ]
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_h6105_contract_report_feature_and_roadmap_document_h61(self):
        self.assertIn("H6.1 — Tony-Julia Daily Usage Pilot", CONTRACT.read_text(encoding="utf-8"))
        self.assertIn("Daily Relationship Snapshot", CONTRACT.read_text(encoding="utf-8"))
        self.assertIn("H6.1 Daily Usage Pilot", REPORT.read_text(encoding="utf-8"))
        self.assertIn("H6.1-T01", FEATURE.read_text(encoding="utf-8"))
        roadmap = ROADMAP.read_text(encoding="utf-8")
        self.assertIn("H6.1 | Tony-Julia Daily Usage Pilot ✅", roadmap)
        self.assertIn("H6.2 | Reality Feedback Analysis", roadmap)


if __name__ == "__main__":
    unittest.main()
