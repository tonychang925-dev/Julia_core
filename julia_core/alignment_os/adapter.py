"""Non-semantic alignment boundary for exact Provider execution ingress."""
from __future__ import annotations

from julia_core.context_admission import (
    AdmissionRejection,
    AdmittedSemanticBundle,
    C03AdmissionRejected,
)

from .contracts import ProviderExecutionEnvelope, _ALIGNMENT_ISSUER, AlignmentExecutionMetadata


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
