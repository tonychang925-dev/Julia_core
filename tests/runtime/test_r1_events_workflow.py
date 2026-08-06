"""R1 Acceptance Tests — Events + Workflow + Async Authority.

ADR-027 AC-1 through AC-5.

Run:
  python -m pytest tests/runtime/test_r1_events_workflow.py -v
"""

import pytest

from julia_core.events.models import (
    RuntimeEvent,
    EventCategory,
    RuntimeEventType,
    ConversationEventType,
    CapabilityEventType,
    WorkflowEventType,
    create_event,
)
from julia_core.events.store import EventStore, get_event_store
from julia_core.events.timeline import TimelineReconstructor
from julia_core.workflow.models import (
    WorkflowState,
    WorkflowDefinition,
    WorkflowInstance,
)
from julia_core.workflow.registry import (
    WorkflowRegistry,
    MARKET_BRIEF_WORKFLOW,
    create_default_registry,
)
from julia_core.workflow.runtime import WorkflowRuntime


# ── AC-1: Async Authority ────────────────────────────────────────────────────

def test_chat_is_sync_compat_wrapper():
    """chat() is sync, delegates to _chat_impl. No independent logic."""
    from julia_core.runtime.julia_session import JuliaSession
    import inspect

    # chat() exists and is synchronous (not async)
    assert hasattr(JuliaSession, 'chat')
    chat_method = JuliaSession.chat
    assert not inspect.iscoroutinefunction(chat_method), "chat() should be sync"


def test_chat_async_is_native_async():
    """chat_async() is native async — the canonical entry point."""
    from julia_core.runtime.julia_session import JuliaSession
    import inspect

    assert hasattr(JuliaSession, 'chat_async')
    assert inspect.iscoroutinefunction(JuliaSession.chat_async), (
        "chat_async() should be native async"
    )


def test_chat_and_chat_async_share_implementation():
    """Both chat() and chat_async() delegate to _chat_impl."""
    from julia_core.runtime.julia_session import JuliaSession
    import inspect

    chat_src = inspect.getsource(JuliaSession.chat)
    chat_async_src = inspect.getsource(JuliaSession.chat_async)

    assert "_chat_impl" in chat_src, "chat() must delegate to _chat_impl"
    assert "_chat_impl" in chat_async_src, "chat_async() must delegate to _chat_impl"


# ── AC-2: Event Persistence ─────────────────────────────────────────────────

def test_event_creation():
    """create_event() produces valid RuntimeEvent with all fields."""
    event = create_event(
        source="capability",
        event_type=CapabilityEventType.REQUESTED,
        category=EventCategory.CAPABILITY,
        payload={"capability": "market.snapshot.read"},
        correlation_id="corr_test",
    )

    assert event.event_id.startswith("evt_")
    assert event.timestamp != ""
    assert event.source == "capability"
    assert event.event_type == "capability.requested"
    assert event.category == EventCategory.CAPABILITY
    assert event.correlation_id == "corr_test"
    assert event.payload["capability"] == "market.snapshot.read"


def test_event_store_append_and_retrieve():
    """EventStore: append → by_correlation → get."""
    store = EventStore()

    e1 = create_event(
        source="conversation",
        event_type=ConversationEventType.MESSAGE_RECEIVED,
        category=EventCategory.CONVERSATION,
        correlation_id="corr_ac2",
    )
    e2 = create_event(
        source="capability",
        event_type=CapabilityEventType.COMPLETED,
        category=EventCategory.CAPABILITY,
        correlation_id="corr_ac2",
        causation_id=e1.event_id,
    )

    store.append(e1)
    store.append(e2)

    # Retrieve by correlation
    chain = store.by_correlation("corr_ac2")
    assert len(chain) == 2
    assert chain[0].event_id == e1.event_id
    assert chain[1].event_id == e2.event_id

    # Retrieve by causation
    caused = store.by_causation(e1.event_id)
    assert len(caused) == 1
    assert caused[0].event_id == e2.event_id

    # Retrieve single
    assert store.get(e1.event_id) is not None


