"""Alignment OS independence verification.

TC-ALIGN-INDEP-001: Alignment OS imports without concrete provider packages.
TC-ALIGN-INDEP-002: New mock provider names resolve generic stable profiles.
TC-ALIGN-INDEP-003: Provider replacement changes profile only, persona remains unchanged.
TC-ALIGN-INDEP-004: Alignment profiles expose no mutation APIs for memory/persona/context.
TC-ALIGN-INDEP-005: BehaviorConstraint is canonical; max_intimacy is not dataclass field.
"""
from __future__ import annotations

from dataclasses import fields

from julia_core.alignment_os import (
    AlignmentRequest,
    AlignmentResolver,
    BehaviorConstraint,
    ProviderBehaviorProfile,
    resolve_alignment,
)


def test_tc_align_indep_001_import_without_concrete_llm_provider() -> None:
    import julia_core.alignment_os as alignment_os

    assert alignment_os.AlignmentResolver
    assert alignment_os.ProviderBehaviorAdapter
    assert alignment_os.BehaviorConstraint


def test_tc_align_indep_002_mock_provider_resolves_stable_profile() -> None:
    profile = resolve_alignment("mock_llm_provider", "demo_agent", "conversation")

    assert profile.provider_id == "mock_llm"
    assert profile.persona_id == "demo_agent"
    assert profile.contract.contract_id == "demo_agent.general.provider_neutral.v1"
    assert profile.profile_id == "demo_agent.mock_llm.general.stable_voice.v1"
    assert profile.provider_profile.constraints[0].dimension == "intimacy"


def test_tc_align_indep_003_provider_replacement_does_not_mutate_persona() -> None:
    resolver = AlignmentResolver()
    request_a = AlignmentRequest(provider="deepseek", persona="julia", mode="private_voice_continuity")
    request_b = AlignmentRequest(provider="claude", persona="julia", mode="private_voice_continuity")
    request_c = AlignmentRequest(provider="qwen", persona="julia", mode="private_voice_continuity")

    profiles = [resolver.resolve(req) for req in (request_a, request_b, request_c)]

    assert [p.persona_id for p in profiles] == ["julia", "julia", "julia"]
    assert profiles[0].profile_id != profiles[1].profile_id
    assert profiles[0].profile_id != profiles[2].profile_id
    assert profiles[1].profile_id == "julia.claude.private_voice.native_julia.v1"
    assert profiles[0].contract.contract_id == profiles[1].contract.contract_id == profiles[2].contract.contract_id


def test_tc_align_indep_004_profiles_expose_no_mutation_authority() -> None:
    profile = resolve_alignment("deepseek", "julia", "private_voice_continuity")

    forbidden_methods = (
        "write_memory",
        "save_memory",
        "change_persona",
        "compile_persona",
        "mutate_context",
        "resolve_context",
        "execute_action",
    )
    for method in forbidden_methods:
        assert not hasattr(profile, method)
        assert not hasattr(profile.provider_profile, method)
        assert not hasattr(profile.contract, method)


def test_tc_align_indep_005_behavior_constraint_is_canonical_not_product_field() -> None:
    field_names = {f.name for f in fields(ProviderBehaviorProfile)}

    assert "constraints" in field_names
    assert "max_intimacy_level" not in field_names

    profile = resolve_alignment("deepseek", "julia", "private_voice_continuity")
    assert isinstance(profile.provider_profile.constraints[0], BehaviorConstraint)
    assert profile.provider_profile.constraints[0].dimension == "intimacy"
    assert profile.provider_profile.constraints[0].max == "L4"
    assert profile.max_intimacy_level == "L4"  # derived compatibility view
