"""Stable public application ingress for external transport adapters."""

from .conversation import (
    CoreConversationConfig,
    CoreConversationIngress,
    CoreConversationRequest,
    CoreConversationResponse,
)
from .lifecycle import shutdown_core_runtime

__all__ = [
    "CoreConversationConfig",
    "CoreConversationIngress",
    "CoreConversationRequest",
    "CoreConversationResponse",
    "shutdown_core_runtime",
]
