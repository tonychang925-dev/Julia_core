"""M3.2 Contract Acceptance Tests — AC-M3.2-1 through AC-M3.2-8.

ADR-030: Integration contract validation with mock data.
NO ai_theme_app MCP connection. Pure contract verification.

Run:
  python -m pytest tests/m3_2/test_contract.py -v
"""

import pytest

from julia_core.awareness.ingestion import IntelligenceAdapter, FORBIDDEN_DOMAIN_FIELDS
from julia_core.awareness.identity import ObservationIdentity, time_window
from julia_core.awareness.models import AwarenessArtifact
from julia_core.experience.tiers import ExperienceTier, ExperienceTierRouter, TierResult


# ── Mock ai_theme_app data ──────────────────────────────────────────────────

MOCK_CAPABILITY_RESULT = {
    "capability": "market.intelligence.observe",
    "source": "ai_theme_app_analyst_workbench",
    "schema_version": "1.1",
    "generated_at": "2026-08-06T09:30:00+08:00",
    "observations": [
        {
            "id": "obs_001",
            "type": "theme.breakout",
            "theme": "AI机器人",
            "signal_level": "L3",
            "summary": "机器人产业链出现资金共振",
            "evidence": ["theme_heat_+18%", "fund_flow_increase", "leader_strength"],
            "confidence": 0.86,
            "prediction_id": "pred_001",
            "decision_envelope_ref": "dec_001",
        },
        {
            "id": "obs_002",
            "type": "risk.emerged",
            "theme": "半导体",
            "signal_level": "L2",
            "summary": "板块出现分化信号",
            "evidence": ["sentiment_shift"],
            "confidence": 0.62,
        },
        {
            "id": "obs_003",
            "type": "sentiment.shift",
            "theme": "整体市场",
            "signal_level": "L1",
            "summary": "大盘情绪小幅波动",
            "evidence": ["index_flat"],
            "confidence": 0.45,
        },
    ],
}

MOCK_CAPABILITY_RESULT_DUPLICATE = {
    "capability": "market.intelligence.observe",
    "source": "ai_theme_app_analyst_workbench",
    "schema_version": "1.1",
    "generated_at": "2026-08-06T09:31:00+08:00",  # same 15min window
    "observations": [
        {
            "id": "obs_001b",
            "type": "theme.breakout",
            "theme": "AI机器人",                      # same subject
            "signal_level": "L3",
            "summary": "机器人产业链资金继续推升",
            "evidence": ["fund_flow_increase"],
            "confidence": 0.84,
            "prediction_id": "pred_001b",
        },
    ],
}


# ── AC-M3.2-1: Adapter Boundary ─────────────────────────────────────────────

def test_adapter_converts_capability_to_observation_events():
    """DecisionEnvelope-level data → ObservationEvents. No raw fields leak."""
    adapter = IntelligenceAdapter()
    events = adapter.convert(MOCK_CAPABILITY_RESULT)

    assert len(events) == 3
    for event in events:
        assert event.source == "ai_theme_app_analyst_workbench"
        assert event.domain == "market"
        assert event.subject != ""
        assert event.event_type.startswith("world.market.")


def test_forbidden_fields_do_not_leak():
    """ai_theme_app internal fields MUST NOT appear in ObservationEvent payload."""
    adapter = IntelligenceAdapter()
    events = adapter.convert(MOCK_CAPABILITY_RESULT)

    for event in events:
        payload_str = str(event.payload)
        for forbidden in FORBIDDEN_DOMAIN_FIELDS:
            assert forbidden not in payload_str, (
                f"Forbidden field '{forbidden}' leaked into ObservationEvent payload"
            )


def test_adapter_provider_metadata_preserved():
    """Provider metadata (source, schema_version) carried through adapter."""
    adapter = IntelligenceAdapter()
    events = adapter.convert(MOCK_CAPABILITY_RESULT)

    for event in events:
        assert "provider_name" in event.payload
        assert "schema_version" in event.payload
        assert event.payload["provider_name"] == "ai_theme_app_analyst_workbench"


def test_adapter_rejects_unknown_schema():
    """Unknown schema_version → reject, don't silently parse."""
    adapter = IntelligenceAdapter()
    ok, reason = adapter.validate_schema({"schema_version": "2.0"})
    assert ok is False
    assert "unknown" in reason.lower() or "2.0" in reason


def test_adapter_accepts_valid_schema():
    """Valid schema versions pass validation."""
    adapter = IntelligenceAdapter()
    assert adapter.validate_schema({"schema_version": "1.0"})[0] is True
    assert adapter.validate_schema({"schema_version": "1.1"})[0] is True


# ── AC-M3.2-2: Deduplication ────────────────────────────────────────────────

