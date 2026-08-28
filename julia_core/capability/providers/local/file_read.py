"""R0.1 file.read — Read a file from the local filesystem.

Wraps legacy ReadFileCapability as a CapabilityProvider.
"""

from __future__ import annotations

from pathlib import Path

from julia_core.capability.models import CapabilityRequest
from julia_core.capability.providers.local.security import (
    DEFAULT_ALLOWED_ROOTS,
    DEFAULT_DENIED_ROOTS,
    authorize_path,
)


class FileReadProvider:
    """CapabilityProvider: file.read — read file contents.

    Permission scope: file.read (path-restricted).
    """

    ALLOWED_ROOTS = [str(path) for path in DEFAULT_ALLOWED_ROOTS]
    DENIED_ROOTS = [str(path) for path in DEFAULT_DENIED_ROOTS]

    async def execute(self, request: CapabilityRequest) -> dict:
        path = request.arguments.get("path", "")
        if not path:
            return {"error": "path is required", "status": "invalid"}

        allowed, reason = self._check_path(path)
        if not allowed:
            return {"error": reason, "status": "denied", "path": path}

        authorization = authorize_path(path, allowed_roots=self.ALLOWED_ROOTS, denied_roots=self.DENIED_ROOTS)
        canonical_path = authorization.canonical_path or path

        try:
            content = Path(canonical_path).read_text(encoding="utf-8", errors="ignore")
            return {
                "status": "success",
                "path": path,
                "canonical_path": canonical_path,
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
        authorization = authorize_path(path, allowed_roots=self.ALLOWED_ROOTS, denied_roots=self.DENIED_ROOTS)
        return authorization.allowed, authorization.reason
