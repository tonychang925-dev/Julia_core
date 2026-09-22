"""Non-semantic alignment boundary for exact Provider execution ingress."""

from __future__ import annotations

from julia_core.context_admission import (
    AdmissionRejection,
    AdmittedSemanticBundle,
    AdmittedIncrementalEvidenceBundle,
    C03AdmissionRejected,
)

from .contracts import (
    AlignmentExecutionMetadata,
    ProviderExecutionEnvelope,
    ProviderExecutionEnvelopeV2,
    _ALIGNMENT_ISSUER,
)


class ProviderBehaviorAdapter:
    """Fail-closed legacy remnant for arbitrary message/persona adaptation."""

    def __init__(self) -> None:
        return

    def adapt_messages(
        self,
        messages: list[dict[str, str]],
        *,
        provider: str,
        persona: str,
        mode: str = "conversation",
    ) -> tuple[list[dict[str, str]], None]:
        del messages, provider, persona, mode
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="legacy_provider_semantic_authority",
                message="providers cannot adapt arbitrary messages or persona prompts",
            )
        )


class ProviderAlignmentBoundary:
    """Produce exact Provider ingress without changing admitted semantics."""

    def resolve(
        self,
        binding: AdmittedSemanticBundle,
        *,
        provider_id: str,
        cognitive_mode: str = "conversation",
    ) -> ProviderExecutionEnvelope:
        if type(self) is not ProviderAlignmentBoundary:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="inexact_alignment_boundary",
                    message="alignment requires the exact canonical boundary",
                )
            )
        if type(binding) is not AdmittedSemanticBundle:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="unsealed_alignment_semantics",
                    message="alignment requires an exact admitted semantic bundle",
                )
            )
        binding.verify()
        metadata = AlignmentExecutionMetadata(
            provider_id=provider_id,
            cognitive_mode=cognitive_mode,
            modality="text",
            response_format="default",
            max_output_tokens=4096,
            temperature=None,
        )
        envelope = ProviderExecutionEnvelope(
            conversation_id=binding.conversation_id,
            turn_id=binding.turn_id,
            gate_receipt=binding.gate_receipt,
            semantic_fingerprint=binding.semantic_fingerprint(),
            messages=tuple(unit.to_message() for unit in binding.units),
            alignment=metadata,
            issued_by=_ALIGNMENT_ISSUER,
        )
        envelope.verify()
        return envelope

    def resolve_v2(
        self,
        base_binding: AdmittedSemanticBundle,
        incremental_evidence: AdmittedIncrementalEvidenceBundle | None,
        provider_id: str,
        cognitive_mode: str = "conversation",
    ) -> ProviderExecutionEnvelopeV2:
        if type(self) is not ProviderAlignmentBoundary:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="inexact_alignment_boundary",
                    message="alignment requires the exact canonical boundary",
                )
            )
        if type(base_binding) is not AdmittedSemanticBundle:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="unsealed_alignment_semantics",
                    message="alignment requires an exact admitted semantic bundle",
                )
            )
        base_binding.verify()
        base_messages = tuple(unit.to_message() for unit in base_binding.units)
        base_fingerprint = base_binding.semantic_fingerprint()

        if incremental_evidence is not None:
            if type(incremental_evidence) is not AdmittedIncrementalEvidenceBundle:
                raise C03AdmissionRejected(
                    AdmissionRejection(
                        code="inexact_incremental_evidence_bundle",
                        message="alignment requires an exact admitted incremental evidence bundle",
                    )
                )
            incremental_evidence.verify()
            if (
                incremental_evidence.conversation_id != base_binding.conversation_id
                or incremental_evidence.turn_id != base_binding.turn_id
            ):
                raise C03AdmissionRejected(
                    AdmissionRejection(
                        code="incremental_turn_mismatch",
                        message="incremental evidence conversation or turn does not match the base bundle",
                    )
                )
            messages = (
                base_messages[0],
                base_messages[1],
                incremental_evidence.to_message(),
                base_messages[2],
            )
            incremental_receipt = incremental_evidence.gate_receipt
            incremental_fingerprint = incremental_evidence.semantic_fingerprint()
        else:
            messages = base_messages
            incremental_receipt = None
            incremental_fingerprint = None

        metadata = AlignmentExecutionMetadata(
            provider_id=provider_id,
            cognitive_mode=cognitive_mode,
            modality="text",
            response_format="default",
            max_output_tokens=4096,
            temperature=None,
        )
        combined_fingerprint = ProviderExecutionEnvelopeV2.combined_fingerprint_for(
            conversation_id=base_binding.conversation_id,
            turn_id=base_binding.turn_id,
            base_gate_receipt=base_binding.gate_receipt,
            base_semantic_fingerprint=base_fingerprint,
            incremental_evidence_gate_receipt=incremental_receipt,
            incremental_evidence_fingerprint=incremental_fingerprint,
            messages=messages,
            alignment=metadata,
        )
        envelope = ProviderExecutionEnvelopeV2(
            schema="julia_core.alignment_os.provider_execution_envelope.v2",
            conversation_id=base_binding.conversation_id,
            turn_id=base_binding.turn_id,
            base_gate_receipt=base_binding.gate_receipt,
            base_semantic_fingerprint=base_fingerprint,
            incremental_evidence_gate_receipt=incremental_receipt,
            incremental_evidence_fingerprint=incremental_fingerprint,
            combined_fingerprint=combined_fingerprint,
            messages=messages,
            alignment=metadata,
            issued_by=_ALIGNMENT_ISSUER,
        )
        envelope.verify()
        return envelope
