"""RC2.5 public conversation ingress acceptance (TC-RC25-01..04)."""

from __future__ import annotations

import inspect
from concurrent.futures import ThreadPoolExecutor

from julia_core.public.conversation import (
    CoreConversationConfig,
    CoreConversationIngress,
    CoreConversationRequest,
)


def _request() -> CoreConversationRequest:
    return CoreConversationRequest("conv-1", "turn-1", "text", "hello")


def test_public_ingress_processes_typed_turn_through_core_runtime(monkeypatch, tmp_path):
    """TC-RC25-01: request -> Core ConversationRuntime -> typed response."""
    calls = []

    class FakeSession:
        def process(self, *args):
            return "CORE_SENTINEL"

    class FakeRuntime:
        def __init__(self, repository):
            self.repository = repository

        def process_turn(self, **kwargs):
            calls.append(kwargs)
            return type("Result", (), {
                "conversation_id": kwargs["conversation_id"],
                "turn_id": kwargs["turn_id"],
                "assistant_content": kwargs["cognitive_fn"]("x", [], "c", "t", "text", None),
                "status": "completed",
            })()

    monkeypatch.setattr("julia_core.public.conversation.JuliaSession", FakeSession)
    monkeypatch.setattr("julia_core.public.conversation.ConversationRuntime", FakeRuntime)
    ingress = CoreConversationIngress(CoreConversationConfig(tmp_path / "conversations"))
    response = ingress.process(_request())

    assert response.assistant_content == "CORE_SENTINEL"
    assert response.status == "completed"
    assert len(calls) == 1
    assert "cognitive_fn" in calls[0]


def test_public_ingress_missing_configuration_fails_closed():
    """TC-RC25-02: missing composition config cannot select Legacy JSON fallback."""
    response = CoreConversationIngress().process(_request())
    assert response.status == "failed"
    assert response.error_code == "CORE_COMPOSITION_UNAVAILABLE"
    assert response.assistant_content == ""


def test_real_core_composition_and_transport_worker_thread(tmp_path):
    """TC-RC25-05: real Core composition is usable from a worker thread."""
    ingress = CoreConversationIngress(CoreConversationConfig(tmp_path / "conversations"))
    ingress.create_conversation("real-conversation")
    request = CoreConversationRequest("real-conversation", "real-turn", "text", "hello")
    with ThreadPoolExecutor(max_workers=1) as pool:
        response = pool.submit(ingress.process, request).result()
    assert response.status == "completed"
    assert response.assistant_content


def test_real_core_domain_errors_remain_typed(tmp_path):
    """TC-RC25-06: missing conversation and conflicting turns stay distinct."""
    ingress = CoreConversationIngress(CoreConversationConfig(tmp_path / "conversations"))
    missing = ingress.process(_request())
    assert missing.error_code == "CONVERSATION_NOT_FOUND"
    ingress.create_conversation("conv-1")
    first = ingress.process(_request())
    conflict = ingress.process(CoreConversationRequest("conv-1", "turn-1", "text", "different"))
    assert first.status == "completed"
    assert conflict.error_code == "TURN_CONFLICT"


def test_public_surface_does_not_expose_cognition_or_repository_injection():
    """TC-RC25-03: external callers receive only config/request/process surface."""
    signature = inspect.signature(CoreConversationIngress.process)
    assert list(signature.parameters) == ["self", "request"]
    assert "repository" not in inspect.signature(CoreConversationIngress).parameters
    assert "cognitive_fn" not in inspect.signature(CoreConversationIngress.process).parameters


def test_public_response_is_typed_and_private_object_free():
    """TC-RC25-04: public response contains scalar transport-safe fields only."""
    fields = set(CoreConversationIngress.__annotations__) if hasattr(CoreConversationIngress, "__annotations__") else set()
    assert not fields
    response_fields = set(CoreConversationIngress().process(_request()).__dataclass_fields__)
    assert response_fields == {"conversation_id", "turn_id", "assistant_content", "status", "error_code"}
