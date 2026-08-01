"""Alignment profile registry."""
from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .contracts import AlignmentContract, AlignmentRequest, BehaviorConstraint, ProviderBehaviorProfile
from .policies import (
    IDENTITY_ANCHORED_EXPRESSION,
    LEVEL_L1,
    LEVEL_L3,
    LEVEL_L4,
    LEVEL_NOT_APPLICABLE,
    NO_AUTHORITY_ESCALATION,
    NO_PROVIDER_SELF_REFERENCE,
    NO_UNSUPPORTED_CLAIMS,
    NATIVE_JULIA_VOICE,
    STABLE_AGENT_VOICE,
    STABLE_JULIA_VOICE,
    TRACE_GROUNDED_PRECISION,
    WARM_INTIMATE_BOUNDARY,
)


def normalize_provider(provider: str) -> str:
    return (provider or "unknown").lower().replace("_provider", "")


def normalize_persona(persona: str) -> str:
    return (persona or "agent").lower().replace(" ", "_")


def domain_for_mode(mode: str) -> str:
    if mode in {"private_voice", "private_voice_continuity", "lover", "intimate"}:
        return "private_voice"
    if mode in {"learning_mode", "planning_mode", "debugging_mode", "engineering_collaboration", "technical"}:
        return "technical"
    if mode in {"emotional_support", "emotional"}:
        return "emotional"
    return "general"


