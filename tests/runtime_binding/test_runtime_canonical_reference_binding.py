from __future__ import annotations

import ast
import inspect
from dataclasses import replace
from pathlib import Path

import pytest

from julia_core.canonical_authority_source import CanonicalSemanticAuthoritySource
from julia_core.identity import IdentityRef, IdentityResolver
from julia_core.memory_experience import (
    MemoryExperienceCandidate,
    MemoryExperienceRepository,
    MemoryExperienceRef,
    MemoryExperienceResolver,
)
from julia_core.projection import ExperienceFrame, IdentityFrame
from julia_core.runtime_canonical_binding import (
    BINDING_SCHEMA_VERSION,
    RuntimeCanonicalAuthorityBinding,
    RuntimeCanonicalAuthorityBindingErrorCode,
    RuntimeCanonicalAuthorityBindingProvenance,
    RuntimeCanonicalAuthorityBindingRef,
    RuntimeCanonicalAuthorityBindingRepository,
    RuntimeCanonicalAuthorityBindingResolver,
    RuntimeCanonicalAuthorityBindingStatus,
)
from tests.canonical_authority.test_canonical_production_authority_source import (
    identity_fixture,
    memory_record,
)


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATH = ROOT / "julia_core/runtime_canonical_binding"
PRODUCTION_PATHS = sorted(PACKAGE_PATH.glob("*.py"))


class SubclassedBindingRef(RuntimeCanonicalAuthorityBindingRef):
    pass


def binding_provenance() -> RuntimeCanonicalAuthorityBindingProvenance:
    return RuntimeCanonicalAuthorityBindingProvenance(
        source_type="governance_decision",
        source_ref="governance://runtime-binding/n4c",
        source_digest="c" * 64,
        admission_metadata=(("decision", "owner-selected canonical refs"),),
    )


def canonical_fixtures():
    identity_repository, identity_ref = identity_fixture()
    memory_repository = MemoryExperienceRepository()
    second_record = replace(
        memory_record(),
        experience_id="experience-n4c-second",
        version_id="v1",
    )
    experience_refs = []
    for record in (memory_record(), second_record):
        candidate = memory_repository.store_candidate(
            MemoryExperienceCandidate(
                record=record,
                submitted_at="2026-09-12T00:00:01Z",
            )
        )
        memory_repository.admit(
            candidate.ref,
            actor="n4c-test-governance",
            reason="test admission",
            occurred_at="2026-09-12T00:01:00Z",
        )
        experience_refs.append(candidate.ref)
    return (
        identity_repository,
        identity_ref,
        memory_repository,
        (
            experience_refs[0],
            experience_refs[1],
        ),
    )


def binding_fixture():
    identity_repository, identity_ref, memory_repository, experience_refs = (
        canonical_fixtures()
    )
    binding = RuntimeCanonicalAuthorityBinding(
        schema_version=BINDING_SCHEMA_VERSION,
        binding_id="production-runtime",
        binding_version="v1",
        predecessor_version_id=None,
        identity_ref=identity_ref,
        experience_refs=experience_refs,
        provenance_refs=(binding_provenance(),),
        created_at="2026-09-12T00:02:00Z",
    )
    return binding, identity_repository, memory_repository


def admitted_binding():
    binding, identity_repository, memory_repository = binding_fixture()
    repository = RuntimeCanonicalAuthorityBindingRepository()
    repository.store_candidate(binding)
    repository.admit(
        binding.ref,
        actor="n4c-test-governance",
        reason="test runtime binding admission",
        occurred_at="2026-09-12T00:03:00Z",
    )
    return repository, binding, identity_repository, memory_repository


def resolver_error(call) -> RuntimeCanonicalAuthorityBindingErrorCode:
    with pytest.raises(Exception) as error:
        call()
    assert isinstance(error.value, Exception)
    return error.value.code


def test_n4c_01_exact_candidate_binding_stored() -> None:
    binding, _, _ = binding_fixture()
    repository = RuntimeCanonicalAuthorityBindingRepository()
    governed = repository.store_candidate(binding)
    assert governed.ref == binding.ref
    assert governed.status is RuntimeCanonicalAuthorityBindingStatus.CANDIDATE


