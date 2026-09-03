"""Trusted machine-review parser for governed external review execution.

The parser consumes a Core-owned raw observation from an exact trusted
``submit_review`` invocation. Provider output can describe review semantics and
reference allowed evidence; it can never mint candidate identity, raw-response
provenance, transport truth, authorization, validation state, or source trust.
"""

from __future__ import annotations

import json
import time
from typing import Any

from julia_core.review.candidate_artifact import (
    _registered_invocation,
    _seal_candidate_with_trusted_authorities,
    is_trusted_raw_observation,
    observe_raw_response,
)
from julia_core.review.contracts import (
    ReviewDecisionCandidate,
    ReviewEvidenceBinding,
    ReviewFindingCandidate,
    ReviewTransportTrace,
    ReviewVerdict,
    validate_identity_isolation,
)
from julia_core.review.invocation import is_trusted_invocation
from julia_core.review.source_binding import (
    CandidateCreatorBinding,
    _binding_fingerprint,
    _CREATOR_BINDINGS,
)
from julia_core.review.validation import (
    assert_review_correlation,
    transport_completed,
    validate_structured_finding_bindings,
)


class ReviewMachineResponseParseError(ValueError):
    """Raised when provider machine output cannot become a trusted candidate."""


_TOP_LEVEL_FIELDS = frozenset(
    {
        "review_id",
        "candidate_id",
        "candidate_sha",
        "bundle_digest",
        "verdict",
        "findings",
        "notes",
    }
)
_FINDING_FIELDS = frozenset(
    {
        "severity",
        "observation",
        "inference",
        "causal_impact",
        "evidence_bindings",
        "confidence",
        "required_change",
        "provider_finding_label",
    }
)
_EVIDENCE_FIELDS = frozenset({"kind", "ref"})


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_machine_json(raw_response: str) -> dict[str, Any]:
    if not raw_response.strip():
        raise ReviewMachineResponseParseError("machine review response is empty")
    try:
        payload = json.loads(
            raw_response,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise ReviewMachineResponseParseError(
            f"machine review response is not strict JSON: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ReviewMachineResponseParseError("machine review response must be a JSON object")
    return payload


def _require_string(payload: dict[str, Any], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ReviewMachineResponseParseError(f"missing or invalid field: {name}")
    return value


def _parse_findings(value: Any) -> tuple[ReviewFindingCandidate, ...]:
    if not isinstance(value, list):
        raise ReviewMachineResponseParseError("findings must be an array")
    findings: list[ReviewFindingCandidate] = []
    for item in value:
        if not isinstance(item, dict):
            raise ReviewMachineResponseParseError("each finding must be an object")
        unknown = set(item) - _FINDING_FIELDS
        if unknown:
            raise ReviewMachineResponseParseError(
                f"unknown finding fields: {', '.join(sorted(unknown))}"
            )
        if "finding_id" in item:
            raise ReviewMachineResponseParseError(
                "provider finding_id is forbidden; canonical finding identity is Core-owned"
            )
        try:
            severity = _require_string(item, "severity")
            observation = _require_string(item, "observation")
            bindings_value = item.get("evidence_bindings", [])
            if not isinstance(bindings_value, list):
                raise ReviewMachineResponseParseError(
                    "evidence_bindings must be an array"
                )
            evidence_bindings: list[ReviewEvidenceBinding] = []
            for binding_value in bindings_value:
                if not isinstance(binding_value, dict):
                    raise ReviewMachineResponseParseError(
                        "each evidence binding must be an object"
                    )
                unknown_binding = set(binding_value) - _EVIDENCE_FIELDS
                if unknown_binding:
                    raise ReviewMachineResponseParseError(
                        f"unknown evidence fields: {', '.join(sorted(unknown_binding))}"
                    )
                evidence_bindings.append(
                    ReviewEvidenceBinding(
                        kind=_require_string(binding_value, "kind"),
                        ref=_require_string(binding_value, "ref"),
                    )
                )
            findings.append(
                ReviewFindingCandidate(
                    severity=severity,
                    observation=observation,
                    inference=str(item.get("inference", "")),
                    causal_impact=str(item.get("causal_impact", "")),
                    evidence_bindings=tuple(evidence_bindings),
                    confidence=item.get("confidence"),
                    required_change=str(item.get("required_change", "")),
                    provider_finding_label=str(item.get("provider_finding_label", "")),
                )
            )
        except ReviewMachineResponseParseError:
            raise
        except (TypeError, ValueError) as exc:
            raise ReviewMachineResponseParseError(str(exc)) from exc
    return tuple(findings)


def _transport_trace(invocation: Any) -> ReviewTransportTrace:
    execution = invocation.execution
    call = execution.capability_call
    tool_result = execution.tool_result
    error = tool_result.error if tool_result is not None else None
    return ReviewTransportTrace(
        source="core.capability_manager",
        status="CAPTURED" if invocation.outcome_status == "success" else "PARTIAL",
        sent_at=call.started_at if call is not None else "",
        response_started_at=tool_result.started_at if tool_result is not None else "",
        response_completed_at=tool_result.completed_at or tool_result.started_at
        if tool_result is not None
        else "",
        error_code=str(error.get("code", "")) if error else "",
        details={
            "capability_call_id": call.capability_call_id if call is not None else "",
            "capability_request_id": call.capability_request_id
            if call is not None
            else "",
            "provider": call.provider if call is not None else "",
            "correlation_id": call.correlation_id if call is not None else "",
            "tool_result_status": invocation.outcome_status,
            "side_effect_state": invocation.side_effect_state,
            "invocation_id": invocation.invocation_id,
        },
    )


class CoreReviewParser:
    """Exact Core-owned creator bound to the trusted raw observation path."""

    def create_candidate(self, *, raw_observation: Any):
        """Parse and seal a candidate from one exact trusted raw observation."""
        if not is_trusted_raw_observation(raw_observation):
            raise ReviewMachineResponseParseError("raw response observation is not trusted")

        invocation = _registered_invocation(raw_observation)
        if not is_trusted_invocation(invocation):
            raise ReviewMachineResponseParseError("raw observation invocation is not trusted")
        if invocation.invocation_id != raw_observation.invocation_id:
            raise ReviewMachineResponseParseError("raw observation invocation mismatch")
        if not transport_completed(invocation.outcome_status):
            raise ReviewMachineResponseParseError(
                f"review transport did not complete: {invocation.outcome_status}"
            )

        snapshot = invocation.transaction.snapshot
        payload = _parse_machine_json(raw_observation.raw_response)
        unknown_top_level = set(payload) - _TOP_LEVEL_FIELDS
        if unknown_top_level:
            raise ReviewMachineResponseParseError(
                f"unknown machine review fields: {', '.join(sorted(unknown_top_level))}"
            )
        try:
            validate_identity_isolation(payload)
        except Exception as exc:
            raise ReviewMachineResponseParseError(f"identity isolation failure: {exc}") from exc

        supplied_identity = (
            _require_string(payload, "review_id"),
            _require_string(payload, "candidate_id"),
            _require_string(payload, "candidate_sha"),
            _require_string(payload, "bundle_digest"),
        )
        trusted_identity = (
            snapshot.review_id,
            snapshot.candidate_id,
            snapshot.candidate_sha,
            snapshot.digest,
        )
        if supplied_identity != trusted_identity:
            raise ReviewMachineResponseParseError(
                "review identity/bundle binding does not match trusted snapshot"
            )

        verdict = _require_string(payload, "verdict")
        try:
            ReviewVerdict(verdict)
        except ValueError as exc:
            raise ReviewMachineResponseParseError(f"unknown verdict: {verdict}") from exc

        notes_value = payload.get("notes", [])
        if not isinstance(notes_value, list) or not all(
            isinstance(note, str) and note.strip() for note in notes_value
        ):
            raise ReviewMachineResponseParseError("notes must be an array of non-empty strings")

        candidate = ReviewDecisionCandidate(
            review_id=snapshot.review_id,
            candidate_id=snapshot.candidate_id,
            candidate_sha=snapshot.candidate_sha,
            verdict=ReviewVerdict(verdict),
            findings=_parse_findings(payload.get("findings", [])),
            notes=tuple(notes_value),
            raw_response_ref=raw_observation.raw_response_ref,
            raw_response_digest=raw_observation.raw_response_digest,
            captured_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            transport_trace=_transport_trace(invocation),
            validation_state="CANDIDATE",
        )

        try:
            assert_review_correlation(
                snapshot,
                candidate,
                max_response_chars=int(
                    snapshot.to_payload().get("limits", {}).get("max_response_chars", 12000)
                ),
            )
            evidence_errors = validate_structured_finding_bindings(
                snapshot,
                candidate,
                raw_response_ref=raw_observation.raw_response_ref,
            )
        except ValueError as exc:
            raise ReviewMachineResponseParseError(str(exc)) from exc
        if evidence_errors:
            raise ReviewMachineResponseParseError("; ".join(evidence_errors))

        return _seal_candidate_with_trusted_authorities(
            candidate,
            creator_binding=_CORE_REVIEW_PARSER_BINDING,
            creator=_CORE_REVIEW_PARSER,
            raw_observation=raw_observation,
        )


_CORE_REVIEW_PARSER = CoreReviewParser()
_CORE_REVIEW_PARSER_BINDING = CandidateCreatorBinding(
    binding_id="core_review_machine_parser_v1",
    provenance={
        "owner": "julia_core.review.parser",
        "contract": "review_decision_candidate.v1",
        "raw_response_authority": "core_trusted_invocation_observation",
    },
)
_CREATOR_BINDINGS[_CORE_REVIEW_PARSER_BINDING.binding_id] = (
    _CORE_REVIEW_PARSER_BINDING,
    _CORE_REVIEW_PARSER,
    _binding_fingerprint(_CORE_REVIEW_PARSER_BINDING),
)


def get_core_review_parser_binding() -> CandidateCreatorBinding:
    """Return the narrow trusted binding for the Core-owned parser."""
    return _CORE_REVIEW_PARSER_BINDING


def parse_review_response(invocation: Any):
    """Observe and parse one exact governed review invocation."""
    if not is_trusted_invocation(invocation):
        raise ReviewMachineResponseParseError("invocation is not trusted")
    raw_observation = observe_raw_response(invocation)
    return _CORE_REVIEW_PARSER.create_candidate(raw_observation=raw_observation)


__all__ = [
    "CoreReviewParser",
    "ReviewMachineResponseParseError",
    "get_core_review_parser_binding",
    "parse_review_response",
]
