from hashlib import sha256

from julia_core.context_admission import (
    ExactPersonaSelfBoundSemanticBinder,
    ExclusiveAdmissionGate,
    PersonaSelfBindingSemanticBindingRequest,
)
from julia_core.context_admission.contracts import canonical_json
from tests.context_admission.production_fixtures import (
    canonical_persona_self_binding,
    canonical_request,
)


def test_dual_digest_projection_is_independent_and_five_messages():
    request = canonical_request()
    package = ExclusiveAdmissionGate().seal(request)
    persona_binding, projection = canonical_persona_self_binding(
        identity=request.identity_frames,
        experiences=request.experience_frames,
    )
    binding = ExactPersonaSelfBoundSemanticBinder().bind(
        PersonaSelfBindingSemanticBindingRequest(
            package=package,
            persona_self_binding=persona_binding,
            persona_self_binding_projection=projection,
            identity_frames=request.identity_frames,
            experience_frames=request.experience_frames,
            current_task_context=request.current_task_context,
        )
    )
    binding.verify()
    assert (
        dict(binding.source_digest_manifest)["identity_frame_set"]
        == dict(package.admitted_frames)["identity_frame_set"]
    )
    assert [unit.frame_name for unit in binding.units] == [
        "persona_self_binding",
        "identity_frame_set",
        "experience_frame_set",
        "relationship_continuity_interpretation",
        "current_task_context",
    ]
    assert [unit.role for unit in binding.units] == [
        "system",
        "system",
        "system",
        "system",
        "user",
    ]
    assert all(
        unit.source_digest != unit.projected_digest for unit in binding.units[:3]
    )
    assert "model_visibility" not in binding.units[1].projected_content
    assert "standing_authorization" not in binding.units[2].projected_content
    assert binding.units[0].projected_content == projection.canonical_serialization()
    assert binding.units[4].projected_content == canonical_json(
        request.current_task_context.to_dict()
    )
    assert (
        binding.units[0].projected_digest
        == sha256(binding.units[0].projected_content.encode()).hexdigest()
    )
