"""Runtime-only provider/persona separation contracts.

These types carry execution provenance. They never carry persona semantics and
are never admitted as model-visible persona authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from julia_core.alignment_os import ProviderExecutionEnvelope
from julia_core.context_admission import PersonaSelfBoundSemanticBundle


_DESCRIPTOR_SCHEMA_VERSION = "julia_core.runtime.execution_substrate_descriptor.v1"
_RECEIPT_SCHEMA_VERSION = "julia_core.runtime.dispatch_receipt.v1"
_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_IDENTIFIER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_TRANSPORT_MODES = {"pre_dispatch"}


class ProviderPersonaSeparationError(RuntimeError):
    """Fail-closed provider/persona runtime separation error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_identifier(value: object, field_name: str) -> str:
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ProviderPersonaSeparationError(
            "inexact_execution_substrate_field",
            f"execution substrate {field_name} is malformed",
        )
    return value


def _contains_provider_identity(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            key in {"provider_id", "model_id", "runtime_instance_id"}
            or _contains_provider_identity(child)
            for key, child in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_provider_identity(child) for child in value)
    return False


@dataclass(frozen=True, slots=True)
class ExecutionSubstrateDescriptor:
    """Exact runtime-only provider/model provenance."""

    schema_version: str
    provider_id: str
    model_id: str
    runtime_instance_id: str
    transport_mode: str
    descriptor_digest: str

    @classmethod
    def bind(
        cls,
        *,
        provider_id: str | None = None,
        model_id: str | None = None,
        runtime_instance_id: str | None = None,
        transport_mode: str = "pre_dispatch",
    ) -> ExecutionSubstrateDescriptor:
        if type(transport_mode) is not str or transport_mode not in _TRANSPORT_MODES:
            raise ProviderPersonaSeparationError(
                "unsupported_execution_transport_mode",
                "execution substrate transport_mode is unsupported",
            )
        payload = {
            "schema_version": _DESCRIPTOR_SCHEMA_VERSION,
            "provider_id": _require_identifier(provider_id, "provider_id"),
            "model_id": _require_identifier(model_id, "model_id"),
            "runtime_instance_id": _require_identifier(
                runtime_instance_id, "runtime_instance_id"
            ),
            "transport_mode": transport_mode,
        }
        return cls(
            schema_version=payload["schema_version"],
            provider_id=payload["provider_id"],
            model_id=payload["model_id"],
            runtime_instance_id=payload["runtime_instance_id"],
            transport_mode=payload["transport_mode"],
            descriptor_digest=_sha256_text(_canonical_json(payload)),
        )

    def canonical_serialization(self) -> str:
        return _canonical_json(self._digest_payload())

    def verify(
        self, *, expected_runtime_instance_id: str | None = None
    ) -> ExecutionSubstrateDescriptor:
        _require_identifier(self.provider_id, "provider_id")
        _require_identifier(self.model_id, "model_id")
        runtime_instance_id = _require_identifier(
            self.runtime_instance_id, "runtime_instance_id"
        )
        if self.schema_version != _DESCRIPTOR_SCHEMA_VERSION:
            raise ProviderPersonaSeparationError(
                "unsupported_execution_substrate_schema",
                "execution substrate schema is unsupported",
            )
        if self.transport_mode not in _TRANSPORT_MODES:
            raise ProviderPersonaSeparationError(
                "unsupported_execution_transport_mode",
                "execution substrate transport_mode is unsupported",
            )
        if type(self.descriptor_digest) is not str or (
            _DIGEST_PATTERN.fullmatch(self.descriptor_digest) is None
        ):
            raise ProviderPersonaSeparationError(
                "inexact_execution_substrate_digest",
                "execution substrate digest is malformed",
            )
        if self.descriptor_digest != _sha256_text(self.canonical_serialization()):
            raise ProviderPersonaSeparationError(
                "execution_substrate_digest_mismatch",
                "execution substrate digest does not match its provenance",
            )
        if (
            expected_runtime_instance_id is not None
            and runtime_instance_id != expected_runtime_instance_id
        ):
            raise ProviderPersonaSeparationError(
                "stale_execution_substrate",
                "execution substrate belongs to another runtime instance",
            )
        return self

    def _digest_payload(self) -> dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "runtime_instance_id": self.runtime_instance_id,
            "transport_mode": self.transport_mode,
        }

    def to_dict(self) -> dict[str, str]:
        return {**self._digest_payload(), "descriptor_digest": self.descriptor_digest}


