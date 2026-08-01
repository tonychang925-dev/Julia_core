"""Alignment resolver."""
from __future__ import annotations

from .contracts import AlignmentProfile, AlignmentRequest
from .registry import ProfileRegistry


class AlignmentResolver:
    """Resolve runtime alignment contract + provider behavior profile."""

    def __init__(self, registry: ProfileRegistry | None = None) -> None:
        self.registry = registry or ProfileRegistry()

    def resolve(self, request: AlignmentRequest) -> AlignmentProfile:
        contract = self.registry.contract_for(request)
        provider_profile = self.registry.profile_for(request)
        return AlignmentProfile(
            provider_id=provider_profile.provider_id,
            persona_id=provider_profile.persona_id,
            mode=request.mode,
            contract=contract,
            provider_profile=provider_profile,
        )


def resolve_alignment(provider: str, persona: str, mode: str = "conversation") -> AlignmentProfile:
    return AlignmentResolver().resolve(AlignmentRequest(provider=provider, persona=persona, mode=mode))
