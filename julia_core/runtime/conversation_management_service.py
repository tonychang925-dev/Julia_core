"""CM-S3 — ConversationManagementService (Wave-2 implementation).

Governed orchestration surface over ConversationRuntime. It NEVER invents
canonical truth, NEVER mutates ConversationRepository directly, and NEVER
auto-creates on an unknown conversation_id (GAP-8).

Canonical-message mutation is out of scope here: it flows through
ConversationRuntime, which is the sole semantic conversation authority.
"""
from __future__ import annotations

import uuid

from .conversation_runtime import ConversationRuntime


class ConversationNotFoundError(Exception):
    """GAP-8: unknown canonical conversation_id → REJECT, never implicit create."""

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        super().__init__(f"conversation not found: {conversation_id}")


class ConversationManagementService:
    """CM-S3-I02/I05/I06: orchestrate, never invent; fail-closed; idempotent create.

    A thin wrapper over ConversationRuntime. It holds NO transcript authority,
    NO context authority, and NO physical persistence authority.
    """

    def __init__(self, runtime: ConversationRuntime):
        self._runtime = runtime
        # idempotency_key → canonical conversation_id (retry identity, NOT canonical identity)
        self._idempotency: dict[str, str] = {}

    # ── create ────────────────────────────────────────────────────────────
    def create(self, idempotency_key: str | None = None, title: str = "New Conversation") -> dict:
        """CM-S3-I06: idempotency_key ≠ conversation_id.

        Same idempotency_key returns the same canonical conversation;
        different idempotency_key is an independent create. The canonical
        conversation_id is assigned by Core (never the idempotency_key).
        """
        if idempotency_key is not None and idempotency_key in self._idempotency:
            cid = self._idempotency[idempotency_key]
            return self.get(cid)

        # Canonical id is Core-domain generated; the management layer ensures
        # uniqueness (Core's timestamp-based default id is collision-prone for
        # sub-second creates — a pre-existing Core issue, flagged separately).
        cid = f"conv_{uuid.uuid4().hex}"
        self._runtime.create_conversation(conversation_id=cid, title=title)
        if idempotency_key is not None:
            self._idempotency[idempotency_key] = cid
        return self._runtime.get_conversation(cid)  # type: ignore[return-value]

    # ── get / open / resume ───────────────────────────────────────────────
    def get(self, conversation_id: str) -> dict:
        """GAP-8: unknown → ConversationNotFoundError. NEVER auto-create."""
        detail = self._runtime.get_conversation(conversation_id)
        if detail is None:
            raise ConversationNotFoundError(conversation_id)
        return detail

    def open(self, conversation_id: str) -> dict:
        """CM-S3-I04: resume attaches id; Core loads canonical truth.
        No client transcript transfer."""
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

    # ── governed lifecycle entry (full semantics owned by CM-S6) ─────────
    def delete(self, conversation_id: str) -> bool:
        """Lifecycle entry point. Full archive/tombstone/purge semantics are
        CM-S6's authority; this delegates the raw delete to Runtime for now."""
        if self._runtime.get_conversation(conversation_id) is None:
            raise ConversationNotFoundError(conversation_id)
        return self._runtime.delete_conversation(conversation_id)
