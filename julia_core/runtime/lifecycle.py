"""Runtime lifecycle — domain-independent.

The Runtime owns lifecycle. It does NOT:
  - resolve context itself
  - load domain providers
  - inject identity, memory, or prompts
"""

from __future__ import annotations

import enum

from .context_runtime import ContextRuntime


class RuntimeState(str, enum.Enum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"


class Runtime:
    """Minimal domain-independent Julia Runtime skeleton.

    Usage::

        rt = Runtime()
        rt.initialize()   # boot Context OS
        rt.start()        # ready for sessions
        ...
        rt.shutdown()
    """

    def __init__(self) -> None:
        self._state = RuntimeState.CREATED
        self._context_runtime: ContextRuntime | None = None

    @property
    def state(self) -> RuntimeState:
        return self._state

    @property
    def context_runtime(self) -> ContextRuntime | None:
        return self._context_runtime

    def initialize(self) -> None:
        """Bootstrap the Runtime — start Context OS."""
        if self._state not in (RuntimeState.CREATED,):
            return
        self._context_runtime = ContextRuntime()
        self._state = RuntimeState.READY

    def start(self) -> None:
        if self._state not in (RuntimeState.READY,):
            return
        self._state = RuntimeState.RUNNING

    def shutdown(self) -> None:
        if self._state in (RuntimeState.STOPPED,):
            return
        self._state = RuntimeState.STOPPED
        self._context_runtime = None
