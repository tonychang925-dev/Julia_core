"""Exact incremental capability-evidence admission and binding contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
import math
from types import MappingProxyType
from typing import Any, Mapping

from julia_core.capability.models import (
    CapabilityCall,
    CapabilityCallStatus,
    Evidence,
    EvidenceSourceType,
    ToolResult,
    ToolResultStatus,
)

from .contracts import C03AdmissionRejected, AdmissionRejection, canonical_json


INCREMENTAL_EVIDENCE_CONTRACT_VERSION = (
    "julia_core.context_admission.incremental_evidence.v1"
)
MAX_INCREMENTAL_EXECUTION_ENTRIES = 6
MAX_CANONICAL_EVIDENCE_OBJECTS = 64
MAX_INCREMENTAL_EVIDENCE_CANONICAL_BYTES = 65536
MAX_INCREMENTAL_EVIDENCE_CANONICAL_DEPTH = 128

_TERMINAL_CAPABILITY_CALL_STATUSES = {
    status.value
    for status in CapabilityCallStatus
    if status
    in {
        CapabilityCallStatus.COMPLETED,
        CapabilityCallStatus.FAILED,
        CapabilityCallStatus.TIMED_OUT,
        CapabilityCallStatus.CANCELLED,
    }
}
_EVIDENTIARY_TOOL_RESULT_STATUSES = {
    ToolResultStatus.SUCCESS,
    ToolResultStatus.PARTIAL,
    ToolResultStatus.TIMEOUT,
    ToolResultStatus.CANCELLED,
    ToolResultStatus.UNAVAILABLE,
    ToolResultStatus.ERROR,
}
_CALL_STATUS_FOR_TOOL_RESULT = {
    ToolResultStatus.SUCCESS: CapabilityCallStatus.COMPLETED,
    ToolResultStatus.PARTIAL: CapabilityCallStatus.COMPLETED,
    ToolResultStatus.TIMEOUT: CapabilityCallStatus.TIMED_OUT,
    ToolResultStatus.CANCELLED: CapabilityCallStatus.CANCELLED,
    ToolResultStatus.UNAVAILABLE: CapabilityCallStatus.FAILED,
    ToolResultStatus.ERROR: CapabilityCallStatus.FAILED,
}
_INCREMENTAL_GATE_ISSUER = object()
_INCREMENTAL_BINDER_ISSUER = object()


def _rejection(code: str, message: str) -> C03AdmissionRejected:
    return C03AdmissionRejected(AdmissionRejection(code=code, message=message))


def _digest(payload: Mapping[str, Any]) -> str:
    return sha256(canonical_json(_json_copy(payload)).encode("utf-8")).hexdigest()


def _json_copy(value: Any, _depth: int = 0, _seen: set[int] | None = None) -> Any:
    if _depth > MAX_INCREMENTAL_EVIDENCE_CANONICAL_DEPTH:
        raise _rejection(
            "non_canonical_incremental_evidence_json",
            "incremental evidence exceeds canonical JSON depth",
        )
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise _rejection(
                "inexact_incremental_evidence_serialization",
                "incremental evidence contains non-string object keys",
            )
        marker = id(value)
        seen = _seen if _seen is not None else set()
        if marker in seen:
            raise _rejection(
                "non_canonical_incremental_evidence_json",
                "incremental evidence contains a cyclic JSON value",
            )
        seen.add(marker)
        copied = {
            key: _json_copy(item, _depth + 1, seen) for key, item in value.items()
        }
        seen.remove(marker)
        return copied
    if type(value) in (tuple, list):
        marker = id(value)
        seen = _seen if _seen is not None else set()
        if marker in seen:
            raise _rejection(
                "non_canonical_incremental_evidence_json",
                "incremental evidence contains a cyclic JSON value",
            )
        seen.add(marker)
        copied = [_json_copy(item, _depth + 1, seen) for item in value]
        seen.remove(marker)
        return copied
    if type(value) not in (str, int, float, bool, type(None)):
        raise _rejection(
            "inexact_incremental_evidence_serialization",
            "incremental evidence contains a non-canonical JSON value",
        )
    if type(value) is float and not math.isfinite(value):
        raise _rejection(
            "non_canonical_incremental_evidence_json",
            "incremental evidence contains NaN or an infinite float",
        )
    return value


def canonical_capability_call(call: CapabilityCall) -> dict[str, Any]:
    return {
        "capability_call_id": call.capability_call_id,
        "capability_request_id": call.capability_request_id,
        "status": _mechanical_string(call.status),
        "started_at": call.started_at,
        "completed_at": call.completed_at,
        "provider": call.provider,
        "correlation_id": call.correlation_id,
        "provenance": _json_copy(call.provenance),
    }


def canonical_tool_result(result: ToolResult) -> dict[str, Any]:
    return {
        "capability_call_id": result.capability_call_id,
        "status": _mechanical_string(result.status),
        "structured_output": _json_copy(result.structured_output),
        "error": _json_copy(result.error),
        "started_at": result.started_at,
        "completed_at": result.completed_at,
        "side_effect_state": _mechanical_string(result.side_effect_state),
        "evidence_refs": list(result.evidence_refs),
        "provider": result.provider,
        "schema_version": result.schema_version,
    }


def canonical_evidence(evidence: Evidence) -> dict[str, Any]:
    return {
        "evidence_id": evidence.evidence_id,
        "source_type": _canonical_evidence_source_type(evidence.source_type),
        "source_ref": evidence.source_ref,
        "observed_at": evidence.observed_at,
        "content_ref": evidence.content_ref,
        "provenance": _json_copy(evidence.provenance),
        "integrity_metadata": _json_copy(evidence.integrity_metadata),
        "freshness": evidence.freshness,
        "confidence": evidence.confidence,
        "correlation_id": evidence.correlation_id,
        "retrieved_at": evidence.retrieved_at,
    }


def _mechanical_string(value: str | Enum) -> str:
    if isinstance(value, Enum):
        return value.value
    if type(value) is not str:
        raise _rejection(
            "inexact_incremental_evidence_serialization",
            "incremental evidence status must mechanically normalize to a string",
        )
    return value


def _canonical_evidence_source_type(value: str | EvidenceSourceType) -> str:
    try:
        return EvidenceSourceType(value).value
    except ValueError as error:
        raise _rejection(
            "inexact_evidence_source_type",
            "Evidence source_type is outside the C-12 canonical taxonomy",
        ) from error


@dataclass(frozen=True, slots=True)
class CapabilityEvidenceSource:
    """One canonical CapabilityCall, ToolResult, and ordered Evidence lineage."""

    turn_id: str
    generation_id: str
    pass_index: int
    capability_call: CapabilityCall
    tool_result: ToolResult
    evidence: tuple[Evidence, ...]

    def __post_init__(self) -> None:
        _require_string(self.turn_id, "source turn_id")
        _require_string(self.generation_id, "source generation_id")
        if (
            type(self.pass_index) is not int
            or not 1 <= self.pass_index <= MAX_INCREMENTAL_EXECUTION_ENTRIES
        ):
            raise _rejection(
                "inexact_incremental_pass_index",
                "incremental evidence pass_index must be in 1..6",
            )
        if type(self.capability_call) is not CapabilityCall:
            raise _rejection(
                "inexact_capability_call",
                "incremental evidence requires an exact CapabilityCall",
            )
        if type(self.tool_result) is not ToolResult:
            raise _rejection(
                "inexact_tool_result",
                "incremental evidence requires an exact ToolResult",
            )
        if type(self.evidence) is not tuple or not self.evidence:
            raise _rejection(
                "control_is_not_evidence",
                "incremental evidence requires canonical Evidence objects",
            )
        for evidence in self.evidence:
            if type(evidence) is not Evidence:
                raise _rejection(
                    "inexact_evidence_object",
                    "incremental evidence requires exact Evidence objects",
                )
            _canonical_evidence_source_type(evidence.source_type)

        _require_string(self.capability_call.capability_call_id, "capability_call_id")
        _require_string(
            self.capability_call.capability_request_id, "capability_request_id"
        )
        if (
            self.capability_call.capability_call_id
            != self.tool_result.capability_call_id
        ):
            raise _rejection(
                "capability_call_id_mismatch",
                "CapabilityCall and ToolResult IDs do not match",
            )
        call_status = _mechanical_string(self.capability_call.status)
        if call_status not in _TERMINAL_CAPABILITY_CALL_STATUSES:
            raise _rejection(
                "non_terminal_capability_call",
                "incremental evidence requires a terminal CapabilityCall",
            )
        try:
            result_status = ToolResultStatus(
                _mechanical_string(self.tool_result.status)
            )
        except ValueError as error:
            raise _rejection(
                "non_evidentiary_tool_result_status",
                "incremental evidence requires an evidentiary ToolResult status",
            ) from error
        if result_status not in _EVIDENTIARY_TOOL_RESULT_STATUSES:
            raise _rejection(
                "non_evidentiary_tool_result_status",
                "incremental evidence requires an evidentiary ToolResult status",
            )
        if call_status != _CALL_STATUS_FOR_TOOL_RESULT[result_status].value:
            raise _rejection(
                "capability_tool_result_status_pair_mismatch",
                "CapabilityCall and ToolResult terminal statuses do not pair",
            )
        if (
            self.capability_call.provider
            and self.tool_result.provider
            and self.capability_call.provider != self.tool_result.provider
        ):
            raise _rejection(
                "capability_provider_mismatch",
                "CapabilityCall and ToolResult providers do not match",
            )

        evidence_ids = tuple(item.evidence_id for item in self.evidence)
        if any(type(item) is not str or not item for item in evidence_ids):
            raise _rejection(
                "inexact_evidence_id",
                "Evidence IDs must be non-empty exact strings",
            )
        if len(evidence_ids) != len(set(evidence_ids)):
            raise _rejection(
                "duplicate_evidence_id",
                "incremental evidence contains duplicate Evidence IDs",
            )
        if tuple(self.tool_result.evidence_refs) != evidence_ids:
            raise _rejection(
                "evidence_refs_mismatch",
                "ToolResult evidence_refs do not exactly match ordered Evidence IDs",
            )
        for evidence in self.evidence:
            provenance_call_id = evidence.provenance.get("capability_call_id")
            if (
                provenance_call_id is not None
                and provenance_call_id != self.capability_call.capability_call_id
            ):
                raise _rejection(
                    "evidence_provenance_mismatch",
                    "Evidence provenance capability_call_id is stale",
                )
            if (
                self.capability_call.correlation_id
                and evidence.correlation_id
                and self.capability_call.correlation_id != evidence.correlation_id
            ):
                raise _rejection(
                    "evidence_correlation_mismatch",
                    "CapabilityCall and Evidence correlation IDs do not match",
                )

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.context_admission.capability_evidence_source.v1",
            "turn_id": self.turn_id,
            "generation_id": self.generation_id,
            "pass_index": self.pass_index,
            "capability_call": canonical_capability_call(self.capability_call),
            "tool_result": canonical_tool_result(self.tool_result),
            "evidence": [canonical_evidence(item) for item in self.evidence],
        }

    def digests(self) -> tuple[str, str, tuple[str, ...], str]:
        payload = self.to_payload()
        capability_digest = _digest(payload["capability_call"])
        tool_result_digest = _digest(payload["tool_result"])
        evidence_digests = tuple(_digest(item) for item in payload["evidence"])
        entry_digest = _digest(payload)
        return capability_digest, tool_result_digest, evidence_digests, entry_digest


@dataclass(frozen=True, slots=True)
class IncrementalEvidenceAdmissionRequest:
    conversation_id: str
    turn_id: str
    entries: tuple[CapabilityEvidenceSource, ...]

    def __post_init__(self) -> None:
        _require_string(self.conversation_id, "request conversation_id")
        _require_string(self.turn_id, "request turn_id")
        if type(self.entries) is not tuple:
            raise _rejection(
                "inexact_incremental_evidence_request",
                "incremental evidence entries must be an exact tuple",
            )
        for entry in self.entries:
            if type(entry) is not CapabilityEvidenceSource:
                raise _rejection(
                    "inexact_capability_evidence_source",
                    "ledger projections cannot substitute for canonical evidence sources",
                )


@dataclass(frozen=True, slots=True)
class SealedIncrementalEvidencePackage:
    """Issuer-only receipt over exact canonical evidence execution lineage."""

    contract_version: str
    conversation_id: str
    turn_id: str
    ordered_entry_digests: tuple[str, ...]
    ordered_capability_call_ids: tuple[str, ...]
    ordered_generation_ids: tuple[str, ...]
    ordered_pass_indexes: tuple[int, ...]
    canonical_byte_count: int
    evidence_object_count: int
    gate_receipt: str
    issued_by: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.issued_by is not _INCREMENTAL_GATE_ISSUER:
            raise _rejection(
                "unauthorized_incremental_evidence_package",
                "only IncrementalEvidenceAdmissionGate seals incremental evidence",
            )
        self._validate_identity()
        if self.gate_receipt != _package_receipt(self):

            raise _rejection(
                "forged_incremental_evidence_receipt",
                "incremental evidence gate receipt is forged",
            )

    def _validate_identity(self) -> None:
        if self.contract_version != INCREMENTAL_EVIDENCE_CONTRACT_VERSION:
            raise _rejection(
                "unsupported_incremental_evidence_contract",
                "incremental evidence contract version is unsupported",
            )
        _require_string(self.conversation_id, "package conversation_id")
        _require_string(self.turn_id, "package turn_id")
        lengths = {
            len(self.ordered_entry_digests),
            len(self.ordered_capability_call_ids),
            len(self.ordered_generation_ids),
            len(self.ordered_pass_indexes),
        }
        if (
            len(lengths) != 1
            or not 1 <= next(iter(lengths)) <= MAX_INCREMENTAL_EXECUTION_ENTRIES
        ):
            raise _rejection(
                "inexact_incremental_evidence_manifest",
                "incremental evidence manifest length is inexact",
            )
        if type(self.canonical_byte_count) is not int or self.canonical_byte_count < 1:
            raise _rejection(
                "inexact_incremental_evidence_byte_count",
                "incremental evidence canonical byte count is inexact",
            )
        if (
            type(self.evidence_object_count) is not int
            or not 1 <= self.evidence_object_count <= MAX_CANONICAL_EVIDENCE_OBJECTS
        ):
            raise _rejection(
                "inexact_incremental_evidence_count",
                "incremental Evidence object count is inexact",
            )

    def verify(self) -> SealedIncrementalEvidencePackage:
        self.__post_init__()
        return self


def _package_receipt(package: SealedIncrementalEvidencePackage) -> str:
    return _incremental_gate_receipt(
        contract_version=package.contract_version,
        conversation_id=package.conversation_id,
        turn_id=package.turn_id,
        ordered_entry_digests=package.ordered_entry_digests,
        ordered_capability_call_ids=package.ordered_capability_call_ids,
        ordered_generation_ids=package.ordered_generation_ids,
        ordered_pass_indexes=package.ordered_pass_indexes,
        canonical_byte_count=package.canonical_byte_count,
        evidence_object_count=package.evidence_object_count,
    )


def _incremental_gate_receipt(
    *,
    contract_version: str,
    conversation_id: str,
    turn_id: str,
    ordered_entry_digests: tuple[str, ...],
    ordered_capability_call_ids: tuple[str, ...],
    ordered_generation_ids: tuple[str, ...],
    ordered_pass_indexes: tuple[int, ...],
    canonical_byte_count: int,
    evidence_object_count: int,
) -> str:
    return _digest(
        {
            "contract_version": contract_version,
            "conversation_id": conversation_id,
            "turn_id": turn_id,
            "ordered_entry_digests": ordered_entry_digests,
            "ordered_capability_call_ids": ordered_capability_call_ids,
            "ordered_generation_ids": ordered_generation_ids,
            "ordered_pass_indexes": ordered_pass_indexes,
            "canonical_byte_count": canonical_byte_count,
            "evidence_object_count": evidence_object_count,
        }
    )


class IncrementalEvidenceAdmissionGate:
    """Sole fail-closed issuer of sealed incremental evidence packages."""

    def seal(
        self, request: IncrementalEvidenceAdmissionRequest
    ) -> SealedIncrementalEvidencePackage:
        if type(self) is not IncrementalEvidenceAdmissionGate:
            raise _rejection(
                "inexact_incremental_evidence_gate",
                "incremental evidence requires the exact admission gate",
            )
        if type(request) is not IncrementalEvidenceAdmissionRequest:
            raise _rejection(
                "inexact_incremental_evidence_request",
                "incremental evidence requires an exact admission request",
            )
        if not 1 <= len(request.entries) <= MAX_INCREMENTAL_EXECUTION_ENTRIES:
            raise _rejection(
                "context_evidence_budget_exceeded",
                "incremental execution entries exceed the frozen P0 budget",
            )
        for entry in request.entries:
            if type(entry) is not CapabilityEvidenceSource:
                raise _rejection(
                    "inexact_capability_evidence_source",
                    "ledger projections cannot substitute for canonical evidence sources",
                )
            entry.__post_init__()
        evidence_count = sum(len(entry.evidence) for entry in request.entries)
        if evidence_count > MAX_CANONICAL_EVIDENCE_OBJECTS:
            raise _rejection(
                "context_evidence_budget_exceeded",
                "incremental Evidence object count exceeds the frozen P0 budget",
            )
        if any(entry.turn_id != request.turn_id for entry in request.entries):
            raise _rejection(
                "incremental_turn_mismatch",
                "incremental evidence turn IDs do not match the request",
            )
        pass_indexes = tuple(entry.pass_index for entry in request.entries)
        generation_ids = tuple(entry.generation_id for entry in request.entries)
        if len(generation_ids) != len(set(generation_ids)):
            raise _rejection(
                "duplicate_generation_id",
                "incremental evidence generation IDs must be unique",
            )
        if any(
            current <= previous
            for previous, current in zip(pass_indexes, pass_indexes[1:], strict=False)
        ):
            raise _rejection(
                "non_monotonic_incremental_pass_index",
                "incremental evidence pass indexes must strictly increase",
            )
        call_ids = tuple(
            entry.capability_call.capability_call_id for entry in request.entries
        )
        if len(call_ids) != len(set(call_ids)):
            raise _rejection(
                "duplicate_capability_call_id",
                "incremental evidence contains duplicate CapabilityCall IDs",
            )
        evidence_ids = [
            evidence.evidence_id
            for entry in request.entries
            for evidence in entry.evidence
        ]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise _rejection(
                "duplicate_evidence_id",
                "incremental evidence contains duplicate Evidence IDs",
            )

        payloads = tuple(entry.to_payload() for entry in request.entries)
        entry_digests = tuple(_digest(payload) for payload in payloads)
        if len(entry_digests) != len(set(entry_digests)):
            raise _rejection(
                "duplicate_incremental_entry_digest",
                "incremental evidence contains ambiguous entry digests",
            )
        byte_count = sum(
            len(canonical_json(payload).encode("utf-8")) for payload in payloads
        )
        if (
            evidence_count > MAX_CANONICAL_EVIDENCE_OBJECTS
            or byte_count > MAX_INCREMENTAL_EVIDENCE_CANONICAL_BYTES
        ):
            raise _rejection(
                "context_evidence_budget_exceeded",
                "incremental canonical evidence exceeds the frozen P0 budget",
            )

        receipt = _incremental_gate_receipt(
            contract_version=INCREMENTAL_EVIDENCE_CONTRACT_VERSION,
            conversation_id=request.conversation_id,
            turn_id=request.turn_id,
            ordered_entry_digests=entry_digests,
            ordered_capability_call_ids=call_ids,
            ordered_generation_ids=generation_ids,
            ordered_pass_indexes=pass_indexes,
            canonical_byte_count=byte_count,
            evidence_object_count=evidence_count,
        )
        return SealedIncrementalEvidencePackage(
            contract_version=INCREMENTAL_EVIDENCE_CONTRACT_VERSION,
            conversation_id=request.conversation_id,
            turn_id=request.turn_id,
            ordered_entry_digests=entry_digests,
            ordered_capability_call_ids=call_ids,
            ordered_generation_ids=generation_ids,
            ordered_pass_indexes=pass_indexes,
            canonical_byte_count=byte_count,
            evidence_object_count=evidence_count,
            gate_receipt=receipt,
            issued_by=_INCREMENTAL_GATE_ISSUER,
        )


@dataclass(frozen=True, slots=True)
class AdmittedIncrementalEvidenceUnit:
    contract_version: str
    capability_call_id: str
    tool_result_digest: str
    entry_digest: str
    canonical_content: str
    issued_by: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.issued_by is not _INCREMENTAL_BINDER_ISSUER:
            raise _rejection(
                "unauthorized_incremental_evidence_unit",
                "only ExactAdmittedIncrementalEvidenceBinder constructs evidence units",
            )
        if self.contract_version != INCREMENTAL_EVIDENCE_CONTRACT_VERSION:
            raise _rejection(
                "unsupported_incremental_evidence_contract",
                "incremental evidence unit contract version is unsupported",
            )
        if (
            sha256(self.canonical_content.encode("utf-8")).hexdigest()
            != self.entry_digest
        ):
            raise _rejection(
                "forged_incremental_evidence_unit",
                "incremental evidence unit digest is forged",
            )
        payload = json.loads(self.canonical_content)
        if (
            payload["tool_result"]["capability_call_id"] != self.capability_call_id
            or _digest(payload["tool_result"]) != self.tool_result_digest
        ):
            raise _rejection(
                "forged_tool_result_identity",
                "incremental evidence ToolResult identity is forged",
            )

    def verify(self) -> AdmittedIncrementalEvidenceUnit:
        self.__post_init__()
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.context_admission.incremental_evidence_unit.v1",
            "contract_version": self.contract_version,
            "capability_call_id": self.capability_call_id,
            "tool_result_digest": self.tool_result_digest,
            "entry_digest": self.entry_digest,
            "canonical_content": self.canonical_content,
        }


@dataclass(frozen=True, slots=True)
class AdmittedIncrementalEvidenceBundle:
    contract_version: str
    conversation_id: str
    turn_id: str
    gate_receipt: str
    ordered_entry_digests: tuple[str, ...]
    ordered_capability_call_ids: tuple[str, ...]
    ordered_generation_ids: tuple[str, ...]
    ordered_pass_indexes: tuple[int, ...]
    canonical_byte_count: int
    evidence_object_count: int
    units: tuple[AdmittedIncrementalEvidenceUnit, ...]
    issued_by: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.issued_by is not _INCREMENTAL_BINDER_ISSUER:
            raise _rejection(
                "unauthorized_incremental_evidence_bundle",
                "only ExactAdmittedIncrementalEvidenceBinder constructs bundles",
            )
        _require_string(self.conversation_id, "bundle conversation_id")
        _require_string(self.turn_id, "bundle turn_id")
        if self.contract_version != INCREMENTAL_EVIDENCE_CONTRACT_VERSION:
            raise _rejection(
                "unsupported_incremental_evidence_contract",
                "incremental evidence bundle contract version is unsupported",
            )
        if (
            type(self.units) is not tuple
            or not 1 <= len(self.units) <= MAX_INCREMENTAL_EXECUTION_ENTRIES
        ):
            raise _rejection(
                "inexact_incremental_evidence_bundle",
                "incremental evidence bundle unit count is inexact",
            )
        for unit in self.units:
            if type(unit) is not AdmittedIncrementalEvidenceUnit:
                raise _rejection(
                    "inexact_incremental_evidence_unit",
                    "incremental evidence bundle requires exact bound units",
                )
            unit.verify()
        manifest_lengths = {
            len(self.ordered_entry_digests),
            len(self.ordered_capability_call_ids),
            len(self.ordered_generation_ids),
            len(self.ordered_pass_indexes),
            len(self.units),
        }
        if len(manifest_lengths) != 1:
            raise _rejection(
                "inexact_incremental_evidence_bundle_manifest",
                "incremental evidence bundle manifest is partial or ambiguous",
            )
        if (
            tuple(unit.entry_digest for unit in self.units)
            != self.ordered_entry_digests
        ):
            raise _rejection(
                "incremental_evidence_unit_substitution",
                "incremental evidence units do not match the sealed digest manifest",
            )
        if (
            tuple(unit.capability_call_id for unit in self.units)
            != self.ordered_capability_call_ids
        ):
            raise _rejection(
                "incremental_evidence_unit_substitution",
                "incremental evidence call IDs do not match the sealed manifest",
            )
        expected_receipt = _incremental_gate_receipt(
            contract_version=self.contract_version,
            conversation_id=self.conversation_id,
            turn_id=self.turn_id,
            ordered_entry_digests=self.ordered_entry_digests,
            ordered_capability_call_ids=self.ordered_capability_call_ids,
            ordered_generation_ids=self.ordered_generation_ids,
            ordered_pass_indexes=self.ordered_pass_indexes,
            canonical_byte_count=self.canonical_byte_count,
            evidence_object_count=self.evidence_object_count,
        )
        if self.gate_receipt != expected_receipt:
            raise _rejection(
                "forged_incremental_evidence_receipt",
                "incremental evidence bundle receipt/manifest is forged",
            )

    def verify(self) -> AdmittedIncrementalEvidenceBundle:
        self.__post_init__()
        return self

    def canonical_content(self) -> str:
        return canonical_json([unit.to_dict() for unit in self.units])

    def semantic_fingerprint(self) -> str:
        return sha256(self.canonical_content().encode("utf-8")).hexdigest()

    def to_message(self) -> dict[str, str]:
        return {"role": "system", "content": self.canonical_content()}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "julia_core.context_admission.admitted_incremental_evidence.v1",
            "contract_version": self.contract_version,
            "conversation_id": self.conversation_id,
            "turn_id": self.turn_id,
            "gate_receipt": self.gate_receipt,
            "semantic_fingerprint": self.semantic_fingerprint(),
            "ordered_entry_digests": [unit.entry_digest for unit in self.units],
            "authority": {
                "canonical": True,
                "turn_evidence_ledger": False,
                "conversation": False,
                "provider": False,
                "assistant_self": False,
            },
        }


class ExactAdmittedIncrementalEvidenceBinder:
    """Bind only exact unchanged canonical sources to a sealed package."""

    def bind(
        self,
        package: SealedIncrementalEvidencePackage,
        request: IncrementalEvidenceAdmissionRequest,
    ) -> AdmittedIncrementalEvidenceBundle:
        if type(self) is not ExactAdmittedIncrementalEvidenceBinder:
            raise _rejection(
                "inexact_incremental_evidence_binder",
                "incremental evidence requires the exact binder",
            )
        if type(package) is not SealedIncrementalEvidencePackage:
            raise _rejection(
                "unsealed_incremental_evidence",
                "incremental evidence binding requires an exact sealed package",
            )
        package.verify()
        if type(request) is not IncrementalEvidenceAdmissionRequest:
            raise _rejection(
                "inexact_incremental_evidence_request",
                "incremental evidence binding requires the original exact request",
            )
        if (
            package.conversation_id != request.conversation_id
            or package.turn_id != request.turn_id
            or len(request.entries) != len(package.ordered_entry_digests)
        ):
            raise _rejection(
                "stale_incremental_evidence_binding",
                "incremental evidence request does not match the sealed package",
            )

        units: list[AdmittedIncrementalEvidenceUnit] = []
        for index, entry in enumerate(request.entries):
            if type(entry) is not CapabilityEvidenceSource:
                raise _rejection(
                    "inexact_capability_evidence_source",
                    "ledger projections cannot substitute for canonical evidence sources",
                )
            payload = entry.to_payload()
            entry_digest = _digest(payload)
            _, tool_result_digest, _, _ = entry.digests()
            if entry_digest != package.ordered_entry_digests[index]:
                raise _rejection(
                    "post_seal_incremental_evidence_mutation",
                    "incremental evidence source changed after package sealing",
                )
            entry.__post_init__()
            if (
                entry.capability_call.capability_call_id
                != package.ordered_capability_call_ids[index]
                or entry.generation_id != package.ordered_generation_ids[index]
                or entry.pass_index != package.ordered_pass_indexes[index]
                or entry.turn_id != package.turn_id
            ):
                raise _rejection(
                    "stale_incremental_evidence_identity",
                    "incremental evidence lineage does not match the sealed package",
                )
            units.append(
                AdmittedIncrementalEvidenceUnit(
                    contract_version=package.contract_version,
                    capability_call_id=entry.capability_call.capability_call_id,
                    tool_result_digest=tool_result_digest,
                    entry_digest=entry_digest,
                    canonical_content=canonical_json(payload),
                    issued_by=_INCREMENTAL_BINDER_ISSUER,
                )
            )
        return AdmittedIncrementalEvidenceBundle(
            contract_version=package.contract_version,
            conversation_id=package.conversation_id,
            turn_id=package.turn_id,
            gate_receipt=package.gate_receipt,
            ordered_entry_digests=package.ordered_entry_digests,
            ordered_capability_call_ids=package.ordered_capability_call_ids,
            ordered_generation_ids=package.ordered_generation_ids,
            ordered_pass_indexes=package.ordered_pass_indexes,
            canonical_byte_count=package.canonical_byte_count,
            evidence_object_count=package.evidence_object_count,
            units=tuple(units),
            issued_by=_INCREMENTAL_BINDER_ISSUER,
        )


def _require_string(value: str, field_name: str) -> None:
    if type(value) is not str or not value:
        raise _rejection(
            "inexact_string_field",
            f"{field_name} must be a non-empty exact string",
        )


__all__ = [
    "MAX_CANONICAL_EVIDENCE_OBJECTS",
    "MAX_INCREMENTAL_EVIDENCE_CANONICAL_BYTES",
    "MAX_INCREMENTAL_EXECUTION_ENTRIES",
    "AdmittedIncrementalEvidenceBundle",
    "AdmittedIncrementalEvidenceUnit",
    "CapabilityEvidenceSource",
    "ExactAdmittedIncrementalEvidenceBinder",
    "IncrementalEvidenceAdmissionGate",
    "IncrementalEvidenceAdmissionRequest",
    "SealedIncrementalEvidencePackage",
    "canonical_capability_call",
    "canonical_evidence",
    "canonical_tool_result",
]
