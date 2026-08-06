"""R0.1 file.search — Search for files by name pattern.

Wraps legacy SearchFilesCapability as a CapabilityProvider.
"""

from __future__ import annotations

from pathlib import Path

from julia_core.capability.models import CapabilityRequest

SEARCH_ROOTS = [
    Path("/Users/admin/.claude-dev/projects/-Users-admin/memory"),
    Path("/Users/admin/julia_core"),
    Path("/Users/admin/julia_ai_assistant"),
]


class FileSearchProvider:
    """CapabilityProvider: file.search — search files by name pattern.

    Permission scope: file.read (read-only).
    """

    async def execute(self, request: CapabilityRequest) -> dict:
        pattern = request.arguments.get("pattern", "")
        if not pattern:
            return {"error": "pattern is required", "status": "invalid"}

        results = []
        for root in SEARCH_ROOTS:
            if not root.exists():
                continue
            try:
                for p in root.rglob(f"*{pattern}*"):
                    if not p.name.startswith(".") and "__pycache__" not in str(p) and ".venv" not in str(p):
                        results.append(str(p))
                        if len(results) >= 20:
                            break
            except PermissionError:
                continue

        return {
            "status": "success" if results else "empty",
            "pattern": pattern,
            "matches": results,
            "count": len(results),
        }

    async def health(self) -> tuple[bool, str]:
        return True, "local filesystem — available"
