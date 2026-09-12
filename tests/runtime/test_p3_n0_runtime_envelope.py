from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

import pytest

from julia_core.alignment_os import (
    ProviderAlignmentBoundary,
    ProviderExecutionEnvelope,
)
from julia_core.context_admission import ExactAdmittedSemanticBinder
from julia_core.runtime.assistant_runtime import (
    JuliaAssistantRuntime,
    RuntimeTurnRequest,
)


SOURCE_PATH = Path("julia_core/runtime/assistant_runtime.py")


def runtime_request():
    from tests.context_admission.test_p3_n0_semantic_binding import bound_bundle

    return RuntimeTurnRequest(bound_bundle(), provider_id="deepseek")


def test_runtime_accepts_only_exact_binding_and_returns_exact_envelope():
    runtime = JuliaAssistantRuntime(ProviderAlignmentBoundary())
    request = runtime_request()
    envelope = runtime.prepare(request)

    assert type(envelope) is ProviderExecutionEnvelope
    assert envelope.conversation_id == request.binding.conversation_id
    assert envelope.turn_id == request.binding.turn_id
    assert envelope.gate_receipt == request.binding.gate_receipt
    assert envelope.semantic_fingerprint == request.binding.semantic_fingerprint()
    assert envelope.messages == tuple(
        unit.to_message() for unit in request.binding.units
    )


def test_runtime_request_has_no_independent_semantic_or_history_ingress():
    field_names = {field.name for field in fields(RuntimeTurnRequest)}

    assert field_names == {"binding", "provider_id", "input_mode"}
    assert not {"message", "context_package", "history", "persona"} & field_names


def test_wrong_binding_type_fails_before_alignment(monkeypatch):
    calls = []
    original = ProviderAlignmentBoundary.resolve

    def resolve(self, binding, **kwargs):
        calls.append((binding, kwargs))
        return original(self, binding, **kwargs)

    monkeypatch.setattr(ProviderAlignmentBoundary, "resolve", resolve)

    with pytest.raises(TypeError, match="exact AdmittedSemanticBundle"):
        RuntimeTurnRequest(object(), provider_id="deepseek")

    runtime = JuliaAssistantRuntime(ProviderAlignmentBoundary())
    with pytest.raises(TypeError, match="exact RuntimeTurnRequest"):
        runtime.prepare(object())
    assert calls == []


def test_runtime_source_has_no_local_semantic_authority_or_provider_call():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert not imported_names & {
        "SelfArchiveRetriever",
        "EvidenceScanner",
        "ExperienceContextReconstructor",
        "RuntimeContinuityHook",
        "JuliaStartupProfile",
        "ProviderStreamRequest",
    }
    assert "persona" not in source
    assert "history" not in source
    assert "context_package" not in source
    assert "verified_c03_package" not in source
    assert "ProviderStreamAdapter" not in source
    runtime_attributes = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    }
    assert "provider" not in runtime_attributes


def test_runtime_trace_is_non_semantic_and_provider_transport_is_not_called():
    runtime = JuliaAssistantRuntime(ProviderAlignmentBoundary())
    trace = runtime.trace(runtime_request()).to_dict()

    assert trace["runtime"] == {"status": "PASS", "semantic_authority": False}
    assert trace["provider"]["transport_called"] is False
