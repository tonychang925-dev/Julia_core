"""Continuity lifecycle events.

Events are emitted by Runtime OS and interpreted by Continuity OS.
Continuity OS does not watch Runtime or own lifecycle control.
"""
from __future__ import annotations

from enum import Enum


class ContinuityEvent(str, Enum):
    """Runtime-detected lifecycle events relevant to continuity checks."""

    SESSION_START = "SESSION_START"
    SESSION_RESTART = "SESSION_RESTART"
    COMPACT_DETECTED = "COMPACT_DETECTED"
    PROVIDER_SWITCH = "PROVIDER_SWITCH"
    RUNTIME_RECOVERY = "RUNTIME_RECOVERY"
