from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

from .test_durable_authority_contract import (
    _binding_repository,
    _identity_repository,
    _memory_repository,
)
from julia_core.durable_authority.contracts import (
    AuthorityFamily,
    DurableAuthorityPersistenceError,
    canonical_json,
)
from julia_core.durable_authority.filesystem_adapter import (
    ExactLocalFilesystemDurableAuthorityAdapter,
)
from julia_core.durable_authority.serialization import (
    build_identity_envelope,
    build_memory_experience_envelope,
    build_runtime_binding_envelope,
)
from julia_core.durable_authority import (
    restore_identity_repository,
    restore_memory_experience_repository,
    restore_runtime_binding_repository,
)


pytestmark = pytest.mark.skipif(
    not all(hasattr(os, name) for name in ("O_NOFOLLOW", "O_DIRECTORY")),
    reason="POSIX local-filesystem durability primitives are unavailable",
)


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    for family in AuthorityFamily:
        (tmp_path / family.value).mkdir()
    return tmp_path


@pytest.fixture()
def adapter(root: Path) -> ExactLocalFilesystemDurableAuthorityAdapter:
    return ExactLocalFilesystemDurableAuthorityAdapter(root)


@pytest.fixture()
def governed():
    identity, identity_v1, identity_v2 = _identity_repository()
    memory, memory_v1, memory_v2 = _memory_repository()
    binding, binding_v1, binding_v2 = _binding_repository(identity_v1, memory_v1)
    return {
        AuthorityFamily.IDENTITY: {
            "repository": identity,
            "refs": (identity_v1, identity_v2),
            "build": build_identity_envelope,
        },
        AuthorityFamily.MEMORY_EXPERIENCE: {
            "repository": memory,
            "refs": (memory_v1, memory_v2),
            "build": build_memory_experience_envelope,
        },
        AuthorityFamily.RUNTIME_BINDING: {
            "repository": binding,
            "refs": (binding_v1, binding_v2),
            "build": build_runtime_binding_envelope,
        },
    }


@pytest.fixture()
def populated_adapter(adapter, governed):
    for family, lane in governed.items():
        for ref in lane["refs"]:
            adapter.write_exact(lane["build"](lane["repository"].resolve(ref)))
    return adapter


def _object_path(root: Path, family: AuthorityFamily, ref_uri: str) -> Path:
    digest = hashlib.sha256(ref_uri.encode("utf-8")).hexdigest()
    return root / family.value / f"{digest}.envelope.json"


def _raw_envelope(envelope) -> bytes:
    return (canonical_json(envelope.to_dict()) + "\n").encode("utf-8")


@pytest.mark.parametrize("family", list(AuthorityFamily))
def test_exact_write_read_roundtrip(adapter, governed, family):
    lane = governed[family]
    ref = lane["refs"][0]
    envelope = lane["build"](lane["repository"].resolve(ref))
    adapter.write_exact(envelope)
    assert adapter.read_exact(family, ref) == envelope


@pytest.mark.parametrize("family", list(AuthorityFamily))
def test_physical_bytes_are_deterministic(root, tmp_path, governed, family):
    second_root = tmp_path / "second-root"
    second_root.mkdir()
    for item in AuthorityFamily:
        (second_root / item.value).mkdir()
    first = ExactLocalFilesystemDurableAuthorityAdapter(root)
    second = ExactLocalFilesystemDurableAuthorityAdapter(second_root)
    lane = governed[family]
    ref = lane["refs"][0]
    envelope = lane["build"](lane["repository"].resolve(ref))
    first.write_exact(envelope)
    second.write_exact(envelope)
    first_bytes = _object_path(root, family, ref.uri).read_bytes()
    second_bytes = _object_path(second_root, family, ref.uri).read_bytes()
    assert first_bytes == second_bytes == _raw_envelope(envelope)


def test_raw_bytes_are_preserved_exactly(root, adapter, governed):
    family = AuthorityFamily.IDENTITY
    lane = governed[family]
    ref = lane["refs"][0]
    envelope = lane["build"](lane["repository"].resolve(ref))
    expected = _raw_envelope(envelope)
    adapter.write_exact(envelope)
    assert _object_path(root, family, ref.uri).read_bytes() == expected


def test_identical_duplicate_is_idempotent(root, adapter, governed):
    family = AuthorityFamily.RUNTIME_BINDING
    lane = governed[family]
    ref = lane["refs"][0]
    envelope = lane["build"](lane["repository"].resolve(ref))
    path = _object_path(root, family, ref.uri)
    adapter.write_exact(envelope)
    before = path.read_bytes()
    adapter.write_exact(envelope)
    assert path.read_bytes() == before


