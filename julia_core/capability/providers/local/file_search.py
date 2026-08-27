"""R0.1 file.search — Search for files by name pattern.

Wraps legacy SearchFilesCapability as a CapabilityProvider.
"""

from __future__ import annotations

from pathlib import Path

from julia_core.capability.models import CapabilityRequest
from julia_core.capability.providers.local.security import authorize_path

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
            root_auth = authorize_path(str(root))
            if not root_auth.allowed:
                continue
            canonical_root = Path(root_auth.canonical_path)
            if not canonical_root.exists():
                continue
            try:
                for p in canonical_root.rglob(f"*{pattern}*"):
                    if p.name.startswith(".") or "__pycache__" in str(p) or ".venv" in str(p):
                        continue
                    result_auth = authorize_path(str(p))
                    if not result_auth.allowed:
                        continue
                    results.append(result_auth.canonical_path)
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
