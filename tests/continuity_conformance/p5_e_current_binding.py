from __future__ import annotations

from pathlib import Path

from julia_core.durable_authority import FilesystemDurableAuthorityReader
from julia_core.durable_authority.contracts import AuthorityFamily
from julia_core.durable_authority.filesystem_adapter import (
    EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS,
    EXPECTED_MEMORY_REFS, EXPECTED_MEMORY_VERSIONS,
)
from julia_core.identity import IdentityRef
from julia_core.memory_experience import MemoryExperienceRef
from julia_core.persona_self_binding import PersonaSelfBindingStore
from tests.continuity_conformance.evaluation_contract import (
    ContinuityEvaluationContract, ContinuityEvaluationRejected,
)

EXPECTED_PSB_VERSION = 'v2'
EXPECTED_PSB_DIGEST = 'a6167069289a0704b207292cd44a509a8f6e2844a143e5dbb7673fbcac38b525'
EXPECTED_IDENTITY_SOURCE_DIGEST = '3f01c2ab9bc578ba8ce4c3809c12bdaf651870b4d04241d88eab5654129cd324'
EXPECTED_IDENTITY_PROJECTED_DIGEST = '5055bf7949c3d3c594c87a2f4aa8e0c5d85bebd7a0848487dbab096c05ce7021'


def build_current_contract(
    *, repository: Path, authority_root: Path, psb_store_root: Path
) -> ContinuityEvaluationContract:
    historical = ContinuityEvaluationContract.load(
        repository / 'artifacts/continuity/P5_D_CONTINUITY_EVALUATION_PREP_V1.json'
    )
    reader = FilesystemDurableAuthorityReader(authority_root)
    refs: list[str] = []
    digests: dict[str, str] = {}
    for lineage_id, version_id in zip(EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS):
        ref = IdentityRef(lineage_id=lineage_id, version_id=version_id)
        envelope = reader.read_exact(AuthorityFamily.IDENTITY, ref)
        refs.append(ref.uri)
        digests[ref.uri] = envelope.payload_digest
    for experience_id, version_id in zip(EXPECTED_MEMORY_REFS, EXPECTED_MEMORY_VERSIONS):
        ref = MemoryExperienceRef(experience_id=experience_id, version_id=version_id)
        envelope = reader.read_exact(AuthorityFamily.MEMORY_EXPERIENCE, ref)
        refs.append(ref.uri)
        digests[ref.uri] = envelope.payload_digest

    active = PersonaSelfBindingStore(psb_store_root).resolve_active('golden-mira')
    if active.binding.binding_version != EXPECTED_PSB_VERSION:
        raise ContinuityEvaluationRejected('current PSB version is stale')
    if active.object_digest != EXPECTED_PSB_DIGEST:
        raise ContinuityEvaluationRejected('current PSB digest is stale')
    identity = active.binding.identity_authority
    if identity.source_digest != EXPECTED_IDENTITY_SOURCE_DIGEST:
        raise ContinuityEvaluationRejected('current identity authority digest is stale')
    if identity.projected_digest != EXPECTED_IDENTITY_PROJECTED_DIGEST:
        raise ContinuityEvaluationRejected('current identity projection digest is stale')
    if len(EXPECTED_IDENTITY_REFS) != 4 or len(EXPECTED_MEMORY_REFS) != 8:
        raise ContinuityEvaluationRejected('current canonical cardinality is stale')

    admitted_input = {
        'selection_rule': 'EXACT_CURRENT_CANONICAL_REF_DIGEST_AND_PSB_ONLY',
        'refs': refs,
        'digests': digests,
        'identity_count': 4,
        'memory_experience_count': 8,
        'identity_source_digest': identity.source_digest,
        'identity_projected_digest': identity.projected_digest,
        'experience_source_digest': active.binding.experience_authority.source_digest,
        'experience_projected_digest': active.binding.experience_authority.projected_digest,
        'psb_version': active.binding.binding_version,
        'psb_digest': active.object_digest,
        'relationship_binding_state': active.binding.relationship_authority.state.value,
    }
    return ContinuityEvaluationContract.from_dict({
        'schema': historical.schema,
        'artifact_id': 'P5_E_CURRENT_CANONICAL_EVALUATION_BINDING_V1',
        'admitted_input': admitted_input,
        'dimensions': list(historical.dimensions),
        'global_disposition_rules': historical.global_disposition_rules,
        'anti_gaming_rules': historical.anti_gaming_rules,
        'authority': historical.authority,
    })
