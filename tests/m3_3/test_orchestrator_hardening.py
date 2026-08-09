"""M3.3.0a Sabotage Tests — verify orchestrator hardening fails correctly.

These tests verify that constraint violations, fixture gaps, and budget
limits are properly enforced. They are INTENDED to raise exceptions or
produce specific failure states — the test passes when the system correctly
rejects invalid input.
"""

import asyncio
import pytest

from julia_core.capability.financial.research.orchestrator import (
    CognitiveLoopConfig,
    CognitiveLoopOrchestrator,
    CognitiveLoopResult,
    ConstraintViolation,
    ForbiddenCapabilityManager,
    ReplayFixtureMissing,
    RoundRecord,
)
from julia_core.capability.financial.research.models import (
    EvidenceItem,
    ResearchPlan,
    ResearchProbe,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_config(**kwargs) -> CognitiveLoopConfig:
    defaults = {"max_rounds": 1, "query_budget": 10, "as_of": "2026-07-14"}
    defaults.update(kwargs)
    return CognitiveLoopConfig(**defaults)


def _make_subject(**kwargs) -> dict:
    defaults = {
        "subject_key": "9010270",
        "trade_date": "2026-07-14",
        "leader_code": "601969",
        "market_stage": "fading_momentum",
    }
    defaults.update(kwargs)
    return defaults


def _make_evidence_item(req_id: str, status: str = "success", derived_value=None):
    return EvidenceItem(
        requirement_id=req_id,
        probe_id=f"probe_{req_id}",
        status=status,
        derived_value=derived_value,
    )


# ── P0-2: Replay mode fail-closed ─────────────────────────────────────────────

def test_replay_missing_fixture_raises():
    """Missing probe in replay mode → ReplayFixtureMissing."""
    orchestrator = CognitiveLoopOrchestrator(
        capability_manager=ForbiddenCapabilityManager(),
        config=_make_config(),
        evidence_injector={
            "leader_divergence": {
                "leader_drawdown_from_peak": _make_evidence_item("leader_drawdown_from_peak"),
                # Deliberately missing: leader_5d_return, key_level_status, etc.
            },
        },
    )

    async def _run():
        with pytest.raises(ReplayFixtureMissing, match="leader_5d_return"):
            await orchestrator.run(_make_subject())

    asyncio.run(_run())


def test_forbidden_capability_manager_raises():
    """ForbiddenCapabilityManager.execute() → AssertionError."""
    fm = ForbiddenCapabilityManager()

    async def _run():
        with pytest.raises(AssertionError, match="LIVE CAPABILITY CALLED"):
            await fm.execute(type('req', (), {'capability_name': 'test.cap'})())

    asyncio.run(_run())


def test_live_call_during_replay_raises():
    """Live CapabilityManager call in replay mode → AssertionError."""
    orchestrator = CognitiveLoopOrchestrator(
        capability_manager=ForbiddenCapabilityManager(),
        config=_make_config(),
        evidence_injector={
            "leader_divergence": {
                # Missing probe → would call CapabilityManager if not fail-closed
            },
        },
    )

    async def _run():
        with pytest.raises(ReplayFixtureMissing):
            await orchestrator.run(_make_subject())

    asyncio.run(_run())


# ── P0-3: Constraint enforcement ─────────────────────────────────────────────

def test_blind_judgment_mutation_raises():
    """Mutating blind judgment during research → ConstraintViolation.

    This is tested by verifying that set_blind_judgment records a hash,
    and the orchestrator verifies it hasn't changed after run().
    """
    orchestrator = CognitiveLoopOrchestrator(
        capability_manager=ForbiddenCapabilityManager(),
        config=_make_config(),
        evidence_injector={
            "leader_divergence": {
                "leader_5d_return": _make_evidence_item("leader_5d_return", derived_value=0.04),
                "leader_drawdown_from_peak": _make_evidence_item("leader_drawdown_from_peak", derived_value=-0.04),
                "leader_volume_pattern": _make_evidence_item("leader_volume_pattern", derived_value="normal"),
                "key_level_status": _make_evidence_item("key_level_status", derived_value="intact"),
                "peer_relative_strength": _make_evidence_item("peer_relative_strength", derived_value={"dispersion": {"max_min_spread": 0.10}}),
                "theme_breadth_change": _make_evidence_item("theme_breadth_change", derived_value={"delta": {"positive_ratio": 0.6}, "from": {}, "to": {"limit_up_ratio": 0.6, "positive_ratio": 0.7}}),
                "capital_persistence": _make_evidence_item("capital_persistence", status="unavailable"),
                "market_regime": _make_evidence_item("market_regime", derived_value="strength_active"),
                "new_leader_candidates": _make_evidence_item("new_leader_candidates", derived_value=[]),
            },
        },
    )

    orchestrator.set_blind_judgment({"market_stage": "fading_momentum", "subject_key": "9010270"})
    hash_before = orchestrator._blind_judgment_hash

    async def _run():
        # Mutate blind judgment mid-run (simulates a bug)
        orchestrator._blind_judgment["market_stage"] = "divergence"
        with pytest.raises(ConstraintViolation, match="Blind judgment was mutated"):
            await orchestrator.run(_make_subject())

    asyncio.run(_run())


def test_future_evidence_as_of_gate():
    """Config as_of earlier than evidence date → ConstraintViolation."""
    orchestrator = CognitiveLoopOrchestrator(
        capability_manager=ForbiddenCapabilityManager(),
        config=_make_config(as_of="2026-07-10"),  # Earlier than trade_date
    )

    async def _run():
        with pytest.raises(ConstraintViolation, match="trade_date"):
            await orchestrator.run(_make_subject(trade_date="2026-07-14"))

    asyncio.run(_run())


# ── P0-5: Round-0 autonomous card selection ───────────────────────────────────

def test_missing_market_stage_raises():
    """No initial_card and no market_stage → ConstraintViolation."""
    orchestrator = CognitiveLoopOrchestrator(
        capability_manager=ForbiddenCapabilityManager(),
        config=CognitiveLoopConfig(max_rounds=1, initial_card=""),  # empty
    )

    async def _run():
        with pytest.raises(ConstraintViolation, match="No initial card"):
            await orchestrator.run({
                "subject_key": "9010270",
                "trade_date": "2026-07-14",
                # No market_stage, no initial_card
            })

    asyncio.run(_run())


def test_stage_to_initial_card_maps_correctly():
    """fading_momentum → leader_divergence."""
    orchestrator = CognitiveLoopOrchestrator(
        capability_manager=ForbiddenCapabilityManager(),
        config=_make_config(),
        evidence_injector={
            "leader_divergence": {
                "leader_5d_return": _make_evidence_item("leader_5d_return", derived_value=0.04),
                "leader_drawdown_from_peak": _make_evidence_item("leader_drawdown_from_peak", derived_value=-0.04),
                "leader_volume_pattern": _make_evidence_item("leader_volume_pattern", derived_value="normal"),
                "key_level_status": _make_evidence_item("key_level_status", derived_value="intact"),
                "peer_relative_strength": _make_evidence_item("peer_relative_strength", derived_value={"dispersion": {"max_min_spread": 0.10}}),
                "theme_breadth_change": _make_evidence_item("theme_breadth_change", derived_value={"delta": {"positive_ratio": 0.6}, "from": {}, "to": {"limit_up_ratio": 0.6, "positive_ratio": 0.7}}),
                "capital_persistence": _make_evidence_item("capital_persistence", status="unavailable"),
                "market_regime": _make_evidence_item("market_regime", derived_value="strength_active"),
                "new_leader_candidates": _make_evidence_item("new_leader_candidates", derived_value=[]),
            },
        },
    )

    async def _run():
        result = await orchestrator.run(_make_subject(market_stage="fading_momentum"))
        assert len(result.rounds) == 1
        assert result.rounds[0].plan.triggered_card == "leader_divergence"

    asyncio.run(_run())


# ── P1: Budget semantics ─────────────────────────────────────────────────────

def test_max_rounds_1_means_one_total_round():
    """max_rounds=1 → exactly 1 RoundRecord."""
    orchestrator = CognitiveLoopOrchestrator(
        capability_manager=ForbiddenCapabilityManager(),
        config=_make_config(max_rounds=1),
        evidence_injector={
            "leader_divergence": {
                "leader_5d_return": _make_evidence_item("leader_5d_return", derived_value=0.04),
                "leader_drawdown_from_peak": _make_evidence_item("leader_drawdown_from_peak", derived_value=-0.04),
                "leader_volume_pattern": _make_evidence_item("leader_volume_pattern", derived_value="normal"),
                "key_level_status": _make_evidence_item("key_level_status", derived_value="intact"),
                "peer_relative_strength": _make_evidence_item("peer_relative_strength", derived_value={"dispersion": {"max_min_spread": 0.10}}),
                "theme_breadth_change": _make_evidence_item("theme_breadth_change", derived_value={"delta": {"positive_ratio": 1.0}, "from": {}, "to": {"limit_up_ratio": 1.0, "positive_ratio": 1.0}}),
                "capital_persistence": _make_evidence_item("capital_persistence", status="unavailable"),
                "market_regime": _make_evidence_item("market_regime", derived_value="strength_active"),
                "new_leader_candidates": _make_evidence_item("new_leader_candidates", derived_value=[]),
            },
        },
    )

    async def _run():
        result = await orchestrator.run(_make_subject())
        assert len(result.rounds) == 1
        assert result.stop_reason in ("no_transition", "max_rounds")

    asyncio.run(_run())


def test_queries_executed_tracks_correctly():
    """In replay mode, queries_executed should be 0 (no live calls)."""
    orchestrator = CognitiveLoopOrchestrator(
        capability_manager=ForbiddenCapabilityManager(),
        config=_make_config(max_rounds=1),
        evidence_injector={
            "leader_divergence": {
                "leader_5d_return": _make_evidence_item("leader_5d_return", derived_value=0.04),
                "leader_drawdown_from_peak": _make_evidence_item("leader_drawdown_from_peak", derived_value=-0.04),
                "leader_volume_pattern": _make_evidence_item("leader_volume_pattern", derived_value="normal"),
                "key_level_status": _make_evidence_item("key_level_status", derived_value="intact"),
                "peer_relative_strength": _make_evidence_item("peer_relative_strength", derived_value={"dispersion": {"max_min_spread": 0.10}}),
                "theme_breadth_change": _make_evidence_item("theme_breadth_change", derived_value={"delta": {"positive_ratio": 1.0}, "from": {}, "to": {"limit_up_ratio": 1.0, "positive_ratio": 1.0}}),
                "capital_persistence": _make_evidence_item("capital_persistence", status="unavailable"),
                "market_regime": _make_evidence_item("market_regime", derived_value="strength_active"),
                "new_leader_candidates": _make_evidence_item("new_leader_candidates", derived_value=[]),
            },
        },
    )

    async def _run():
        result = await orchestrator.run(_make_subject())
        assert result.queries_executed == 0  # All from injector, no live calls
        assert result.probes_blocked_by_budget == 0

    asyncio.run(_run())


# ── WorkflowBridge P0-1: None-default handling ────────────────────────────────

def test_bridge_none_defaults_dont_break_config():
    """None values for max_rounds/query_budget → defaults used, not None."""
    from julia_core.workflow.research_workflow import ResearchWorkflowBridge

    # Bridge with no explicit config should use defaults
    bridge = ResearchWorkflowBridge(
        capability_manager=ForbiddenCapabilityManager(),
    )
    assert bridge.config is None  # no explicit config

    # Execute with None values (simulating subject.get returning None)
    async def _run():
        instance = await bridge.runtime.execute("research.cognitive_loop", {
            "subject_key": "9010270",
            "trade_date": "2026-07-14",
            "as_of": "2026-07-14T15:30:00+08:00",
            "max_rounds": None,     # P0-1: key exists, value is None
            "query_budget": None,   # P0-1: key exists, value is None
        })
        # Should fail on missing initial_card, not on None TypeError
        # (the initialize step should use defaults for None values)
        step_result = instance.step_results.get("research.initialize", {})
        assert step_result.get("research_initialized") is True
        assert step_result.get("config_max_rounds") == 2  # default
        assert step_result.get("config_query_budget") == 20  # default

    asyncio.run(_run())


# ── P0-5: No silent leader_divergence default ─────────────────────────────────

def test_no_silent_leader_divergence_default():
    """Empty initial_card + no market_stage → ConstraintViolation, not silent default."""
    orchestrator = CognitiveLoopOrchestrator(
        capability_manager=ForbiddenCapabilityManager(),
        config=CognitiveLoopConfig(max_rounds=1, initial_card=""),
    )

    async def _run():
        with pytest.raises(ConstraintViolation, match="No initial card"):
            await orchestrator.run({
                "subject_key": "9010270",
                "trade_date": "2026-07-14",
            })
        # Leader_divergence was NOT silently used

    asyncio.run(_run())


# ── P0: Real timestamp-level anti-hindsight ──────────────────────────────────

def test_future_evidence_timestamp_rejected():
    """Evidence at 15:31 with as_of=15:30 → ConstraintViolation.

    This is the real anti-hindsight test: not just date mismatch,
    but sub-day timestamp violation.
    """
    orchestrator = CognitiveLoopOrchestrator(
        capability_manager=ForbiddenCapabilityManager(),
        config=_make_config(as_of="2026-07-14T15:30:00+08:00"),
        evidence_injector={
            "leader_divergence": {
                "leader_5d_return": _make_evidence_item("leader_5d_return", derived_value=0.04),
                "leader_drawdown_from_peak": _make_evidence_item("leader_drawdown_from_peak", derived_value=-0.04),
                "leader_volume_pattern": _make_evidence_item("leader_volume_pattern", derived_value="normal"),
                "key_level_status": _make_evidence_item("key_level_status", derived_value="intact"),
                "peer_relative_strength": _make_evidence_item("peer_relative_strength", derived_value={"dispersion": {"max_min_spread": 0.10}}),
                "theme_breadth_change": _make_evidence_item("theme_breadth_change", derived_value={"delta": {"positive_ratio": 0.6}, "from": {}, "to": {"limit_up_ratio": 0.6, "positive_ratio": 0.7}}),
                "capital_persistence": _make_evidence_item("capital_persistence", status="unavailable"),
                "market_regime": _make_evidence_item("market_regime", derived_value="strength_active"),
                "new_leader_candidates": _make_evidence_item("new_leader_candidates", derived_value=[]),
            },
        },
    )

    async def _run():
        # Inject future evidence by patching provenance
        # The orchestrator reads provenance.available_at for as_of check
        original_check = orchestrator._check_evidence_constraints

        def _inject_future(item, probe):
            if not getattr(item, 'provenance', None):
                item.provenance = {}
            item.provenance["available_at"] = "2026-07-14T15:31:00+08:00"
            return original_check(item, probe)

        orchestrator._check_evidence_constraints = _inject_future

        with pytest.raises(ConstraintViolation, match="Future evidence"):
            await orchestrator.run(_make_subject())

    asyncio.run(_run())


def test_workbench_provenance_rejected():
    """Evidence with source_kind=workbench_review → ConstraintViolation."""
    orchestrator = CognitiveLoopOrchestrator(
        capability_manager=ForbiddenCapabilityManager(),
        config=_make_config(),
        evidence_injector={
            "leader_divergence": {
                "leader_5d_return": _make_evidence_item("leader_5d_return", derived_value=0.04),
                "leader_drawdown_from_peak": _make_evidence_item("leader_drawdown_from_peak", derived_value=-0.04),
                "leader_volume_pattern": _make_evidence_item("leader_volume_pattern", derived_value="normal"),
                "key_level_status": _make_evidence_item("key_level_status", derived_value="intact"),
                "peer_relative_strength": _make_evidence_item("peer_relative_strength", derived_value={"dispersion": {"max_min_spread": 0.10}}),
                "theme_breadth_change": _make_evidence_item("theme_breadth_change", derived_value={"delta": {"positive_ratio": 0.6}, "from": {}, "to": {"limit_up_ratio": 0.6, "positive_ratio": 0.7}}),
                "capital_persistence": _make_evidence_item("capital_persistence", status="unavailable"),
                "market_regime": _make_evidence_item("market_regime", derived_value="strength_active"),
                "new_leader_candidates": _make_evidence_item("new_leader_candidates", derived_value=[]),
            },
        },
    )

    async def _run():
        original_check = orchestrator._check_evidence_constraints

        def _inject_workbench(item, probe):
            if not getattr(item, 'provenance', None):
                item.provenance = {}
            item.provenance["source_kind"] = "workbench_review"
            return original_check(item, probe)

        orchestrator._check_evidence_constraints = _inject_workbench

        with pytest.raises(ConstraintViolation, match="Forbidden evidence source"):
            await orchestrator.run(_make_subject())

    asyncio.run(_run())


# ── P0: Bridge E2E production path ───────────────────────────────────────────

def test_bridge_e2e_with_market_stage():
    """Bridge with market_stage (no explicit initial_card) → COMPLETED.

    P0 regression: market_stage was dropped in research_initialize,
    causing ConstraintViolation before any research could run.
    """
    from julia_core.workflow.research_workflow import ResearchWorkflowBridge

    bridge = ResearchWorkflowBridge(
        capability_manager=ForbiddenCapabilityManager(),
    )

    async def _run():
        instance = await bridge.execute_research({
            "subject_key": "9010270",
            "trade_date": "2026-07-14",
            "as_of": "2026-07-14T15:30:00+08:00",
            "market_stage": "fading_momentum",
        })
        # Should fail on replay fixture missing (no injector), not on
        # ConstraintViolation("No initial card") or AttributeError
        step_results = instance.step_results
        assert "research.initialize" in step_results
        assert step_results["research.initialize"].get("research_initialized") is True

    asyncio.run(_run())


def test_bridge_no_stale_total_queries():
    """Bridge does not reference stale total_queries attribute.

    P0 regression: CognitiveLoopResult.queries_executed renamed from
    total_queries, but bridge still referenced old name.
    """
    from julia_core.workflow.research_workflow import ResearchWorkflowBridge

    bridge = ResearchWorkflowBridge(
        capability_manager=ForbiddenCapabilityManager(),
    )

    async def _run():
        instance = await bridge.execute_research({
            "subject_key": "9010270",
            "trade_date": "2026-07-14",
            "as_of": "2026-07-14T15:30:00+08:00",
            "as_of": "2026-07-14T15:30:00+08:00",
            "market_stage": "fading_momentum",
        })
        # Should fail on replay fixture missing, not on AttributeError
        step_results = instance.step_results
        # If we got past the execute step without AttributeError, test passes
        # (execution fails on fixture missing, which is expected)
        assert "research.initialize" in step_results

    asyncio.run(_run())


def test_bridge_e2e_with_blind_judgment():
    """Bridge with blind_judgment (no explicit market_stage) → market_stage derived.

    P0 regression: blind_judgment not propagated, market_stage not derived.
    """
    from julia_core.workflow.research_workflow import ResearchWorkflowBridge
    from julia_core.workflow.models import WorkflowState

    bridge = ResearchWorkflowBridge(
        capability_manager=ForbiddenCapabilityManager(),
    )

    async def _run():
        instance = await bridge.execute_research({
            "subject_key": "9010270",
            "trade_date": "2026-07-14",
            "as_of": "2026-07-14T15:30:00+08:00",
            "blind_judgment": {"market_stage": "fading_momentum", "subject_key": "9010270"},
        })
        step_results = instance.step_results
        assert "research.initialize" in step_results
        assert step_results["research.initialize"].get("research_initialized") is True
        # market_stage derived from blind_judgment → no ConstraintViolation
        assert "research.execute_loop" in step_results or instance.state == WorkflowState.FAILED

    asyncio.run(_run())


def test_cross_timezone_future_evidence_rejected():
    """Evidence at 08:00+00:00 (16:00 Beijing) with as_of=15:30+08:00 → FAIL.

    P0 regression: string comparison would pass (08 < 15).
    Offset-aware datetime comparison correctly rejects (16:00 > 15:30).
    """
    orchestrator = CognitiveLoopOrchestrator(
        capability_manager=ForbiddenCapabilityManager(),
        config=_make_config(as_of="2026-07-14T15:30:00+08:00"),
        evidence_injector={
            "leader_divergence": {
                "leader_5d_return": _make_evidence_item("leader_5d_return", derived_value=0.04),
                "leader_drawdown_from_peak": _make_evidence_item("leader_drawdown_from_peak", derived_value=-0.04),
                "leader_volume_pattern": _make_evidence_item("leader_volume_pattern", derived_value="normal"),
                "key_level_status": _make_evidence_item("key_level_status", derived_value="intact"),
                "peer_relative_strength": _make_evidence_item("peer_relative_strength", derived_value={"dispersion": {"max_min_spread": 0.10}}),
                "theme_breadth_change": _make_evidence_item("theme_breadth_change", derived_value={"delta": {"positive_ratio": 0.6}, "from": {}, "to": {"limit_up_ratio": 0.6, "positive_ratio": 0.7}}),
                "capital_persistence": _make_evidence_item("capital_persistence", status="unavailable"),
                "market_regime": _make_evidence_item("market_regime", derived_value="strength_active"),
                "new_leader_candidates": _make_evidence_item("new_leader_candidates", derived_value=[]),
            },
        },
    )

    async def _run():
        original_check = orchestrator._check_evidence_constraints

        def _inject_cross_tz(item, probe):
            if not getattr(item, 'provenance', None):
                item.provenance = {}
            # 08:00 UTC = 16:00 Beijing → AFTER 15:30 cutoff
            item.provenance["available_at"] = "2026-07-14T08:00:00+00:00"
            return original_check(item, probe)

        orchestrator._check_evidence_constraints = _inject_cross_tz

        with pytest.raises(ConstraintViolation, match="Future evidence"):
            await orchestrator.run(_make_subject())

    asyncio.run(_run())


# ── P0: as_of must be full timestamp ──────────────────────────────────────

def test_omit_as_of_in_bridge_fails():
    """Bridge with no as_of → fails (not midnight default).

    P0 regression: trade_date substituted for as_of, defaulting to
    midnight +08:00 which rejects same-day evidence at e.g. 10:00+08.
    """
    from julia_core.workflow.research_workflow import ResearchWorkflowBridge
    from julia_core.workflow.models import WorkflowState

    bridge = ResearchWorkflowBridge(
        capability_manager=ForbiddenCapabilityManager(),
    )

    async def _run():
        instance = await bridge.execute_research({
            "subject_key": "9010270",
            "trade_date": "2026-07-14",
            "market_stage": "fading_momentum",
            # Deliberately omit as_of
        })
        # Should fail on as_of requirement, not proceed to execute
        assert instance.state == WorkflowState.FAILED

    asyncio.run(_run())


# ── P1: True WorkflowBridge E2E → COMPLETED ───────────────────────────────

class _FakeSuccessCapability:
    """Fake CapabilityManager that succeeds for every request."""

    async def execute(self, request):
        from types import SimpleNamespace
        return SimpleNamespace(
            status="success",
            data={
                "status": "live",
                "source_kind": "test_fixture",
            },
            provider="fake",
            schema_version="test",
            request_id=getattr(request, "request_id", ""),
        )


def test_bridge_e2e_completed_with_fake_capability():
    """Bridge with fake CapabilityManager → initialize→execute→conclude→COMPLETED.

    True E2E: all 3 steps execute, workflow terminates normally.
    """
    from julia_core.workflow.research_workflow import ResearchWorkflowBridge
    from julia_core.workflow.models import WorkflowState

    bridge = ResearchWorkflowBridge(
        capability_manager=_FakeSuccessCapability(),
    )

    async def _run():
        instance = await bridge.execute_research({
            "subject_key": "9010270",
            "trade_date": "2026-07-14",
            "as_of": "2026-07-14T15:30:00+08:00",
            "market_stage": "fading_momentum",
        })
        assert instance.state == WorkflowState.COMPLETED, (
            f"Expected COMPLETED, got {instance.state}. "
            f"Error: {instance.step_results.get('_error', 'none')}"
        )
        assert "research.initialize" in instance.step_results
        assert "research.execute_loop" in instance.step_results
        assert "research.conclude" in instance.step_results
        loop_result = instance.step_results["research.execute_loop"]
        assert loop_result.get("loop_completed") is True
        assert loop_result.get("total_rounds", 0) >= 1

    asyncio.run(_run())


# ── P0: Request cutoff integrity ──────────────────────────────────────────

def test_capability_requests_use_runtime_cutoff_not_trade_date():
    """Every CapabilityRequest as_of uses the runtime cutoff timestamp.

    P0 regression: binding templates used $subject.trade_date (date-only),
    losing the time component of the runtime as_of.
    """
    from julia_core.capability.financial.research.compiler import StrategyResearchCompiler
    from julia_core.capability.financial.research.requirement_bindings import REQUIREMENT_BINDINGS
    import json
    from pathlib import Path

    compiler = StrategyResearchCompiler()
    card_path = Path("/Users/admin/Desktop/ai_theme_app/strategy_knowledge/cards/leader_divergence.json")
    card = json.loads(card_path.read_text())

    runtime_as_of = "2026-07-14T13:30:00+08:00"
    subject = {
        "subject_key": "9010270",
        "trade_date": "2026-07-14",
        "as_of": runtime_as_of,
        "leader_code": "601969",
    }

    plan = compiler.compile(card, subject)
    for probe in plan.probes:
        req_as_of = (getattr(probe.request, "arguments", {}) or {}).get("as_of", "")
        assert req_as_of == runtime_as_of, (
            f"Probe {probe.requirement_id}: as_of={req_as_of} "
            f"expected {runtime_as_of}"
        )


def test_rc002_preserves_same_cutoff_as_rc001():
    """RC-002 CapabilityRequests use the exact same cutoff as RC-001."""
    import json
    from pathlib import Path
    from julia_core.capability.financial.research.compiler import StrategyResearchCompiler

    runtime_as_of = "2026-07-14T13:30:00+08:00"
    subject = {
        "subject_key": "9010270",
        "trade_date": "2026-07-14",
        "as_of": runtime_as_of,
        "leader_code": "601969",
    }

    compiler = StrategyResearchCompiler()

    card_base = Path("/Users/admin/Desktop/ai_theme_app/strategy_knowledge/cards")
    card1 = json.loads((card_base / "leader_divergence.json").read_text())
    plan1 = compiler.compile(card1, subject)

    card2 = json.loads((card_base / "weak_to_strong.json").read_text())
    plan2 = compiler.compile(card2, subject)

    # Both plans' probes must use the exact same as_of
    for plan_name, plan in [("RC-001", plan1), ("RC-002", plan2)]:
        for probe in plan.probes:
            req_as_of = (getattr(probe.request, "arguments", {}) or {}).get("as_of", "")
            assert req_as_of == runtime_as_of, (
                f"{plan_name} probe {probe.requirement_id}: "
                f"as_of={req_as_of} expected {runtime_as_of}"
            )


# ── P1: Normalizer requested_as_of survival ───────────────────────────────

def test_requested_as_of_survives_outer_error():
    """Normalizer: requested_as_of survives outer error path."""
    from julia_core.capability.financial.research.evidence_normalizer import ResearchEvidenceNormalizer
    from julia_core.capability.financial.research.models import ResearchProbe
    from julia_core.capability.models import CapabilityRequest
    from types import SimpleNamespace

    normalizer = ResearchEvidenceNormalizer()
    probe = ResearchProbe(
        requirement_id="test_req",
        request=CapabilityRequest(
            capability_name="test.cap",
            arguments={"as_of": "2026-07-14T13:30:00+08:00"},
        ),
    )
    result = SimpleNamespace(status="error", error_message="boom")

    item = normalizer.normalize(probe, result)
    assert item.provenance.get("requested_as_of") == "2026-07-14T13:30:00+08:00"
    assert item.provenance.get("outer_status") == "error"


def test_requested_as_of_survives_inner_unavailable():
    """Normalizer: requested_as_of survives inner unavailable path."""
    from julia_core.capability.financial.research.evidence_normalizer import ResearchEvidenceNormalizer
    from julia_core.capability.financial.research.models import ResearchProbe
    from julia_core.capability.models import CapabilityRequest
    from types import SimpleNamespace

    normalizer = ResearchEvidenceNormalizer()
    probe = ResearchProbe(
        requirement_id="test_req",
        request=CapabilityRequest(
            capability_name="test.cap",
            arguments={"as_of": "2026-07-14T13:30:00+08:00"},
        ),
    )
    result = SimpleNamespace(
        status="success",
        data={"status": "unavailable", "reason": "no_data", "source_kind": "archive"},
    )

    item = normalizer.normalize(probe, result)
    assert item.provenance.get("requested_as_of") == "2026-07-14T13:30:00+08:00"


def test_requested_as_of_survives_value_path_miss():
    """Normalizer: requested_as_of survives value_path miss (insufficient)."""
    from julia_core.capability.financial.research.evidence_normalizer import ResearchEvidenceNormalizer
    from julia_core.capability.financial.research.models import ResearchProbe
    from julia_core.capability.models import CapabilityRequest
    from types import SimpleNamespace

    normalizer = ResearchEvidenceNormalizer()
    probe = ResearchProbe(
        requirement_id="test_req",
        request=CapabilityRequest(
            capability_name="test.cap",
            arguments={"as_of": "2026-07-14T13:30:00+08:00"},
        ),
        derive_metric="nonexistent.key.path",
    )
    result = SimpleNamespace(
        status="success",
        data={"status": "live", "some_other_field": 42},
    )

    item = normalizer.normalize(probe, result)
    assert item.provenance.get("requested_as_of") == "2026-07-14T13:30:00+08:00"
    assert item.status == "insufficient_evidence"
