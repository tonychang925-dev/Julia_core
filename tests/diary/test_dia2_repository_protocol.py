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


# ── structural: get/list return AcceptedDiaryEntry only ─────────────────────
def test_protocol_returns_accepted_entry_only():
    get_hints = get_type_hints(DiaryRepository.get)
    assert get_hints["return"] is AcceptedDiaryEntry or "AcceptedDiaryEntry" in str(get_hints["return"])
    list_hints = get_type_hints(DiaryRepository.list_entries)
    assert "AcceptedDiaryEntry" in str(list_hints["return"])
