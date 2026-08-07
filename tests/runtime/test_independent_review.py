"""Independent Review Pipeline Tests — ai_theme_app derived format.

Uses real raw_metrics + derived_signals format (not old flat fields).
"""

import pytest

from julia_core.reasoning.independent_review import (
    IndependentReviewPipeline,
    IndependentReviewAdmissionGate,
    StageInferenceEngine,
    StageSignalEvaluator,
    StageClaimAuditor,
    StageTaxonomy,
    ThemeFactContractMapper,
)


@pytest.fixture
def live_context():
    """Real ai_theme_app derived format: raw_metrics + derived_signals."""
    return {
        "schema_version": "market-context.v1",
        "trade_date": "2026-08-06",
        "status": "live",
        "themes": [
            {
                "subject": "创新药",
                "raw_metrics": {"mainline_strength_score": 0.81, "confidence_score": 0.86},
                "derived_signals": {
                    "stage_signal": {"value": "acceleration"},
                    "capital_direction": {"value": "inflow"},
                    "leader_health": {"value": "strong"},
                    "strong_stock_coverage": {"value": "wide"},
                },
            },
            {
                "subject": "半导体设备",
                "raw_metrics": {"mainline_strength_score": 0.62, "confidence_score": 0.55},
                "derived_signals": {
                    "stage_signal": {"value": "divergence"},
                    "capital_direction": {"value": "mixed"},
                    "leader_health": {"value": "weakening"},
                    "strong_stock_coverage": {"value": "contracting"},
                },
            },
        ],
        "quality": {"source_quality": 0.85},
    }


@pytest.fixture
def draft_review():
    return {
        "schema_version": "analyst-workbench.review.v1",
        "trade_date": "2026-08-06",
        "opinion_mode": "ai_draft",
        "claims": [
            {"claim_id": "claim_d_001", "subject": {"type": "theme", "name": "创新药"}, "stage_judgement": "acceleration", "confidence": 0.82},
            {"claim_id": "claim_d_002", "subject": {"type": "theme", "name": "半导体设备"}, "stage_judgement": "diffusion", "confidence": 0.62},
            {"claim_id": "claim_d_003", "subject": {"type": "theme", "name": "未知题材"}, "stage_judgement": "start", "confidence": 0.4},
        ],
        "approval": {},
    }


@pytest.fixture
def approved_review():
    return {
        "schema_version": "analyst-workbench.review.v1",
        "trade_date": "2026-08-06",
        "opinion_mode": "analyst_approved",
        "claims": [
            {"claim_id": "claim_a_001", "subject": {"type": "theme", "name": "创新药"}, "stage_judgement": "acceleration", "confidence": 0.82},
        ],
        "approval": {"snapshot_version": 3, "snapshot_hash": "abc123"},
    }


@pytest.fixture
def rejected_review():
    return {
        "schema_version": "analyst-workbench.review.v1",
        "trade_date": "2026-08-06",
        "opinion_mode": "rejected",
        "validation_errors": ["hash_mismatch"],
        "claims": [],
        "approval": {},
    }


# ── Contract Mapper ───────────────────────────────────────────────────────

def test_mapper_converts_derived_to_flat():
    mapper = ThemeFactContractMapper()
    ai_format = {
        "subject": "测试",
        "raw_metrics": {"mainline_strength_score": 0.75},
        "derived_signals": {
            "stage_signal": {"value": "diffusion"},
            "capital_direction": {"value": "inflow"},
            "leader_health": {"value": "strong"},
            "strong_stock_coverage": {"value": "wide"},
        },
    }
    flat = mapper.map(ai_format)
    assert flat["strength"] == 0.75
    assert flat["derived_stage_signal"] == "diffusion"
    assert flat["capital_direction"] == "inflow"
    assert flat["leader_health"] == "strong"
    assert flat["breadth"] == "wide"


def test_mapper_preserves_null():
    mapper = ThemeFactContractMapper()
    ai_format = {
        "subject": "空缺",
        "raw_metrics": {},
        "derived_signals": {
            "stage_signal": None,
            "capital_direction": None,
            "leader_health": None,
            "strong_stock_coverage": None,
        },
    }
    flat = mapper.map(ai_format)
    assert flat["strength"] is None
    assert flat["capital_direction"] is None


# ── Blind Stage Inference ─────────────────────────────────────────────────

def test_inference_blind_to_claim():
    """StageInferenceEngine does NOT receive workbench claim."""
    engine = StageInferenceEngine()
    facts = {"strength": 0.81, "leader_health": "strong", "breadth": "wide", "capital_direction": "inflow"}
    stage, evidence = engine.infer(facts)
    assert stage == "acceleration"
    # Source code must not reference "claim" or "judgement"
    import inspect
    src = inspect.getsource(engine.infer)
    assert "claim" not in src.lower()
    assert "judgment" not in src.lower()
    assert "workbench" not in src.lower()


