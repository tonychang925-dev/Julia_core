"""Assistant Runtime streaming bound to production C03 admission.

The runtime transports a verified sealed CognitiveContextPackage to a provider.
It does not assemble identity, relationship, experience, memory, persona, or
continuity semantics locally.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, Literal, Mapping

from julia_core.context_admission import (
    ModelVisibilityTransport,
    SealedCognitiveContextPackage,
)
from julia_core.context_admission.contracts import canonical_json
from julia_core.providers.streaming import ProviderStreamAdapter, ProviderStreamRequest


RuntimeStreamEventType = Literal[
    "runtime_ready", "context_ready", "text_delta", "done", "error"
]


@dataclass(frozen=True, slots=True)
class RuntimeStreamRequest:
    session_id: str
    message: str
    context_package: SealedCognitiveContextPackage
    input_mode: str = "text"
    stream: bool = True
    provider_id: str = "deterministic_runtime_provider"

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id is required")
        if not self.message:
            raise ValueError("message is required")
        if type(self.context_package) is not SealedCognitiveContextPackage:
            raise ValueError("an exact sealed C03 context package is required")
        if not self.input_mode:
            raise ValueError("input_mode is required")
        if not self.stream:
            raise ValueError("RuntimeStreamRequest.stream must be true")

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "message": self.message,
            "context_package": ModelVisibilityTransport().render(self.context_package),
            "input_mode": self.input_mode,
            "stream": self.stream,
            "provider_id": self.provider_id,
        }


@dataclass(frozen=True, slots=True)
class RuntimeStreamEvent:
    event: RuntimeStreamEventType
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return {"event": self.event, "payload": dict(self.payload)}


@dataclass(frozen=True, slots=True)
class RuntimeBindingTrace:
    session_id: str
    input_mode: str
    contract_version: str
    conversation_id: str
    turn_id: str
    gate_receipt: str
    source_digests: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_digests", dict(self.source_digests))

    def to_dict(self) -> dict[str, Any]:
        return {
            "interaction": {"mode": self.input_mode, "stream": True},
            "runtime": {"session_id": self.session_id, "status": "PASS"},
            "context": {
                "status": "PASS_VERIFIED_C03",
                "contract_version": self.contract_version,
                "conversation_id": self.conversation_id,
                "turn_id": self.turn_id,
                "gate_receipt": self.gate_receipt,
                "source_digests": dict(self.source_digests),
            },
            "provider": {"status": "PASS", "streaming": True},
            "boundary": {
                "runtime_semantic_authority": False,
                "provider_semantic_authority": False,
                "partial_admission": False,
            },
        }


class JuliaAssistantRuntime:
    """Runtime transport for model visibility sealed by production C03."""

    def __init__(self, provider: ProviderStreamAdapter | None = None) -> None:
        if provider is None:
            raise ValueError("an explicit ProviderStreamAdapter is required")
        self.provider = provider
        self.context_transport = ModelVisibilityTransport()

    def stream(self, request: RuntimeStreamRequest) -> Iterator[RuntimeStreamEvent]:
        if not request.stream:
            raise ValueError("RuntimeStreamRequest.stream must be true")
        package_payload = self.context_transport.render(request.context_package)
        if request.context_package.conversation_id != request.session_id:
            raise ValueError(
                "context package conversation does not match runtime session"
            )
        return self._stream_verified(request, package_payload)

    def _stream_verified(
        self,
        request: RuntimeStreamRequest,
        package_payload: Mapping[str, Any],
    ) -> Iterator[RuntimeStreamEvent]:
        trace = RuntimeBindingTrace(
            session_id=request.session_id,
            input_mode=request.input_mode,
            contract_version=request.context_package.contract_version,
            conversation_id=request.context_package.conversation_id,
            turn_id=request.context_package.turn_id,
            gate_receipt=request.context_package.gate_receipt,
            source_digests=package_payload["source_digests"],
        )
        trace_payload = trace.to_dict()
        yield RuntimeStreamEvent(
            event="runtime_ready", payload={"trace": trace_payload}
        )
        yield RuntimeStreamEvent(
            event="context_ready", payload={"trace": trace_payload}
        )

        provider_request = self._provider_request(request, trace, package_payload)
        provider_trace: dict[str, Any] = {}
        for provider_event in self.provider.stream(provider_request):
            if provider_event.trace:
                provider_trace = dict(
                    provider_event.trace.get("provider", provider_event.trace)
                )
            if provider_event.event == "delta" and provider_event.delta is not None:
                yield RuntimeStreamEvent(
                    event="text_delta",
                    payload={
                        "type": "text_delta",
                        "content": provider_event.delta.text,
                    },
                )
            if provider_event.event == "error":
                yield RuntimeStreamEvent(
                    event="error",
                    payload={"error": provider_event.error or "provider_error"},
                )
        yield RuntimeStreamEvent(
            event="done",
            payload={
                "ok": True,
                "trace": trace_payload,
                "provider_trace": provider_trace,
            },
        )

    @staticmethod
    def _provider_request(
        request: RuntimeStreamRequest,
        trace: RuntimeBindingTrace,
        package_payload: Mapping[str, Any],
    ) -> ProviderStreamRequest:
        system_context = canonical_json(
            {
                "directive": (
                    "The verified context package is the only model-visible "
                    "semantic authority; do not infer or substitute another one."
                ),
                "context_package": dict(package_payload),
            }
        )
        return ProviderStreamRequest(
            messages=(
                {"role": "system", "content": system_context},
                {"role": "user", "content": request.message},
            ),
            stream=True,
            model=request.provider_id,
            provider_name=request.provider_id,
            context_blocks=("verified_c03_package",),
            trace={**trace.to_dict(), "context_package": dict(package_payload)},
        )
