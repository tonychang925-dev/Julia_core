from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from julia_core.context_admission import (
    C03AdmissionRejected,
    SealedCognitiveContextPackage,
)
from julia_core.context_admission import ExclusiveAdmissionGate
from julia_core.providers.streaming import ProviderStreamEvent
from julia_core.runtime.assistant_runtime import (
    JuliaAssistantRuntime,
    RuntimeStreamRequest,
)

from tests.context_admission.production_fixtures import canonical_request


ROOT = Path(__file__).resolve().parents[2]


class RecordingProvider:
    provider_name = "recording"
    model = "recording-model"

    def __init__(self) -> None:
        self.requests = []

    def stream(self, request):
        self.requests.append(request)
        yield ProviderStreamEvent(event="delta", delta=None)
        yield ProviderStreamEvent(event="done")


def sealed_package():
    return ExclusiveAdmissionGate().seal(canonical_request())


def runtime_request(package=None, *, session_id="conversation-eng12a"):
    return RuntimeStreamRequest(
        session_id=session_id,
        message="runtime transport request",
        context_package=package if package is not None else sealed_package(),
    )


def test_valid_sealed_package_is_the_only_system_authority_payload():
    provider = RecordingProvider()
    runtime = JuliaAssistantRuntime(provider=provider)
    package = sealed_package()

    events = list(runtime.stream(runtime_request(package)))

    assert [event.event for event in events] == [
        "runtime_ready",
        "context_ready",
        "done",
    ]
    assert len(provider.requests) == 1
    provider_request = provider.requests[0]
    assert [message["role"] for message in provider_request.messages] == [
        "system",
        "user",
    ]
    assert provider_request.messages[-1]["content"] == "runtime transport request"
    assert provider_request.context_blocks == ("verified_c03_package",)
    rendered = provider_request.trace["context_package"]
    assert rendered == package.to_dict()
    system_payload = json.loads(provider_request.messages[0]["content"])
    assert system_payload == {
        "directive": (
            "The verified context package is the only model-visible "
            "semantic authority; do not infer or substitute another one."
        ),
        "context_package": rendered,
    }


def test_unsealed_or_forged_package_fails_closed_before_stream_events():
    runtime = JuliaAssistantRuntime(RecordingProvider())
    provider = runtime.provider

    with pytest.raises(ValueError, match="exact sealed C03"):
        runtime.stream(runtime_request(object()))

    forged = object.__new__(SealedCognitiveContextPackage)
    for name in SealedCognitiveContextPackage.__dataclass_fields__:
        object.__setattr__(forged, name, getattr(sealed_package(), name))
    object.__setattr__(forged, "gate_receipt", "0" * 64)

    with pytest.raises(C03AdmissionRejected, match="receipt is forged"):
        runtime.stream(runtime_request(forged))

    assert provider.requests == []


def test_conversation_mismatch_fails_closed_before_stream_events():
    provider = RecordingProvider()
    runtime = JuliaAssistantRuntime(provider)

    with pytest.raises(ValueError, match="does not match runtime session"):
        runtime.stream(runtime_request(session_id="different-conversation"))

    assert provider.requests == []


def test_runtime_requires_explicit_provider_and_streaming_request() -> None:
    with pytest.raises(ValueError, match="explicit ProviderStreamAdapter"):
        JuliaAssistantRuntime()

    request = runtime_request()
    object.__setattr__(request, "stream", False)
    with pytest.raises(ValueError, match="stream must be true"):
        JuliaAssistantRuntime(RecordingProvider()).stream(request)


def test_runtime_source_has_no_local_semantic_authority_dependencies():
    source = (ROOT / "julia_core" / "runtime" / "assistant_runtime.py").read_text()
    tree = ast.parse(source)
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported_names.update(alias.name for alias in node.names)

    assert not imported_names & {
        "SelfArchiveRetriever",
        "ExperienceContextReconstructor",
        "EvidenceScanner",
        "JuliaStartupProfile",
        "RuntimeContinuityHook",
    }
    forbidden_attributes = {
        "self_archive_retriever",
        "relationship_artifact",
        "experience_context",
        "startup_profile",
        "recall_policy",
        "continuity_hook",
        "persona",
    }
    attributes = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    }
    assert attributes.isdisjoint(forbidden_attributes)