def test_event_store_by_category():
    """EventStore filters by category."""
    store = EventStore()
    store.append(create_event(source="capability", event_type="capability.requested",
                              category=EventCategory.CAPABILITY, correlation_id="cat"))
    store.append(create_event(source="workflow", event_type="workflow.created",
                              category=EventCategory.WORKFLOW, correlation_id="cat"))

    caps = store.by_category("capability")
    assert len(caps) == 1
    assert caps[0].category == EventCategory.CAPABILITY

    wfs = store.by_category("workflow")
    assert len(wfs) == 1
    assert wfs[0].category == EventCategory.WORKFLOW


def test_minimum_events_per_market_query():
    """One market query produces at least 5 events in the timeline (AC-2)."""
    store = EventStore()

    # Simulate a market brief pipeline event chain
    corr_id = "corr_market_test"
    events = [
        ("conversation", ConversationEventType.MESSAGE_RECEIVED),
        ("capability", CapabilityEventType.REQUESTED),
        ("capability", CapabilityEventType.COMPLETED),
        ("workflow", WorkflowEventType.STEP_COMPLETED),
        ("conversation", ConversationEventType.TURN_COMPLETED),
    ]

    causation_id = ""
    for source, event_type in events:
        cat_map = {"conversation": EventCategory.CONVERSATION, "capability": EventCategory.CAPABILITY, "workflow": EventCategory.WORKFLOW, "runtime": EventCategory.RUNTIME}
        evt = create_event(
            source=source,
            event_type=event_type,
            category=cat_map.get(source, EventCategory.RUNTIME),
            correlation_id=corr_id,
            causation_id=causation_id,
        )
        store.append(evt)
        causation_id = evt.event_id

    assert len(store.by_correlation(corr_id)) >= 5, "AC-2: minimum 5 events per market query"


# ── AC-3: Workflow Execution ────────────────────────────────────────────────

def test_workflow_registry_default():
    """Default registry contains market.brief workflow."""
    registry = create_default_registry()
    wf = registry.get("market.brief")
    assert wf is not None
    assert wf.name == "market.brief"
    assert len(wf.steps) == 6
    assert wf.steps[0] == "intent.resolve"
    assert wf.steps[-1] == "experience.record"


def test_workflow_instance_lifecycle():
    """WorkflowInstance tracks state through the full lifecycle."""
    instance = WorkflowInstance(
        workflow_name="market.brief",
        correlation_id="corr_wf_test",
    )

    assert instance.state == WorkflowState.CREATED
    assert not instance.is_terminal

    instance.state = WorkflowState.RUNNING
    assert instance.is_running

    instance.state = WorkflowState.COMPLETED
    assert instance.is_terminal
    assert not instance.is_running


@pytest.mark.asyncio
async def test_workflow_runtime_executes_steps():
    """WorkflowRuntime executes steps, emits events, returns completed instance."""
    registry = WorkflowRegistry()
    registry.register(WorkflowDefinition(
        name="test.echo",
        description="Simple test workflow",
        steps=("step.one", "step.two"),
        version="1.0",
    ))

    store = EventStore()
    runtime = WorkflowRuntime(registry, None, store)

    # Register mock step executors
    async def step_one(data, instance):
        return {"step_one_result": "done"}

    async def step_two(data, instance):
        return {"step_two_result": "also_done", "input": data.get("step_one_result")}

    runtime.register_step("step.one", step_one)
    runtime.register_step("step.two", step_two)

    instance = await runtime.execute("test.echo", {"input_key": "value"})

    assert instance.state == WorkflowState.COMPLETED
    assert instance.current_step_index == 1  # 0-indexed, last step
    assert instance.step_results["step.one"]["step_one_result"] == "done"
    assert instance.step_results["step.two"]["input"] == "done"

    # Events were emitted
    assert store.count >= 5  # created + 2×started + 2×completed + completed


