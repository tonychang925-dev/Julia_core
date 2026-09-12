from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any
from collections.abc import Mapping

from julia_core.continuity import ContinuityCheckpoint


CHECKPOINT_ENVELOPE_SCHEMA = "continuity_checkpoint_envelope_v1"
CHECKPOINT_PAYLOAD_SCHEMA = "continuity_checkpoint_v1"
CONTINUITY_PROVENANCE_AUTHORITY = "continuity_os"
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


class RecoveryEnvelopeRejected(RuntimeError):
    """Raised when a recovery envelope violates the exact durability contract."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class CheckpointProvenance:
    checkpoint_id: str
    agent_id: str
    created_at: str
    authority: str
    canonical_refs_digest: str

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, str) and value
            for value in (
                self.checkpoint_id,
                self.agent_id,
                self.created_at,
                self.authority,
                self.canonical_refs_digest,
            )
        ):
            raise RecoveryEnvelopeRejected("checkpoint provenance requires exact fields")
        if self.authority != CONTINUITY_PROVENANCE_AUTHORITY:
            raise RecoveryEnvelopeRejected("checkpoint provenance authority is inexact")
        if DIGEST_PATTERN.fullmatch(self.canonical_refs_digest) is None:
            raise RecoveryEnvelopeRejected("checkpoint provenance refs digest is inexact")

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "agent_id": self.agent_id,
            "created_at": self.created_at,
            "authority": self.authority,
            "canonical_refs_digest": self.canonical_refs_digest,
        }


@dataclass(frozen=True, slots=True)
class CheckpointEnvelope:
    payload_digest: str
    provenance: CheckpointProvenance
    checkpoint: ContinuityCheckpoint

    def __post_init__(self) -> None:
        if DIGEST_PATTERN.fullmatch(self.payload_digest) is None:
            raise RecoveryEnvelopeRejected("checkpoint payload digest is inexact")
        if type(self.provenance) is not CheckpointProvenance:
            raise RecoveryEnvelopeRejected("checkpoint provenance type is inexact")
        if type(self.checkpoint) is not ContinuityCheckpoint:
            raise RecoveryEnvelopeRejected("checkpoint payload type is inexact")
        expected = _covered_payload(self.checkpoint, self.provenance)
        if self.payload_digest != _digest(expected):
            raise RecoveryEnvelopeRejected("checkpoint payload digest does not match")
        object.__setattr__(
            self,
            "checkpoint",
            replace_checkpoint(self.checkpoint, _freeze(self.checkpoint.to_dict())),
        )


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze(item) for item in value)
    return value


def replace_checkpoint(
    current: ContinuityCheckpoint, payload: Mapping[str, Any]
) -> ContinuityCheckpoint:
    return ContinuityCheckpoint(
        checkpoint_version=payload["checkpoint_version"],
        checkpoint_id=payload["checkpoint_id"],
        agent_id=payload["agent_id"],
        created_at=payload["created_at"],
        identity_refs=list(payload["identity_refs"]),
        protected_memory_refs=list(payload["protected_memory_refs"]),
        relationship_refs=list(payload["relationship_refs"]),
        active_project_refs=list(payload["active_project_refs"]),
        continuity_levels=dict(payload["continuity_levels"]),
        integrity=dict(payload["integrity"]),
    )


def _covered_payload(
    checkpoint: ContinuityCheckpoint, provenance: CheckpointProvenance
) -> dict[str, Any]:
    payload = checkpoint.to_dict()
    integrity = payload.get("integrity")
    if type(integrity) is not dict or set(integrity) != {"schema"}:
        raise RecoveryEnvelopeRejected("checkpoint integrity fields are inexact")
    if integrity.get("schema") != CHECKPOINT_PAYLOAD_SCHEMA:
        raise RecoveryEnvelopeRejected("checkpoint payload schema is unsupported")
    return {
        "checkpoint": payload,
        "provenance": provenance.to_dict(),
    }


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def canonical_refs_digest(checkpoint: ContinuityCheckpoint) -> str:
    payload = checkpoint.to_dict()
    refs = {
        "identity_refs": payload["identity_refs"],
        "protected_memory_refs": payload["protected_memory_refs"],
        "relationship_refs": payload["relationship_refs"],
        "active_project_refs": payload["active_project_refs"],
        "continuity_levels": payload["continuity_levels"],
    }
    return _digest(refs)


def seal_checkpoint(checkpoint: ContinuityCheckpoint) -> CheckpointEnvelope:
    if checkpoint.integrity != {"schema": CHECKPOINT_PAYLOAD_SCHEMA}:
        raise RecoveryEnvelopeRejected("checkpoint payload integrity is inexact")
    provenance = CheckpointProvenance(
        checkpoint_id=checkpoint.checkpoint_id,
        agent_id=checkpoint.agent_id,
        created_at=checkpoint.created_at,
        authority=CONTINUITY_PROVENANCE_AUTHORITY,
        canonical_refs_digest=canonical_refs_digest(checkpoint),
    )
    return CheckpointEnvelope(
        payload_digest=_digest(_covered_payload(checkpoint, provenance)),
        provenance=provenance,
        checkpoint=checkpoint,
    )


def validate_checkpoint_envelope(envelope: CheckpointEnvelope) -> ContinuityCheckpoint:
    if type(envelope) is not CheckpointEnvelope:
        raise RecoveryEnvelopeRejected("recovery envelope type is inexact")
    if envelope.payload_digest != _digest(
        _covered_payload(envelope.checkpoint, envelope.provenance)
    ):
        raise RecoveryEnvelopeRejected("recovery payload was tampered after sealing")
    if envelope.provenance.checkpoint_id != envelope.checkpoint.checkpoint_id:
        raise RecoveryEnvelopeRejected("recovery checkpoint identity does not match provenance")
    if envelope.provenance.agent_id != envelope.checkpoint.agent_id:
        raise RecoveryEnvelopeRejected("recovery agent identity does not match provenance")
    if envelope.provenance.created_at != envelope.checkpoint.created_at:
        raise RecoveryEnvelopeRejected("recovery creation time does not match provenance")
    if envelope.provenance.canonical_refs_digest != canonical_refs_digest(envelope.checkpoint):
        raise RecoveryEnvelopeRejected("recovery canonical refs do not match provenance")
    return envelope.checkpoint


def package_model_view_is_absent(payload: Mapping[str, Any]) -> bool:
    forbidden_keys = {
        "provider",
        "provider_id",
        "model",
        "model_id",
        "model_message",
        "messages",
        "prompt",
        "rendered_context",
        "context_block",
    }

    def contains_forbidden(value: Any) -> bool:
        if isinstance(value, Mapping):
            return any(
                key in forbidden_keys or contains_forbidden(item)
                for key, item in value.items()
            )
        if isinstance(value, (tuple, list)):
            return any(contains_forbidden(item) for item in value)
        return False

    return not contains_forbidden(payload)
