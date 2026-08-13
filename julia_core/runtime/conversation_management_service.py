"""CM-S3 — ConversationManagementService (Wave-2 implementation).

Governed orchestration surface over ConversationRuntime. It NEVER invents
canonical truth, NEVER mutates ConversationRepository directly, and NEVER
auto-creates on an unknown conversation_id (GAP-8).

Canonical conversation_id allocation and canonical-message mutation flow
through ConversationRuntime (sole semantic authority). Durable idempotency
persistence is delegated to a CreateIdempotencyPort whose physical
implementation belongs to the Assistant composition layer (F2 path opacity).
"""
from __future__ import annotations

from typing import Protocol

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
    No local-fallback id is ever manufactured."""

    def __init__(self, detail: str = ""):
        super().__init__(detail or "canonical conversation create failed")


class ConversationStateConflictError(Exception):
    """409: semantic management state conflict (e.g. idempotency/lifecycle conflict)."""

    def __init__(self, detail: str = "conversation state conflict"):
        super().__init__(detail)


class ConversationBusyError(Exception):
    """423: conversation busy/locked for a governed operation."""

    def __init__(self, detail: str = "conversation busy/locked"):
        super().__init__(detail)


class CreateIdempotencyConflict(Exception):
    """Semantic idempotency conflict (corrupt/conflicting reservation) → 409."""

    def __init__(self, detail: str = "idempotency conflict"):
        super().__init__(detail)


class CreateIdempotencyPersistenceFailure(Exception):
    """Physical persistence/unavailability failure in the idempotency port → 500."""

    def __init__(self, detail: str = "idempotency persistence failure"):
        super().__init__(detail)


class CreateIdempotencyPort(Protocol):
    """Core semantic port for create idempotency.

    Core decides WHAT: a given idempotency_key MUST converge to one reserved
    canonical conversation identity. The port exposes an atomic put-if-absent
    reservation. It knows NOTHING about Path / JSON / fsync / filesystem.

    Physical implementation belongs to Julia-AI-Assistant.
    """

    def get_or_reserve(self, idempotency_key: str, candidate_id: str) -> str:
        """Atomically reserve candidate_id for idempotency_key.

        Returns the reserved canonical conversation_id: candidate_id if this is
        the first reservation, else the already-reserved id. Raises on
        corruption/unavailability (fail-closed — never treats corruption as empty).
        """
        ...


class ConversationManagementService:
    """CM-S3-I02/I05/I06: orchestrate, never invent; fail-closed; idempotent create."""

    def __init__(self, runtime: ConversationRuntime, idempotency_port: CreateIdempotencyPort):
        self._runtime = runtime
        self._idempotency = idempotency_port

    # ── create ────────────────────────────────────────────────────────────
    def create(self, idempotency_key: str | None = None, title: str = "New Conversation") -> dict:
        """CM-S3-I06 + W2-IDEMP reserve-before-create order:

            allocate candidate cid → get_or_reserve(key, cid) → create(reserved cid)

        Reservation precedes canonical creation, so any crash window converges
        to a single canonical conversation for the same idempotency_key.
        """
        cid = self._runtime.allocate_conversation_id()  # Core allocates identity
        if idempotency_key is not None:
            try:
                cid = self._idempotency.get_or_reserve(idempotency_key, cid)
            except CreateIdempotencyConflict as e:
                raise ConversationStateConflictError(str(e)) from e   # 409
            except CreateIdempotencyPersistenceFailure as e:
                raise CreateFailedError(str(e)) from e                 # 500
            except Exception as e:
                raise CreateFailedError(str(e)) from e                 # unclassified → 500, never 409
        try:
            self._runtime.create_conversation(conversation_id=cid, title=title)
        except Exception as e:  # AT-CMS-02: governed failure, no local fallback id
            raise CreateFailedError(str(e)) from e
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

    def get_messages(self, conversation_id: str, max_messages: int = 100) -> list[dict]:
        """CM-S4: read canonical messages through the governed management surface.

        HTTP/Electron call THIS, never the Runtime's private internals.
        """
        self.get(conversation_id)  # GAP-8: 404 on unknown, never implicit create
        return self._runtime.get_messages(conversation_id, max_messages)

    # ── lifecycle (CM-S6 authority; fail-closed until implemented) ────────
    def delete(self, conversation_id: str) -> bool:
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