def test_identity_key_same_subject_type_window():
    """Same domain+subject+type+window → same key (duplicate)."""
    key1 = ObservationIdentity.key_from_dict({
        "domain": "market", "theme": "AI机器人",
        "type": "theme.breakout",
        "generated_at": "2026-08-06T09:30:00+08:00",
    })
    key2 = ObservationIdentity.key_from_dict({
        "domain": "market", "theme": "AI机器人",
        "type": "theme.breakout",
        "generated_at": "2026-08-06T09:31:00+08:00",  # same window
    })
    assert key1 == key2, f"Same-window events should have same key: {key1} != {key2}"


def test_identity_key_different_window():
    """Different 15min window → different key."""
    key1 = ObservationIdentity.key_from_dict({
        "domain": "market", "theme": "AI机器人",
        "type": "theme.breakout",
        "generated_at": "2026-08-06T09:30:00+08:00",
    })
    key2 = ObservationIdentity.key_from_dict({
        "domain": "market", "theme": "AI机器人",
        "type": "theme.breakout",
        "generated_at": "2026-08-06T09:46:00+08:00",  # next window
    })
    assert key1 != key2


def test_identity_is_duplicate_detection():
    """is_duplicate() returns True for same event within window."""
    identity = ObservationIdentity()

    from julia_core.awareness.models import ObservationEvent
    event = ObservationEvent(
        source="test", domain="market", event_type="world.market.changed",
        subject="AI机器人", change_type="heat_jump", confidence=0.8,
        detected_at="2026-08-06T09:30:00+08:00",
    )

    assert identity.is_duplicate(event) is False  # first time
    assert identity.is_duplicate(event) is True   # second time (same key)


# ── AC-M3.2-3 & AC-M3.2-4: Tier Routing ────────────────────────────────────

def test_tier_l1_goes_to_cache():
    """L1 signal → cache (not experience)."""
    router = ExperienceTierRouter()
    artifact = AwarenessArtifact(subject="test", confidence=0.5, evidence_refs=("e1",))
    result = router.route(artifact, signal_level="L1")
    assert result.tier == ExperienceTier.CACHE


def test_tier_l0_goes_to_discard():
    """L0 signal → discard."""
    router = ExperienceTierRouter()
    artifact = AwarenessArtifact(subject="test", confidence=0.1, evidence_refs=())
    result = router.route(artifact, signal_level="L0")
    assert result.tier == ExperienceTier.DISCARD


def test_tier_l3_high_quality_goes_to_experience():
    """L3 + confidence>=0.7 + evidence>=2 → experience."""
    router = ExperienceTierRouter()
    artifact = AwarenessArtifact(
        subject="AI机器人", confidence=0.86,
        evidence_refs=("pred_001", "dec_001"),
    )
    result = router.route(artifact, signal_level="L3")
    assert result.tier == ExperienceTier.EXPERIENCE
    assert "confidence" in result.reason
    assert "evidence" in result.reason


def test_tier_l3_low_confidence_falls_to_working():
    """L3 with insufficient confidence → working, not experience."""
    router = ExperienceTierRouter()
    artifact = AwarenessArtifact(
        subject="test", confidence=0.5,
        evidence_refs=("e1", "e2"),
    )
    result = router.route(artifact, signal_level="L3")
    assert result.tier == ExperienceTier.WORKING


def test_tier_l4_experience_threshold():
    """L4 requires confidence >= 0.8 for experience."""
    router = ExperienceTierRouter()
    artifact = AwarenessArtifact(
        subject="critical", confidence=0.85,
        evidence_refs=("e1", "e2"),
    )
    result = router.route(artifact, signal_level="L4")
    assert result.tier == ExperienceTier.EXPERIENCE


# ── AC-M3.2-5: Timeline (structural) ────────────────────────────────────────

def test_artifact_preserves_full_chain():
    """Artifact carries observation_id, evidence_refs for timeline reconstruction."""
    adapter = IntelligenceAdapter()
    events = adapter.convert(MOCK_CAPABILITY_RESULT)

    # First event → awareness artifact
    l3_event = events[0]
    artifact = AwarenessArtifact(
        observation_id=l3_event.observation_id,
        subject=l3_event.subject,
        observation=l3_event.payload.get("summary", ""),
        evidence_refs=l3_event.evidence_refs,
        confidence=l3_event.confidence,
    )

    # Artifact linked back to observation
    assert artifact.observation_id == l3_event.observation_id
    assert len(artifact.evidence_refs) >= 1
    assert artifact.confidence == 0.86


# ── AC-M3.2-6 & AC-M3.2-7: Provider Failure Isolation ──────────────────────

def test_provider_unavailable_does_not_crash_runtime():
    """When ai_theme_app is unavailable, adapter handles empty data gracefully."""
    adapter = IntelligenceAdapter()
    events = adapter.convert({"observations": []})
    assert events == []


def test_schema_mismatch_rejected():
    """Unknown schema version → adapter rejects."""
    adapter = IntelligenceAdapter()
    ok, reason = adapter.validate_schema({"schema_version": "3.0-beta"})
    assert ok is False
