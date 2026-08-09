"""Julia Agent HTTP Adapter — capability name ↔ HTTP endpoint mapping.

This adapter is the DESIGNATED BOUNDARY between julia_core and Julia Agent.
It knows about HTTP endpoints. It does NOT know Julia's persona internals.
It does NOT own identity. It translates and transports.

Capability names (Julia cognitive interface) → HTTP endpoints:
  julia.chat           → POST /chat
  julia.identity       → GET  /identity
  julia.memory.search  → POST /memory/search

Pattern: mirrors MCPToolAdapter for ai_theme_app, using HTTP transport instead
of in-process import. ADR-026 P4: Provider supplies capability, not cognition.
"""

from __future__ import annotations

from typing import Any

import httpx


# ── Capability → HTTP Endpoint Mapping ───────────────────────────────────────

CAPABILITY_TO_ENDPOINT: dict[str, tuple[str, str]] = {
    "julia.chat":           ("POST", "/chat"),
    "julia.identity":       ("GET",  "/identity"),
    "julia.memory.search":  ("POST", "/memory/search"),
}

ENDPOINT_TO_CAPABILITY: dict[str, str] = {
    "/chat":           "julia.chat",
    "/identity":       "julia.identity",
    "/memory/search":  "julia.memory.search",
}


# ── HTTP Tool Adapter ────────────────────────────────────────────────────────

class JuliaAgentAdapter:
    """Adapts Julia Agent HTTP calls into Capability results.

    Responsibilities:
      1. Map capability names → HTTP endpoints
      2. Call Julia Agent via HTTP
      3. Return raw response dict

    Does NOT:
      - Know what Julia's persona is
      - Own identity or memory
      - Interpret chat responses
    """

    def __init__(self, base_url: str = "http://127.0.0.1:9020", transport=None):
        """base_url: Julia Agent HTTP sidecar URL.
        transport: optional callable(method, path, body) -> dict for testing.
        """
        self.base_url = base_url.rstrip("/")
        self._transport = transport

    # ── Public API ────────────────────────────────────────────────────────

    async def call(
        self,
        capability_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a Julia Agent call through capability→endpoint mapping."""
        entry = CAPABILITY_TO_ENDPOINT.get(capability_name)
        if entry is None:
            raise ValueError(f"Unknown capability for Julia Agent: {capability_name}")

        method, path = entry
        args = arguments or {}

        if self._transport:
            return await self._transport(method, path, args)

        return await self._call_http(method, path, args)

    async def _call_http(
        self, method: str, path: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        """HTTP call to Julia Agent sidecar."""
        url = f"{self.base_url}{path}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                resp = await client.get(url)
            elif method == "POST":
                resp = await client.post(url, json=body)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if resp.status_code >= 400:
                return {
                    "error": True,
                    "status_code": resp.status_code,
                    "detail": resp.text[:500],
                }

            return resp.json()

    async def health(self) -> tuple[bool, str]:
        """Check if Julia Agent sidecar is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/health")
                if resp.status_code == 200:
                    data = resp.json()
                    return True, f"Julia Agent healthy — persona: {data.get('persona', '?')}"
                return False, f"Julia Agent returned {resp.status_code}"
        except Exception as exc:
            return False, f"Julia Agent unreachable: {exc}"


__all__ = ["JuliaAgentAdapter", "CAPABILITY_TO_ENDPOINT", "ENDPOINT_TO_CAPABILITY"]
