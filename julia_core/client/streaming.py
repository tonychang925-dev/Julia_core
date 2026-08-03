"""H4 streaming conversation contracts.

This module is transport/runtime neutral. It defines stream event shapes and a
small deterministic chunker for the H4 interface MVP. It does not own Persona,
Memory, Continuity, Context, Evidence, Provider selection, or Voice identity.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Iterator, Literal, Mapping


StreamEventType = Literal["trace", "chunk", "done", "error"]


@dataclass(frozen=True, slots=True)
class ResponseChunk:
    index: int
    text: str
    is_final: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StreamingTrace:
    session_id: str | None
    interaction_mode: str
    stream: bool = True
    continuity_status: str = "PENDING_RUNTIME_BINDING"
    memory_status: str = "PENDING_RUNTIME_BINDING"
    context_status: str = "PENDING_RUNTIME_BINDING"
    evidence_status: str = "PENDING_RUNTIME_BINDING"
    provider_streaming: bool = True
    context_blocks_used: tuple[str, ...] = ()
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "client_owns_identity": False,
            "voice_owns_identity": False,
            "client_writes_memory": False,
            "provider_reads_files": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "context_blocks_used", tuple(self.context_blocks_used))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "interaction": {"mode": self.interaction_mode, "stream": self.stream},
            "runtime": {"session_id": self.session_id},
            "continuity": {"status": self.continuity_status},
            "memory": {"status": self.memory_status},
            "context": {"status": self.context_status, "blocks_used": list(self.context_blocks_used)},
            "evidence": {"status": self.evidence_status},
            "provider": {"streaming": self.provider_streaming},
            "boundary": dict(self.boundary),
        }


@dataclass(frozen=True, slots=True)
class ConversationStreamEvent:
    event: StreamEventType
    data: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", dict(self.data))

    def to_dict(self) -> dict[str, Any]:
        return {"event": self.event, "data": dict(self.data)}


def chunk_text(text: str, *, chunk_size: int = 8) -> tuple[ResponseChunk, ...]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not text:
        return (ResponseChunk(index=0, text="", is_final=True),)
    chunks: list[ResponseChunk] = []
    for index, start in enumerate(range(0, len(text), chunk_size)):
        part = text[start : start + chunk_size]
        chunks.append(ResponseChunk(index=index, text=part, is_final=False))
    chunks[-1] = ResponseChunk(index=chunks[-1].index, text=chunks[-1].text, is_final=True)
    return tuple(chunks)


def conversation_stream_events(reply: str, trace: StreamingTrace, *, chunk_size: int = 8) -> Iterator[ConversationStreamEvent]:
    yield ConversationStreamEvent(event="trace", data=trace.to_dict())
    for chunk in chunk_text(reply, chunk_size=chunk_size):
        yield ConversationStreamEvent(event="chunk", data=chunk.to_dict())
    yield ConversationStreamEvent(event="done", data={"ok": True})
