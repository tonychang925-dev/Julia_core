"""Stable public application ingress for external transport adapters."""

from .conversation import (
    CoreConversationConfig,
    CoreConversationDetailResult,
    CoreConversationHandle,
    CoreConversationIngress,
    CoreConversationListResult,
    CoreConversationMessagesResult,
    CoreConversationRequest,
    CoreConversationResponse,
)
from .lifecycle import shutdown_core_runtime

__all__ = [
    "CoreConversationConfig",
    "CoreConversationDetailResult",
    "CoreConversationHandle",
    "CoreConversationIngress",
    "CoreConversationListResult",
    "CoreConversationMessagesResult",
    "CoreConversationRequest",
    "CoreConversationResponse",
    "shutdown_core_runtime",
]
