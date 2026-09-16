"""Typed, package-level conversation ingress owned by Julia Core.

External bodies may submit a request and receive a response. They cannot supply
repositories, cognitive callables, providers, or private runtime objects.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.runtime.conversation_runtime import ConversationRuntime
from julia_core.runtime.julia_session import JuliaSession


@dataclass(frozen=True, slots=True)
class CoreConversationConfig:
    """Deployment configuration; dependency construction remains Core-owned."""

    conversation_data_dir: str | Path | None = None

    def resolve_data_dir(self) -> Path | None:
        configured = self.conversation_data_dir or os.environ.get("JULIA_CONVERSATION_DATA_DIR")
        return Path(configured) if configured else None


@dataclass(frozen=True, slots=True)
class CoreConversationRequest:
    conversation_id: str
    turn_id: str
    modality: str
    user_input: str


@dataclass(frozen=True, slots=True)
class CoreConversationResponse:
    conversation_id: str
    turn_id: str
    assistant_content: str
    status: str
    error_code: str | None = None


class CoreConversationIngress:
    """Single public façade over Core's composed conversation turn path."""

    def __init__(self, config: CoreConversationConfig | None = None) -> None:
        self._composition_error: Exception | None = None
        self._runtime: ConversationRuntime | None = None
        self._session: JuliaSession | None = None
        try:
            data_dir = (config or CoreConversationConfig()).resolve_data_dir()
            if data_dir is None:
                raise CoreConversationConfigurationError(
                    "JULIA_CONVERSATION_DATA_DIR is required for public ingress"
                )
            repository = StorageV2ConversationRepository(data_dir)
            self._runtime = ConversationRuntime(repository=repository)
            self._session = JuliaSession()
        except Exception as exc:
            self._composition_error = exc

    def process(self, request: CoreConversationRequest) -> CoreConversationResponse:
        """Process one typed request through ConversationRuntime exactly once."""
        if type(request) is not CoreConversationRequest:
            raise TypeError("public ingress requires CoreConversationRequest")
        if self._composition_error is not None:
            return CoreConversationResponse(
                conversation_id=request.conversation_id,
                turn_id=request.turn_id,
                assistant_content="",
                status="failed",
                error_code="CORE_COMPOSITION_UNAVAILABLE",
            )
        assert self._runtime is not None and self._session is not None
        try:
            result = self._runtime.process_turn(
                conversation_id=request.conversation_id,
                turn_id=request.turn_id,
                modality=request.modality,
                input=request.user_input,
                cognitive_fn=self._session.process,
            )
            return CoreConversationResponse(
                conversation_id=result.conversation_id,
                turn_id=result.turn_id,
                assistant_content=result.assistant_content,
                status=result.status,
            )
        except Exception:
            return CoreConversationResponse(
                conversation_id=request.conversation_id,
                turn_id=request.turn_id,
                assistant_content="",
                status="failed",
                error_code="CORE_CONVERSATION_UNAVAILABLE",
            )


class CoreConversationConfigurationError(RuntimeError):
    """Typed composition configuration failure; no fallback is permitted."""


__all__ = [
    "CoreConversationConfig",
    "CoreConversationIngress",
    "CoreConversationRequest",
    "CoreConversationResponse",
]
