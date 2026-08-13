"""CM-S3 — ConversationManagementService (Wave-2 implementation).

Governed orchestration surface over ConversationRuntime. It NEVER invents
canonical truth, NEVER mutates ConversationRepository directly, and NEVER
auto-creates on an unknown conversation_id (GAP-8).

Canonical-message mutation and canonical conversation_id allocation flow
through ConversationRuntime (sole semantic authority).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .conversation_runtime import ConversationRuntime


class ConversationNotFoundError(Exception):
    """GAP-8: unknown canonical conversation_id → REJECT, never implicit create."""

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        super().__init__(f"conversation not found: {conversation_id}")


class LifecycleUnavailableError(Exception):
    """CM-S3-I08: archive/delete governance is CM-S6's authority, not yet
    implemented. Fail-closed — zero canonical mutation."""

    def __init__(self, operation: str):
        self.operation = operation
        super().__init__(f"lifecycle operation not implemented: {operation}")


class CreateFailedError(Exception):
    """AT-CMS-02: canonical create failure propagates a governed failure.
    No local-fallback id, no idempotency mapping recorded."""

    def __init__(self, detail: str = ""):
        super().__init__(detail or "canonical conversation create failed")


class CreateIdempotencyStore:
    """Management-level durable idempotency_key → canonical conversation_id.

    Deliberately OUTSIDE the frozen 12-method ConversationRepository port.
    This is Wave-2 management state, not canonical transcript truth.
    """

    def __init__(self, path: Path | str):
        self._path = Path(path)
        self._data: dict[str, str] = self._load()

    def _load(self) -> dict[str, str]:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text())
                if isinstance(data, dict):
                    return {str(k): str(v) for k, v in data.items()}
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def get(self, key: str) -> str | None:
        return self._data.get(key)

    def put(self, key: str, cid: str) -> None:
        self._data[key] = cid
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._data))
        os.replace(tmp, self._path)  # atomic durable write


class ConversationManagementService:
    """CM-S3-I02/I05/I06: orchestrate, never invent; fail-closed; idempotent create."""

    def __init__(self, runtime: ConversationRuntime, idempotency_store: CreateIdempotencyStore):
        self._runtime = runtime
        self._idempotency = idempotency_store

    # ── create ────────────────────────────────────────────────────────────
    def create(self, idempotency_key: str | None = None, title: str = "New Conversation") -> dict:
        """CM-S3-I06: idempotency_key ≠ conversation_id.

        Same idempotency_key returns the same canonical conversation (durable
        across reconstruction). Canonical conversation_id is allocated by
        ConversationRuntime, never by this layer.
        """
        if idempotency_key is not None:
            existing = self._idempotency.get(idempotency_key)
            if existing is not None:
                return self.get(existing)

        try:
            handle = self._runtime.create_conversation(title=title)
        except Exception as e:  # AT-CMS-02: no mapping recorded on failure
            raise CreateFailedError(str(e)) from e

        cid = handle.conversation_id  # Core-allocated canonical id
        if idempotency_key is not None:
            self._idempotency.put(idempotency_key, cid)
        return self._runtime.get_conversation(cid)  # type: ignore[return-value]

    # ── get / open / resume ───────────────────────────────────────────────
    def get(self, conversation_id: str) -> dict:
        """GAP-8: unknown → ConversationNotFoundError. NEVER auto-create."""
        detail = self._runtime.get_conversation(conversation_id)
        if detail is None:
            raise ConversationNotFoundError(conversation_id)
        return detail

    def open(self, conversation_id: str) -> dict:
        """CM-S3-I04: resume attaches id; Core loads canonical truth."""
        return self.get(conversation_id)

    # ── list / rename / search ────────────────────────────────────────────
    def list(self) -> list:
        return self._runtime.list_conversations()

    def rename(self, conversation_id: str, title: str):
        handle = self._runtime.rename_conversation(conversation_id, title)
        if handle is None:
            raise ConversationNotFoundError(conversation_id)
        return handle

    def search(self, query: str) -> list:
        return self._runtime.search_conversations(query)

    # ── lifecycle (CM-S6 authority; fail-closed until implemented) ────────
    def delete(self, conversation_id: str) -> bool:
        """CM-S3-I08 / AT-CMS-08: archive/delete governance is NOT implemented.
        Fail-closed — zero canonical mutation, conversation remains intact."""
        if self._runtime.get_conversation(conversation_id) is None:
            raise ConversationNotFoundError(conversation_id)
        raise LifecycleUnavailableError("delete")

    def archive(self, conversation_id: str) -> bool:
        if self._runtime.get_conversation(conversation_id) is None:
            raise ConversationNotFoundError(conversation_id)
        raise LifecycleUnavailableError("archive")

    def restore(self, conversation_id: str) -> bool:
        if self._runtime.get_conversation(conversation_id) is None:
            raise ConversationNotFoundError(conversation_id)
        raise LifecycleUnavailableError("restore")