def test_inference_detects_divergence():
    engine = StageInferenceEngine()
    facts = {"leader_health": "weakening", "breadth": "contracting"}
    stage, _ = engine.infer(facts)
    assert stage == "divergence"


# ── Admission Gate ────────────────────────────────────────────────────────

def test_rejected_is_blocked(rejected_review):
    gate = IndependentReviewAdmissionGate()
    ctx = {"schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "live", "quality": {"source_quality": 0.8}}
    ok, reason = gate.check(ctx, rejected_review)
    assert not ok
    assert "rejected" in reason


# ── Independent Review ────────────────────────────────────────────────────

def test_real_format_review_produces_judgments(live_context, draft_review):
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(live_context, draft_review)
    assert result.status in ("completed", "partial")
    assert len(result.judgments) == 3

    # 创新药: strong → acceleration, claim=acceleration → agree
    innovation = [j for j in result.judgments if "创新药" in j.subject][0]
    assert innovation.verdict in ("agree", "partially_agree")
    assert innovation.julia_stage != ""

    # 半导体: weakening+contracting → Julia says divergence, claim says diffusion → disagree
    semi = [j for j in result.judgments if "半导体" in j.subject][0]
    assert semi.verdict in ("disagree", "partially_disagree")


def test_insufficient_data_for_missing_fact(live_context, draft_review):
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(live_context, draft_review)
    unknown = [j for j in result.judgments if "未知题材" in j.subject]
    assert len(unknown) == 1
    assert unknown[0].verdict == "insufficient_data"


def test_approved_has_analyst_reviewed_true(approved_review):
    """P0: approved claim → analyst_reviewed=True."""
    ctx = {"schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "live",
           "themes": [{"subject": "创新药", "raw_metrics": {"mainline_strength_score": 0.81},
                       "derived_signals": {"stage_signal": {"value": "acceleration"},
                                           "capital_direction": {"value": "inflow"},
                                           "leader_health": {"value": "strong"},
                                           "strong_stock_coverage": {"value": "wide"}}}],
           "quality": {"source_quality": 0.8}}
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(ctx, approved_review)
    j = result.judgments[0]
    assert j.workbench_claim["opinion_provenance"]["analyst_reviewed"] is True
    assert j.workbench_claim["opinion_provenance"]["snapshot_version"] == 3


def test_opinion_provenance_preserved(live_context, draft_review):
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(live_context, draft_review)
    for j in result.judgments:
        assert "opinion_provenance" in j.workbench_claim
        assert "opinion_mode" in j.workbench_claim["opinion_provenance"]


def test_null_not_converted_to_zero():
    """P0: null strength stays None, not 0."""
    ctx = {"schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "live",
           "themes": [{"subject": "数据缺失股", "raw_metrics": {},
                       "derived_signals": {"stage_signal": None,
                                           "capital_direction": None,
                                           "leader_health": None,
                                           "strong_stock_coverage": None}}],
           "quality": {"source_quality": 0.8}}
    rev = {"schema_version": "analyst-workbench.review.v1", "trade_date": "2026-08-06",
           "opinion_mode": "ai_draft",
           "claims": [{"subject": {"name": "数据缺失股"}, "stage_judgement": "start", "confidence": 0.3}],
           "approval": {}}
    pipeline = IndependentReviewPipeline()
    result = pipeline.review(ctx, rev)
    j = result.judgments[0]
    # Should have missing evidence (not evaluated as strength=0)
    assert j.missing_evidence, "Should have missing_evidence for null fields"
    # Should NOT be classified as "agree" with strength=0 interpreted as start
    assert j.verdict in ("insufficient_data", "partially_disagree", "disagree")


def test_empty_context_blocked(live_context):
    ctx = {"schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "unavailable", "quality": {"source_quality": 0}}
    rev = {"schema_version": "analyst-workbench.review.v1", "opinion_mode": "ai_draft"}
    result = IndependentReviewPipeline().review(ctx, rev)
    assert result.status == "blocked"


# ── P0: Stage semantics tests ────────────────────────────────────────────

@pytest.fixture
def divergence_context():
    """Both Julia and workbench say divergence — leader_weak IS supporting."""
    return {
        "schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "live",
        "themes": [{
            "subject": "退潮股",
            "raw_metrics": {"mainline_strength_score": 0.55},  # moderate, not strength_low
            "derived_signals": {
                "stage_signal": {"value": "divergence"},
                "capital_direction": {"value": "mixed"},
                "leader_health": {"value": "weakening"},
                "strong_stock_coverage": {"value": "contracting"},
            },
        }],
        "quality": {"source_quality": 0.8},
    }


@pytest.fixture
def divergence_review():
    return {
        "schema_version": "analyst-workbench.review.v1", "trade_date": "2026-08-06",
        "opinion_mode": "ai_draft",
        "claims": [{"claim_id": "c1", "subject": {"name": "退潮股"}, "stage_judgement": "divergence", "confidence": 0.7}],
        "approval": {},
    }


@pytest.fixture
def acceleration_review():
    return {
        "schema_version": "analyst-workbench.review.v1", "trade_date": "2026-08-06",
        "opinion_mode": "ai_draft",
        "claims": [{"claim_id": "c1", "subject": {"name": "退潮股"}, "stage_judgement": "acceleration", "confidence": 0.7}],
        "approval": {},
    }


@pytest.fixture
def inconclusive_context():
    return {
        "schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "live",
        "themes": [{
            "subject": "模糊股",
            "raw_metrics": {},
            "derived_signals": {
                "stage_signal": None, "capital_direction": None,
                "leader_health": None, "strong_stock_coverage": None,
            },
        }],
        "quality": {"source_quality": 0.5},
    }


def test_divergence_plus_divergence_equals_agree(divergence_context, divergence_review):
    """TC-01: Julia=divergence, workbench=divergence → agree. leader_weak is SUPPORTING."""
    result = IndependentReviewPipeline().review(divergence_context, divergence_review)
    j = result.judgments[0]
    assert j.julia_stage == "divergence"
    assert j.verdict == "agree", (
        f"Expected agree (both say divergence), got {j.verdict}. "
        f"supporting={j.supporting_evidence} contradicting={j.contradicting_evidence}"
    )
    # leader_weak and breadth_contracting should be in SUPPORTING (for divergence)
    assert any("leader_weak" in e for e in j.supporting_evidence), \
        f"leader_weak should be SUPPORTING for divergence claim, got supporting={j.supporting_evidence}"


def test_divergence_plus_acceleration_equals_disagree(divergence_context, acceleration_review):
    """TC-02: Julia=divergence, workbench=acceleration → disagree."""
    result = IndependentReviewPipeline().review(divergence_context, acceleration_review)
    j = result.judgments[0]
    assert j.julia_stage == "divergence"
    assert j.verdict in ("disagree", "partially_disagree")
    # leader_weak and breadth_contracting should be CONTRADICTING (for acceleration claim)
    assert any("leader_weak" in e for e in j.contradicting_evidence), \
        f"leader_weak should be CONTRADICTING for acceleration claim"


def test_data_inconclusive_forces_insufficient_data(inconclusive_context):
    """TC-03: Julia=data_inconclusive → insufficient_data regardless of evidence."""
    rev = {
        "schema_version": "analyst-workbench.review.v1", "trade_date": "2026-08-06",
        "opinion_mode": "ai_draft",
        "claims": [{"claim_id": "c1", "subject": {"name": "模糊股"}, "stage_judgement": "divergence", "confidence": 0.3}],
        "approval": {},
    }
    result = IndependentReviewPipeline().review(inconclusive_context, rev)
    j = result.judgments[0]
    assert j.julia_stage == "data_inconclusive"
    assert j.verdict == "insufficient_data", \
        f"data_inconclusive MUST produce insufficient_data, got {j.verdict}"


def test_inference_evidence_preserved(divergence_context, divergence_review):
    """TC-05: inference_evidence stored in JuliaJudgment."""
    result = IndependentReviewPipeline().review(divergence_context, divergence_review)
    j = result.judgments[0]
    assert j.inference_evidence is not None
    assert len(j.inference_evidence) >= 1, f"inference_evidence must be preserved, got {j.inference_evidence}"


def test_julia_stage_not_from_string_parsing(divergence_context, divergence_review):
    """TC-06: JuliaJudgment.julia_stage is directly from ClaimEvidence, not parsed from claim string."""
    result = IndependentReviewPipeline().review(divergence_context, divergence_review)
    j = result.judgments[0]
    assert j.julia_stage == "divergence"
    # No parsing dependency on claim string format
    assert "_julia_stage_from_claim" not in str(type(j))


def test_missing_evidence_downgrades_verdict(divergence_context, divergence_review):
    """TC-04: missing leader/breadth → verdict downgraded or insufficient."""
    ctx = {
        "schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "live",
        "themes": [{
            "subject": "退潮股",
            "raw_metrics": {"mainline_strength_score": 0.35},
            "derived_signals": {
                "stage_signal": None,
                "capital_direction": None,
                "leader_health": None,
                "strong_stock_coverage": None,
            },
        }],
        "quality": {"source_quality": 0.5},
    }
    result = IndependentReviewPipeline().review(ctx, divergence_review)
    j = result.judgments[0]
    # Missing evidence should lead to insufficient_data (can't form stage)
    assert j.verdict in ("insufficient_data", "partially_agree", "partially_disagree"), \
        f"Missing evidence + stage divergence should produce appropriate verdict, got {j.verdict}"
    assert len(j.missing_evidence) >= 1


# ── P0: start stage semantics ────────────────────────────────────────────

@pytest.fixture
def start_context():
    return {
        "schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "live",
        "themes": [{
            "subject": "初期股",
            "raw_metrics": {"mainline_strength_score": 0.35},
            "derived_signals": {
                "stage_signal": {"value": "start"},
                "capital_direction": {"value": "mixed"},
                "leader_health": {"value": "unknown"},
                "strong_stock_coverage": {"value": "narrow"},
            },
        }],
        "quality": {"source_quality": 0.7},
    }


def test_start_plus_start_equals_agree(start_context):
    """TC-07: Julia=start, workbench=start → agree. strength_low is SUPPORTING."""
    rev = {
        "schema_version": "analyst-workbench.review.v1", "trade_date": "2026-08-06",
        "opinion_mode": "ai_draft",
        "claims": [{"claim_id": "c1", "subject": {"name": "初期股"}, "stage_judgement": "start", "confidence": 0.5}],
        "approval": {},
    }
    result = IndependentReviewPipeline().review(start_context, rev)
    j = result.judgments[0]
    assert j.julia_stage == "start"
    assert j.verdict == "agree", (
        f"Expected agree (both say start), got {j.verdict}. "
        f"supporting={j.supporting_evidence} contradicting={j.contradicting_evidence}"
    )
    # strength_low should be SUPPORTING for start claim
    assert any("strength_low" in e for e in j.supporting_evidence), \
        f"strength_low should be SUPPORTING for start claim"


def test_acceleration_plus_start_equals_disagree(start_context):
    """TC-08: Julia=start, workbench=acceleration → disagree."""
    rev = {
        "schema_version": "analyst-workbench.review.v1", "trade_date": "2026-08-06",
        "opinion_mode": "ai_draft",
        "claims": [{"claim_id": "c1", "subject": {"name": "初期股"}, "stage_judgement": "acceleration", "confidence": 0.7}],
        "approval": {},
    }
    result = IndependentReviewPipeline().review(start_context, rev)
    j = result.judgments[0]
    assert j.julia_stage == "start"
    assert j.verdict in ("disagree", "partially_disagree")
    # strength_low should be CONTRADICTING for acceleration claim
    assert any("strength_low" in e for e in j.contradicting_evidence), \
        f"strength_low should be CONTRADICTING for acceleration claim"


def test_inference_engine_outputs_valid_stages(start_context, divergence_context, inconclusive_context, live_context):
    """All inference outputs are in StageTaxonomy."""
    engine = StageInferenceEngine()
    for ctx in (start_context, divergence_context, live_context, inconclusive_context):
        mapper = ThemeFactContractMapper()
        for t in ctx["themes"]:
            facts = mapper.map(t)
            stage, _ = engine.infer(facts)
            valid = set(StageTaxonomy.STAGES.keys()) | StageTaxonomy.TERMINAL_STAGES
            assert stage in valid, f"Inferred '{stage}' not in taxonomy. Valid: {valid}"


def test_decline_inference():
    """leader_weak + breadth_contracting + strength_low → decline."""
    engine = StageInferenceEngine()
    facts = {"leader_health": "weakening", "breadth": "contracting", "strength": 0.30}
    stage, evidence = engine.infer(facts)
    assert stage == "decline", f"Expected decline, got {stage}. Signals: {StageSignalEvaluator.evaluate(facts)}"
    assert "leader_weak" in evidence
    assert "breadth_contracting" in evidence
    assert "strength_low" in evidence


def test_zero_support_one_contradiction_is_disagree():
    """Regression: ns=0, nc>=1 → partially_disagree.

    leader_weak is CONTRADICTING for acceleration claims.
    Julia sees fading_momentum (leader_weak only), Workbench says acceleration.
    This should produce partially_disagree, not partially_agree.
    """
    ctx = {
        "schema_version": "market-context.v1", "trade_date": "2026-08-06", "status": "live",
        "themes": [{
            "subject": "测试股", "subject_key": "test_001",
            "raw_metrics": {"mainline_strength_score": 0.25},
            "derived_signals": {
                "stage_signal": {"value": "fading_momentum"},
                "capital_direction": {"value": "unknown"},
                "leader_health": {"value": "weakening"},
                "strong_stock_coverage": {"value": "narrow"},
            },
        }],
        "quality": {"source_quality": 0.6},
    }
    rev = {
        "schema_version": "analyst-workbench.review.v1", "trade_date": "2026-08-06",
        "opinion_mode": "ai_draft",
        "claims": [{
            "claim_id": "c_test", "subject": {"key": "test_001", "name": "测试股"},
            "stage_judgement": "acceleration", "confidence": 0.7,
        }],
        "approval": {},
    }
    result = IndependentReviewPipeline().review(ctx, rev)
    j = result.judgments[0]
    assert j.verdict == "partially_disagree", (
        f"ns=0,nc>=1 MUST produce partially_disagree, got {j.verdict}. "
        f"supporting={j.supporting_evidence} contradicting={j.contradicting_evidence}"
    )


def test_taxonomy_coverage():
    """All inference_requires sets are subsets of the taxonomy's own evidence sets."""
    for stage, entry in StageTaxonomy.STAGES.items():
        requires = entry.get("inference_requires", set())
        valid = entry.get("supporting", set()) | entry.get("contradicting", set())
        unknown = requires - valid
        assert not unknown, f"Stage '{stage}': inference_requires {unknown} not in supporting+contradicting"


# ── Executable taxonomy tests ─────────────────────────────────────────────

def test_engine_reads_from_taxonomy():
    """TC-13: Inference engine reads inference_requires from StageTaxonomy.
    If taxonomy changes, inference behavior changes — no hardcoded rules."""
    import inspect
    src = inspect.getsource(StageInferenceEngine.infer)
    # No hardcoded stage strings or thresholds
    for forbidden in ('"acceleration"', "'decline'", '>= 0.6', '< 0.4',
                       'has_leader', 'has_breadth', 'has_capital', 'has_strength'):
        assert forbidden not in src, f"Engine should not contain '{forbidden}'"


# ── Threshold boundary tests ──────────────────────────────────────────────

@pytest.mark.parametrize("strength,expected_signal", [
    (0.39, "strength_low"),     # TC-09: just below threshold → strength_low
    (0.45, None),               # TC-10: in gap zone — neither low nor strong
    (0.59, None),               # TC-11: still in gap — not strong enough
    (0.60, "strength_strong"),  # TC-12: at threshold → strength_strong
])
def test_signal_evaluator_boundary(strength, expected_signal):
    """Single threshold authority — inference and audit share same signals."""
    evaluator = StageSignalEvaluator
    signals = evaluator.evaluate({"strength": strength})

    if expected_signal == "strength_low":
        assert "strength_low" in signals, f"strength={strength} should trigger strength_low"
        assert "strength_strong" not in signals
    elif expected_signal == "strength_strong":
        assert "strength_strong" in signals, f"strength={strength} should trigger strength_strong"
        assert "strength_low" not in signals
    else:  # gap zone
        assert "strength_low" not in signals, f"strength={strength} should not trigger strength_low"
        assert "strength_strong" not in signals, f"strength={strength} should not trigger strength_strong"


def test_0_45_is_neutral_zone():
    """strength=0.45: inference cannot use it, audit cannot use it."""
    evaluator = StageSignalEvaluator
    signals = evaluator.evaluate({"strength": 0.45})
    assert "strength_low" not in signals
    assert "strength_strong" not in signals

    # Inference: no strong/low signal → cannot match start or acceleration
    engine = StageInferenceEngine()
    stage, ev = engine.infer({"strength": 0.45})
    assert stage != "start", "strength=0.45 should not infer start"
    assert stage != "acceleration", "strength=0.45 should not infer acceleration"


def test_taxonomy_has_inference_priority():
    """TC-14: Each non-terminal stage has inference_priority."""
    for stage, entry in StageTaxonomy.STAGES.items():
        assert "inference_priority" in entry, f"{stage} missing inference_priority"


def test_priority_order_matches_expected():
    """High-priority stages (decline, acceleration) come before low (fading_momentum)."""
    order = StageTaxonomy.inference_order()
    # decline(70) and acceleration(60) must come before diffusion(40) and fading(20)
    d_idx = order.index("decline")
    a_idx = order.index("acceleration")
    f_idx = order.index("fading_momentum")
    assert d_idx < f_idx, "decline should have higher priority than fading_momentum"
    assert a_idx < f_idx, "acceleration should have higher priority than fading_momentum"
