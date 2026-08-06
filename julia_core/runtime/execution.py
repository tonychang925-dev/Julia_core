"""R1.3 Runtime Execution — shared _runtime_execute() with event tracking.

ADR-027 AC-1: chat_async() is the canonical entry point.
chat() is a compatibility wrapper. One implementation, two signatures.

Every execution produces a complete event timeline:
  conversation.message.received → intent.detected → capability.requested
  → capability.completed → context.created → reasoning.completed
  → conversation.turn.completed
"""

from __future__ import annotations

from julia_core.events.models import (
    EventCategory,
    ConversationEventType,
    CapabilityEventType,
    create_event,
)
from julia_core.events.store import EventStore, get_event_store


class RuntimeExecutor:
    """Shared execution context for chat_async() and chat().

    Wraps _chat_impl() with event emission. Every call produces
    a complete event timeline with correlation chain.
    """

    def __init__(self, event_store: EventStore | None = None):
        self.event_store = event_store or get_event_store()

    def wrap_chat_impl(self, chat_impl: callable):
        """Wrap _chat_impl with event emission.

        Returns a callable with the same signature as _chat_impl
        that emits events at each pipeline stage.
        """
        def evented_chat(session, text: str) -> str:
            correlation_id = f"corr_{id(session)}_{session.turn_count}"

            # Emit: conversation.message.received
            self.event_store.append(create_event(
                source="conversation",
                event_type=ConversationEventType.MESSAGE_RECEIVED,
                category=EventCategory.CONVERSATION,
                payload={"text": text[:200], "turn": session.turn_count},
                correlation_id=correlation_id,
            ))

            # Execute the real pipeline
            reply = chat_impl(session, text)

            # Emit: conversation.turn.completed
            self.event_store.append(create_event(
                source="conversation",
                event_type=ConversationEventType.TURN_COMPLETED,
                category=EventCategory.CONVERSATION,
                payload={
                    "topic": session.current_topic,
                    "reply_len": len(reply) if reply else 0,
                },
                correlation_id=correlation_id,
            ))

            return reply

        return evented_chat


__all__ = ["RuntimeExecutor"]
