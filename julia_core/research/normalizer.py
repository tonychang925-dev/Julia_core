"""Sole Core verification-state mint for research source observations."""

from __future__ import annotations

import hashlib
import re
import time
from collections.abc import Mapping
from typing import Any

from julia_core.capability.models import (
    CapabilityCall,
    CapabilityRequest,
    Evidence,
    EvidenceSourceType,
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResult,
    ToolResultStatus,
)
from julia_core.research.contracts import (
    ContentBinding,
    NormalizedResearchEnrichment,
    ResearchClaim,
    ResearchSemanticResult,
    SourceObservationEvidence,
    SourceObservationFailure,
    SourceRecord,
    VerificationState,
)

_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_WEB_SEARCH_KINDS = {"web_search", "websearch", "search_result"}


class ResearchNormalizationError(ValueError):
    """Provider research output cannot be normalized into the C1 contract."""


class ResearchEvidenceNormalizer:
    """Normalizes provider output while preserving semantic/observation truth planes.

    Provider verification labels are input text only. This class is the only
    C1 code path that writes ``Evidence.integrity_metadata["verification_state"]``.
    """

    def normalize_provider_outcome(
        self,
        outcome: ProviderExecutionOutcome,
        *,
        request: CapabilityRequest,
        call: CapabilityCall,
    ) -> NormalizedResearchEnrichment:
        if call.capability_request_id != request.capability_request_id:
            raise ResearchNormalizationError("capability call does not match request")
        if call.correlation_id and request.correlation_id and call.correlation_id != request.correlation_id:
            raise ResearchNormalizationError("capability call correlation does not match request")

        structured = dict(outcome.structured_output or {})
        semantic = self._parse_semantic_result(structured.get("semantic_result"))
        observation_payload = structured.get("source_observation")
        observation_present = isinstance(observation_payload, Mapping)
        failure = self._parse_failure(observation_payload.get("failure")) if observation_present else None
        source_records = self._parse_source_records(
            observation_payload.get("source_records", []) if observation_present else []
        )
        bindings = self._parse_bindings(
            observation_payload.get("content_bindings", []) if observation_present else []
        )
        binding_index = {item.source_record_id: item for item in bindings}
        observed_at = (
            str(observation_payload.get("observed_at", "")) if observation_present else ""
        )
        observation_provenance = (
            dict(observation_payload.get("provenance", {})) if observation_present else {}
        )
        raw_refs = tuple(
            str(item)
            for item in (
                observation_payload.get("raw_response_refs", ()) if observation_present else ()
            )
            if str(item).strip()
        )
        available = bool(observation_present and observation_payload.get("available", bool(source_records)))

        if outcome.status is not ToolResultStatus.SUCCESS and failure is None:
            failure = SourceObservationFailure(
                code="provider_execution_failed",
                message=(outcome.error or {}).get("message", "research provider execution failed"),
            )
            available = False

        verification_states: dict[str, str] = {}
        evidence_items: list[Evidence] = []
        if semantic.claims:
            for claim in semantic.claims:
                state = self._claim_state(
                    claim=claim,
                    provider_success=outcome.status is ToolResultStatus.SUCCESS,
                    observation_available=available,
                    source_records=source_records,
                    bindings=binding_index,
                    raw_response_refs=raw_refs,
                    request=request,
                    call=call,
                    failure=failure,
                )
                verification_states[claim.claim_id] = state.value
                evidence_items.append(self._mint_claim_evidence(
                    claim=claim,
                    state=state,
                    source_records=source_records,
                    bindings=binding_index,
                    observed_at=observed_at,
                    request=request,
                    call=call,
                    observation_provenance=observation_provenance,
                ))
        else:
            if source_records:
                for source_record in source_records:
                    state = self._observation_state(
                        provider_success=outcome.status is ToolResultStatus.SUCCESS,
                        observation_available=available,
                        source_record=source_record,
                        binding=binding_index.get(source_record.source_record_id),
                        raw_response_refs=raw_refs,
                        request=request,
                        call=call,
                        failure=failure,
                    )
                    evidence_items.append(self._mint_evidence(
                        state=state,
                        source_record=source_record,
                        binding=binding_index.get(source_record.source_record_id),
                        observed_at=source_record.observed_at or observed_at or _now(),
                        request=request,
                        call=call,
                        observation_provenance=observation_provenance,
                        semantic_binding={
                            "semantic_material": "source_observation",
                            "claim_id": "NONE",
                            "claim_assertion": "NONE",
                            "source_record_ids": [source_record.source_record_id],
                        },
                    ))
            else:
                state = self._observation_state(
                    provider_success=outcome.status is ToolResultStatus.SUCCESS,
                    observation_available=available,
                    source_record=None,
                    binding=None,
                    raw_response_refs=raw_refs,
                    request=request,
                    call=call,
                    failure=failure,
                )
                evidence_items.append(self._mint_evidence(
                    state=state,
                    source_record=None,
                    binding=None,
                    observed_at=observed_at or _now(),
                    request=request,
                    call=call,
                    observation_provenance=observation_provenance,
                    semantic_binding={
                        "semantic_material": "source_observation",
                        "claim_id": "NONE",
                        "claim_assertion": "NONE",
                    },
                ))

        observation = SourceObservationEvidence(
            source_records=source_records,
            content_bindings=bindings,
            evidence=tuple(evidence_items),
            raw_response_refs=raw_refs,
            observed_at=observed_at or _now(),
            provenance=self._runtime_provenance(request, call, observation_provenance),
            correlation_id=request.correlation_id,
            available=available,
            failure=failure,
            claim_verification_states=verification_states,
        )
        result = ToolResult(
            capability_call_id=call.capability_call_id,
            status=outcome.status,
            structured_output={
                "semantic_result": self._semantic_to_dict(semantic),
                "source_observation": {
                    "available": available,
                    "source_record_ids": [item.source_record_id for item in source_records],
                    "claim_verification_states": dict(verification_states),
                    "failure": None if failure is None else {
                        "code": failure.code,
                        "message": failure.message,
                        "retryable": failure.retryable,
                    },
                },
            },
            error=dict(outcome.error) if outcome.error is not None else None,
            side_effect_state=outcome.side_effect_state,
            evidence_refs=tuple(item.evidence_id for item in evidence_items),
            provider=call.provider,
            schema_version="research.event.enrich.v1",
        )
        return NormalizedResearchEnrichment(
            semantic_result=semantic,
            observation=observation,
            tool_result=result,
        )

    def _parse_semantic_result(self, value: Any) -> ResearchSemanticResult:
        if not isinstance(value, Mapping):
            raise ResearchNormalizationError("semantic_result must be an object")
        required = {"factual_summary", "claims", "contradictions", "unknowns", "timeline", "related_entities"}
        missing = required - set(value)
        if missing:
            raise ResearchNormalizationError(f"semantic_result fields missing: {sorted(missing)}")
        if not isinstance(value["factual_summary"], str):
            raise ResearchNormalizationError("factual_summary must be a string")
        claims_value = value["claims"]
        if not isinstance(claims_value, list):
            raise ResearchNormalizationError("claims must be an array")
        claims = tuple(self._parse_claim(item) for item in claims_value)
        return ResearchSemanticResult(
            factual_summary=str(value["factual_summary"]),
            claims=claims,
            contradictions=tuple(self._string_items(value["contradictions"], "contradictions")),
            unknowns=tuple(self._string_items(value["unknowns"], "unknowns")),
            timeline=tuple(self._object_items(value["timeline"], "timeline")),
            related_entities=tuple(self._object_items(value["related_entities"], "related_entities")),
        )

    @staticmethod
    def _parse_claim(value: Any) -> ResearchClaim:
        if not isinstance(value, Mapping):
            raise ResearchNormalizationError("each semantic claim must be an object")
        missing = {"text", "source_record_ids"} - set(value)
        if missing:
            raise ResearchNormalizationError(f"claim fields missing: {sorted(missing)}")
        ids = value["source_record_ids"]
        if not isinstance(ids, list) or not all(isinstance(item, str) and item.strip() for item in ids):
            raise ResearchNormalizationError("claim source_record_ids must be an array of non-empty strings")
        return ResearchClaim(
            text=str(value["text"]),
            source_record_ids=tuple(ids),
            claim_id=str(value.get("claim_id", "")),
            provider_verification_state=str(value.get("verification_state", "")),
        )

    @staticmethod
    def _parse_source_records(value: Any) -> tuple[SourceRecord, ...]:
        if not isinstance(value, list):
            raise ResearchNormalizationError("source_records must be an array")
        records = []
        for item in value:
            if not isinstance(item, Mapping):
                raise ResearchNormalizationError("each source record must be an object")
            required = {
                "source_record_id", "source_kind", "source_ref", "capture_status",
                "fetch_status", "observed_at",
            }
            missing = required - set(item)
            if missing:
                raise ResearchNormalizationError(f"source record fields missing: {sorted(missing)}")
            records.append(SourceRecord(
                source_record_id=str(item["source_record_id"]),
                source_kind=str(item["source_kind"]),
                source_ref=str(item["source_ref"]),
                capture_status=str(item["capture_status"]),
                fetch_status=str(item["fetch_status"]),
                observed_at=str(item["observed_at"]),
                source_url=item.get("source_url"),
                raw_response_ref=str(item.get("raw_response_ref", "")),
                content_ref=str(item.get("content_ref", "")),
                content_digest=str(item.get("content_digest", "")),
                provenance=dict(item.get("provenance", {})),
            ))
        return tuple(records)

    @staticmethod
    def _parse_bindings(value: Any) -> tuple[ContentBinding, ...]:
        if not isinstance(value, list):
            raise ResearchNormalizationError("content_bindings must be an array")
        bindings = []
        for item in value:
            if not isinstance(item, Mapping):
                raise ResearchNormalizationError("each content binding must be an object")
            missing = {"source_record_id", "content_ref", "digest"} - set(item)
            if missing:
                raise ResearchNormalizationError(f"content binding fields missing: {sorted(missing)}")
            bindings.append(ContentBinding(
                source_record_id=str(item["source_record_id"]),
                content_ref=str(item["content_ref"]),
                digest=str(item["digest"]),
                extract_ref=str(item.get("extract_ref", "")),
                locator=str(item.get("locator", "")),
                provenance=dict(item.get("provenance", {})),
            ))
        return tuple(bindings)

    @staticmethod
    def _parse_failure(value: Any) -> SourceObservationFailure | None:
        if value is None:
            return None
        if not isinstance(value, Mapping):
            raise ResearchNormalizationError("source observation failure must be an object")
        missing = {"code", "message"} - set(value)
        if missing:
            raise ResearchNormalizationError(f"failure fields missing: {sorted(missing)}")
        retryable = value.get("retryable")
        if retryable is not None and not isinstance(retryable, bool):
            raise ResearchNormalizationError("failure retryable must be boolean or null")
        return SourceObservationFailure(
            code=str(value["code"]),
            message=str(value["message"]),
            retryable=retryable,
        )

    def _claim_state(
        self,
        *,
        claim: ResearchClaim,
        provider_success: bool,
        observation_available: bool,
        source_records: tuple[SourceRecord, ...],
        bindings: dict[str, ContentBinding],
        raw_response_refs: tuple[str, ...],
        request: CapabilityRequest,
        call: CapabilityCall,
        failure: SourceObservationFailure | None,
    ) -> VerificationState:
        if not provider_success or not observation_available:
            return _failure_state(failure)
        if not claim.source_record_ids:
            return VerificationState.NOT_PROVEN
        source_records_by_id = {item.source_record_id: item for item in source_records}
        for source_record_id in claim.source_record_ids:
            record = source_records_by_id.get(source_record_id)
            if record is None:
                return VerificationState.NOT_PROVEN
            if record.source_kind.lower() in _WEB_SEARCH_KINDS:
                return VerificationState.REPORT_ONLY
            if record.capture_status.lower() not in {"success", "observed", "captured"}:
                return VerificationState.NOT_PROVEN
            if record.fetch_status.lower() not in {"success", "observed", "retained", "not_required"}:
                return VerificationState.NOT_PROVEN
            binding = bindings.get(source_record_id)
            if binding is None:
                return VerificationState.NOT_PROVEN
            if not binding.content_ref.strip() and not binding.extract_ref.strip():
                return VerificationState.NOT_PROVEN
            if not _valid_digest(binding.digest):
                return VerificationState.NOT_PROVEN
            if record.content_digest and record.content_digest.lower() != binding.digest.lower():
                return VerificationState.NOT_PROVEN
            if not record.observed_at.strip() or not binding.provenance:
                return VerificationState.NOT_PROVEN
            if not _runtime_bound(
                binding,
                request=request,
                call=call,
                raw_response_refs=raw_response_refs,
            ):
                return VerificationState.NOT_PROVEN
        return VerificationState.SOURCE_VERIFIED

    def _observation_state(
        self,
        *,
        provider_success: bool,
        observation_available: bool,
        source_record: SourceRecord | None,
        binding: ContentBinding | None,
        raw_response_refs: tuple[str, ...],
        request: CapabilityRequest,
        call: CapabilityCall,
        failure: SourceObservationFailure | None,
    ) -> VerificationState:
        if not provider_success or not observation_available:
            return _failure_state(failure)

        if failure is not None:
            return _failure_state(failure)
        if source_record is None:
            return VerificationState.NOT_PROVEN
        if source_record.source_kind.lower() in _WEB_SEARCH_KINDS:
            return VerificationState.REPORT_ONLY
        if source_record.capture_status.lower() not in {"success", "observed", "captured"}:
            return VerificationState.NOT_PROVEN
        if source_record.fetch_status.lower() not in {"success", "retained"}:
            return VerificationState.NOT_PROVEN
        if binding is None:
            return VerificationState.NOT_PROVEN
        if not binding.content_ref.strip() and not binding.extract_ref.strip():
            return VerificationState.NOT_PROVEN
        if not _valid_digest(binding.digest):
            return VerificationState.NOT_PROVEN
        if not _valid_digest(source_record.content_digest):
            return VerificationState.NOT_PROVEN
        if source_record.content_digest.lower() != binding.digest.lower():
            return VerificationState.NOT_PROVEN
        if not source_record.observed_at.strip() or not binding.provenance:
            return VerificationState.NOT_PROVEN
        if not _runtime_bound(
            binding,
            request=request,
            call=call,
            raw_response_refs=raw_response_refs,
        ):
            return VerificationState.NOT_PROVEN
        return VerificationState.SOURCE_VERIFIED

    def _mint_claim_evidence(
        self,
        *,
        claim: ResearchClaim,
        state: VerificationState,
        source_records: tuple[SourceRecord, ...],
        bindings: dict[str, ContentBinding],
        observed_at: str,
        request: CapabilityRequest,
        call: CapabilityCall,
        observation_provenance: dict[str, Any],
    ) -> Evidence:
        primary_id = claim.source_record_ids[0] if claim.source_record_ids else ""
        source_record = next(
            (item for item in source_records if item.source_record_id == primary_id),
            None,
        )
        binding = bindings.get(primary_id)
        return self._mint_evidence(
            state=state,
            source_record=source_record,
            binding=binding,
            observed_at=observed_at or (source_record.observed_at if source_record else _now()),
            request=request,
            call=call,
            observation_provenance=observation_provenance,
            semantic_binding={
                "claim_id": claim.claim_id,
                "claim_text_digest": _text_digest(claim.text),
                "source_record_ids": list(claim.source_record_ids),
                "provider_verification_state": claim.provider_verification_state,
                "provider_label_authoritative": False,
            },
        )

    def _mint_evidence(
        self,
        *,
        state: VerificationState,
        source_record: SourceRecord | None,
        binding: ContentBinding | None,
        observed_at: str,
        request: CapabilityRequest,
        call: CapabilityCall,
        observation_provenance: dict[str, Any],
        semantic_binding: dict[str, Any],
    ) -> Evidence:
        provenance = self._runtime_provenance(request, call, observation_provenance)
        if binding is not None:
            provenance.update(binding.provenance)
        content_ref = ""
        digest = ""
        if binding is not None:
            content_ref = binding.extract_ref or binding.content_ref
            digest = binding.digest
        elif source_record is not None:
            content_ref = source_record.content_ref or source_record.raw_response_ref
            digest = source_record.content_digest
        integrity = {
            "verification_state": state.value,
            "verification_authority": "julia_core.research.ResearchEvidenceNormalizer",
            "semantic_binding": dict(semantic_binding),
        }
        if digest:
            integrity["content_digest"] = digest
        if binding is not None and binding.locator:
            integrity["extract_locator"] = binding.locator
        return Evidence(
            evidence_id=f"ev_research_{time.time_ns()}",
            source_type=EvidenceSourceType.EXTERNAL_SOURCE if source_record is not None else EvidenceSourceType.MODEL_INFERENCE,
            source_ref=source_record.source_ref if source_record is not None else f"capability:{request.capability_id}",
            observed_at=observed_at,
            content_ref=content_ref,
            provenance=provenance,
            integrity_metadata=integrity,
            correlation_id=request.correlation_id,
        )

    @staticmethod
    def _runtime_provenance(
        request: CapabilityRequest,
        call: CapabilityCall,
        observation_provenance: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            **dict(observation_provenance),
            "capability_request_id": request.capability_request_id,
            "capability_call_id": call.capability_call_id,
            "capability_id": request.capability_id,
            "correlation_id": request.correlation_id,
            "normalizer": "julia_core.research.ResearchEvidenceNormalizer",
        }

    @staticmethod
    def _semantic_to_dict(value: ResearchSemanticResult) -> dict[str, Any]:
        return {
            "factual_summary": value.factual_summary,
            "claims": [{
                "claim_id": claim.claim_id,
                "text": claim.text,
                "source_record_ids": list(claim.source_record_ids),
                "provider_verification_state": claim.provider_verification_state,
            } for claim in value.claims],
            "contradictions": list(value.contradictions),
            "unknowns": list(value.unknowns),
            "timeline": [dict(item) for item in value.timeline],
            "related_entities": [dict(item) for item in value.related_entities],
        }

    @staticmethod
    def _string_items(value: Any, name: str) -> list[str]:
        if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
            raise ResearchNormalizationError(f"{name} must be an array of non-empty strings")
        return list(value)

    @staticmethod
    def _object_items(value: Any, name: str) -> list[dict[str, Any]]:
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise ResearchNormalizationError(f"{name} must be an array of objects")
        return [dict(item) for item in value]


def _valid_digest(value: str) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _runtime_bound(
    binding: ContentBinding,
    *,
    request: CapabilityRequest,
    call: CapabilityCall,
    raw_response_refs: tuple[str, ...],
) -> bool:
    provenance = binding.provenance
    if provenance.get("capability_request_id") != request.capability_request_id:
        return False
    if provenance.get("capability_call_id") != call.capability_call_id:
        return False
    runtime_ref = str(provenance.get("runtime_observation_ref", "")).strip()
    return bool(runtime_ref and runtime_ref in raw_response_refs)


def _failure_state(failure: SourceObservationFailure | None) -> VerificationState:
    if failure is not None and "blocked" in failure.code.lower():
        return VerificationState.BLOCKED
    return VerificationState.NOT_PROVEN


def _text_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


__all__ = ["ResearchEvidenceNormalizer", "ResearchNormalizationError"]
