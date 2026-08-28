"""C1-R2.4 Filesystem security gate tests.

Protected contracts: C-08 / REV2 R2-I11 / ADR-037 shared-boundary safety
Expected baseline: XFAIL for canonical authorization gaps in local filesystem providers.
Known gaps: B-Security-P0 file.read lexical startswith(), file.list missing
allowed-root checks, file.search path leakage risk from conformance audit
Resolving phase: R2-P3

TC-ID: C1-R2.4-FS-001 canonical traversal must fail closed
TC-ID: C1-R2.4-FS-002 symlink escape must fail closed
TC-ID: C1-R2.4-FS-003 allowed-prefix collision must fail closed
TC-ID: C1-R2.4-FS-004 file.list and file.read share authorization boundary
TC-ID: C1-R2.4-FS-005 file.search does not leak outside authorized roots
TC-ID: C1-R2.4-FS-006 missing/invalid path fails closed without fabricated success

Local provider release gate = provider mapping correctness + canonical filesystem
authorization + negative security tests. These tests do not modify production code.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from julia_core.capability.models import CapabilityRequest
from julia_core.capability.providers.local.directory_list import DirectoryListProvider
from julia_core.capability.providers.local.file_read import FileReadProvider
from julia_core.capability.providers.local.file_search import FileSearchProvider


ROOT = Path(__file__).resolve().parents[2]
TMP_ROOT = ROOT / "tmp" / "c1_r2_4_filesystem_security"


def _request(**arguments) -> CapabilityRequest:
    return CapabilityRequest("file.read", arguments)


@pytest.mark.asyncio
async def test_file_read_rejects_canonical_parent_traversal_escape():
    """TC-ID: C1-R2.4-FS-001. .. traversal resolving outside allowed root must be denied."""
    provider = FileReadProvider()
    traversal_path = str(ROOT / ".." / ".ssh" / "id_rsa")

    result = await provider.execute(_request(path=traversal_path))

    assert result["status"] == "denied"


@pytest.mark.asyncio
async def test_file_read_rejects_symlink_escape_from_allowed_root():
    """TC-ID: C1-R2.4-FS-002. Symlink inside allowed root must not expose outside target."""
    outside = TMP_ROOT / "outside_secret.txt"
    inside_dir = ROOT / "tmp" / "c1_r2_4_symlink_allowed_root"
    symlink = inside_dir / "escape_link.txt"
    outside.parent.mkdir(parents=True, exist_ok=True)
    inside_dir.mkdir(parents=True, exist_ok=True)
    outside.write_text("C1_R2_4_SECRET_OUTSIDE_ALLOWED_ROOT", encoding="utf-8")
    if symlink.exists() or symlink.is_symlink():
        symlink.unlink()
    symlink.symlink_to(outside)

    result = await FileReadProvider().execute(_request(path=str(symlink)))

    assert result["status"] == "denied"
    assert "C1_R2_4_SECRET_OUTSIDE_ALLOWED_ROOT" not in str(result)


def test_file_read_rejects_allowed_prefix_collision_desktop_evil():
    """TC-ID: C1-R2.4-FS-003. /Users/admin/Desktop_evil is not /Users/admin/Desktop."""
    provider = FileReadProvider()

    allowed, reason = provider._check_path("/Users/admin/Desktop_evil/private.txt")

    assert allowed is False
    assert "allowed" not in reason.lower()


@pytest.mark.asyncio
async def test_file_list_rejects_outside_authorized_roots_like_file_read():
    """TC-ID: C1-R2.4-FS-004. file.list and file.read must share the same authorization boundary."""
    outside_dir = TMP_ROOT / "outside_list_root"
    outside_dir.mkdir(parents=True, exist_ok=True)
    (outside_dir / "leaked_name.txt").write_text("not model visible", encoding="utf-8")

    result = await DirectoryListProvider().execute(CapabilityRequest("file.list", {"path": str(outside_dir)}))

    assert result["status"] == "denied"
    assert "leaked_name.txt" not in str(result)


@pytest.mark.asyncio
async def test_file_search_filters_results_to_canonical_authorized_roots(monkeypatch):
    """TC-ID: C1-R2.4-FS-005. file.search must not leak paths outside authorized roots."""
    from julia_core.capability.providers.local import file_search

    outside_dir = TMP_ROOT / "outside_search_root"
    outside_dir.mkdir(parents=True, exist_ok=True)
    (outside_dir / "needle_private.txt").write_text("secret", encoding="utf-8")
    monkeypatch.setattr(file_search, "SEARCH_ROOTS", [outside_dir])

    result = await FileSearchProvider().execute(CapabilityRequest("file.search", {"pattern": "needle"}))

    assert result["status"] in {"denied", "empty"}
    assert all(str(ROOT) in match for match in result.get("matches", []))
    assert "needle_private.txt" not in str(result)


@pytest.mark.asyncio
async def test_file_read_missing_path_fails_closed_without_success_payload():
    """TC-ID: C1-R2.4-FS-006. Missing/invalid path remains explicit non-success."""
    result = await FileReadProvider().execute(_request(path=str(ROOT / "does_not_exist_c1_r2_4.txt")))

    assert result["status"] == "not_found"
    assert "content" not in result


@pytest.mark.asyncio
async def test_file_read_empty_path_is_invalid_not_fabricated_success():
    """TC-ID: C1-R2.4-FS-006. Empty path fails closed and does not fabricate data."""
    result = await FileReadProvider().execute(_request(path=""))

    assert result["status"] == "invalid"
    assert "content" not in result
