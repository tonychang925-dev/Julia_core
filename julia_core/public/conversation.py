"""Typed, package-level conversation ingress owned by Julia Core.

External bodies may submit a request and receive a response. They cannot supply
repositories, cognitive callables, providers, or private runtime objects.
"""

from __future__ import annotations

import logging
import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.conversation_state.repository import (
    ConversationAdvancedError,
    ConversationNotFoundError,
    InvalidTurnStateError,
    TurnConflictError,
)
from julia_core.runtime.conversation_runtime import ConversationRuntime
from julia_core.runtime.julia_session import JuliaSession


logger = logging.getLogger("julia.public.conversation")

_MARKET_BINDING_LOCK = threading.Lock()
_market_binding_adapter: object | None = None
_market_binding_attempted = False
_market_binding_error: Exception | None = None
_RESEARCH_BINDING_LOCK = threading.Lock()
_research_binding_provider: object | None = None
_research_binding_attempted = False
_research_binding_error: Exception | None = None


def _ensure_market_public_binding() -> None:
    """Bind Market's public provider to Core exactly once per process.

    Market owns provider construction/configuration. Core owns only the
    mechanical binding into its generic capability namespace.

    The whole Market binding state transition is serialized. A completed
    optional-unavailable state still rechecks the provider namespace on every
    later ingress, so a foreign provider can never appear after failure without
    becoming a sticky Core composition error.
    """
    global _market_binding_adapter, _market_binding_attempted, _market_binding_error

    with _MARKET_BINDING_LOCK:
        if _market_binding_error is not None:
            raise _market_binding_error

        from julia_core.runtime.capability_bridge import get_capability_bridge

        bridge = get_capability_bridge()
        existing = bridge.manager.providers.get("market")

        if _market_binding_adapter is not None:
            if existing is _market_binding_adapter:
                return
            error = CoreConversationConfigurationError(
                "canonical Market binding no longer owns the market provider namespace"
            )
            _market_binding_error = error
            raise error

        # A prior optional binding failure is terminal for construction in this
        # process, but not for authority checks. Never retry the factory; always
        # verify that no foreign provider has appeared later.
        if _market_binding_attempted:
            if existing is None:
                return
            error = CoreConversationConfigurationError(
                "market provider namespace became occupied after canonical binding failed"
            )
            _market_binding_error = error
            raise error

        if existing is not None:
            error = CoreConversationConfigurationError(
                "market provider namespace is already occupied before canonical binding"
            )
            _market_binding_error = error
            raise error

        _market_binding_attempted = True
        try:
            from market_public import MarketPublicFactory
            from julia_core.capability.providers.market_public import (
                MarketPublicProviderAdapter,
            )

            # No Core DB/repository/private configuration crosses this boundary.
            public_provider = MarketPublicFactory.create()
            adapter = MarketPublicProviderAdapter(public_provider)
            bridge.register_provider("market", adapter)

            # register_provider is atomic. Verify the exact object actually won
            # the namespace before publishing BOUND state.
            if bridge.manager.providers.get("market") is not adapter:
                error = CoreConversationConfigurationError(
                    "canonical Market provider did not win the market namespace"
                )
                _market_binding_error = error
                raise error

            _market_binding_adapter = adapter
        except Exception as exc:
            from julia_core.runtime.capability_bridge import (
                ProviderAlreadyRegisteredError,
            )

            if isinstance(exc, (ProviderAlreadyRegisteredError, CoreConversationConfigurationError)):
                error = (
                    exc
                    if isinstance(exc, CoreConversationConfigurationError)
                    else CoreConversationConfigurationError(
                        "canonical Market provider registration was rejected"
                    )
                )
                _market_binding_error = error
                raise error from exc

            logger.warning(
                "Market public binding unavailable; market capabilities remain "
                "typed-unavailable: %s",
                exc,
            )