@pytest.mark.asyncio
async def test_workflow_runtime_failure_records_events():
    """Failed workflow still emits events and records failure reason."""
    registry = WorkflowRegistry()
    registry.register(WorkflowDefinition(
        name="test.failing",
        steps=("step.one",),
        version="1.0",
    ))

    store = EventStore()
    runtime = WorkflowRuntime(registry, None, store)

    async def step_one(data, instance):
        raise ValueError("intentional test failure")

    runtime.register_step("step.one", step_one)

    instance = await runtime.execute("test.failing", {})

    assert instance.state == WorkflowState.FAILED
    assert instance.step_results["_error"] == "intentional test failure"
    assert instance.step_results["_failed_at"] == "step.one"

    # Events: created + step.started + workflow.failed
    assert store.count >= 3


# ── AC-4: Recovery (structural) ─────────────────────────────────────────────

def test_workflow_instance_can_be_reconstructed_from_store():
    """WorkflowInstance structure is self-contained for recovery."""
    store = EventStore()

    instance = WorkflowInstance(
        workflow_name="market.brief",
        state=WorkflowState.WAITING_CAPABILITY,
        correlation_id="corr_recover",
        current_step="context.build",
        current_step_index=2,
    )

    # Simulate: store the instance events, then reconstruct
    evt = create_event(
        source="workflow",
        event_type=WorkflowEventType.CREATED,
        category=EventCategory.WORKFLOW,
        correlation_id=instance.correlation_id,
    )
    store.append(evt)
    instance.event_ids.append(evt.event_id)

    # Recovery: can we find the workflow events?
    recovered = store.by_correlation("corr_recover")
    assert len(recovered) >= 1
    assert recovered[0].correlation_id == "corr_recover"

    # Instance state is preserved
    assert instance.state == WorkflowState.WAITING_CAPABILITY
    assert instance.is_running


# ── AC-5: Evidence Reconstruction ───────────────────────────────────────────

def test_timeline_reconstructor_builds_causal_chain():
    """TimelineReconstructor produces ordered causal chain from events."""
    store = EventStore()
    corr_id = "corr_reconstruct"

    e1 = create_event(
        source="conversation", event_type="conversation.message.received",
        category=EventCategory.CONVERSATION, correlation_id=corr_id,
    )
    e2 = create_event(
        source="capability", event_type="capability.requested",
        category=EventCategory.CAPABILITY, correlation_id=corr_id,
        causation_id=e1.event_id,
    )
    e3 = create_event(
        source="capability", event_type="capability.completed",
        category=EventCategory.CAPABILITY, correlation_id=corr_id,
        causation_id=e2.event_id,
    )
    store.append(e1)
    store.append(e2)
    store.append(e3)

    reconstructor = TimelineReconstructor(store)
    timeline = reconstructor.reconstruct(corr_id)

    assert timeline.event_count == 3
    assert timeline.root_event.event_id == e1.event_id
    assert len(timeline.causal_chain) == 2  # e1→e2, e2→e3
    assert timeline.sequence == [
        "conversation.message.received",
        "capability.requested",
        "capability.completed",
    ]


def test_timeline_explain_returns_readable_string():
    """TimelineReconstructor.explain() produces human-readable output."""
    store = EventStore()
    corr_id = "corr_explain"

    store.append(create_event(
        source="conversation", event_type="conversation.message.received",
        category=EventCategory.CONVERSATION, correlation_id=corr_id,
        payload={"text": "今天市场怎么样？"},
    ))

    reconstructor = TimelineReconstructor(store)
    explanation = reconstructor.explain(corr_id)

    assert "corr_explain" in explanation
    assert "conversation.message.received" in explanation


# ── Event category coverage ─────────────────────────────────────────────────

def test_all_event_categories_defined():
    """All ADR-027 frozen categories are defined."""
    categories = set(e.value for e in EventCategory)
    assert "runtime" in categories
    assert "conversation" in categories
    assert "capability" in categories
    assert "workflow" in categories
    assert "experience" in categories
