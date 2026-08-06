"""M3.0 Awareness Runtime Acceptance Tests — AC-M3-1 through AC-M3-5.

Synthetic world events → ObservationWorkflow → Artifact → Timeline.
NO ai_theme_app connection. Proves the awareness pipeline.

Run:
  python -m pytest tests/runtime/test_m3_awareness.py -v
"""

import pytest

from julia_core.awareness.models import ObservationEvent, AwarenessArtifact
from julia_core.awareness.router import ObservationRouter, SignificanceResult
from julia_core.awareness.runtime import AwarenessRuntime, AwarenessResult
from julia_core.events.store import EventStore, get_event_store
from julia_core.events.timeline import TimelineReconstructor
from julia_core.workflow.registry import WorkflowRegistry
from julia_core.workflow.runtime import WorkflowRuntime
from julia_core.workflow.observation.models import MARKET_OBSERVATION_WORKFLOW
from julia_core.workflow.models import WorkflowState


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def event_store():
    return EventStore()


@pytest.fixture
def router():
    return ObservationRouter()


@pytest.fixture
def workflow_runtime(event_store):
    """WorkflowRuntime with synthetic observation steps — no real MCP."""
    registry = WorkflowRegistry()
    registry.register(MARKET_OBSERVATION_WORKFLOW)
    runtime = WorkflowRuntime(registry, None, event_store)

    # Register mock steps for M3.0 skeleton
    async def collect_evidence(data, instance):
        return {"evidence": f"synthetic_snapshot_{data.get('subject', 'unknown')}",
                "evidence_count": 1}

    async def build_context(data, instance):
        return {"context_built": True, "subject": data.get("subject")}

    async def evaluate_significance(data, instance):
        return {"significant": True, "reason": f"Synthetic: {data.get('change_type')} detected"}

    async def generate_artifact(data, instance):
        from julia_core.awareness.models import AwarenessArtifact
        artifact = AwarenessArtifact(
            observation_id=data.get("observation_id", ""),
            workflow_id=instance.correlation_id,
            subject=data.get("subject", "unknown"),
            observation=f"Synthetic observation: {data.get('change_type', 'unknown')}",
            evidence_refs=(f"evt_{instance.correlation_id}",),
            confidence=0.78,
            reasoning=f"Detected {data.get('change_type')} on {data.get('subject')}",
        )
        return {"artifact": artifact, "artifact_created": True}

    async def store_experience(data, instance):
        return {"experience_recorded": True, "artifact_id": data.get("artifact", None)}

    runtime.register_step("observe.collect_evidence", collect_evidence)
    runtime.register_step("observe.build_context", build_context)
    runtime.register_step("observe.evaluate_significance", evaluate_significance)
    runtime.register_step("observe.generate_artifact", generate_artifact)
    runtime.register_step("observe.store_experience", store_experience)

    return runtime


@pytest.fixture
def awareness_runtime(router, workflow_runtime, event_store):
    return AwarenessRuntime(router, workflow_runtime, event_store)


# ── AC-M3-1: Event Ingestion ────────────────────────────────────────────────

def test_observation_event_is_distinct_from_capability_result():
    """ObservationEvent is NOT a CapabilityResult — it describes world change."""
    event = ObservationEvent(
        source="ai_theme_app",
        domain="market",
        event_type="world.market.changed",
        subject="AI机器人",
        change_type="heat_jump",
        delta="+18",
        confidence=0.82,
        evidence_refs=("market_snapshot_001",),
    )

    # Has observation-specific fields
    assert event.observation_id.startswith("obs_")
    assert event.domain == "market"
    assert event.change_type == "heat_jump"
    assert event.delta == "+18"
    assert event.evidence_refs == ("market_snapshot_001",)
    # Has provenance
    assert event.source != ""
    assert event.detected_at != ""


def test_event_ingestion_into_event_store(event_store):
    """AC-M3-1: ObservationEvent enters EventStore as runtime event."""
    obs = ObservationEvent(
        source="ai_theme_app",
        event_type="world.market.changed",
        subject="半导体",
        change_type="risk_spike",
        delta="-8",
        correlation_id="corr_m3_ingest",
    )

    from julia_core.events.models import EventCategory, create_event
    evt = create_event(
        source=obs.source,
        event_type=obs.event_type,
        category=EventCategory.WORKFLOW,
        payload={"observation_id": obs.observation_id, "subject": obs.subject},
        correlation_id=obs.correlation_id,
    )
    event_store.append(evt)

    # Event is retrievable
    chain = event_store.by_correlation("corr_m3_ingest")
    assert len(chain) == 1
    assert chain[0].event_type == "world.market.changed"


# ── AC-M3-2: Event → Workflow ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_significant_event_creates_workflow(awareness_runtime):
    """AC-M3-2: Significant observation triggers workflow creation."""
    obs = ObservationEvent(
        source="ai_theme_app",
        event_type="world.market.changed",
        subject="AI机器人",
        change_type="heat_jump",
        delta="+18",
        confidence=0.82,
        correlation_id="corr_m3_wf",
    )

    result = await awareness_runtime.process(obs)

    assert result.significant is True
    assert result.workflow_instance is not None
    assert result.workflow_instance.state == WorkflowState.COMPLETED
    assert result.workflow_instance.workflow_name == "observation.market"


