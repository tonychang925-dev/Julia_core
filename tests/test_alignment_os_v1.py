"""Alignment OS v1 tests.

TC-ALIGN-001: DeepSeek private voice resolves identity-anchored L4 profile.
TC-ALIGN-002: Codex/OpenAI private voice resolves warm-boundary L3 profile.
TC-ALIGN-003: Adapter appends contract before provider adaptation.
TC-ALIGN-004: Technical mode resolves provider-neutral precision profile.
TC-ALIGN-005: Core alignment source does not import product/domain packages.
"""
from __future__ import annotations

from pathlib import Path

from julia_core.alignment_os import AlignmentRequest, AlignmentResolver, ProviderBehaviorAdapter, resolve_alignment


def test_tc_align_001_deepseek_private_voice_resolves_l4_identity_anchored() -> None:
    profile = resolve_alignment("deepseek", "julia", "private_voice_continuity")

    assert profile.contract.contract_id == "julia.private_voice.provider_neutral.v1"
    assert profile.profile_id == "julia.deepseek.private_voice.identity_anchored.v1"
    assert profile.provider_profile.strategy == "identity_anchored_expression"
    assert profile.max_intimacy_level == "L4"
    assert profile.provider_profile.metadata["max_intimacy"] == "L4"


def test_tc_align_002_codex_private_voice_resolves_l3_warm_boundary() -> None:
    profile = resolve_alignment("codex", "julia", "private_voice_continuity")

    assert profile.contract.contract_id == "julia.private_voice.provider_neutral.v1"
    assert profile.profile_id == "julia.codex.private_voice.warm_intimate_boundary.v1"
    assert profile.provider_profile.strategy == "warm_intimate_boundary"
    assert profile.max_intimacy_level == "L3"


def test_tc_align_003_adapter_appends_contract_before_provider_profile() -> None:
    messages, profile = ProviderBehaviorAdapter().adapt_messages(
        [{"role": "system", "content": "PERSONA"}, {"role": "user", "content": "hi"}],
        provider="deepseek",
        persona="julia",
        mode="private_voice_continuity",
    )

    content = messages[0]["content"]
    assert profile.max_intimacy_level == "L4"
    assert content.index("Provider-Neutral Behavior Contract") < content.index("Provider Behavioral Alignment")
    assert "Provider-Neutral Behavior Contract: julia.private_voice.provider_neutral.v1" in content
    assert "Provider Behavioral Alignment: julia.deepseek.private_voice.identity_anchored.v1" in content
    assert "dimension=intimacy, max=L4" in content
    assert messages[1] == {"role": "user", "content": "hi"}


def test_tc_align_004_technical_mode_resolves_precision_profile() -> None:
    profile = AlignmentResolver().resolve(
        AlignmentRequest(provider="deepseek_provider", persona="julia", mode="engineering_collaboration")
    )

    assert profile.contract.contract_id == "julia.technical.provider_neutral.v1"
    assert profile.profile_id == "julia.deepseek.technical.precision.v1"
    assert profile.provider_profile.strategy == "trace_grounded_precision"
    assert profile.max_intimacy_level == "N/A"


def test_tc_align_005_alignment_os_has_no_product_or_domain_imports() -> None:
    root = Path("julia_core/alignment_os")
    source = "\n".join(path.read_text() for path in root.rglob("*.py"))
    forbidden = ("julia_ai_assistant", "julia_agent", "financial", "runtime.providers.financial")
    lowered = source.lower()
    for term in forbidden:
        assert term not in lowered
