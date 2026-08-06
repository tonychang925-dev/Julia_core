"""M3.1 Cognitive Gates Acceptance Tests — AC-M3.1-1 through AC-M3.1-4.

ADR-029: ObservationPolicy (rate limit + cooldown) and
ExperienceAdmission (confidence + evidence gate).

NO ai_theme_app connection. Pure cognitive filter tests.

Run:
  python -m pytest tests/runtime/test_m3_1_cognitive_gates.py -v
"""

import pytest

from julia_core.awareness.models import ObservationEvent, AwarenessArtifact
from julia_core.awareness.policy import ObservationPolicy
from julia_core.awareness.admission import ExperienceAdmission


# ── AC-M3.1-1: Noise Control — ObservationPolicy ────────────────────────────

def test_policy_accepts_significant_event():
    """First significant event is accepted."""
    policy = ObservationPolicy()
    event = ObservationEvent(
        subject="AI机器人", change_type="heat_jump", delta="+18",
        domain="market", confidence=0.82,
    )
    allowed, reason = policy.should_process(event)
    assert allowed, f"First event should be accepted, got: {reason}"


def test_policy_cooldown_blocks_repeat():
    """Same subject + same change_type blocked during cooldown."""
    policy = ObservationPolicy(cooldown_seconds=99999)  # effectively infinite
    event = ObservationEvent(
        subject="半导体", change_type="risk_spike", delta="-12",
        domain="market", confidence=0.75,
    )

    # First: accepted
    assert policy.should_process(event)[0] is True

    # Second (identical): rejected by cooldown
    allowed, reason = policy.should_process(event)
    assert allowed is False
    assert "cooldown" in reason


def test_policy_cooldown_per_subject_change_type():
    """Same subject but different change_type: NOT blocked by cooldown."""
    policy = ObservationPolicy(cooldown_seconds=99999)
    e1 = ObservationEvent(subject="低空经济", change_type="heat_jump", delta="+20", domain="market", confidence=0.8)
    e2 = ObservationEvent(subject="低空经济", change_type="risk_spike", delta="-10", domain="market", confidence=0.8)

    assert policy.should_process(e1)[0] is True   # heat_jump accepted
    assert policy.should_process(e2)[0] is True   # risk_spike — different type, not in cooldown


def test_policy_subject_rate_limit():
    """Same subject exceeds per_subject rate limit → blocked."""
    policy = ObservationPolicy(rate_limits={"per_subject": 3, "per_domain": 100, "global": 100})
    # Disable cooldown so we test pure rate limiting
    policy.cooldown_seconds = 0

    for i in range(3):
        e = ObservationEvent(subject="AI机器人", change_type=f"change_{i}", delta="+10", domain="market", confidence=0.8)
        allowed, _ = policy.should_process(e)
        assert allowed, f"Event {i} should be accepted"

    # 4th event: blocked
    e4 = ObservationEvent(subject="AI机器人", change_type="change_4", delta="+10", domain="market", confidence=0.8)
    allowed, reason = policy.should_process(e4)
    assert allowed is False
    assert "subject rate limit" in reason


# ── AC-M3.1-2: Memory Protection — ExperienceAdmission ─────────────────────

def test_admission_accepts_high_quality():
    """High confidence + multiple evidence → admitted."""
    admission = ExperienceAdmission(min_confidence=0.7, min_evidence_refs=2)
    artifact = AwarenessArtifact(
        subject="AI机器人", observation="heat increasing",
        confidence=0.85, evidence_refs=("evt_a", "evt_b"),
    )
    admitted, reason = admission.admit(artifact)
    assert admitted, f"High-quality artifact should be admitted, got: {reason}"


def test_admission_rejects_low_confidence():
    """Low confidence → short-term log only."""
    admission = ExperienceAdmission(min_confidence=0.7, min_evidence_refs=2)
    artifact = AwarenessArtifact(
        subject="noise", observation="minor fluctuation",
        confidence=0.5, evidence_refs=("evt_x", "evt_y", "evt_z"),
    )
    admitted, reason = admission.admit(artifact)
    assert admitted is False
    assert "confidence" in reason.lower()


