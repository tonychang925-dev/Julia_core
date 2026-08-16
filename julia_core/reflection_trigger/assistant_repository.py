"""DIA-3 R2 — Assistant-side ReflectionTrigger persistence + scheduler.

This is an application-side adapter for the frozen R1 Core contract. It stores
PendingOpportunity objects without changing their semantic identity.

Durability model:
  * pending/<opportunity_id>.json is the canonical pending record.
  * acked/<opportunity_id>.json is the minimal delivery tombstone.
  * writes are temp-file -> fsync -> os.replace.
  * list_outbox excludes acked opportunities.
  * compaction removes pending records that already have ack tombstones.

The adapter is deliberately local/filesystem-bound; Core models and the Port
remain storage-agnostic.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from .models import (
    CANONICAL_VERSION,
    ActivityWindowAnchor,
    DeterministicTimerEligibilityBoundary,
    EventEligibilityBoundary,
    EvidenceBasis,
    OpportunityKey,
    PendingOpportunity,
    QuietWindowAnchor,
    ReflectionOpportunity,
    SingleEventAnchor,
    TriggerKind,
    TriggerReason,
    TriggerSourceRef,
)
from .repository_protocol import TriggerIdentityConflict

ADAPTER_SCHEMA_VERSION = "dia3-r2-trigger-state-v1"


class TriggerStatePersistenceError(RuntimeError):
    """Persistence adapter failed before establishing durable state."""


def _require_non_empty_str(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty str")


def _source_ref_to_dict(ref: TriggerSourceRef) -> dict[str, str]:
    return {"ref_type": ref.ref_type, "opaque_ref": ref.opaque_ref}


def _source_ref_from_dict(data: dict[str, Any]) -> TriggerSourceRef:
    return TriggerSourceRef(data["ref_type"], data["opaque_ref"])


def _evidence_to_dict(evidence: EvidenceBasis) -> dict[str, Any]:
    return {
        "digest_function": evidence.digest_function,
        "source_refs": [_source_ref_to_dict(ref) for ref in evidence.source_refs],
    }


def _evidence_from_dict(data: dict[str, Any]) -> EvidenceBasis:
    return EvidenceBasis(
        tuple(_source_ref_from_dict(ref) for ref in data["source_refs"]),
        digest_function=data["digest_function"],
    )


def _boundary_to_dict(boundary: EventEligibilityBoundary | DeterministicTimerEligibilityBoundary) -> dict[str, str]:
    if type(boundary) is EventEligibilityBoundary:
        return {"variant": "event", "eligibility_event_id": boundary.eligibility_event_id}
    if type(boundary) is DeterministicTimerEligibilityBoundary:
        return {
            "variant": "deterministic_timer",
            "deterministic_activity_boundary_id": boundary.deterministic_activity_boundary_id,
        }
    raise ValueError("unknown eligibility boundary")


def _boundary_from_dict(data: dict[str, Any]) -> EventEligibilityBoundary | DeterministicTimerEligibilityBoundary:
    variant = data["variant"]
    if variant == "event":
        return EventEligibilityBoundary(data["eligibility_event_id"])
    if variant == "deterministic_timer":
        return DeterministicTimerEligibilityBoundary(data["deterministic_activity_boundary_id"])
    raise ValueError(f"unknown eligibility boundary variant: {variant}")


def _anchor_to_dict(anchor: SingleEventAnchor | ActivityWindowAnchor | QuietWindowAnchor) -> dict[str, Any]:
    if type(anchor) is SingleEventAnchor:
        return {"variant": "single_event", "event_id": anchor.event_id}
    if type(anchor) is ActivityWindowAnchor:
        return {
            "variant": "activity_window",
            "window_start_event_id": anchor.window_start_event_id,
            "eligibility_boundary": _boundary_to_dict(anchor.eligibility_boundary),
            "evidence_basis": _evidence_to_dict(anchor.evidence_basis),
        }
    if type(anchor) is QuietWindowAnchor:
        return {
            "variant": "quiet_window",
            "last_event_id": anchor.last_event_id,
            "quiet_boundary_id": anchor.quiet_boundary_id,
        }
    raise ValueError("unknown causal anchor")


def _anchor_from_dict(data: dict[str, Any]) -> SingleEventAnchor | ActivityWindowAnchor | QuietWindowAnchor:
    variant = data["variant"]
    if variant == "single_event":
        return SingleEventAnchor(data["event_id"])
    if variant == "activity_window":
        return ActivityWindowAnchor(
            data["window_start_event_id"],
            _boundary_from_dict(data["eligibility_boundary"]),
            _evidence_from_dict(data["evidence_basis"]),
        )
    if variant == "quiet_window":
        return QuietWindowAnchor(data["last_event_id"], data["quiet_boundary_id"])
    raise ValueError(f"unknown causal anchor variant: {variant}")


def _key_to_dict(key: OpportunityKey) -> dict[str, Any]:
    return {
        "schema_version": key.schema_version,
        "conversation_id": key.conversation_id,
        "policy_revision": key.policy_revision,
        "trigger_kind": key.trigger_kind.value,
        "causal_anchor": _anchor_to_dict(key.causal_anchor),
    }


def _key_from_dict(data: dict[str, Any]) -> OpportunityKey:
    return OpportunityKey(
        data["schema_version"],
        data["conversation_id"],
        data["policy_revision"],
        TriggerKind(data["trigger_kind"]),
        _anchor_from_dict(data["causal_anchor"]),
    )


def _reason_to_dict(reason: TriggerReason) -> dict[str, Any]:
    return {
        "kind": reason.kind.value,
        "evidence_refs": [_source_ref_to_dict(ref) for ref in reason.evidence_refs],
    }


def _reason_from_dict(data: dict[str, Any]) -> TriggerReason:
    return TriggerReason(
        TriggerKind(data["kind"]),
        tuple(_source_ref_from_dict(ref) for ref in data["evidence_refs"]),
    )


def _opportunity_to_dict(opportunity: ReflectionOpportunity) -> dict[str, Any]:
    return {
        "opportunity_id": opportunity.opportunity_id,
        "opportunity_key": _key_to_dict(opportunity.opportunity_key),
        "source_refs": [_source_ref_to_dict(ref) for ref in opportunity.source_refs],
        "reasons": [_reason_to_dict(reason) for reason in opportunity.reasons],
    }


def _opportunity_from_dict(data: dict[str, Any]) -> ReflectionOpportunity:
    return ReflectionOpportunity(
        opportunity_key=_key_from_dict(data["opportunity_key"]),
        source_refs=tuple(_source_ref_from_dict(ref) for ref in data["source_refs"]),
        reasons=tuple(_reason_from_dict(reason) for reason in data["reasons"]),
        opportunity_id=data["opportunity_id"],
    )


def pending_to_record(state: PendingOpportunity) -> dict[str, Any]:
    return {
        "adapter_schema_version": ADAPTER_SCHEMA_VERSION,
        "core_schema_version": CANONICAL_VERSION,
        "status": "pending",
        "opportunity_id": state.opportunity_id,
        "triggered_at": state.triggered_at,
        "opportunity": _opportunity_to_dict(state.opportunity),
        "opportunity_canonical_hex": state.opportunity.canonical_bytes().hex(),
    }


def pending_from_record(data: dict[str, Any]) -> PendingOpportunity:
    if data["adapter_schema_version"] != ADAPTER_SCHEMA_VERSION:
        raise ValueError("unsupported trigger state adapter schema")
    if data["core_schema_version"] != CANONICAL_VERSION:
        raise ValueError("unsupported trigger state core schema")
    if data["status"] != "pending":
        raise ValueError("pending record status must be pending")
    opportunity = _opportunity_from_dict(data["opportunity"])
    state = PendingOpportunity(data["opportunity_id"], opportunity, data["triggered_at"])
    if data["opportunity_canonical_hex"] != state.opportunity.canonical_bytes().hex():
        raise ValueError("pending record canonical bytes mismatch")
    return state


def ack_to_record(state: PendingOpportunity, *, delivered_at: str, ack_id: str) -> dict[str, Any]:
    _require_non_empty_str("delivered_at", delivered_at)
    _require_non_empty_str("ack_id", ack_id)
    record = pending_to_record(state)
    return {
        "adapter_schema_version": ADAPTER_SCHEMA_VERSION,
        "core_schema_version": CANONICAL_VERSION,
        "status": "delivered",
        "opportunity_id": state.opportunity_id,
        "delivered_at": delivered_at,
        "ack_id": ack_id,
        "pending_record": record,
    }


class FileReflectionTriggerStateRepository:
    """Filesystem-backed Assistant adapter for ReflectionTriggerStateRepository."""

    def __init__(self, base_dir: str | Path):
        self._base = Path(base_dir)
        self._pending = self._base / "pending"
        self._acked = self._base / "acked"
        self._lock = threading.RLock()
        self._pending.mkdir(parents=True, exist_ok=True)
        self._acked.mkdir(parents=True, exist_ok=True)
        self._fsync_dir(self._base)

    def _pending_path(self, opportunity_id: str) -> Path:
        _require_non_empty_str("opportunity_id", opportunity_id)
        return self._pending / f"{opportunity_id}.json"

    def _ack_path(self, opportunity_id: str) -> Path:
        _require_non_empty_str("opportunity_id", opportunity_id)
        return self._acked / f"{opportunity_id}.json"

    def _atomic_write_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.tmp")
        encoded = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)
        try:
            with open(tmp, "w") as f:
                f.write(encoded)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
            self._fsync_dir(path.parent)
        except Exception as exc:  # pragma: no cover - defensive wrapper
            try:
                if tmp.exists():
                    tmp.unlink()
            finally:
                raise TriggerStatePersistenceError(str(exc)) from exc

    def _read_pending_path(self, path: Path) -> PendingOpportunity:
        return pending_from_record(json.loads(path.read_text()))

    def _read_ack_path(self, path: Path) -> PendingOpportunity:
        data = json.loads(path.read_text())
        if data["adapter_schema_version"] != ADAPTER_SCHEMA_VERSION:
            raise ValueError("unsupported ack adapter schema")
        if data["status"] != "delivered":
            raise ValueError("ack record status must be delivered")
        return pending_from_record(data["pending_record"])

    @staticmethod
    def _fsync_dir(path: Path) -> None:
        if not hasattr(os, "O_DIRECTORY"):
            return
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def create_pending(self, state: PendingOpportunity) -> PendingOpportunity:
        """Create, idempotently return, or fail closed on semantic conflict."""
        with self._lock:
            pending_path = self._pending_path(state.opportunity_id)
            ack_path = self._ack_path(state.opportunity_id)
            if pending_path.exists():
                existing = self._read_pending_path(pending_path)
                if existing.opportunity.semantic_equals(state.opportunity):
                    return existing
                raise TriggerIdentityConflict(state.opportunity_id)
            if ack_path.exists():
                existing = self._read_ack_path(ack_path)
                if existing.opportunity.semantic_equals(state.opportunity):
                    return existing
                raise TriggerIdentityConflict(state.opportunity_id)
            self._atomic_write_json(pending_path, pending_to_record(state))
            return self._read_pending_path(pending_path)

    def get_pending(self, opportunity_id: str) -> PendingOpportunity | None:
        with self._lock:
            path = self._pending_path(opportunity_id)
            if not path.exists() or self._ack_path(opportunity_id).exists():
                return None
            return self._read_pending_path(path)

    def list_outbox(self, *, limit: int | None = None) -> list[PendingOpportunity]:
        """Return durable pending opportunities not acknowledged for delivery."""
        with self._lock:
            states: list[PendingOpportunity] = []
            acked_ids = {path.stem for path in self._acked.glob("*.json")}
            for path in sorted(self._pending.glob("*.json")):
                if path.stem in acked_ids:
                    continue
                states.append(self._read_pending_path(path))
            states.sort(key=lambda item: (item.triggered_at, item.opportunity_id))
            if limit is not None:
                return states[:limit]
            return states

    def mark_delivery_ack(self, opportunity_id: str, *, delivered_at: str, ack_id: str) -> None:
        """Record minimal delivery tombstone. Idempotent for the same ack."""
        with self._lock:
            ack_path = self._ack_path(opportunity_id)
            if ack_path.exists():
                data = json.loads(ack_path.read_text())
                if data.get("ack_id") != ack_id:
                    raise TriggerIdentityConflict(opportunity_id)
                return
            pending_path = self._pending_path(opportunity_id)
            if not pending_path.exists():
                raise KeyError(f"pending opportunity not found: {opportunity_id}")
            state = self._read_pending_path(pending_path)
            self._atomic_write_json(ack_path, ack_to_record(state, delivered_at=delivered_at, ack_id=ack_id))

    def compact(self) -> int:
        """Remove pending records that have durable ack tombstones."""
        removed = 0
        with self._lock:
            for ack_path in sorted(self._acked.glob("*.json")):
                pending_path = self._pending_path(ack_path.stem)
                if pending_path.exists():
                    pending_path.unlink()
                    removed += 1
            if removed:
                self._fsync_dir(self._pending)
            return removed


class ReflectionTriggerRuntimeScheduler:
    """Small runtime facade: schedule -> outbox -> ack without changing Core semantics."""

    def __init__(self, repository: FileReflectionTriggerStateRepository):
        self._repository = repository

    def schedule(self, opportunity: ReflectionOpportunity, *, triggered_at: str) -> PendingOpportunity:
        return self._repository.create_pending(PendingOpportunity.pending(opportunity, triggered_at=triggered_at))

    def outbox(self, *, limit: int | None = None) -> list[PendingOpportunity]:
        return self._repository.list_outbox(limit=limit)

    def ack(self, opportunity_id: str, *, delivered_at: str, ack_id: str) -> None:
        self._repository.mark_delivery_ack(opportunity_id, delivered_at=delivered_at, ack_id=ack_id)

    def compact(self) -> int:
        return self._repository.compact()
