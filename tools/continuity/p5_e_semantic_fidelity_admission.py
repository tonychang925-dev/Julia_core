"""Owner-authorized P5-E GM-CMIR-004 semantic-fidelity admission transaction.

This tool never mutates the source authority or source PSB roots. It constructs
an append-only v2 durable authority package and a v3 PersonaSelfBinding store
under new target roots, then verifies both fail-closed before returning success.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from julia_core.canonical_authority_source import CanonicalSemanticAuthoritySource
from julia_core.durable_authority.contracts import canonical_json
from julia_core.durable_authority.filesystem_adapter import (
    EXPECTED_IDENTITY_REFS,
    EXPECTED_IDENTITY_VERSIONS,
    FilesystemDurableAuthorityReader,
)
from julia_core.durable_authority.golden_mira_v2 import (
    ACTIVE_MEMORY_REFS_V2,
    ACTIVE_MEMORY_VERSIONS_V2,
    DURABLE_MEMORY_REFS_V2,
    DURABLE_MEMORY_VERSIONS_V2,
    EXPORT_TOOL_VERSION_V2,
    GOVERNANCE_SCHEMA_VERSION_V3,
    GoldenMiraDurableAuthorityV2Reader,
    MANIFEST_SCHEMA_VERSION_V2,
    P5E_AUTHORIZATION_TIME,
    P5E_AUTHORITY_REASON,
    P5E_CORRECTION_MANIFEST,
    P5E_OWNER_AUTHORIZATION,
    P5E_SUCCESSOR_PREP,
    P5E_TASK_ID,
)
from julia_core.durable_authority.reconstruction import reconstruct_from_durable_authority
from julia_core.durable_authority.serialization import (
    build_identity_envelope,
    build_memory_experience_envelope,
    parse_memory_experience_record,
)
from julia_core.identity import IdentityRef, IdentityResolver
from julia_core.memory_experience import (
    MemoryExperienceCandidate,
    MemoryExperienceRef,
    MemoryExperienceResolver,
)
from julia_core.persona_self_binding import (
    PersonaSelfBindingProjectorV2,
    PersonaSelfBindingStore,
)
from julia_core.persona_self_binding.contracts import (
    AuthorityFamily,
    AuthorityReference,
    GovernanceEventType,
    GovernanceProvenanceEvent,
    PersonaSelfBindingLifecycle,
    SupersessionContract,
)
from julia_core.projection import ExperienceFrameSet, IdentityFrameSet
from julia_core.runtime.mira_composition import (
    _semantic_projection_digest,
    _with_canonical_binding,
)


PERSONA_ID = "golden-mira"
SOURCE_REPO = "https://github.com/tonychang925-dev/Julia_core.git"
RECORD_SCHEMA_VERSION = "julia_core.durable_authority.record.v1"
PREDECESSOR_REF = MemoryExperienceRef(
    "golden-mira:GM-CMIR-004", "v0.1-preview"
)
SUCCESSOR_REF = MemoryExperienceRef(
    "golden-mira:GM-CMIR-004", "v0.2-semantic-fidelity-preview"
)
EXPECTED_PREDECESSOR_DIGEST = (
    "ba4edeff89bc8054be19d7a48226fcef74359bc85d17dbd6abea4b754b905f97"
)
EXPECTED_SOURCE_PSB_DIGEST = (
    "a6167069289a0704b207292cd44a509a8f6e2844a143e5dbb7673fbcac38b525"
)


class P5ESemanticFidelityAdmissionError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if condition is not True:
        raise P5ESemanticFidelityAdmissionError(f"FAIL_CLOSED: {message}")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8", newline="\n")


def _git_head(repository: Path) -> str:
    value = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _require(
        len(value) == 40 and all(c in "0123456789abcdef" for c in value),
        "repository HEAD must be exact SHA",
    )
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(type(value) is dict, f"JSON object required: {path}")
    return value


def _verify_owner_authorization(repository: Path) -> dict[str, Any]:
    path = repository / P5E_OWNER_AUTHORIZATION
    value = _load_json(path)
    _require(value.get("artifact_id") == "P5_E_GM_CMIR_004_OWNER_AUTHORIZATION_V1", "owner authorization artifact")
    _require(value.get("owner") == "owner:tony", "owner actor")
    _require(value.get("status") == "GRANTED", "owner authorization status")
    _require(value.get("authorized_at") == P5E_AUTHORIZATION_TIME, "owner authorization time")
    scope = value.get("scope")
    _require(type(scope) is dict, "owner authorization scope")
    _require(scope.get("predecessor_ref") == PREDECESSOR_REF.uri, "authorized predecessor")
    _require(scope.get("successor_ref") == SUCCESSOR_REF.uri, "authorized successor")
    for key in (
        "successor_admission",
        "predecessor_supersession",
        "psb_experience_authority_rebind",
        "new_durable_package_generation",
    ):
        _require(scope.get(key) is True, f"authorized scope: {key}")
    for key in (
        "production_cutover",
        "other_memory_experience_mutation",
        "identity_mutation",
        "relationship_authority_mutation",
    ):
        _require(scope.get(key) is False, f"forbidden scope: {key}")
    return value


def _load_successor(repository: Path):
    manifest = _load_json(repository / P5E_CORRECTION_MANIFEST)
    prep = _load_json(repository / P5E_SUCCESSOR_PREP)
    _require(manifest.get("task_id") == P5E_TASK_ID, "correction task")
    _require(manifest.get("status") == "PREP_ONLY", "correction remains prep-only")
    _require(prep.get("task_id") == P5E_TASK_ID, "successor task")
    _require(
        prep.get("status") == "PREP_COMPLETE_NO_ADMISSION",
        "successor prep status",
    )
    source = prep.get("source")
    candidate = prep.get("successor_candidate")
    _require(type(source) is dict and type(candidate) is dict, "successor prep structure")
    _require(source.get("historical_canonical_ref") == PREDECESSOR_REF.uri, "successor predecessor ref")
    _require(source.get("historical_canonical_digest") == EXPECTED_PREDECESSOR_DIGEST, "successor predecessor digest")
    _require(candidate.get("predecessor_ref") == PREDECESSOR_REF.uri, "candidate predecessor ref")
    _require(candidate.get("proposed_version_id") == SUCCESSOR_REF.version_id, "candidate successor version")
    payload = candidate.get("proposed_canonical_payload")
    _require(type(payload) is dict, "successor canonical payload")
    record = parse_memory_experience_record(payload)
    _require(record.ref == SUCCESSOR_REF, "typed successor ref")
    _require(record.predecessor_version_id == PREDECESSOR_REF.version_id, "typed predecessor version")
    _require(record.digest() == candidate.get("proposed_canonical_digest"), "successor digest exact")
    return manifest, prep, record


def _old_admission_provenance(source_authority_root: Path) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for directory in ("identity", "memory_experience"):
        for path in sorted((source_authority_root / directory).glob("*.json")):
            item = _load_json(path)
            result[(item["canonical_ref"], item["version"])] = copy.deepcopy(
                item["admission_provenance"]
            )
    return result


def _active_frames(identity_repository, memory_repository):
    source = CanonicalSemanticAuthoritySource(
        identity_resolver=IdentityResolver(identity_repository),
        memory_resolver=MemoryExperienceResolver(memory_repository),
    )
    identity_frames = IdentityFrameSet(
        schema_version="1.0.0",
        frames=tuple(
            _with_canonical_binding(
                source.resolve_identity_frame(
                    IdentityRef(lineage_id=ref, version_id=version)
                )
            )
            for ref, version in zip(EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS)
        ),
    )
    experience_frames = ExperienceFrameSet(
        schema_version="1.0.0",
        frames=tuple(
            _with_canonical_binding(
                source.resolve_experience_frame(
                    MemoryExperienceRef(experience_id=ref, version_id=version)
                )
            )
            for ref, version in zip(ACTIVE_MEMORY_REFS_V2, ACTIVE_MEMORY_VERSIONS_V2)
        ),
    )
    return identity_frames, experience_frames


def _rebind_psb_v3(
    source_psb_root: Path,
    target_psb_root: Path,
    experience_frames: ExperienceFrameSet,
) -> dict[str, str]:
    _require(not target_psb_root.exists(), "target PSB root must not exist")
    shutil.copytree(source_psb_root, target_psb_root)
    store = PersonaSelfBindingStore(target_psb_root)
    active = store.resolve_active(PERSONA_ID)
    _require(active.object_digest == EXPECTED_SOURCE_PSB_DIGEST, "source PSB v2 digest")
    current = active.binding
    _require(current.binding_version == "v2", "source PSB version")
    source_digest = experience_frames.digest()
    projected_digest = _semantic_projection_digest(
        experience_frames.model_visible_projection()
    )
    proposal = GovernanceProvenanceEvent(
        event_id="golden-mira-psb-rebind-v3-propose",
        event_type=GovernanceEventType.PROPOSE_BINDING,
        actor="owner:tony",
        reason=P5E_AUTHORITY_REASON,
        occurred_at=P5E_AUTHORIZATION_TIME,
    )
    successor = replace(
        current,
        experience_authority=AuthorityReference(
            authority_type=AuthorityFamily.EXPERIENCE_FRAME_SET,
            authority_id=source_digest,
            source_digest=source_digest,
            projected_digest=projected_digest,
        ),
        binding_version="v3",
        predecessor_binding_version="v2",
        predecessor_binding_id=current.binding_id,
        lifecycle_status=PersonaSelfBindingLifecycle.GOVERNANCE_REVIEW,
        supersession=SupersessionContract(None, None),
        governance_provenance=(proposal,),
    )
    record = store.apply_transition(
        active.object_digest,
        GovernanceEventType.REBIND_AUTHORITY_VERSION,
        event_id="golden-mira-psb-rebind-v3-predecessor",
        actor="owner:tony",
        reason=P5E_AUTHORITY_REASON,
        occurred_at=P5E_AUTHORIZATION_TIME,
        successor=successor,
        successor_event_id="golden-mira-psb-rebind-v3-activate",
    )
    _require(record.binding.binding_version == "v3", "PSB v3 version")
    _require(
        record.binding.identity_authority == current.identity_authority,
        "identity authority unchanged",
    )
    _require(
        record.binding.relationship_authority == current.relationship_authority,
        "relationship authority unchanged",
    )
    _require(
        record.binding.execution_substrate_policy == current.execution_substrate_policy,
        "execution substrate policy unchanged",
    )
    _require(
        record.binding.experience_authority.source_digest == source_digest
        and record.binding.experience_authority.projected_digest == projected_digest,
        "experience authority rebound exactly",
    )
    projected = PersonaSelfBindingProjectorV2.project(record.binding)
    return {
        "binding_version": "v3",
        "object_digest": record.object_digest,
        "projected_digest": projected.digest(),
        "experience_source_digest": source_digest,
        "experience_projected_digest": projected_digest,
    }


def _record(
    *,
    envelope,
    record_type: str,
    canonical_ref: str,
    version: str,
    order_index: int,
    admission_provenance: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": RECORD_SCHEMA_VERSION,
        "record_type": record_type,
        "canonical_ref": canonical_ref,
        "version": version,
        "payload": envelope.payload_object,
        "payload_digest": envelope.payload_digest,
        "governance": list(envelope.governance_events),
        "lifecycle_status": envelope.lifecycle_status,
        "source_provenance": list(envelope.provenance),
        "admission_provenance": admission_provenance,
        "order_index": order_index,
        "authority_family": envelope.authority_family.value,
        "authority_object_ref": envelope.authority_object_ref,
        "authority_object_schema": envelope.authority_object_schema,
        "serialized_payload": envelope.serialized_payload,
        "lineage_metadata": envelope.lineage_metadata,
        "envelope_digest": envelope.envelope_digest,
    }


def _export_v2(
    *,
    repository: Path,
    target_authority_root: Path,
    source_authority_root: Path,
    identity_repository,
    memory_repository,
    psb_binding: dict[str, str],
    correction_manifest: dict[str, Any],
    successor_prep: dict[str, Any],
    successor_digest: str,
) -> dict[str, Any]:
    _require(not target_authority_root.exists(), "target authority root must not exist")
    old_provenance = _old_admission_provenance(source_authority_root)
    identity_envelopes = [
        build_identity_envelope(
            identity_repository.resolve(IdentityRef(ref, version))
        )
        for ref, version in zip(EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS)
    ]
    memory_envelopes = [
        build_memory_experience_envelope(
            memory_repository.resolve(MemoryExperienceRef(ref, version))
        )
        for ref, version in zip(DURABLE_MEMORY_REFS_V2, DURABLE_MEMORY_VERSIONS_V2)
    ]

    identity_records = []
    for index, (env, ref, version) in enumerate(
        zip(identity_envelopes, EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS)
    ):
        identity_records.append(
            _record(
                envelope=env,
                record_type="IDENTITY",
                canonical_ref=ref,
                version=version,
                order_index=index,
                admission_provenance=copy.deepcopy(old_provenance[(ref, version)]),
            )
        )

    memory_records = []
    for index, (env, ref, version) in enumerate(
        zip(memory_envelopes, DURABLE_MEMORY_REFS_V2, DURABLE_MEMORY_VERSIONS_V2)
    ):
        if ref == PREDECESSOR_REF.experience_id and version == PREDECESSOR_REF.version_id:
            provenance = copy.deepcopy(old_provenance[(ref, version)])
            provenance.update(
                {
                    "supersession_task_id": P5E_TASK_ID,
                    "source_semantic_fidelity_artifact": P5E_SUCCESSOR_PREP,
                    "source_owner_authorization_artifact": P5E_OWNER_AUTHORIZATION,
                    "supersession_event": env.governance_events[-1]["admission"],
                }
            )
        elif ref == SUCCESSOR_REF.experience_id and version == SUCCESSOR_REF.version_id:
            provenance = {
                "task_id": P5E_TASK_ID,
                "source_semantic_fidelity_artifact": P5E_SUCCESSOR_PREP,
                "source_owner_authorization_artifact": P5E_OWNER_AUTHORIZATION,
                "source_sha": _git_head(repository),
                "event": env.governance_events[-1]["admission"],
            }
        else:
            provenance = copy.deepcopy(old_provenance[(ref, version)])
        memory_records.append(
            _record(
                envelope=env,
                record_type="MEMORY_EXPERIENCE",
                canonical_ref=ref,
                version=version,
                order_index=index,
                admission_provenance=provenance,
            )
        )

    staging = target_authority_root.with_name(f".{target_authority_root.name}.tmp")
    _require(not staging.exists(), "authority staging root exists")
    governance = {
        "schema_version": GOVERNANCE_SCHEMA_VERSION_V3,
        "persona_id": PERSONA_ID,
        "owner_actor": "owner:tony",
        "authority_reason": P5E_AUTHORITY_REASON,
        "authorization_time": P5E_AUTHORIZATION_TIME,
        "records_admitted": 13,
        "identity_lifecycle": "ADMITTED",
        "memory_experience_lifecycle": "MIXED_ADMITTED_AND_SUPERSEDED",
        "source_p5_artifact": "artifacts/continuity/P5_A1_OWNER_AUTHORIZED_GOLDEN_MIRA_CANONICAL_ADMISSION_V1.json",
        "source_p4_artifact": "artifacts/continuity/MIRA_RELATIONSHIP_ROLE_C04_ADMISSION_SOURCE_P4_V1.json",
        "source_semantic_fidelity_artifact": P5E_SUCCESSOR_PREP,
        "source_owner_authorization_artifact": P5E_OWNER_AUTHORIZATION,
    }

    record_digests: dict[str, dict[str, str]] = {}
    for directory, records in (
        ("identity", identity_records),
        ("memory_experience", memory_records),
    ):
        for item in records:
            path = f"{directory}/{item['order_index']:08d}.json"
            _write_json(staging / path, item)
            record_digests[path] = {
                "payload_digest": item["payload_digest"],
                "envelope_digest": item["envelope_digest"],
            }
    _write_json(staging / "governance" / "state.json", governance)

    package_paths = (
        *(f"identity/{index:08d}.json" for index in range(4)),
        *(f"memory_experience/{index:08d}.json" for index in range(9)),
        "governance/state.json",
    )
    package_files = {path: _sha256_file(staging / path) for path in package_paths}
    owner_auth_path = repository / P5E_OWNER_AUTHORIZATION
    correction_path = repository / P5E_CORRECTION_MANIFEST
    successor_path = repository / P5E_SUCCESSOR_PREP
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION_V2,
        "authority_type": "CANONICAL_SEMANTIC_AUTHORITY",
        "persona_id": PERSONA_ID,
        "created_from_p5_admission": True,
        "source_repo": SOURCE_REPO,
        "source_sha": _git_head(repository),
        "export_tool_version": EXPORT_TOOL_VERSION_V2,
        "identity_count": 4,
        "memory_experience_count": 9,
        "ordered_identity_refs": list(EXPECTED_IDENTITY_REFS),
        "ordered_memory_experience_refs": list(DURABLE_MEMORY_REFS_V2),
        "active_memory_experience_refs": list(ACTIVE_MEMORY_REFS_V2),
        "active_memory_experience_versions": list(ACTIVE_MEMORY_VERSIONS_V2),
        "record_digests": record_digests,
        "governance_state": {
            "owner_actor": "owner:tony",
            "reason": P5E_AUTHORITY_REASON,
            "authorization_time": P5E_AUTHORIZATION_TIME,
            "records_admitted": 13,
        },
        "lineage": {
            "identity": [item["lineage_metadata"] for item in identity_records],
            "memory_experience": [
                item["lineage_metadata"] for item in memory_records
            ],
        },
        "package_files": package_files,
        "semantic_fidelity": {
            "task_id": P5E_TASK_ID,
            "correction_manifest": P5E_CORRECTION_MANIFEST,
            "correction_manifest_sha256": _sha256_file(correction_path),
            "correction_manifest_digest": successor_prep["source"]["correction_manifest_digest"],
            "successor_prep": P5E_SUCCESSOR_PREP,
            "successor_prep_sha256": _sha256_file(successor_path),
            "owner_authorization": P5E_OWNER_AUTHORIZATION,
            "owner_authorization_sha256": _sha256_file(owner_auth_path),
            "predecessor_ref": PREDECESSOR_REF.uri,
            "successor_ref": SUCCESSOR_REF.uri,
            "successor_payload_digest": successor_digest,
        },
        "psb_binding": dict(psb_binding),
    }
    unsigned = dict(manifest)
    manifest["manifest_digest"] = _sha256_text(canonical_json(unsigned))
    _write_json(staging / "manifest.json", manifest)
    os.replace(staging, target_authority_root)
    for path in sorted(target_authority_root.rglob("*"), reverse=True):
        if path.is_file():
            path.chmod(0o444)
        elif path.is_dir():
            path.chmod(0o555)
    return manifest


def execute(
    *,
    repository: Path,
    source_authority_root: Path,
    source_psb_root: Path,
    target_authority_root: Path,
    target_psb_root: Path,
) -> dict[str, Any]:
    repository = repository.resolve()
    source_authority_root = source_authority_root.resolve()
    source_psb_root = source_psb_root.resolve()
    target_authority_root = target_authority_root.resolve()
    target_psb_root = target_psb_root.resolve()

    _verify_owner_authorization(repository)
    correction_manifest, successor_prep, successor = _load_successor(repository)

    source_reader = FilesystemDurableAuthorityReader(source_authority_root)
    identities, memories = reconstruct_from_durable_authority(source_reader)
    predecessor_before = memories.resolve(PREDECESSOR_REF)
    _require(predecessor_before.status.value == "ADMITTED", "predecessor must be admitted")
    _require(
        predecessor_before.record.digest() == EXPECTED_PREDECESSOR_DIGEST,
        "predecessor digest",
    )

    before = {
        item.uri: (
            memories.resolve(item).record.digest(),
            memories.resolve(item).status.value,
        )
        for item in (
            MemoryExperienceRef(ref, version)
            for ref, version in zip(
                ACTIVE_MEMORY_REFS_V2,
                (
                    "v0.2-preview",
                    "v0.2-preview",
                    "v0.1-preview",
                    "v0.1-preview",
                    "v0.1-preview",
                    "formation-draft-preview",
                    "frozen-final-preview",
                    "v0.2-preview",
                ),
            )
        )
    }

    memories.store_candidate(
        MemoryExperienceCandidate(
            record=successor,
            submitted_at=P5E_AUTHORIZATION_TIME,
        )
    )
    memories.admit(
        SUCCESSOR_REF,
        actor="owner:tony",
        reason=P5E_AUTHORITY_REASON,
        occurred_at=P5E_AUTHORIZATION_TIME,
    )
    memories.supersede(
        PREDECESSOR_REF,
        actor="owner:tony",
        reason=P5E_AUTHORITY_REASON,
        occurred_at=P5E_AUTHORIZATION_TIME,
    )

    _require(
        memories.resolve(PREDECESSOR_REF).status.value == "SUPERSEDED",
        "predecessor superseded",
    )
    _require(
        memories.resolve(SUCCESSOR_REF).status.value == "ADMITTED",
        "successor admitted",
    )
    _require(
        memories.resolve(SUCCESSOR_REF).record.digest()
        == successor_prep["successor_candidate"]["proposed_canonical_digest"],
        "successor admitted digest",
    )
    for uri, (digest, status) in before.items():
        if uri == PREDECESSOR_REF.uri:
            continue
        experience_id, version = uri[len("memory-experience://") :].split("/", 1)
        governed = memories.resolve(MemoryExperienceRef(experience_id, version))
        _require(governed.record.digest() == digest, f"unchanged payload: {uri}")
        _require(governed.status.value == status, f"unchanged status: {uri}")

    identity_frames, experience_frames = _active_frames(identities, memories)
    psb_binding = _rebind_psb_v3(
        source_psb_root,
        target_psb_root,
        experience_frames,
    )
    manifest = _export_v2(
        repository=repository,
        target_authority_root=target_authority_root,
        source_authority_root=source_authority_root,
        identity_repository=identities,
        memory_repository=memories,
        psb_binding=psb_binding,
        correction_manifest=correction_manifest,
        successor_prep=successor_prep,
        successor_digest=successor.digest(),
    )

    reader = GoldenMiraDurableAuthorityV2Reader(target_authority_root)
    restored_identities, restored_memories = reconstruct_from_durable_authority(reader)
    restored_predecessor = restored_memories.resolve(PREDECESSOR_REF)
    restored_successor = restored_memories.resolve(SUCCESSOR_REF)
    _require(restored_predecessor.status.value == "SUPERSEDED", "roundtrip predecessor")
    _require(restored_successor.status.value == "ADMITTED", "roundtrip successor")
    _require(restored_successor.record.digest() == successor.digest(), "roundtrip successor digest")

    restored_identity_frames, restored_experience_frames = _active_frames(
        restored_identities, restored_memories
    )
    _require(restored_identity_frames.digest() == identity_frames.digest(), "identity frame roundtrip")
    _require(restored_experience_frames.digest() == experience_frames.digest(), "experience frame roundtrip")
    _require(
        _semantic_projection_digest(restored_experience_frames.model_visible_projection())
        == psb_binding["experience_projected_digest"],
        "experience projection roundtrip",
    )

    active_psb = PersonaSelfBindingStore(target_psb_root).resolve_active(PERSONA_ID)
    _require(active_psb.binding.binding_version == "v3", "roundtrip PSB v3")
    _require(active_psb.object_digest == psb_binding["object_digest"], "roundtrip PSB digest")
    _require(
        PersonaSelfBindingProjectorV2.project(active_psb.binding).digest()
        == psb_binding["projected_digest"],
        "roundtrip PSB projection",
    )
    _require(
        active_psb.binding.experience_authority.source_digest
        == restored_experience_frames.digest(),
        "PSB experience source binding",
    )

    return {
        "schema": "julia_core.continuity.p5_e.semantic_fidelity_admission.v1",
        "task_id": P5E_TASK_ID,
        "owner_authorization": "GRANTED",
        "repository_head": _git_head(repository),
        "source_authority_root": str(source_authority_root),
        "source_psb_root": str(source_psb_root),
        "target_authority_root": str(target_authority_root),
        "target_psb_root": str(target_psb_root),
        "predecessor": {
            "ref": PREDECESSOR_REF.uri,
            "digest": EXPECTED_PREDECESSOR_DIGEST,
            "final_status": restored_predecessor.status.value,
        },
        "successor": {
            "ref": SUCCESSOR_REF.uri,
            "digest": restored_successor.record.digest(),
            "final_status": restored_successor.status.value,
        },
        "active_experience_frame_set": {
            "ref_count": len(restored_experience_frames.frames),
            "source_digest": restored_experience_frames.digest(),
            "projected_digest": _semantic_projection_digest(
                restored_experience_frames.model_visible_projection()
            ),
        },
        "psb_v3": psb_binding,
        "durable_manifest_digest": manifest["manifest_digest"],
        "authority": {
            "production_cutover": 0,
            "identity_mutation": 0,
            "relationship_authority_mutation": 0,
            "other_memory_experience_payload_mutation": 0,
        },
        "final_result": "P5_E_SEMANTIC_FIDELITY_SUCCESSOR_ADMISSION_AND_PSB_V3_REBIND_COMPLETE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-authority-root", required=True, type=Path)
    parser.add_argument("--source-psb-root", required=True, type=Path)
    parser.add_argument("--target-authority-root", required=True, type=Path)
    parser.add_argument("--target-psb-root", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    result = execute(
        repository=args.repository,
        source_authority_root=args.source_authority_root,
        source_psb_root=args.source_psb_root,
        target_authority_root=args.target_authority_root,
        target_psb_root=args.target_psb_root,
    )
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
