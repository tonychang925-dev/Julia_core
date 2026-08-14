"""DIA-2A — Core DiaryRepository Port boundary tests (AT-DP-C01..04)."""
from __future__ import annotations

from pathlib import Path
from typing import get_type_hints

from julia_core.diary import AcceptedDiaryEntry, DiaryCandidate, DiaryRepository


def _src() -> str:
    return (
        Path(__file__).resolve().parents[2]
        / "julia_core" / "diary" / "repository_protocol.py"
    ).read_text()


# ── AT-DP-C01: Core protocol imports no filesystem (pathlib/os) ────────────
def test_protocol_no_filesystem_imports():
    src = _src()
    assert "pathlib" not in src
    assert "import os" not in src
    assert "from os" not in src


# ── AT-DP-C02: Core protocol exposes no physical filename/path ─────────────
def test_protocol_no_physical_details():
    src = _src()
    for forbidden in ("memory/diary", ".md", "YYYY/MM", "filename", "private_root", "fsync", "chmod", "BEGIN", "END"):
        assert forbidden not in src, f"protocol must not expose {forbidden}"


# ── AT-DP-C03: port accepts AcceptedDiaryEntry, never DiaryCandidate ────────
def test_protocol_accepts_accepted_entry_only():
    hints = get_type_hints(DiaryRepository.append_accepted)
    assert hints["entry"] is AcceptedDiaryEntry
    src = _src()
    assert "DiaryCandidate" not in src


# ── AT-DP-C04: port API exposes no fsync/framing/private-root details ───────
def test_protocol_api_no_persistence_details():
    src = _src()
    for forbidden in ("fsync", "framing", "private_root", "chmod", "directory barrier", "open(", "json", "sqlite"):
        assert forbidden not in src, f"protocol API must not expose {forbidden}"


# ── AT-DP-C05: durable success boundary (normal return == DIARY_DURABLE) ────
def test_durable_success_boundary():
    src = _src()
    assert "Normal return means DIARY_DURABLE" in src
    assert "MUST fail" in src
    assert "MUST NOT become observable" in src


# ── AT-DP-C06: exact read return types (no DiaryCandidate/Any/mixed union) ──
def test_exact_read_return_types():
    from types import NoneType
    from typing import get_args, get_origin

    get_ret = get_type_hints(DiaryRepository.get)["return"]
    get_ret_args = get_args(get_ret)
    assert AcceptedDiaryEntry in get_ret_args
    assert NoneType in get_ret_args
    assert DiaryCandidate not in get_ret_args
    assert len(get_ret_args) == 2

    list_ret = get_type_hints(DiaryRepository.list_entries)["return"]
    assert get_origin(list_ret) is list
    (elem,) = get_args(list_ret)
    assert elem is AcceptedDiaryEntry
