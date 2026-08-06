"""M0.5 Mock Provider — Validates the Capability Runtime chain end-to-end.

Provides system.time.read without any external dependency.
This is the FIRST capability Julia can invoke through the full
CapabilityManager pipeline — proving the architecture works.

After M0 validation, real providers (ai_theme_app MCP, etc.) plug in
through the same CapabilityProvider protocol.
"""

from __future__ import annotations

import time as _time
from datetime import datetime, timezone, timedelta

from julia_core.capability.models import CapabilityRequest

CST = timezone(timedelta(hours=8))


class MockTimeProvider:
    """Provides system.time.read — returns current timestamp.

    Implements CapabilityProvider protocol.
    Used to validate the full Manager → Registry → Policy → Provider chain
    before connecting to any real external system.
    """

    def __init__(self, simulated_time: str | None = None):
        """If simulated_time is set, always return this ISO timestamp."""
        self._simulated = simulated_time

    async def execute(self, request: CapabilityRequest) -> dict:
        """Execute system.time.read. Returns current CST time."""
        if self._simulated:
            now_str = self._simulated
        else:
            now = datetime.now(CST)
            now_str = now.isoformat()

        return {
            "time": now_str,
            "timezone": "Asia/Shanghai",
            "unix_epoch": _time.time(),
            "source": "mock_time_provider",
            "request_id": request.request_id,
        }

    async def health(self) -> tuple[bool, str]:
        """Mock provider is always healthy."""
        return True, "mock provider — always available"


class MockDenyProvider:
    """A provider that always fails — used for permission denial testing."""

    async def execute(self, request: CapabilityRequest) -> dict:
        return {"error": "this should never be called"}

    async def health(self) -> tuple[bool, str]:
        return False, "mock deny provider — permanently unavailable"


__all__ = ["MockTimeProvider", "MockDenyProvider"]