def test_admission_rejects_single_source():
    """Single evidence source → unreliable, rejected."""
    admission = ExperienceAdmission(min_confidence=0.7, min_evidence_refs=2)
    artifact = AwarenessArtifact(
        subject="rumor", observation="unverified signal",
        confidence=0.9, evidence_refs=("evt_x",),
    )
    admitted, reason = admission.admit(artifact)
    assert admitted is False
    assert "evidence_refs" in reason


def test_admission_edge_case_exact_threshold():
    """Exactly at threshold → admitted (not rejected)."""
    admission = ExperienceAdmission(min_confidence=0.7, min_evidence_refs=2)
    artifact = AwarenessArtifact(
        subject="edge_case", observation="boundary test",
        confidence=0.7, evidence_refs=("evt_a", "evt_b"),
    )
    admitted, _ = admission.admit(artifact)
    assert admitted is True


# ── AC-M3.1-3: Evidence Preservation ────────────────────────────────────────

def test_artifact_preserves_evidence_chain():
    """Admitted artifact retains observation_id, evidence_refs, workflow_id."""
    artifact = AwarenessArtifact(
        observation_id="obs_test_123",
        workflow_id="corr_wf_test",
        subject="AI机器人",
        observation="heat increasing",
        evidence_refs=("evt_cap_001", "evt_ctx_002"),
        confidence=0.85,
        reasoning="Multiple sources confirm theme acceleration",
    )

    # Evidence chain is intact
    assert artifact.observation_id != ""
    assert artifact.workflow_id != ""
    assert len(artifact.evidence_refs) >= 2

    # Admission preserves these fields (doesn't mutate)
    admission = ExperienceAdmission()
    admitted, _ = admission.admit(artifact)
    assert admitted

    # Original artifact unchanged
    assert artifact.observation_id == "obs_test_123"
    assert artifact.evidence_refs == ("evt_cap_001", "evt_ctx_002")


# ── AC-M3.1-4: Capability Boundary ──────────────────────────────────────────

def test_policy_has_no_llm_dependency():
    """ObservationPolicy must NOT call LLM."""
    import inspect
    source = inspect.getsource(ObservationPolicy.should_process)
    assert "llm" not in source.lower()
    assert "provider" not in source.lower()
    assert "model" not in source.lower()


def test_admission_has_no_llm_dependency():
    """ExperienceAdmission must NOT call LLM."""
    import inspect
    source = inspect.getsource(ExperienceAdmission.admit)
    assert "llm" not in source.lower()
    assert "provider" not in source.lower()
    assert "model" not in source.lower()


# ── Integration: Policy + Admission end-to-end ──────────────────────────────

def test_full_cognitive_gate_pipeline():
    """Significant event → passes policy → artifact → passes admission."""
    # Step 1: Policy accepts
    policy = ObservationPolicy()
    event = ObservationEvent(
        subject="AI机器人", change_type="heat_jump", delta="+25",
        domain="market", confidence=0.85,
    )
    allowed, reason = policy.should_process(event)
    assert allowed, f"Policy should accept: {reason}"

    # Step 2: Artifact created (simulated workflow output)
    artifact = AwarenessArtifact(
        observation_id=event.observation_id,
        subject=event.subject,
        observation=f"{event.change_type} detected with delta {event.delta}",
        evidence_refs=("evt_cap_001", "evt_ctx_002"),
        confidence=0.85,
        reasoning="Strong multi-source signal",
    )

    # Step 3: Admission accepts
    admission = ExperienceAdmission()
    admitted, reason = admission.admit(artifact)
    assert admitted, f"Admission should accept: {reason}"

    # Step 4: Evidence chain is complete
    assert artifact.observation_id == event.observation_id
    assert len(artifact.evidence_refs) == 2
