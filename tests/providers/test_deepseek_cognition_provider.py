"""Focused transport-only DeepSeek provider and cold-start proofs."""

from __future__ import annotations

import importlib
import io
import json
from pathlib import Path

import pytest

import julia_core.providers.core_cognition as core_cognition
from julia_core.providers.deepseek import (
    DeepSeekCognitionProvider,
    DeepSeekCognitionProviderError,
)


@pytest.fixture(autouse=True)
def reset_provider_registry():
    core_cognition._providers.clear()
    core_cognition._production_initialization_attempted = False
    yield
    core_cognition._providers.clear()
    core_cognition._production_initialization_attempted = False


class FakeHTTPResponse:
    def __init__(self, payload: bytes):
        self._stream = io.BytesIO(payload)

    def read(self) -> bytes:
        return self._stream.read()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


def _success_response(content: str) -> bytes:
    return json.dumps(
        {"choices": [{"message": {"role": "assistant", "content": content}}]}
    ).encode()


def test_exact_core_messages_are_transported_without_semantic_edits(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    requests = []

    def fake_urlopen(request, timeout=None):
        requests.append(request)
        return FakeHTTPResponse(_success_response("REAL MODEL ANSWER"))

    monkeypatch.setattr("julia_core.providers.deepseek.urllib.request.urlopen", fake_urlopen)
    provider = DeepSeekCognitionProvider()
    exact_messages = [
        {"role": "system", "content": "identity context"},
        {
            "message_id": "msg_internal",
            "conversation_id": "conv_internal",
            "turn_id": "turn_internal",
            "role": "user",
            "modality": "text",
            "content": "查一下 600519 今天的行情",
            "status": "completed",
        },
    ]

    result = provider.chat(exact_messages, cognitive_mode="market")

    assert result == "REAL MODEL ANSWER"
    assert len(requests) == 1
    transported = json.loads(requests[0].data.decode("utf-8"))
    assert transported["messages"] == [
        {"role": "system", "content": "identity context"},
        {"role": "user", "content": "查一下 600519 今天的行情"},
    ]


def test_missing_credential_fails_closed_before_network(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    network_calls = []
    monkeypatch.setattr(
        "julia_core.providers.deepseek.urllib.request.urlopen",
        lambda *args, **kwargs: network_calls.append(1),
    )

    with pytest.raises(core_cognition.CoreCognitionProviderUnavailable):
        core_cognition.initialize_production_cognition()

    assert network_calls == []
    assert core_cognition._get_cognition_provider("production") is None


def test_missing_credential_provider_constructor_fails_closed(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(DeepSeekCognitionProviderError):
        DeepSeekCognitionProvider()


def test_fresh_initialization_resolves_one_production_provider(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    provider = core_cognition.initialize_production_cognition()

    assert provider is not None
    assert provider is core_cognition._get_cognition_provider("production")
    assert isinstance(provider, DeepSeekCognitionProvider)


def test_initialization_is_idempotent_and_rejects_namespace_replacement(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    first = core_cognition.initialize_production_cognition()
    second = core_cognition.initialize_production_cognition()

    assert first is second
    with pytest.raises(RuntimeError, match="already bound"):
        core_cognition._register_cognition_provider("production", object())


def test_malformed_and_empty_responses_fail_without_fallback(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    provider = DeepSeekCognitionProvider()

    for payload in (b"{}", json.dumps({"choices": [{}]}).encode(), json.dumps(
        {"choices": [{"message": {"content": ""}}]}
    ).encode()):
        monkeypatch.setattr(
            "julia_core.providers.deepseek.urllib.request.urlopen",
            lambda *args, **kwargs: FakeHTTPResponse(payload),
        )
        with pytest.raises(DeepSeekCognitionProviderError):
            provider.chat([{"role": "user", "content": "request"}])


def test_provider_source_has_no_semantic_or_cross_component_dependencies():
    source = Path(importlib.import_module("julia_core.providers.deepseek").__file__).read_text()
    forbidden = (
        "Persona",
        "ProviderBehaviorAdapter",
        "Julia-AI-Assistant",
        "julia_core.market",
        "julia_core.research",
        "identity_repository",
        "memory_repository",
        "Narrative",
    )
    assert all(term not in source for term in forbidden)
