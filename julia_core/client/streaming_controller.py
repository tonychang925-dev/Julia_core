"""HTTP-facing streaming controller for Julia Client.

The controller adapts HTTP/client requests to JuliaAssistantRuntime. It does not
own Core OS state and does not implement Persona, Memory, Context, Evidence, or
Provider logic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterator, Mapping

from julia_core.observer import JsonlPilotObserver, PilotObserverPort, elapsed_ms, record_from_runtime_trace, start_timer
from julia_core.runtime.assistant_runtime import JuliaAssistantRuntime, RuntimeStreamEvent, RuntimeStreamRequest


@dataclass(frozen=True, slots=True)
class ClientChatEnvelope:
    text: str
    session_id: str | None
    interaction_mode: str = "text"
    voice_output: bool = False


class StreamingController:
    def __init__(self, runtime: JuliaAssistantRuntime | None = None, observer: PilotObserverPort | None = None) -> None:
        self.runtime = runtime or JuliaAssistantRuntime()
        self.observer = observer or JsonlPilotObserver()

    def stream_sse(self, envelope: ClientChatEnvelope | Mapping[str, Any]) -> Iterator[str]:
        request = self._runtime_request(envelope)
        started = start_timer()
        events: list[RuntimeStreamEvent] = []
        for event in self.runtime.stream(request):
            events.append(event)
            yield self._sse(event.event, event.payload)
        self._observe(envelope, request, events, elapsed_ms(started))

    def complete_response(self, envelope: ClientChatEnvelope | Mapping[str, Any]) -> dict[str, Any]:
        text = ""
        trace: dict[str, Any] = {}
        request = self._runtime_request(envelope)
        started = start_timer()
        events: list[RuntimeStreamEvent] = []
        for event in self.runtime.stream(request):
            events.append(event)
            if event.event in {"runtime_ready", "context_ready", "done"}:
                trace = dict(event.payload.get("trace", trace))
            if event.event == "text_delta":
                text += str(event.payload.get("content", ""))
        self._observe(envelope, request, events, elapsed_ms(started))
        return {"reply": text, "intent": "chat", "trace": trace}


    def _observe(
        self,
        envelope: ClientChatEnvelope | Mapping[str, Any],
        request: RuntimeStreamRequest,
        events: list[RuntimeStreamEvent],
        duration_ms: int,
    ) -> None:
        trace: dict[str, Any] = {}
        for event in events:
            if event.event in {"runtime_ready", "context_ready", "done"}:
                trace = dict(event.payload.get("trace", trace))
        if not trace:
            return
        voice_output = envelope.voice_output if isinstance(envelope, ClientChatEnvelope) else bool(envelope.get("voice_output", False))
        record = record_from_runtime_trace(
            session_id=request.session_id,
            duration_ms=duration_ms,
            trace=trace,
            input_mode=request.input_mode,
            voice_output=voice_output,
        )
        self.observer.observe(record)

    @staticmethod
    def _sse(event_name: str, data: Mapping[str, Any]) -> str:
        return f"event: {event_name}\ndata: {json.dumps(dict(data), ensure_ascii=False)}\n\n"

    @staticmethod
    def _runtime_request(envelope: ClientChatEnvelope | Mapping[str, Any]) -> RuntimeStreamRequest:
        if isinstance(envelope, ClientChatEnvelope):
            text = envelope.text
            session_id = envelope.session_id or "session-anonymous"
            mode = envelope.interaction_mode
        else:
            text = str(envelope.get("text", ""))
            session_id = str(envelope.get("session_id") or "session-anonymous")
            mode = str(envelope.get("interaction_mode", "text"))
        return RuntimeStreamRequest(session_id=session_id, message=text, input_mode=mode, stream=True)