def _ensure_claude_client_research_binding() -> None:
    """Bind the configured Claude_client Research provider once per process."""
    global _research_binding_provider, _research_binding_attempted, _research_binding_error

    with _RESEARCH_BINDING_LOCK:
        if _research_binding_error is not None:
            raise _research_binding_error

        from julia_core.runtime.capability_bridge import get_capability_bridge

        bridge = get_capability_bridge()
        existing = bridge.manager.providers.get("research")

        if _research_binding_provider is not None:
            if existing is not None:
                return
            error = CoreConversationConfigurationError(
                "canonical Research binding no longer owns the research provider namespace"
            )
            _research_binding_error = error
            raise error

        if _research_binding_attempted:
            if existing is None:
                return
            error = CoreConversationConfigurationError(
                "research provider namespace became occupied after canonical binding was unavailable"
            )
            _research_binding_error = error
            raise error

        if existing is not None:
            error = CoreConversationConfigurationError(
                "research provider namespace is already occupied before canonical binding"
            )
            _research_binding_error = error
            raise error

        _research_binding_attempted = True
        from julia_core.research import (
            ClaudeClientExecutionConfig,
            ClaudeClientWebResearchProvider,
        )

        config = ClaudeClientExecutionConfig.from_environment()
        if config is None:
            return

        try:
            provider = ClaudeClientWebResearchProvider(config)
            bridge.register_provider("research", provider)
            if bridge._providers.get("research") is not provider:
                raise CoreConversationConfigurationError(
                    "canonical Research provider did not win the research namespace"
                )
            _research_binding_provider = provider
        except Exception as exc:
            from julia_core.runtime.capability_bridge import (
                ProviderAlreadyRegisteredError,
            )

            if isinstance(exc, (ProviderAlreadyRegisteredError, CoreConversationConfigurationError)):
                error = (
                    exc
                    if isinstance(exc, CoreConversationConfigurationError)
                    else CoreConversationConfigurationError(
                        "canonical Research provider registration was rejected"
                    )
                )
                _research_binding_error = error
                raise error from exc

            logger.warning(
                "Claude_client Research binding unavailable; research capability "
                "remains typed-unavailable: %s",
                exc,
            )


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
            from julia_core.providers.core_cognition import _get_cognition_provider
            provider = _get_cognition_provider("production")
            if provider is None:
                raise CoreConversationProviderUnavailable("configured Core provider is unavailable")

            # Core mechanically composes external evidence providers. Provider
            # owners construct their own configuration; Assistant is not involved.
            _ensure_market_public_binding()
            _ensure_claude_client_research_binding()

            self._session = JuliaSession(provider=provider)
        except Exception as exc:
            self._composition_error = exc

    def process(self, request: CoreConversationRequest) -> CoreConversationResponse:
        """Process one typed request through ConversationRuntime exactly once."""
        if type(request) is not CoreConversationRequest:
            raise TypeError("public ingress requires CoreConversationRequest")
        validation_error = self._validate_request(request)
        if validation_error is not None:
            return CoreConversationResponse(
                request.conversation_id, request.turn_id, "", "failed", validation_error
            )
        if self._composition_error is not None:
            return CoreConversationResponse(
                conversation_id=request.conversation_id,
                turn_id=request.turn_id,
                assistant_content="",
                status="failed",
                error_code=(
                    "CORE_PROVIDER_UNAVAILABLE"
                    if isinstance(self._composition_error, CoreConversationProviderUnavailable)
                    else "CORE_COMPOSITION_UNAVAILABLE"
                ),
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
            error_code = "CORE_CONVERSATION_UNAVAILABLE" if result.status == "failed" else None
            return CoreConversationResponse(
                conversation_id=result.conversation_id,
                turn_id=result.turn_id,
                assistant_content=result.assistant_content,
                status=result.status,
                error_code=error_code,
            )
        except ConversationNotFoundError:
            return CoreConversationResponse(
                request.conversation_id, request.turn_id, "", "failed", "CONVERSATION_NOT_FOUND"
            )
        except TurnConflictError:
            return CoreConversationResponse(
                request.conversation_id, request.turn_id, "", "failed", "TURN_CONFLICT"
            )
        except (ConversationAdvancedError, InvalidTurnStateError):
            return CoreConversationResponse(
                request.conversation_id, request.turn_id, "", "failed", "CORE_CONVERSATION_UNAVAILABLE"
            )
        except Exception:
            return CoreConversationResponse(
                request.conversation_id, request.turn_id, "", "failed", "CORE_CONVERSATION_UNAVAILABLE"
            )

    def create_conversation(self, conversation_id: str, title: str = "New Conversation") -> str:
        """Explicitly bind/create a conversation; process() never auto-creates."""
        if self._composition_error is not None:
            raise CoreConversationConfigurationError("Core composition is unavailable")
        assert self._runtime is not None
        if not self._valid_identifier(conversation_id):
            raise ValueError("invalid conversation_id")
        return self._runtime.create_conversation(conversation_id, title).conversation_id

    @staticmethod
    def _valid_identifier(value: str) -> bool:
        return bool(
            isinstance(value, str)
            and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value)
            and value not in {".", ".."}
        )

    @classmethod
    def _validate_request(cls, request: CoreConversationRequest) -> str | None:
        if not cls._valid_identifier(request.conversation_id):
            return "INVALID_REQUEST"
        if not cls._valid_identifier(request.turn_id):
            return "INVALID_REQUEST"
        if request.modality not in {"text", "voice"}:
            return "INVALID_REQUEST"
        if not isinstance(request.user_input, str) or not request.user_input.strip():
            return "INVALID_REQUEST"
        return None


class CoreConversationConfigurationError(RuntimeError):
    """Typed composition configuration failure; no fallback is permitted."""


class CoreConversationProviderUnavailable(RuntimeError):
    """No explicitly registered real Core cognition provider is available."""


__all__ = [
    "CoreConversationConfig",
    "CoreConversationIngress",
    "CoreConversationRequest",
    "CoreConversationResponse",
]
