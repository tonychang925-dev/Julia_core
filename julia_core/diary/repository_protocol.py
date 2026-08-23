"""DIA-2A — Core DiaryRepository Port (application-agnostic semantic contract).

Core owns diary semantics; Assistant owns physical persistence. This port is
a pure semantic surface over AcceptedDiaryEntry — it carries no storage
implementation detail.

append_accepted accepts only AcceptedDiaryEntry (already past semantic
acceptance). Calling it does not by itself create accepted truth: durable
accepted truth forms only after governance approval AND successful physical
durability (the adapter's DIARY_DURABLE barrier).
"""
from __future__ import annotations

from typing import Protocol

from .models import AcceptedDiaryEntry


class DiaryRepository(Protocol):
    """Durable store for accepted DiaryEntry objects (semantic surface only)."""

    def append_accepted(self, entry: AcceptedDiaryEntry) -> None:
        """Establish durable diary persistence for an accepted entry.

        Normal return means DIARY_DURABLE has been established.

        If DIARY_DURABLE cannot be established, the implementation MUST fail
        rather than return success, and the entry MUST NOT become observable
        through get()/list_entries().
        """
        ...

    def get(self, entry_id: str) -> AcceptedDiaryEntry | None:
        """Return the accepted entry with the given id, or None if absent."""
        ...

    def list_entries(
        self,
        *,
        before: str | None = None,
        after: str | None = None,
        limit: int | None = None,
    ) -> list[AcceptedDiaryEntry]:
        """List accepted entries (opaque cursor/pagination; adapter-decided)."""
        ...
