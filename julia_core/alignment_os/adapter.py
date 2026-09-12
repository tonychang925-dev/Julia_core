"""Provider behavior adapter for message-based LLM providers."""

from __future__ import annotations

from dataclasses import dataclass

from julia_core.context_admission import AdmissionRejection, C03AdmissionRejected

from .contracts import AdmittedSemanticBundle, AlignmentProfile, AlignmentRequest
from .resolver import AlignmentResolver


@dataclass(frozen=True, slots=True)
class ProviderExecutionEnvelope:
    """Execution-only view of verified C03 semantics."""

    messages: tuple[dict[str, str], ...]
    profile: AlignmentProfile
    semantic_fingerprint: str


class ProviderBehaviorAdapter:
    """Render exact admitted semantics without adding provider authority."""

    def __init__(self, resolver: AlignmentResolver | None = None) -> None:
        self.resolver = resolver or AlignmentResolver()

    def adapt_messages(
        self,
        messages: list[dict[str, str]],
        *,
        provider: str,
        persona: str,
        mode: str = "conversation",
    ) -> tuple[list[dict[str, str]], AlignmentProfile]:
        raise C03AdmissionRejected(
            AdmissionRejection(
                code="legacy_provider_semantic_authority",
                message="providers cannot adapt arbitrary messages or persona prompts",
            )
        )

    def render_admitted(
        self,
        bundle: AdmittedSemanticBundle,
        *,
        provider: str,
        mode: str = "conversation",
    ) -> ProviderExecutionEnvelope:
        if type(bundle) is not AdmittedSemanticBundle:
            raise C03AdmissionRejected(
                AdmissionRejection(
                    code="unsealed_provider_semantics",
                    message="provider rendering requires an admitted semantic bundle",
                )
            )
        bundle.verify()
        profile = self.resolver.resolve(
            AlignmentRequest(
                provider=provider,
                persona="admitted_context",
                mode=mode,
            )
        )
        return ProviderExecutionEnvelope(
            messages=tuple(unit.to_message() for unit in bundle.units),
            profile=profile,
            semantic_fingerprint=bundle.semantic_fingerprint(),
        )
