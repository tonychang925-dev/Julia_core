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
_DISPATCH_AUTHORIZATION_SCHEMA_VERSION = (
    "julia_core.runtime.golden_mira_dispatch_authorization.v1"
)
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
    transport_called_before_gate: bool = False

    def __post_init__(self) -> None:
        self.verify()

    def verify(self) -> ProviderDispatchPreparation:
        if type(self.transport_called_before_gate) is not bool:
            raise ProviderPersonaSeparationError(
                "inexact_transport_pre_gate_state",
                "pre-gate transport state is inexact",
            )
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
            "transport_called_before_gate": self.transport_called_before_gate,
            "transport_called": False,
        }


@dataclass(frozen=True, slots=True)
class GoldenMiraDispatchAuthorization:
    """Typed non-semantic output exclusively issued by the Golden Mira gate."""

    schema_version: str
    approved_preparation: ProviderDispatchPreparation
    authorization_digest: str
    issued_by: GoldenMiraDispatchGate

    def verify(self) -> GoldenMiraDispatchAuthorization:
        if self.schema_version != _DISPATCH_AUTHORIZATION_SCHEMA_VERSION:
            raise ProviderPersonaSeparationError(
                "unsupported_dispatch_authorization_schema",
                "Golden Mira dispatch authorization schema is unsupported",
            )
        if type(self.issued_by) is not GoldenMiraDispatchGate:
            raise ProviderPersonaSeparationError(
                "unauthorized_golden_mira_dispatch",
                "only the exact Golden Mira gate issues dispatch authorization",
            )
        expected = self.issued_by.authorize(self.approved_preparation)
        if self != expected:
            raise ProviderPersonaSeparationError(
                "golden_mira_dispatch_authorization_mismatch",
                "Golden Mira dispatch authorization is forged or stale",
            )
        return self

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "authorization_digest": self.authorization_digest,
            "runtime_only": True,
            "semantic_authority": False,
        }


@dataclass(frozen=True, slots=True)
class GoldenMiraDispatchGate:
    """Single fail-closed gate from verified preparation to transport ingress."""

    expected_active_psb_digest: str
    expected_runtime_instance_id: str

    def __post_init__(self) -> None:
        if (
            type(self.expected_active_psb_digest) is not str
            or _DIGEST_PATTERN.fullmatch(self.expected_active_psb_digest) is None
        ):
            raise ProviderPersonaSeparationError(
                "inexact_golden_mira_psb_pin",
                "Golden Mira dispatch gate PSB pin is malformed",
            )
        _require_identifier(
            self.expected_runtime_instance_id,
            "expected_runtime_instance_id",
        )

    def authorize(
        self, preparation: ProviderDispatchPreparation
    ) -> GoldenMiraDispatchAuthorization:
        if type(self) is not GoldenMiraDispatchGate:
            raise ProviderPersonaSeparationError(
                "inexact_golden_mira_dispatch_gate",
                "Golden Mira dispatch requires the exact typed gate",
            )
        if type(preparation) is not ProviderDispatchPreparation:
            raise ProviderPersonaSeparationError(
                "inexact_golden_mira_dispatch_preparation",
                "Golden Mira dispatch requires an exact verified preparation",
            )
        preparation.verify()
        if preparation.transport_called_before_gate:
            raise ProviderPersonaSeparationError(
                "transport_already_called_before_gate",
                "Golden Mira dispatch cannot authorize after transport",
            )
        if preparation.dispatch_receipt.active_persona_self_binding_digest != (
            self.expected_active_psb_digest
        ):
            raise ProviderPersonaSeparationError(
                "wrong_active_persona_self_binding",
                "Golden Mira dispatch requires the pinned active PSB digest",
            )
        if preparation.expected_runtime_instance_id != (
            self.expected_runtime_instance_id
        ):
            raise ProviderPersonaSeparationError(
                "stale_execution_substrate",
                "Golden Mira dispatch substrate belongs to another runtime",
            )
        payload = {
            "schema_version": _DISPATCH_AUTHORIZATION_SCHEMA_VERSION,
            "active_persona_self_binding_digest": (
                preparation.dispatch_receipt.active_persona_self_binding_digest
            ),
            "c03_parent_digest": preparation.dispatch_receipt.c03_parent_digest,
            "current_task_context_digest": (
                preparation.dispatch_receipt.current_task_context_digest
            ),
            "execution_substrate_descriptor_digest": (
                preparation.dispatch_receipt.execution_substrate_descriptor_digest
            ),
            "provider_envelope_semantic_fingerprint": (
                preparation.dispatch_receipt.provider_envelope_semantic_fingerprint
            ),
            "expected_runtime_instance_id": self.expected_runtime_instance_id,
        }
        return GoldenMiraDispatchAuthorization(
            schema_version=_DISPATCH_AUTHORIZATION_SCHEMA_VERSION,
            approved_preparation=preparation,
            authorization_digest=_sha256_text(_canonical_json(payload)),
            issued_by=self,
        )


@dataclass(frozen=True, slots=True)
class GoldenMiraSealedTransport:
    """Exact gated transport-boundary object; no transport is invoked here."""

    authorization: GoldenMiraDispatchAuthorization

    def verify(self) -> GoldenMiraSealedTransport:
        self.authorization.verify()
        return self

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "julia_core.runtime.golden_mira_sealed_transport.v1",
            "authorization": self.authorization.to_dict(),
            "transport_called": False,
        }


@dataclass(frozen=True, slots=True)
class GoldenMiraTransportBoundary:
    """Transport-capable ingress that accepts only gated authorization."""

    def seal(
        self, authorization: GoldenMiraDispatchAuthorization
    ) -> GoldenMiraSealedTransport:
        if type(self) is not GoldenMiraTransportBoundary:
            raise ProviderPersonaSeparationError(
                "inexact_golden_mira_transport_boundary",
                "Golden Mira transport requires the exact typed boundary",
            )
        if type(authorization) is not GoldenMiraDispatchAuthorization:
            raise ProviderPersonaSeparationError(
                "ungated_golden_mira_dispatch",
                "Golden Mira transport cannot accept raw or unreceipted input",
            )
        authorization.verify()
        return GoldenMiraSealedTransport(authorization=authorization)


def _reject_provider_identity_in_projection(
    projection: object,
) -> None:
    if _contains_provider_identity(projection):
        raise ProviderPersonaSeparationError(
            "provider_metadata_in_persona_authority",
            "provider or model metadata cannot become persona identity authority",
        )