def test_n4c_02_candidate_admitted_through_governed_lifecycle() -> None:
    repository, binding, _, _ = admitted_binding()
    governed = repository.resolve(binding.ref)
    assert governed.status is RuntimeCanonicalAuthorityBindingStatus.ADMITTED
    assert [event.status for event in governed.governance_events] == [
        RuntimeCanonicalAuthorityBindingStatus.CANDIDATE,
        RuntimeCanonicalAuthorityBindingStatus.ADMITTED,
    ]


def test_n4c_03_through_n4c_05_exact_binding_refs_resolve() -> None:
    repository, binding, _, _ = admitted_binding()
    governed = RuntimeCanonicalAuthorityBindingResolver(repository).resolve_exact(
        binding.ref
    )
    assert governed.binding.identity_ref == binding.identity_ref
    assert type(governed.binding.identity_ref) is IdentityRef
    assert governed.binding.experience_refs == binding.experience_refs
    assert type(governed.binding.experience_refs) is tuple
    assert all(
        type(ref) is MemoryExperienceRef for ref in governed.binding.experience_refs
    )


def test_n4c_06_and_n4c_07_provenance_and_digest_deterministic() -> None:
    first, _, _ = binding_fixture()
    second, _, _ = binding_fixture()
    assert first.provenance_refs[0].to_dict() == second.provenance_refs[0].to_dict()
    assert first.digest() == second.digest()
    assert first.canonical_serialization() == second.canonical_serialization()


def test_n4c_08_and_n4c_09_n4b_resolves_bound_refs() -> None:
    _, binding, identity_repository, memory_repository = admitted_binding()
    source = CanonicalSemanticAuthoritySource(
        identity_resolver=IdentityResolver(identity_repository),
        memory_resolver=MemoryExperienceResolver(memory_repository),
    )
    identity_frame = source.resolve_identity_frame(binding.identity_ref)
    experience_frames = [
        source.resolve_experience_frame(ref) for ref in binding.experience_refs
    ]
    assert type(identity_frame) is IdentityFrame
    assert all(type(frame) is ExperienceFrame for frame in experience_frames)


def test_n4c_10_binding_is_reference_only() -> None:
    binding, _, _ = binding_fixture()
    payload = binding.to_dict()
    assert set(payload) == {
        "schema_version",
        "binding_id",
        "binding_version",
        "predecessor_version_id",
        "identity_ref",
        "experience_refs",
        "provenance_refs",
        "created_at",
    }
    assert set(payload["identity_ref"]) == {"lineage_id", "version_id"}
    assert all(
        set(item) == {"experience_id", "version_id"}
        for item in payload["experience_refs"]
    )


def test_n4c_11_missing_repository_fails_closed() -> None:
    assert (
        resolver_error(
            lambda: RuntimeCanonicalAuthorityBindingResolver().resolve_exact(
                RuntimeCanonicalAuthorityBindingRef("runtime", "v1")
            )
        )
        is RuntimeCanonicalAuthorityBindingErrorCode.SOURCE_NOT_BOUND
    )


def test_n4c_12_unknown_binding_ref_fails_closed() -> None:
    repository, binding, _, _ = admitted_binding()
    assert (
        resolver_error(
            lambda: RuntimeCanonicalAuthorityBindingResolver(repository).resolve_exact(
                RuntimeCanonicalAuthorityBindingRef(
                    binding.binding_id,
                    "missing-version",
                )
            )
        )
        is RuntimeCanonicalAuthorityBindingErrorCode.REF_NOT_FOUND
    )


@pytest.mark.parametrize(
    ("transition", "expected_code"),
    [
        ("candidate", RuntimeCanonicalAuthorityBindingErrorCode.REF_NOT_ADMITTED),
        ("supersede", RuntimeCanonicalAuthorityBindingErrorCode.REF_NOT_ADMITTED),
        ("retire", RuntimeCanonicalAuthorityBindingErrorCode.REF_RETIRED),
    ],
)
def test_n4c_13_through_n4c_15_nonadmitted_lifecycle_fails_closed(
    transition: str, expected_code: RuntimeCanonicalAuthorityBindingErrorCode
) -> None:
    binding, _, _ = binding_fixture()
    repository = RuntimeCanonicalAuthorityBindingRepository()
    repository.store_candidate(binding)
    if transition != "candidate":
        getattr(repository, transition)(
            binding.ref,
            actor="n4c-test-governance",
            reason=f"test {transition}",
            occurred_at="2026-09-12T00:04:00Z",
        )
    resolver = RuntimeCanonicalAuthorityBindingResolver(repository)
    assert resolver_error(lambda: resolver.resolve_exact(binding.ref)) is expected_code


