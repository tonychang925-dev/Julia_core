"""Async Event Bus — pub/sub for Gateway → Client event broadcast.

Core generates events. EventBus fans them out to all connected clients.
"""

from __future__ import annotations
import asyncio
import logging
from typing import Callable, Awaitable

logger = logging.getLogger("julia.event_bus")

Handler = Callable[[dict], Awaitable[None]]


class EventBus:
    """Simple pub/sub. Subscribers receive every event."""

    def __init__(self):
        self._subscribers: list[Handler] = []

    def subscribe(self, handler: Handler):
        self._subscribers.append(handler)

    def unsubscribe(self, handler: Handler):
        try:
            self._subscribers.remove(handler)
        except ValueError:
            pass

    async def publish(self, event: dict):
        """Send event to all subscribers concurrently."""
        tasks = [handler(event) for handler in self._subscribers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
