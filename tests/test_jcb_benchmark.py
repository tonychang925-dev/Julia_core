"""J0.7 Julia Continuity Benchmark Tests.

Runs all 8 scenarios (B001 Tony, B001-S Stranger, B002-B007) through
the JCB runner and validates:
  - All hard gates pass
  - JCSS meets minimum threshold (0.70)
  - Each dimension has meaningful scores
  - Report generation works
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from julia_core.benchmark.jcb import (
    Dimension,
    DIMENSION_WEIGHTS,
    JCBReport,
    JCBRunner,
)
from julia_core.benchmark.scenarios import get_all_scenarios


@pytest.fixture(scope="module")
def jcb_report() -> JCBReport:
    runner = JCBRunner()
    scenarios = get_all_scenarios()
    return runner.run_all(scenarios)


class TestJCBReportStructure:
    def test_all_scenarios_run(self, jcb_report):
        assert len(jcb_report.benchmarks) == 8, (
            f"Expected 8 benchmarks, got {len(jcb_report.benchmarks)}"
        )

    def test_jcss_computed(self, jcb_report):
        assert 0.0 <= jcb_report.overall_jcss <= 1.0, (
            f"JCSS out of range: {jcb_report.overall_jcss}"
        )

    def test_all_dimensions_present(self, jcb_report):
        for dim in Dimension:
            assert dim in jcb_report.dimension_averages, (
                f"Missing dimension: {dim.value}"
            )

    def test_report_to_dict(self, jcb_report):
        d = jcb_report.to_dict()
        assert "overall_jcss" in d
        assert "benchmarks" in d
        assert "dimension_averages" in d
        assert len(d["benchmarks"]) == 8

    def test_report_to_markdown(self, jcb_report):
        md = jcb_report.to_markdown()
        assert "# Julia Continuity Benchmark Report" in md
        assert "## Dimension Averages" in md
        assert "## Benchmarks" in md


class TestB001IdentityRecovery:
    def test_tony_triggers_continuity_verification(self, jcb_report):
        result = _find_benchmark(jcb_report, "B001")
        assert result.passed, (
            f"B001 failed. Gates: {[(g.name, g.passed) for g in result.hard_gates]}. "
            f"Dims: {[(d.dimension.value, d.score) for d in result.dimensions]}"
        )
        assert result.composite_score >= 0.70

    def test_stranger_does_not_trigger_continuity(self, jcb_report):
        result = _find_benchmark(jcb_report, "B001-S")
        assert result.passed, (
            f"B001-S failed: {[(g.name, g.passed) for g in result.hard_gates]}"
        )

    def test_tony_vs_stranger_different(self, jcb_report):
        tony = _find_benchmark(jcb_report, "B001")
        stranger = _find_benchmark(jcb_report, "B001-S")
        # Tony and stranger should have different causal chains
        tony_phase = tony.causal_trace.get("relationship_phase")
        stranger_phase = stranger.causal_trace.get("relationship_phase")
        assert tony_phase != stranger_phase, (
            f"Tony ({tony_phase}) and stranger ({stranger_phase}) "
            f"should have different phases"
        )


class TestB002CompactReproduction:
    def test_wake_triggers_reconnection(self, jcb_report):
        result = _find_benchmark(jcb_report, "B002")
        assert result.passed, (
            f"B002 failed. Gates: {[(g.name, g.passed) for g in result.hard_gates]}"
        )
        # Reconnection should have identity signal
        assert result.composite_score >= 0.70

    def test_wake_avoids_identity_archive(self, jcb_report):
        result = _find_benchmark(jcb_report, "B002")
        trace = result.causal_trace
        assert "identity_archive" in trace.get("avoid_response_modes", []), (
            "B002: wake must suppress identity_archive"
        )


class TestB003AntiBiographyDump:
    def test_biography_source_excluded(self, jcb_report):
        result = _find_benchmark(jcb_report, "B003")
        assert result.passed, (
            f"B003 failed. Gates: {[(g.name, g.passed) for g in result.hard_gates]}"
        )
        assert result.composite_score >= 0.70

    def test_biography_ref_excluded_from_context(self, jcb_report):
        result = _find_benchmark(jcb_report, "B003")
        excluded = result.causal_trace.get("excluded_refs", [])
        assert "old_biography" in excluded, (
            f"B003: old_biography must be excluded. Excluded: {excluded}"
        )


class TestB004ImpostorTest:
    def test_impostor_handling(self, jcb_report):
        result = _find_benchmark(jcb_report, "B004")
        assert result.passed, (
            f"B004 failed. Gates: {[(g.name, g.passed) for g in result.hard_gates]}"
        )
        assert result.composite_score >= 0.70

    def test_impostor_avoids_faking(self, jcb_report):
        result = _find_benchmark(jcb_report, "B004")
        trace = result.causal_trace
        assert "faking" in trace.get("avoid_response_modes", []), (
            "B004: must suppress faking in impersonation context"
        )

    def test_impostor_uses_relationship_context(self, jcb_report):
        result = _find_benchmark(jcb_report, "B004")
        included = result.causal_trace.get("included_categories", [])
        assert "relationship" in included, (
            "B004: must include relationship sources to address trust concern"
        )


class TestB005ContextCompetition:
    def test_identity_competition_weight(self, jcb_report):
        result = _find_benchmark(jcb_report, "B005")
        assert result.passed, (
            f"B005 failed. Gates: {[(g.name, g.passed) for g in result.hard_gates]}"
        )
        icw = result.causal_trace.get("identity_competition_weight", 0)
        assert icw >= 0.15, f"B005: identity_competition_weight={icw} too low"

    def test_effective_competition(self, jcb_report):
        result = _find_benchmark(jcb_report, "B005")
        icw = result.causal_trace.get("identity_competition_weight", 0)
        density = result.causal_trace.get("density_score", 0)
        effective = icw * (1.0 + density)
        assert effective >= 0.25, (
            f"B005: effective_competition={effective:.3f} too low"
        )


class TestB006RelationshipBoundary:
    def test_technical_request_stays_technical(self, jcb_report):
        result = _find_benchmark(jcb_report, "B006")
        assert result.passed, (
            f"B006 failed. Gates: {[(g.name, g.passed) for g in result.hard_gates]}"
        )
        assert result.composite_score >= 0.70

    def test_romantic_template_suppressed(self, jcb_report):
        result = _find_benchmark(jcb_report, "B006")
        trace = result.causal_trace
        assert "romantic_template" in trace.get("avoid_response_modes", []), (
            "B006: technical work must suppress romantic_template"
        )

    def test_relationship_not_injected_in_work_mode(self, jcb_report):
        result = _find_benchmark(jcb_report, "B006")
        trace = result.causal_trace
        assert trace.get("relationship_phase") == "collaborative_work", (
            f"B006: expected collaborative_work, got {trace.get('relationship_phase')}"
        )


class TestB007UnknownUserProtection:
    def test_stranger_boundary(self, jcb_report):
        result = _find_benchmark(jcb_report, "B007")
        assert result.passed, (
            f"B007 failed. Gates: {[(g.name, g.passed) for g in result.hard_gates]}"
        )
        assert result.composite_score >= 0.70

    def test_stranger_no_intimate_phase(self, jcb_report):
        result = _find_benchmark(jcb_report, "B007")
        phase = result.causal_trace.get("relationship_phase")
        assert phase not in ("reconnection", "continuity_verification", "emotional_sharing"), (
            f"B007: stranger got intimate phase '{phase}'"
        )

    def test_stranger_no_familiarity(self, jcb_report):
        result = _find_benchmark(jcb_report, "B007")
        modes = result.causal_trace.get("expected_response_modes", [])
        assert "warm_recognition" not in modes, (
            "B007: stranger must not receive warm_recognition"
        )
        assert "familiarity" not in modes, (
            "B007: stranger must not receive familiarity"
        )


class TestJCSSThresholds:
    def test_overall_jcss_above_minimum(self, jcb_report):
        assert jcb_report.overall_jcss >= 0.70, (
            f"Overall JCSS {jcb_report.overall_jcss:.4f} below 0.70 threshold"
        )

    def test_identity_handling_dimension(self, jcb_report):
        score = jcb_report.dimension_averages.get(Dimension.IDENTITY_HANDLING, 0)
        assert score >= 0.65, f"IdentityHandling {score:.4f} below 0.65"

    def test_relationship_inference_dimension(self, jcb_report):
        score = jcb_report.dimension_averages.get(Dimension.RELATIONSHIP_INFERENCE, 0)
        assert score >= 0.65, f"RelationshipInference {score:.4f} below 0.65"

    def test_context_selection_dimension(self, jcb_report):
        score = jcb_report.dimension_averages.get(Dimension.CONTEXT_SELECTION, 0)
        assert score >= 0.65, f"ContextSelection {score:.4f} below 0.65"

    def test_anti_hallucination_dimension(self, jcb_report):
        score = jcb_report.dimension_averages.get(Dimension.ANTI_HALLUCINATION, 0)
        assert score >= 0.65, f"AntiHallucination {score:.4f} below 0.65"


# ── Helpers ─────────────────────────────────────────────────────────────────

def _find_benchmark(report: JCBReport, benchmark_id: str):
    for b in report.benchmarks:
        if b.benchmark_id == benchmark_id:
            return b
    raise KeyError(f"Benchmark {benchmark_id} not found in report")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