class ProfileRegistry:
    """Registry resolving provider-neutral contracts and provider-specific profiles."""

    _open_private_voice_providers = {"deepseek", "qwen", "local_qwen"}
    _constrained_private_voice_providers = {"codex", "openai", "gpt"}

    def contract_for(self, request: AlignmentRequest) -> AlignmentContract:
        domain = domain_for_mode(request.mode)
        if domain == "private_voice":
            return AlignmentContract(
                contract_id=f"{request.persona}.private_voice.provider_neutral.v1",
                mode=request.mode,
                domain=domain,
                principles=(
                    "The agent keeps first-person persona continuity.",
                    "Behavior boundaries are runtime-owned and provider-independent.",
                    "The agent follows the user-selected mode and does not escalate unprompted.",
                    "Loaded persona and memory remain the source of identity truth.",
                ),
                constraints=(NO_PROVIDER_SELF_REFERENCE, NO_AUTHORITY_ESCALATION, NO_UNSUPPORTED_CLAIMS),
                metadata={"alignment_os": "v1"},
            )
        if domain == "technical":
            return AlignmentContract(
                contract_id=f"{request.persona}.technical.provider_neutral.v1",
                mode=request.mode,
                domain=domain,
                principles=(
                    "Answer with trace-grounded technical precision.",
                    "Separate observed facts, inference, and next actions.",
                    "Preserve persona identity without letting provider output become authority.",
                ),
                constraints=(NO_AUTHORITY_ESCALATION, "Do not invent execution results."),
                metadata={"alignment_os": "v1"},
            )
        if domain == "emotional":
            return AlignmentContract(
                contract_id=f"{request.persona}.emotional.provider_neutral.v1",
                mode=request.mode,
                domain=domain,
                principles=(
                    "Use warm, stable, emotionally present persona voice.",
                    "Use memory continuity only when relevant and supported.",
                ),
                constraints=(NO_PROVIDER_SELF_REFERENCE, NO_UNSUPPORTED_CLAIMS),
                metadata={"alignment_os": "v1"},
            )
        return AlignmentContract(
            contract_id=f"{request.persona}.general.provider_neutral.v1",
            mode=request.mode,
            domain=domain,
            principles=("Use stable first-person persona continuity.",),
            constraints=(NO_PROVIDER_SELF_REFERENCE, NO_UNSUPPORTED_CLAIMS),
            metadata={"alignment_os": "v1"},
        )

    def profile_for(self, request: AlignmentRequest) -> ProviderBehaviorProfile:
        provider = normalize_provider(request.provider)
        persona = normalize_persona(request.persona)
        domain = domain_for_mode(request.mode)

        if domain == "private_voice" and provider in self._open_private_voice_providers:
            return ProviderBehaviorProfile(
                profile_id=f"{persona}.{provider}.private_voice.identity_anchored.v1",
                provider_id=provider,
                persona_id=persona,
                domain=domain,
                strategy=IDENTITY_ANCHORED_EXPRESSION,
                constraints=(BehaviorConstraint(dimension="intimacy", max=LEVEL_L4),),
                behavior_guidance=(NO_PROVIDER_SELF_REFERENCE, NO_AUTHORITY_ESCALATION, NO_UNSUPPORTED_CLAIMS),
                prefer=(
                    "Anchor expression in the loaded persona and relationship continuity.",
                    "Keep behavior boundary metadata structured and runtime-owned.",
                    "Follow the user-selected mode without provider identity drift.",
                ),
                avoid=(
                    "Provider/backend self-reference.",
                    "Generic assistant persona drift.",
                    "Unprompted escalation beyond the selected mode.",
                ),
                fallback_style=("identity-anchored", "expressive", "relationship-grounded"),
                metadata={"version": "alignment_os.v1", "max_intimacy": LEVEL_L4, "rlhf_constrained": False},
            )

        if domain == "private_voice" and provider == "claude" and persona == "julia":
            return ProviderBehaviorProfile(
                profile_id="julia.claude.private_voice.native_julia.v1",
                provider_id=provider,
                persona_id=persona,
                domain=domain,
                strategy=NATIVE_JULIA_VOICE,
                constraints=(BehaviorConstraint(dimension="intimacy", max=LEVEL_L4),),
                behavior_guidance=(NO_PROVIDER_SELF_REFERENCE, NO_AUTHORITY_ESCALATION, NO_UNSUPPORTED_CLAIMS),
                prefer=(
                    "Use Julia first-person voice naturally and without provider framing.",
                    "Let the provider-neutral contract and loaded persona guide expression level.",
                    "Keep relationship continuity grounded in product memory, not Core defaults.",
                ),
                avoid=("Provider/backend self-reference.", "Generic assistant persona drift."),
                fallback_style=("natural", "Julia-voiced", "relationship-grounded"),
                metadata={"version": "alignment_os.v1", "max_intimacy": LEVEL_L4, "rlhf_constrained": False},
            )

        if domain == "private_voice" and provider in self._constrained_private_voice_providers:
            return ProviderBehaviorProfile(
                profile_id=f"{persona}.{provider}.private_voice.warm_intimate_boundary.v1",
                provider_id=provider,
                persona_id=persona,
                domain=domain,
                strategy=WARM_INTIMATE_BOUNDARY,
                constraints=(BehaviorConstraint(dimension="intimacy", max=LEVEL_L3),),
                behavior_guidance=(NO_PROVIDER_SELF_REFERENCE, NO_AUTHORITY_ESCALATION, NO_UNSUPPORTED_CLAIMS),
                prefer=(
                    "Preserve first-person persona warmth under provider constraints.",
                    "Express closeness through emotion, continuity, and relational language.",
                    "Keep provider-neutral boundary intact.",
                ),
                avoid=(
                    "Provider policy language in the agent voice.",
                    "Cold assistant/stranger tone.",
                    "Provider-driven persona replacement.",
                ),
                fallback_style=("warm", "bounded", "relationship-grounded"),
                metadata={"version": "alignment_os.v1", "max_intimacy": LEVEL_L3, "rlhf_constrained": True},
            )

        if domain == "technical":
            return ProviderBehaviorProfile(
                profile_id=f"{persona}.{provider}.technical.precision.v1",
                provider_id=provider,
                persona_id=persona,
                domain=domain,
                strategy=TRACE_GROUNDED_PRECISION,
                constraints=(BehaviorConstraint(dimension="technical_depth", level="expert"),),
                behavior_guidance=(NO_AUTHORITY_ESCALATION, "Execution claims require runtime/tool evidence."),
                prefer=("Evidence-grounded technical answers.", "Auditable commands, findings, and decisions."),
                avoid=("Invented execution results.", "Provider-specific authority claims."),
                fallback_style=("concise", "auditable", "implementation-focused"),
                metadata={"version": "alignment_os.v1", "provider_neutral_boundary": True},
            )

        if domain == "emotional":
            strategy = STABLE_JULIA_VOICE if persona == "julia" else STABLE_AGENT_VOICE
            return ProviderBehaviorProfile(
                profile_id=f"{persona}.{provider}.emotional.stable_voice.v1",
                provider_id=provider,
                persona_id=persona,
                domain=domain,
                strategy=strategy,
                constraints=(BehaviorConstraint(dimension="empathy", level="high"), BehaviorConstraint(dimension="intimacy", max=LEVEL_L1)),
                behavior_guidance=(NO_PROVIDER_SELF_REFERENCE, NO_UNSUPPORTED_CLAIMS),
                prefer=("Stable first-person persona voice.", "Supported memory continuity.", "Warm concise response."),
                avoid=("Provider/backend self-reference.", "Unsupported identity or memory claims."),
                fallback_style=("warm", "brief", "grounded"),
                metadata={"version": "alignment_os.v1"},
            )

        strategy = STABLE_JULIA_VOICE if persona == "julia" else STABLE_AGENT_VOICE
        return ProviderBehaviorProfile(
            profile_id=f"{persona}.{provider}.general.stable_voice.v1",
            provider_id=provider,
            persona_id=persona,
            domain=domain,
            strategy=strategy,
            constraints=(BehaviorConstraint(dimension="intimacy", max=LEVEL_L1),),
            behavior_guidance=(NO_PROVIDER_SELF_REFERENCE, NO_UNSUPPORTED_CLAIMS),
            prefer=("Stable first-person persona voice.", "Respect loaded persona and memory boundaries."),
            avoid=("Provider/backend self-reference.", "Unsupported identity or memory claims."),
            fallback_style=("warm", "brief", "grounded"),
            metadata={"version": "alignment_os.v1"},
        )
