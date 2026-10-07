"""Stable public application ingress for external transport adapters."""

from .conversation import (
    CONVERSATION_ID_PATTERN,
    CoreConversationConfig,
    CoreConversationInvalidId,
    CoreConversationIngress,
    CoreConversationRequest,
    CoreConversationResponse,
    is_valid_conversation_id,
)
from .lifecycle import shutdown_core_runtime

__all__ = [
    "CONVERSATION_ID_PATTERN",
    "CoreConversationConfig",
    "CoreConversationInvalidId",
    "CoreConversationIngress",
    "CoreConversationRequest",
    "CoreConversationResponse",
    "is_valid_conversation_id",
    "shutdown_core_runtime",
]
