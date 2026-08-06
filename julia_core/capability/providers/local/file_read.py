"""R0.1 file.read — Read a file from the local filesystem.

Wraps legacy ReadFileCapability as a CapabilityProvider.
"""

from __future__ import annotations

from pathlib import Path

from julia_core.capability.models import CapabilityRequest


class FileReadProvider:
    """CapabilityProvider: file.read — read file contents.

    Permission scope: file.read (path-restricted).
    """

    ALLOWED_ROOTS = [
        "/Users/admin/julia_core",
        "/Users/admin/julia_ai_assistant",
        "/Users/admin/Desktop",
        "/Users/admin/.claude-dev/projects",
    ]
    DENIED_ROOTS = [
        "/Users/admin/.ssh",
        "/Users/admin/.aws",
        "/Users/admin/Library/Keychains",
    ]

    async def execute(self, request: CapabilityRequest) -> dict:
        path = request.arguments.get("path", "")
        if not path:
            return {"error": "path is required", "status": "invalid"}

        # Permission check
        allowed, reason = self._check_path(path)
        if not allowed:
            return {"error": reason, "status": "denied", "path": path}

        try:
            content = Path(path).read_text(encoding="utf-8", errors="ignore")
            return {
                "status": "success",
                "path": path,
                "content": content[:5000],
                "size": len(content),
            }
        except FileNotFoundError:
            return {"error": "file not found", "status": "not_found", "path": path}
        except Exception as e:
            return {"error": str(e), "status": "error", "path": path}

    async def health(self) -> tuple[bool, str]:
        return True, "local filesystem — available"

    def _check_path(self, path: str) -> tuple[bool, str]:
        for d in self.DENIED_ROOTS:
            if path.startswith(d):
                return False, f"path denied: {d}"
        for a in self.ALLOWED_ROOTS:
            if path.startswith(a):
                return True, "ok"
        return False, "path not in allowed scope"