@dataclass(frozen=True, slots=True)
class DispatchReceipt:
    """Exact runtime provenance binding for one PSB-bound provider turn."""

    schema_version: str
    active_persona_self_binding_digest: str
    c03_parent_digest: str
    current_task_context_digest: str
    execution_substrate_descriptor_digest: str
    provider_envelope_semantic_fingerprint: str
    receipt_digest: str

    @classmethod
    def bind(
        cls,
        *,
        binding: PersonaSelfBoundSemanticBundle,
        envelope: ProviderExecutionEnvelope,
        execution_substrate: ExecutionSubstrateDescriptor,
    ) -> DispatchReceipt:
        descriptor = execution_substrate.verify()
        binding.verify()
        envelope.verify()
        projection = json.loads(binding.units[0].projected_content)
        _reject_provider_identity_in_projection(projection)
        if descriptor.provider_id != envelope.alignment.provider_id:
            raise ProviderPersonaSeparationError(
                "execution_provider_mismatch",
                "execution substrate and provider envelope identify different runtimes",
            )
        payload = {
            "schema_version": _RECEIPT_SCHEMA_VERSION,
            "active_persona_self_binding_digest": (
                binding.source_digest_manifest["persona_self_binding"]
            ),
            "c03_parent_digest": binding.parent_binding.digest(),
            "current_task_context_digest": (
                binding.source_digest_manifest["current_task_context"]
            ),
            "execution_substrate_descriptor_digest": descriptor.descriptor_digest,
            "provider_envelope_semantic_fingerprint": envelope.semantic_fingerprint,
        }
        return cls(**payload, receipt_digest=_sha256_text(_canonical_json(payload)))

    def canonical_serialization(self) -> str:
        return _canonical_json(self._digest_payload())

    def verify(self) -> DispatchReceipt:
        if self.schema_version != _RECEIPT_SCHEMA_VERSION:
            raise ProviderPersonaSeparationError(
                "unsupported_dispatch_receipt_schema",
                "dispatch receipt schema is unsupported",
            )
        for field_name in (
            "active_persona_self_binding_digest",
            "c03_parent_digest",
            "current_task_context_digest",
            "execution_substrate_descriptor_digest",
            "provider_envelope_semantic_fingerprint",
            "receipt_digest",
        ):
            value = getattr(self, field_name)
            if type(value) is not str or _DIGEST_PATTERN.fullmatch(value) is None:
                raise ProviderPersonaSeparationError(
                    "inexact_dispatch_receipt_digest",
                    f"dispatch receipt {field_name} is malformed",
                )
        if self.receipt_digest != _sha256_text(self.canonical_serialization()):
            raise ProviderPersonaSeparationError(
                "dispatch_receipt_digest_mismatch",
                "dispatch receipt digest does not match its bound inputs",
            )
        return self

    def verify_against(
        self,
        *,
        binding: PersonaSelfBoundSemanticBundle,
        envelope: ProviderExecutionEnvelope,
        execution_substrate: ExecutionSubstrateDescriptor,
    ) -> DispatchReceipt:
        descriptor = execution_substrate.verify()
        binding.verify()
        envelope.verify()
        self.verify()
        expected = DispatchReceipt.bind(
            binding=binding,
            envelope=envelope,
            execution_substrate=descriptor,
        )
        if self != expected:
            raise ProviderPersonaSeparationError(
                "dispatch_receipt_binding_mismatch",
                "dispatch receipt is bound to different runtime semantics",
            )
        return self

    def _digest_payload(self) -> dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "active_persona_self_binding_digest": (
                self.active_persona_self_binding_digest
            ),
            "c03_parent_digest": self.c03_parent_digest,
            "current_task_context_digest": self.current_task_context_digest,
            "execution_substrate_descriptor_digest": (
                self.execution_substrate_descriptor_digest
            ),
            "provider_envelope_semantic_fingerprint": (
                self.provider_envelope_semantic_fingerprint
            ),
        }

    def to_dict(self) -> dict[str, str]:
        return {**self._digest_payload(), "receipt_digest": self.receipt_digest}


@dataclass(frozen=True, slots=True)
class ProviderDispatchPreparation:
    """Verified pre-transport result; transport_called is always false here."""

    semantic_binding: PersonaSelfBoundSemanticBundle
    envelope: ProviderExecutionEnvelope
    execution_substrate: ExecutionSubstrateDescriptor
    dispatch_receipt: DispatchReceipt
    expected_runtime_instance_id: str

    def __post_init__(self) -> None:
        self.verify()

    def verify(self) -> ProviderDispatchPreparation:
        self.envelope.verify()
        self.execution_substrate.verify(
            expected_runtime_instance_id=self.expected_runtime_instance_id
        )
        self.dispatch_receipt.verify_against(
            binding=self.semantic_binding,
            envelope=self.envelope,
            execution_substrate=self.execution_substrate,
        )
        return self

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "julia_core.runtime.provider_dispatch_preparation.v1",
            "execution_substrate": self.execution_substrate.to_dict(),
            "dispatch_receipt": self.dispatch_receipt.to_dict(),
            "transport_called": False,
        }


def _reject_provider_identity_in_projection(
    projection: object,
) -> None:
    if _contains_provider_identity(projection):
        raise ProviderPersonaSeparationError(
            "provider_metadata_in_persona_authority",
            "provider or model metadata cannot become persona identity authority",
        )