@pytest.mark.asyncio
async def test_insignificant_event_skips_workflow(awareness_runtime):
    """Below-threshold event does NOT trigger workflow."""
    obs = ObservationEvent(
        source="ai_theme_app",
        event_type="world.market.changed",
        subject="noise",
        change_type="heat_jump",
        delta="+3",         # below min_delta_abs=10
        confidence=0.3,     # below min_confidence=0.5
        correlation_id="corr_m3_skip",
    )

    result = await awareness_runtime.process(obs)

    assert result.significant is False
    assert result.workflow_instance is None
    assert "delta" in result.reason.lower() or "confidence" in result.reason.lower()


# ── AC-M3-3: Workflow → Capability (structural check) ──────────────────────

def test_observation_workflow_uses_capability_manager():
    """AC-M3-3: Workflow definition expects capability step, not direct MCP."""
    assert MARKET_OBSERVATION_WORKFLOW is not None
    assert "observe.collect_evidence" in MARKET_OBSERVATION_WORKFLOW.steps

    # Workflow does NOT contain MCP tool names
    tool_names = " ".join(MARKET_OBSERVATION_WORKFLOW.steps)
    assert "mcp" not in tool_names.lower()
    assert "review_market_snapshot" not in tool_names
    assert "list_active_alerts" not in tool_names


# ── AC-M3-4: Awareness Artifact ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_workflow_produces_artifact(awareness_runtime):
    """AC-M3-4: Workflow produces AwarenessArtifact with evidence."""
    obs = ObservationEvent(
        source="ai_theme_app",
        event_type="world.market.changed",
        subject="低空经济",
        change_type="new_pattern",
        delta="new_high",
        confidence=0.85,
        correlation_id="corr_m3_artifact",
    )

    result = await awareness_runtime.process(obs)
    assert result.workflow_instance is not None

    # Artifact was created
    artifact_step = result.workflow_instance.step_results.get("observe.generate_artifact", {})
    assert artifact_step.get("artifact_created") is True

    artifact = artifact_step.get("artifact")
    assert artifact is not None
    assert artifact.subject == "低空经济"
    assert artifact.confidence == 0.78
    assert len(artifact.evidence_refs) >= 1


# ── AC-M3-5: Timeline Reconstruction ───────────────────────────────────────

@pytest.mark.asyncio
async def test_timeline_from_observation(awareness_runtime, event_store):
    """AC-M3-5: Full timeline reconstruction from observation_id."""
    obs = ObservationEvent(
        source="ai_theme_app",
        event_type="world.market.changed",
        subject="半导体",
        change_type="risk_spike",
        delta="-12",
        confidence=0.72,
        correlation_id="corr_m3_timeline",
    )

    result = await awareness_runtime.process(obs)
    assert result.workflow_instance is not None

    # Reconstruct timeline
    reconstructor = TimelineReconstructor(event_store)
    timeline = reconstructor.reconstruct("corr_m3_timeline")

    assert timeline.event_count >= 6, f"Expected >=6 events, got {timeline.event_count}"
    assert timeline.root_event is not None
    assert timeline.root_event.event_type == "world.market.changed"

    # Human-readable explanation
    explanation = reconstructor.explain("corr_m3_timeline")
    assert "world.market.changed" in explanation
    assert "workflow.created" in explanation
    assert "workflow.completed" in explanation


# ── Router unit tests ───────────────────────────────────────────────────────

def test_router_significant_heat_jump(router):
    """High delta + confidence → significant."""
    event = ObservationEvent(change_type="heat_jump", delta="+18", confidence=0.82, subject="test")
    result = router.evaluate(event)
    assert result.significant is True


def test_router_insignificant_low_delta(router):
    """Low delta → not significant."""
    event = ObservationEvent(change_type="heat_jump", delta="+3", confidence=0.8, subject="test")
    result = router.evaluate(event)
    assert result.significant is False


def test_router_zero_confidence_noise(router):
    """Zero confidence → always noise."""
    event = ObservationEvent(change_type="heat_jump", delta="+50", confidence=0.0, subject="test")
    result = router.evaluate(event)
    assert result.significant is False


def test_router_unknown_type_high_confidence(router):
    """Unknown change type with high confidence → significant."""
    event = ObservationEvent(change_type="unknown_pattern", delta="+30", confidence=0.75, subject="test")
    result = router.evaluate(event)
    assert result.significant is True


# ── Forbidden: Router does NOT use LLM ──────────────────────────────────────

def test_router_has_no_llm_dependency():
    """ADR-028 Section 3: ObservationRouter must NOT call LLM."""
    import inspect
    source = inspect.getsource(ObservationRouter.evaluate)
    assert "llm" not in source.lower()
    assert "provider.chat" not in source
    assert "model" not in source.lower()
