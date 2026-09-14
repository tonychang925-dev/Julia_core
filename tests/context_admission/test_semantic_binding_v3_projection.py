from hashlib import sha256

from julia_core.context_admission import (
    ExactAdmittedSemanticBinder, ExclusiveAdmissionGate, SemanticBindingRequest,
)
from julia_core.context_admission.contracts import canonical_json
from tests.context_admission.production_fixtures import canonical_request


def test_dual_digest_projection_is_independent_and_three_messages():
    request = canonical_request()
    package = ExclusiveAdmissionGate().seal(request)
    binding = ExactAdmittedSemanticBinder().bind(
        SemanticBindingRequest(package, request.identity_frames,
                               request.experience_frames, request.current_task_context)
    )
    binding.verify()
    assert dict(binding.source_digest_manifest) == dict(package.admitted_frames)
    assert [unit.role for unit in binding.units] == ["system", "system", "user"]
    assert all(unit.source_digest != unit.projected_digest for unit in binding.units[:2])
    assert "model_visibility" not in binding.units[0].projected_content
    assert "standing_authorization" not in binding.units[1].projected_content
    assert binding.units[2].projected_content == canonical_json(request.current_task_context.to_dict())
    assert binding.units[0].projected_digest == sha256(binding.units[0].projected_content.encode()).hexdigest()