def test_enumeration_is_deterministic_exact_refs(populated_adapter, governed):
    expected = {
        family: tuple(sorted(ref.uri for ref in lane["refs"]))
        for family, lane in governed.items()
    }
    actual = {
        family: populated_adapter.list_exact_refs(family) for family in AuthorityFamily
    }
    assert actual == expected
    assert populated_adapter.list_exact_refs(AuthorityFamily.IDENTITY) == (
        populated_adapter.list_exact_refs(AuthorityFamily.IDENTITY)
    )


def test_reconstruction_works_through_filesystem_adapter(populated_adapter, governed):
    identity = governed[AuthorityFamily.IDENTITY]["repository"]
    memory = governed[AuthorityFamily.MEMORY_EXPERIENCE]["repository"]
    binding = governed[AuthorityFamily.RUNTIME_BINDING]["repository"]
    restored_identity = restore_identity_repository(populated_adapter)
    restored_memory = restore_memory_experience_repository(populated_adapter)
    restored_binding = restore_runtime_binding_repository(populated_adapter)
    for ref in governed[AuthorityFamily.IDENTITY]["refs"]:
        assert restored_identity.resolve(ref) == identity.resolve(ref)
    for ref in governed[AuthorityFamily.MEMORY_EXPERIENCE]["refs"]:
        assert restored_memory.resolve(ref) == memory.resolve(ref)
    for ref in governed[AuthorityFamily.RUNTIME_BINDING]["refs"]:
        assert restored_binding.resolve(ref) == binding.resolve(ref)


def test_adapter_adds_semantic_authority_delta_zero(populated_adapter, governed):
    before = {
        family: tuple(lane["repository"].resolve(ref) for ref in lane["refs"])
        for family, lane in governed.items()
    }
    assert populated_adapter.read_exact(
        AuthorityFamily.IDENTITY, governed[AuthorityFamily.IDENTITY]["refs"][0]
    )
    after = {
        family: tuple(lane["repository"].resolve(ref) for ref in lane["refs"])
        for family, lane in governed.items()
    }
    assert before == after
    public_surface = dir(populated_adapter)
    for forbidden in ("store_candidate", "admit", "supersede", "retire"):
        assert forbidden not in public_surface


def test_missing_root_fails_closed(tmp_path):
    missing = tmp_path / "missing-root"
    with pytest.raises(DurableAuthorityPersistenceError):
        ExactLocalFilesystemDurableAuthorityAdapter(missing)
    assert not missing.exists()


def test_missing_family_directory_fails_closed(tmp_path):
    root = tmp_path / "partial-root"
    root.mkdir()
    (root / AuthorityFamily.IDENTITY.value).mkdir()
    with pytest.raises(DurableAuthorityPersistenceError):
        ExactLocalFilesystemDurableAuthorityAdapter(root)
    assert not (root / AuthorityFamily.MEMORY_EXPERIENCE.value).exists()
    assert not (root / AuthorityFamily.RUNTIME_BINDING.value).exists()


def test_symlink_object_rejected(root, adapter, governed, tmp_path):
    family = AuthorityFamily.IDENTITY
    lane = governed[family]
    ref = lane["refs"][0]
    target = tmp_path / "target"
    target.write_bytes(b"not-authority\n")
    path = _object_path(root, family, ref.uri)
    path.symlink_to(target)
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.read_exact(family, ref)


def test_nonregular_object_rejected(root, adapter, governed):
    family = AuthorityFamily.MEMORY_EXPERIENCE
    lane = governed[family]
    ref = lane["refs"][0]
    _object_path(root, family, ref.uri).mkdir()
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.read_exact(family, ref)


def test_truncated_file_rejected(root, adapter, governed):
    _corrupt_physical(root, adapter, governed, lambda raw: raw[:-1])
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.read_exact(
            AuthorityFamily.IDENTITY, governed[AuthorityFamily.IDENTITY]["refs"][0]
        )


def test_invalid_utf8_rejected(root, adapter, governed):
    _corrupt_physical(root, adapter, governed, lambda raw: b"\xff\n")
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.read_exact(
            AuthorityFamily.IDENTITY, governed[AuthorityFamily.IDENTITY]["refs"][0]
        )


def test_invalid_json_rejected(root, adapter, governed):
    _corrupt_physical(root, adapter, governed, lambda raw: b"{\n")
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.read_exact(
            AuthorityFamily.IDENTITY, governed[AuthorityFamily.IDENTITY]["refs"][0]
        )


def test_extra_lf_rejected(root, adapter, governed):
    _corrupt_physical(root, adapter, governed, lambda raw: raw + b"\n")
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.read_exact(
            AuthorityFamily.IDENTITY, governed[AuthorityFamily.IDENTITY]["refs"][0]
        )


def test_payload_digest_corruption_rejected(root, adapter, governed):
    def corrupt(raw: bytes) -> bytes:
        data = json.loads(raw)
        data["serialized_payload"] = canonical_json({"corrupted": True})
        return (canonical_json(data) + "\n").encode("utf-8")

    _corrupt_physical(root, adapter, governed, corrupt)
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.read_exact(
            AuthorityFamily.IDENTITY, governed[AuthorityFamily.IDENTITY]["refs"][0]
        )


