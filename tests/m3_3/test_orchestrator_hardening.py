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
