"""DIA-5 R1 — Core Reflection Context Handoff contract.

DIA-5 validates and transports DIA-4 ReflectionContext semantic bytes. It does
not own, recompute, repair, or reinterpret context identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Protocol, runtime_checkable

from julia_core.reflection_context import CANONICAL_VERSION as CONTEXT_VERSION
from julia_core.reflection_context import ReflectionContext

HANDOFF_VERSION = "dia5-reflection-handoff-v1"
HANDOFF_DOMAIN_SEPARATOR = "julia_core.reflection_handoff.envelope.v1"
HANDOFF_INTEGRITY_DIGEST_FUNCTION = "sha256:handoff-semantic-bytes:v1"


def _require_non_empty_str(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty str")


def _require_bytes(name: str, value: object) -> None:
    if type(value) is not bytes:
        raise ValueError(f"{name} must be bytes")


def _frame(value: str) -> bytes:
    _require_non_empty_str("canonical field", value)
    encoded = value.encode("utf-8")
    return str(len(encoded)).encode("ascii") + b":" + encoded + b"\n"


def _bytes_frame(value: bytes) -> bytes:
    _require_bytes("canonical bytes", value)
    return str(len(value)).encode("ascii") + b":" + value + b"\n"


def _field(name: str, value: str) -> bytes:
    return _frame(name) + _frame(value)


def _bytes_field(name: str, value: bytes) -> bytes:
    return _frame(name) + _bytes_frame(value)


def _digest_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def _require_sha256_hex(name: str, value: object) -> None:
    _require_non_empty_str(name, value)
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{name} must be a 64-character lowercase SHA-256 hex digest")


@dataclass(frozen=True)
class HandoffEndpoint:
    endpoint_id: str
    endpoint_kind: str
    protocol_version: str

    def __post_init__(self) -> None:
        _require_non_empty_str("HandoffEndpoint.endpoint_id", self.endpoint_id)
        _require_non_empty_str("HandoffEndpoint.endpoint_kind", self.endpoint_kind)
        _require_non_empty_str("HandoffEndpoint.protocol_version", self.protocol_version)

    def canonical_bytes(self) -> bytes:
        return (
            _field("endpoint.id", self.endpoint_id)
            + _field("endpoint.kind", self.endpoint_kind)
            + _field("endpoint.protocol_version", self.protocol_version)
        )


@dataclass(frozen=True)
class HandoffIntegrity:
    context_digest: str
    semantic_bytes_sha256: str
    digest_algorithm: str = HANDOFF_INTEGRITY_DIGEST_FUNCTION
    context_version: str = CONTEXT_VERSION

    def __post_init__(self) -> None:
        _require_sha256_hex("HandoffIntegrity.context_digest", self.context_digest)
        _require_sha256_hex("HandoffIntegrity.semantic_bytes_sha256", self.semantic_bytes_sha256)
        _require_non_empty_str("HandoffIntegrity.digest_algorithm", self.digest_algorithm)
        _require_non_empty_str("HandoffIntegrity.context_version", self.context_version)
        if self.digest_algorithm != HANDOFF_INTEGRITY_DIGEST_FUNCTION:
            raise ValueError("HandoffIntegrity.digest_algorithm is frozen")
        if self.context_version != CONTEXT_VERSION:
            raise ValueError("HandoffIntegrity.context_version is not supported")

    @classmethod
    def from_context(cls, context: ReflectionContext) -> "HandoffIntegrity":
        if type(context) is not ReflectionContext:
            raise ValueError("context must be exact ReflectionContext")
        return cls(
            context_digest=context.context_digest or "",
            semantic_bytes_sha256=_digest_hex(context.semantic_canonical_bytes()),
            context_version=context.schema_version,
        )

    def verify(self, *, context_digest: str, semantic_bytes: bytes) -> None:
        _require_bytes("semantic_bytes", semantic_bytes)
        if context_digest != self.context_digest:
            raise ValueError("handoff context_digest mismatch")
        if _digest_hex(semantic_bytes) != self.semantic_bytes_sha256:
            raise ValueError("handoff semantic bytes hash mismatch")

    def canonical_bytes(self) -> bytes:
        return (
            _field("integrity.context_digest", self.context_digest)
            + _field("integrity.semantic_bytes_sha256", self.semantic_bytes_sha256)
            + _field("integrity.digest_algorithm", self.digest_algorithm)
            + _field("integrity.context_version", self.context_version)
        )


@dataclass(frozen=True)
class ReflectionContextHandoff:
    handoff_version: str
    handoff_id: str
    context_version: str
    context_digest: str
    context_semantic_bytes: bytes
    producer: HandoffEndpoint
    consumer: HandoffEndpoint
    created_at: str
    integrity: HandoffIntegrity

    def __post_init__(self) -> None:
        for name in ("handoff_version", "handoff_id", "context_version", "created_at"):
            _require_non_empty_str(f"ReflectionContextHandoff.{name}", getattr(self, name))
        _require_sha256_hex("ReflectionContextHandoff.context_digest", self.context_digest)
        if self.handoff_version != HANDOFF_VERSION:
            raise ValueError("ReflectionContextHandoff.handoff_version is not supported")
        if self.context_version != CONTEXT_VERSION:
            raise ValueError("ReflectionContextHandoff.context_version is not supported")
        _require_bytes("ReflectionContextHandoff.context_semantic_bytes", self.context_semantic_bytes)
        if type(self.producer) is not HandoffEndpoint:
            raise ValueError("ReflectionContextHandoff.producer must be exact HandoffEndpoint")
        if type(self.consumer) is not HandoffEndpoint:
            raise ValueError("ReflectionContextHandoff.consumer must be exact HandoffEndpoint")
        if type(self.integrity) is not HandoffIntegrity:
            raise ValueError("ReflectionContextHandoff.integrity must be exact HandoffIntegrity")
        if self.integrity.context_version != self.context_version:
            raise ValueError("ReflectionContextHandoff integrity context_version mismatch")
        self.integrity.verify(context_digest=self.context_digest, semantic_bytes=self.context_semantic_bytes)

    @classmethod
    def from_context(
        cls,
        *,
        handoff_id: str,
        context: ReflectionContext,
        producer: HandoffEndpoint,
        consumer: HandoffEndpoint,
        created_at: str,
    ) -> "ReflectionContextHandoff":
        if type(context) is not ReflectionContext:
            raise ValueError("context must be exact ReflectionContext")
        return cls(
            handoff_version=HANDOFF_VERSION,
            handoff_id=handoff_id,
            context_version=context.schema_version,
            context_digest=context.context_digest or "",
            context_semantic_bytes=context.semantic_canonical_bytes(),
            producer=producer,
            consumer=consumer,
            created_at=created_at,
            integrity=HandoffIntegrity.from_context(context),
        )

    def canonical_envelope_bytes(self) -> bytes:
        """Envelope identity bytes include transport metadata and semantic bytes.

        This is handoff identity, not context identity.
        """
        return (
            _field("handoff.domain", HANDOFF_DOMAIN_SEPARATOR)
            + _field("handoff.version", self.handoff_version)
            + _field("handoff.id", self.handoff_id)
            + _field("handoff.context_version", self.context_version)
            + _field("handoff.context_digest", self.context_digest)
            + _bytes_field("handoff.context_semantic_bytes", self.context_semantic_bytes)
            + _field("handoff.producer", self.producer.canonical_bytes().decode("utf-8"))
            + _field("handoff.consumer", self.consumer.canonical_bytes().decode("utf-8"))
            + _field("handoff.created_at", self.created_at)
            + _field("handoff.integrity", self.integrity.canonical_bytes().decode("utf-8"))
        )

    def handoff_envelope_digest(self) -> str:
        return _digest_hex(self.canonical_envelope_bytes())

    def validate_for_consumer(self, consumer: HandoffEndpoint) -> None:
        if type(consumer) is not HandoffEndpoint:
            raise ValueError("consumer must be exact HandoffEndpoint")
        if consumer != self.consumer:
            raise ValueError("handoff consumer mismatch")
        self.integrity.verify(context_digest=self.context_digest, semantic_bytes=self.context_semantic_bytes)


class HandoffReceiptStatus(Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class HandoffReceipt:
    handoff_id: str
    context_digest: str
    consumer: HandoffEndpoint
    received_at: str
    status: HandoffReceiptStatus
    rejection_reason: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str("HandoffReceipt.handoff_id", self.handoff_id)
        _require_sha256_hex("HandoffReceipt.context_digest", self.context_digest)
        if type(self.consumer) is not HandoffEndpoint:
            raise ValueError("HandoffReceipt.consumer must be exact HandoffEndpoint")
        _require_non_empty_str("HandoffReceipt.received_at", self.received_at)
        if type(self.status) is not HandoffReceiptStatus:
            raise ValueError("HandoffReceipt.status must be HandoffReceiptStatus")
        if self.status is HandoffReceiptStatus.REJECTED:
            _require_non_empty_str("HandoffReceipt.rejection_reason", self.rejection_reason)
        elif self.rejection_reason is not None:
            raise ValueError("accepted HandoffReceipt must not carry rejection_reason")


@runtime_checkable
class ReflectionHandoffValidator(Protocol):
    def validate(self, handoff: ReflectionContextHandoff, consumer: HandoffEndpoint) -> HandoffReceipt:
        ...


class StrictReflectionHandoffValidator:
    def validate(self, handoff: ReflectionContextHandoff, consumer: HandoffEndpoint) -> HandoffReceipt:
        if type(handoff) is not ReflectionContextHandoff:
            raise ValueError("handoff must be exact ReflectionContextHandoff")
        handoff.validate_for_consumer(consumer)
        return HandoffReceipt(
            handoff_id=handoff.handoff_id,
            context_digest=handoff.context_digest,
            consumer=consumer,
            received_at="validation-time-not-identity",
            status=HandoffReceiptStatus.ACCEPTED,
        )