def test_envelope_digest_corruption_rejected(root, adapter, governed):
    def corrupt(raw: bytes) -> bytes:
        data = json.loads(raw)
        data["envelope_digest"] = "0" * 64
        return (canonical_json(data) + "\n").encode("utf-8")

    _corrupt_physical(root, adapter, governed, corrupt)
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.read_exact(
            AuthorityFamily.IDENTITY, governed[AuthorityFamily.IDENTITY]["refs"][0]
        )


def test_wrong_family_rejected(root, adapter, governed):
    identity_lane = governed[AuthorityFamily.IDENTITY]
    ref = identity_lane["refs"][0]
    envelope = identity_lane["build"](identity_lane["repository"].resolve(ref))
    target = _object_path(root, AuthorityFamily.MEMORY_EXPERIENCE, ref.uri)
    target.write_bytes(_raw_envelope(envelope))
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.read_exact(AuthorityFamily.MEMORY_EXPERIENCE, ref)


def test_wrong_exact_ref_rejected(root, adapter, governed):
    lane = governed[AuthorityFamily.IDENTITY]
    adapter.write_exact(lane["build"](lane["repository"].resolve(lane["refs"][0])))
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.read_exact(AuthorityFamily.IDENTITY, lane["refs"][1])


def test_wrong_path_hash_rejected(root, adapter, governed):
    family = AuthorityFamily.IDENTITY
    lane = governed[family]
    ref = lane["refs"][0]
    path = _object_path(root, family, ref.uri)
    adapter.write_exact(lane["build"](lane["repository"].resolve(ref)))
    path.rename(path.with_name(f"{'0' * 64}.envelope.json"))
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.list_exact_refs(family)


def test_conflicting_duplicate_rejected(root, adapter, governed):
    family = AuthorityFamily.RUNTIME_BINDING
    lane = governed[family]
    ref = lane["refs"][0]
    envelope = lane["build"](lane["repository"].resolve(ref))
    adapter.write_exact(envelope)
    path = _object_path(root, family, ref.uri)
    path.write_bytes(path.read_bytes()[:-1])
    with pytest.raises(DurableAuthorityPersistenceError) as captured:
        adapter.write_exact(envelope)
    assert captured.value.code.value == "DUPLICATE_CONFLICT"


def test_unexpected_enumeration_entry_rejects_whole(root, adapter, governed):
    family = AuthorityFamily.IDENTITY
    lane = governed[family]
    ref = lane["refs"][0]
    adapter.write_exact(lane["build"](lane["repository"].resolve(ref)))
    (root / family.value / "unexpected.txt").write_text("unexpected")
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.list_exact_refs(family)


def test_corrupt_enumeration_member_rejects_whole(root, adapter, governed):
    family = AuthorityFamily.IDENTITY
    lane = governed[family]
    for ref in lane["refs"]:
        adapter.write_exact(lane["build"](lane["repository"].resolve(ref)))
    path = _object_path(root, family, lane["refs"][0].uri)
    path.write_bytes(path.read_bytes()[:-1])
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.list_exact_refs(family)


def test_temporary_file_is_never_authority(root, adapter, governed):
    family = AuthorityFamily.IDENTITY
    lane = governed[family]
    ref = lane["refs"][0]
    envelope = lane["build"](lane["repository"].resolve(ref))
    (root / family.value / ".temporary.envelope.json").write_bytes(
        _raw_envelope(envelope)
    )
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.list_exact_refs(family)
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.read_exact(family, ref)


def test_no_implicit_directory_creation(root, adapter, governed):
    family = AuthorityFamily.IDENTITY
    lane = governed[family]
    ref = lane["refs"][0]
    (root / family.value).rmdir()
    with pytest.raises(DurableAuthorityPersistenceError):
        adapter.write_exact(lane["build"](lane["repository"].resolve(ref)))
    assert not (root / family.value).exists()


def test_no_selection_or_alias_surface():
    module = sys.modules[ExactLocalFilesystemDurableAuthorityAdapter.__module__]
    text = Path(module.__file__).read_text(encoding="utf-8")
    forbidden = (
        "fallback",
        "default",
        "latest",
        "current",
        "active",
        "first",
        "best",
        "alias",
        "repair",
        "skip",
        "ignore",
        "except Exception",
        "mkdir",
        "replace",
        "pickle",
        "mock",
        "stub",
        "shadow",
    )
    assert not any(item in text for item in forbidden)


def _corrupt_physical(root, adapter, governed, corrupt) -> None:
    family = AuthorityFamily.IDENTITY
    lane = governed[family]
    ref = lane["refs"][0]
    envelope = lane["build"](lane["repository"].resolve(ref))
    adapter.write_exact(envelope)
    path = _object_path(root, family, ref.uri)
    path.write_bytes(corrupt(path.read_bytes()))
