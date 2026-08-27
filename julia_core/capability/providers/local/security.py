"""Canonical local filesystem authorization for Julia local providers.

R2-P2 security rule: authorization is based on expanded, canonical path
containment, never lexical string prefix matching. Denied roots override allowed
roots. Relative paths fail closed instead of inheriting ambient cwd authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[4]


DEFAULT_ALLOWED_ROOTS: tuple[Path, ...] = (
    REPO_ROOT,
    Path("/Users/admin/julia_core"),
    Path("/Users/admin/julia_ai_assistant"),
    Path("/Users/admin/Desktop"),
    Path("/Users/admin/.claude-dev/projects"),
)

DEFAULT_DENIED_ROOTS: tuple[Path, ...] = (
    REPO_ROOT / "tmp",
    Path("/Users/admin/julia_core/tmp"),
    Path("/Users/admin/.ssh"),
    Path("/Users/admin/.aws"),
    Path("/Users/admin/Library/Keychains"),
)


@dataclass(frozen=True, slots=True)
class FilesystemAuthorization:
    allowed: bool
    reason: str
    requested_path: str
    canonical_path: str = ""


def _canonical_root(root: Path) -> Path:
    return root.expanduser().resolve(strict=False)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _canonical_candidate(path: Path) -> Path:
    """Resolve existing targets and symlink targets; tolerate missing leaf.

    ``Path.resolve(strict=False)`` resolves ``..`` components and follows existing
    symlinks while allowing a missing final path. That lets read/list return
    not_found for authorized missing leaves but still rejects symlink escapes and
    denied-root aliases before any provider reads or lists.
    """
    return path.expanduser().resolve(strict=False)


def authorize_path(
    path: str,
    *,
    allowed_roots: Iterable[Path | str] = DEFAULT_ALLOWED_ROOTS,
    denied_roots: Iterable[Path | str] = DEFAULT_DENIED_ROOTS,
) -> FilesystemAuthorization:
    if not path:
        return FilesystemAuthorization(False, "path is required", path)

    try:
        requested = Path(path).expanduser()
        if not requested.is_absolute():
            return FilesystemAuthorization(False, "relative paths are not allowed", path)
        canonical = _canonical_candidate(requested)
        canonical_allowed = tuple(_canonical_root(Path(root)) for root in allowed_roots)
        canonical_denied = tuple(_canonical_root(Path(root)) for root in denied_roots)
    except Exception as exc:
        return FilesystemAuthorization(False, f"path authorization failed: {exc}", path)

    for denied in canonical_denied:
        if canonical == denied or _is_within(canonical, denied):
            return FilesystemAuthorization(False, f"path denied: {denied}", path, str(canonical))

    for allowed in canonical_allowed:
        if canonical == allowed or _is_within(canonical, allowed):
            return FilesystemAuthorization(True, "ok", path, str(canonical))

    return FilesystemAuthorization(False, "path outside permitted scope", path, str(canonical))
