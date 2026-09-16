"""RC2.5 public conversation ingress acceptance (TC-RC25-01..04)."""

from __future__ import annotations

import inspect

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
        def __init__(self, provider=None):
            self.provider = provider

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
    monkeypatch.setattr("julia_core.providers.core_cognition._get_cognition_provider", lambda _name: object())
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


def test_no_registered_real_provider_fails_closed(tmp_path):
    """TC-RC25-07: deterministic or Assistant providers are never a default."""
    response = CoreConversationIngress(CoreConversationConfig(tmp_path / "conversations")).process(_request())
    assert response.status == "failed"
    assert response.error_code == "CORE_PROVIDER_UNAVAILABLE"
    assert response.assistant_content == ""


def test_real_composition_requires_explicit_test_provider(tmp_path, monkeypatch):
    """TC-RC25-08: test provider injection is explicit and registry-mediated."""
    class TestProvider:
        def chat(self, messages, *, cognitive_mode=""):
            return "TEST_PROVIDER_SENTINEL"

    monkeypatch.setattr(
        "julia_core.providers.core_cognition._get_cognition_provider",
        lambda _name: TestProvider(),
    )
    ingress = CoreConversationIngress(CoreConversationConfig(tmp_path / "conversations"))
    ingress.create_conversation("configured")
    response = ingress.process(CoreConversationRequest("configured", "turn", "text", "hello"))
    assert response.status == "completed"
    assert response.assistant_content == "TEST_PROVIDER_SENTINEL"


def test_real_core_domain_errors_remain_typed(tmp_path, monkeypatch):
    """TC-RC25-06: missing conversation and conflicting turns stay distinct."""
    monkeypatch.setattr(
        "julia_core.providers.core_cognition._get_cognition_provider",
        lambda _name: type("TestProvider", (), {"chat": lambda self, messages, cognitive_mode="": "domain answer"})(),
    )
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
    response_fields = set(CoreConversationIngress().process(_request()).__dataclass_fields__)
    assert response_fields == {"conversation_id", "turn_id", "assistant_content", "status", "error_code"}
