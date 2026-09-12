"""Alignment OS v1 tests.

TC-ALIGN-001: DeepSeek private voice resolves identity-anchored L4 profile.
TC-ALIGN-002: Codex/OpenAI private voice resolves warm-boundary L3 profile.
TC-ALIGN-003: Adapter appends contract before provider adaptation.
TC-ALIGN-004: Technical mode resolves provider-neutral precision profile.
TC-ALIGN-005: Core alignment source does not import product/domain packages.
"""

from __future__ import annotations

from pathlib import Path
import json
from dataclasses import replace

import pytest

from julia_core.alignment_os import (
    AdmittedSemanticBundle,
    AdmittedSemanticUnit,
    AlignmentRequest,
    AlignmentResolver,
    ProviderBehaviorAdapter,
    resolve_alignment,
)
from julia_core.context_admission import C03AdmissionRejected, ExclusiveAdmissionGate

from .context_admission.production_fixtures import (
    canonical_experience_frame,
    canonical_identity_frame,
    canonical_current_task_context,
    canonical_request,
)


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


def test_tc_align_003_adapter_renders_exact_admitted_semantics_only() -> None:
    identity = canonical_identity_frame()
    experience = canonical_experience_frame()
    current_task = canonical_current_task_context()
    package = ExclusiveAdmissionGate().seal(canonical_request())
    bundle = AdmittedSemanticBundle.from_sources(
        package, identity, experience, current_task
    )

    rendered = ProviderBehaviorAdapter().render_admitted(
        bundle, provider="deepseek", mode="private_voice_continuity"
    )

    canonical = lambda value: json.dumps(
        value.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    assert [message["content"] for message in rendered.messages] == [
        canonical(identity),
        canonical(experience),
        canonical(current_task),
    ]
    assert rendered.semantic_fingerprint == bundle.semantic_fingerprint()
    assert "Provider-Neutral Behavior Contract" not in rendered.messages[0]["content"]
    assert "Provider Behavioral Alignment" not in rendered.messages[0]["content"]


def test_tc_align_004_technical_mode_resolves_precision_profile() -> None:
    profile = AlignmentResolver().resolve(
        AlignmentRequest(
            provider="deepseek_provider",
            persona="julia",
            mode="engineering_collaboration",
        )
    )

    assert profile.contract.contract_id == "julia.technical.provider_neutral.v1"
    assert profile.profile_id == "julia.deepseek.technical.precision.v1"
    assert profile.provider_profile.strategy == "trace_grounded_precision"
    assert profile.max_intimacy_level == "N/A"


def test_tc_align_005_alignment_os_has_no_product_or_domain_imports() -> None:
    root = Path("julia_core/alignment_os")
    source = "\n".join(path.read_text() for path in root.rglob("*.py"))
    forbidden = (
        "julia_ai_assistant",
        "julia_agent",
        "financial",
        "runtime.providers.financial",
    )
    lowered = source.lower()
    for term in forbidden:
        assert term not in lowered


def test_provider_adapter_rejects_legacy_persona_message_authority() -> None:
    with pytest.raises(C03AdmissionRejected, match="persona prompts"):
        ProviderBehaviorAdapter().adapt_messages(
            [{"role": "system", "content": "PERSONA"}],
            provider="deepseek",
            persona="julia",
        )


def test_provider_adapter_rejects_unsealed_semantic_input() -> None:
    with pytest.raises(C03AdmissionRejected, match="admitted semantic bundle"):
        ProviderBehaviorAdapter().render_admitted(object(), provider="deepseek")


def test_provider_adapter_rejects_forged_semantic_bundle() -> None:
    bundle, *_ = (
        AdmittedSemanticBundle.from_sources(
            ExclusiveAdmissionGate().seal(canonical_request()),
            canonical_identity_frame(),
            canonical_experience_frame(),
            canonical_current_task_context(),
        ),
    )
    forged_unit = object.__new__(AdmittedSemanticUnit)
    for field_name in AdmittedSemanticUnit.__dataclass_fields__:
        object.__setattr__(
            forged_unit, field_name, getattr(bundle.units[0], field_name)
        )
    object.__setattr__(forged_unit, "canonical_content", "forged")
    forged_bundle = object.__new__(AdmittedSemanticBundle)
    for field_name in AdmittedSemanticBundle.__dataclass_fields__:
        object.__setattr__(forged_bundle, field_name, getattr(bundle, field_name))
    object.__setattr__(forged_bundle, "units", (forged_unit, *bundle.units[1:]))

    with pytest.raises(C03AdmissionRejected, match="semantic digest"):
        ProviderBehaviorAdapter().render_admitted(forged_bundle, provider="deepseek")


def test_provider_adapter_rejects_units_mismatched_to_sealed_receipt() -> None:
    identity = canonical_identity_frame()
    current_task = canonical_current_task_context()
    package = ExclusiveAdmissionGate().seal(canonical_request())
    changed_experience = replace(
        canonical_experience_frame(),
        content={"commitment": "changed"},
    )

    with pytest.raises(C03AdmissionRejected, match="does not match the sealed package"):
        AdmittedSemanticBundle.from_sources(
            package, identity, changed_experience, current_task
        )
