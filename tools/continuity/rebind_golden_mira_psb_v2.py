from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import replace
from pathlib import Path

from julia_core.canonical_authority_source import CanonicalSemanticAuthoritySource
from julia_core.durable_authority import (
    FilesystemDurableAuthorityReader,
    reconstruct_from_durable_authority,
)
from julia_core.durable_authority.filesystem_adapter import (
    EXPECTED_IDENTITY_REFS,
    EXPECTED_IDENTITY_VERSIONS,
)
from julia_core.identity import IdentityRef, IdentityResolver
from julia_core.memory_experience import MemoryExperienceResolver
from julia_core.persona_self_binding import PersonaSelfBindingStore
from julia_core.persona_self_binding.contracts import (
    AuthorityFamily,
    AuthorityReference,
    GovernanceEventType,
    GovernanceProvenanceEvent,
    PersonaSelfBindingLifecycle,
    SupersessionContract,
)
from julia_core.projection import IdentityFrameSet
from julia_core.runtime.mira_composition import (
    _semantic_projection_digest,
    _with_canonical_binding,
)

EXPECTED_V1_DIGEST = (
    "6f221843961e32e8ffad1af709f54fce1123007eaf11aa440682d1b60bd6aaad"
)
EXPECTED_V2_DIGEST = (
    "a6167069289a0704b207292cd44a509a8f6e2844a143e5dbb7673fbcac38b525"
)
EXPECTED_IDENTITY_SOURCE_DIGEST = (
    "3f01c2ab9bc578ba8ce4c3809c12bdaf651870b4d04241d88eab5654129cd324"
)
EXPECTED_IDENTITY_PROJECTED_DIGEST = (
    "5055bf7949c3d3c594c87a2f4aa8e0c5d85bebd7a0848487dbab096c05ce7021"
)


def _identity_authority(authority_root: Path) -> AuthorityReference:
    reader = FilesystemDurableAuthorityReader(authority_root)
    identity_repository, memory_repository = reconstruct_from_durable_authority(reader)
    source = CanonicalSemanticAuthoritySource(
        identity_resolver=IdentityResolver(identity_repository),
        memory_resolver=MemoryExperienceResolver(memory_repository),
    )
    frames = IdentityFrameSet(
        schema_version="1.0.0",
        frames=tuple(
            _with_canonical_binding(
                source.resolve_identity_frame(
                    IdentityRef(lineage_id=ref, version_id=version)
                )
            )
            for ref, version in zip(
                EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS
            )
        ),
    )
    source_digest = frames.digest()
    projected_digest = _semantic_projection_digest(
        frames.model_visible_projection()
    )
    if source_digest != EXPECTED_IDENTITY_SOURCE_DIGEST:
        raise RuntimeError("unexpected four-identity source digest")
    if projected_digest != EXPECTED_IDENTITY_PROJECTED_DIGEST:
        raise RuntimeError("unexpected four-identity projected digest")
    return AuthorityReference(
        authority_type=AuthorityFamily.IDENTITY_FRAME_SET,
        authority_id=source_digest,
        source_digest=source_digest,
        projected_digest=projected_digest,
    )


def rebind(
    authority_root: Path, source_psb_root: Path, target_psb_root: Path
) -> dict[str, object]:
    if target_psb_root.exists():
        raise RuntimeError("target PSB root must not already exist")
    shutil.copytree(source_psb_root, target_psb_root)
    store = PersonaSelfBindingStore(target_psb_root)
    active = store.resolve_active("golden-mira")
    if active.object_digest == EXPECTED_V2_DIGEST:
        if active.binding.binding_version != "v2":
            raise RuntimeError("approved v2 digest has the wrong semantic version")
        return {
            "binding_id": active.binding.binding_id,
            "binding_version": active.binding.binding_version,
            "object_digest": active.object_digest,
            "lifecycle_status": active.binding.lifecycle_status.value,
            "identity_source_digest": active.binding.identity_authority.source_digest,
            "identity_projected_digest": active.binding.identity_authority.projected_digest,
            "relationship_authority_state": active.binding.relationship_authority.state.value,
            "experience_authority_unchanged": True,
        }
    if active.object_digest != EXPECTED_V1_DIGEST:
        raise RuntimeError("source active PSB digest is neither approved v1 nor approved v2")
    current = active.binding
    if current.binding_version != "v1":
        raise RuntimeError("source active PSB version is not v1")

    proposal = GovernanceProvenanceEvent(
        event_id="golden-mira-psb-rebind-v2-propose",
        event_type=GovernanceEventType.PROPOSE_BINDING,
        actor="owner:tony",
        reason=(
            "Propose rebinding Golden Mira identity authority to the "
            "owner-authorized four-identity frame set"
        ),
        occurred_at="2026-09-25T16:54:00+08:00",
    )
    successor = replace(
        current,
        identity_authority=_identity_authority(authority_root),
        binding_version="v2",
        predecessor_binding_version="v1",
        predecessor_binding_id=current.binding_id,
        lifecycle_status=PersonaSelfBindingLifecycle.GOVERNANCE_REVIEW,
        supersession=SupersessionContract(None, None),
        governance_provenance=(proposal,),
    )
    record = store.apply_transition(
        active.object_digest,
        GovernanceEventType.REBIND_AUTHORITY_VERSION,
        event_id="golden-mira-psb-rebind-v2-predecessor",
        actor="owner:tony",
        reason=(
            "Rebind Golden Mira identity authority to admitted C04 "
            "relationship-role identity"
        ),
        occurred_at="2026-09-25T16:54:30+08:00",
        successor=successor,
        successor_event_id="golden-mira-psb-rebind-v2-activate",
    )
    if record.object_digest != EXPECTED_V2_DIGEST:
        raise RuntimeError("unexpected PSB v2 object digest")
    if record.binding.experience_authority != current.experience_authority:
        raise RuntimeError("experience authority changed during identity rebind")
    if record.binding.relationship_authority != current.relationship_authority:
        raise RuntimeError("relationship authority changed during identity rebind")
    if (
        record.binding.execution_substrate_policy
        != current.execution_substrate_policy
    ):
        raise RuntimeError("execution substrate policy changed during identity rebind")
    return {
        "binding_id": record.binding.binding_id,
        "binding_version": record.binding.binding_version,
        "object_digest": record.object_digest,
        "lifecycle_status": record.binding.lifecycle_status.value,
        "identity_source_digest": record.binding.identity_authority.source_digest,
        "identity_projected_digest": (
            record.binding.identity_authority.projected_digest
        ),
        "relationship_authority_state": (
            record.binding.relationship_authority.state.value
        ),
        "experience_authority_unchanged": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority-root", type=Path, required=True)
    parser.add_argument("--source-psb-root", type=Path, required=True)
    parser.add_argument("--target-psb-root", type=Path, required=True)
    args = parser.parse_args()
    result = rebind(
        args.authority_root.resolve(),
        args.source_psb_root.resolve(),
        args.target_psb_root.resolve(),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