@pytest.mark.parametrize(
    "candidate",
    [
        object(),
        {
            "binding_id": "production-runtime",
            "binding_version": "v1",
        },
        SubclassedBindingRef("production-runtime", "v1"),
    ],
)
def test_n4c_16_and_n4c_17_forged_refs_fail_closed(candidate: object) -> None:
    repository, _, _, _ = admitted_binding()
    resolver = RuntimeCanonicalAuthorityBindingResolver(repository)
    assert (
        resolver_error(lambda: resolver.resolve_exact(candidate))
        is RuntimeCanonicalAuthorityBindingErrorCode.TYPE_MISMATCH
    )


def test_n4c_18_malformed_identity_ref_fails_closed() -> None:
    binding, _, _ = binding_fixture()
    with pytest.raises(TypeError):
        RuntimeCanonicalAuthorityBinding(
            schema_version=binding.schema_version,
            binding_id=binding.binding_id,
            binding_version=binding.binding_version,
            predecessor_version_id=binding.predecessor_version_id,
            identity_ref=object(),
            experience_refs=binding.experience_refs,
            provenance_refs=binding.provenance_refs,
            created_at=binding.created_at,
        )


def test_n4c_19_malformed_experience_refs_fail_closed() -> None:
    binding, _, _ = binding_fixture()
    fields = {
        "schema_version": binding.schema_version,
        "binding_id": binding.binding_id,
        "binding_version": binding.binding_version,
        "predecessor_version_id": binding.predecessor_version_id,
        "identity_ref": binding.identity_ref,
        "experience_refs": (object(),),
        "provenance_refs": binding.provenance_refs,
        "created_at": binding.created_at,
    }
    with pytest.raises(TypeError):
        RuntimeCanonicalAuthorityBinding(**fields)


def test_n4c_20_through_n4c_22_no_selection_or_alias_api() -> None:
    public_resolver = {
        name
        for name, _ in inspect.getmembers(
            RuntimeCanonicalAuthorityBindingResolver,
            inspect.isfunction,
        )
        if not name.startswith("_")
    }
    assert public_resolver == {"resolve_exact"}
    public_repository = {
        name
        for name, _ in inspect.getmembers(
            RuntimeCanonicalAuthorityBindingRepository,
            inspect.isfunction,
        )
        if not name.startswith("_")
    }
    assert not {
        "latest",
        "current",
        "active",
        "default",
        "first",
        "first_available",
        "alias",
    }.intersection(public_repository)


def test_n4c_23_consumer_has_no_mutation_api() -> None:
    resolver = RuntimeCanonicalAuthorityBindingResolver()
    assert not hasattr(resolver, "store_candidate")
    assert not hasattr(resolver, "admit")
    assert not hasattr(resolver, "supersede")
    assert not hasattr(resolver, "retire")
    with pytest.raises(TypeError):
        resolver.repository = RuntimeCanonicalAuthorityBindingRepository()


def test_n4c_24_production_fixture_import_is_zero() -> None:
    for path in PRODUCTION_PATHS:
        source = path.read_text(encoding="utf-8")
        assert "tests." not in source
        assert "production_fixtures" not in source


def test_n4c_25_static_constitutional_gate() -> None:
    forbidden_fragments = {
        "fallback",
        "mock",
        "stub",
        "shadow",
        "best_effort",
        "silent_degrade",
        "latest",
        "default",
        "first_available",
        "alias",
        "fixture",
        "auto_admission",
        "auto_bootstrap",
    }
    violations: list[str] = []
    for path in PRODUCTION_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Name):
                names.append(node.id)
            elif isinstance(node, ast.Attribute):
                names.append(node.attr)
            elif isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                names.append(node.name)
            for name in names:
                if any(fragment in name.lower() for fragment in forbidden_fragments):
                    violations.append(f"{path.name}:{node.lineno}:{name}")
    assert violations == []
