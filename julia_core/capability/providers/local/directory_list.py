"""R0.1 file.list — List contents of a directory.

Wraps legacy ListDirectoryCapability as a CapabilityProvider.
"""

from __future__ import annotations

from pathlib import Path

from julia_core.capability.models import CapabilityRequest
from julia_core.capability.providers.local.security import authorize_path


class DirectoryListProvider:
    """CapabilityProvider: file.list — list directory contents.

    Permission scope: file.read (read-only).
    """

    async def execute(self, request: CapabilityRequest) -> dict:
        path = request.arguments.get("path", "")
        if not path:
            return {"error": "path is required", "status": "invalid"}

        authorization = authorize_path(path)
        if not authorization.allowed:
            return {"error": authorization.reason, "status": "denied", "path": path}

        p = Path(authorization.canonical_path)
        if not p.exists():
            return {"error": "directory not found", "status": "not_found", "path": path}
        if not p.is_dir():
            return {"error": "not a directory", "status": "invalid", "path": path}

        items = []
        for item in sorted(p.iterdir()):
            suffix = "/" if item.is_dir() else ""
            items.append(f"  {item.name}{suffix}")
            if len(items) >= 30:
                break

        return {
            "status": "success",
            "path": path,
            "canonical_path": str(p),
            "items": items,
            "count": len(items),
        }

    async def health(self) -> tuple[bool, str]:
        return True, "local filesystem — available"
