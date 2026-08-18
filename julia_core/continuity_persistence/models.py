"""DIA-7 R2.1 — Runtime / Persistence continuity binding contract.

Persistence stores and reloads continuity trust artifacts. It does not create,
repair, reinterpret, upgrade, or recover continuity truth. Persisted bytes are
untrusted until deserialized, reconstructed, and cross-validated.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol, runtime_checkable

from julia_core.assistant_continuity import (
    AssistantContinuitySessionBinding,
    AssistantContinuityStatePackage,
    ContinuityStateBindingStore,
    StrictAssistantContinuityBinder,
)
from julia_core.continuity_projection import ContinuityState

CANONICAL_VERSION = "dia7-continuity-persistence-r21-v1"
PACKAGE_RECORD_DOMAIN_SEPARATOR = "julia_core.continuity_persistence.package_record.v1"
BINDING_RECORD_DOMAIN_SEPARATOR = "julia_core.continuity_persistence.binding_record.v1"
SNAPSHOT_DOMAIN_SEPARATOR = "julia_core.continuity_persistence.snapshot.v1"
TRANSACTION_DOMAIN_SEPARATOR = "julia_core.continuity_persistence.transaction.v1"
PACKAGE_RECORD_ALGORITHM_REVISION = "dia7-r21-package-record-v1"
BINDING_RECORD_ALGORITHM_REVISION = "dia7-r21-binding-record-v1"
SNAPSHOT_ALGORITHM_REVISION = "dia7-r21-snapshot-v1"


def _require_non_empty_str(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty str")


def _require_tuple(name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")


def _require_sha256_hex(name: str, value: object) -> None:
    _require_non_empty_str(name, value)
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{name} must be a 64-character lowercase SHA-256 hex digest")


def _frame(value: str) -> bytes:
    _require_non_empty_str("canonical field", value)
    encoded = value.encode("utf-8")
    return str(len(encoded)).encode("ascii") + b":" + encoded + b"\n"


def _field(name: str, value: str) -> bytes:
    return _frame(name) + _frame(value)


def _digest_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def _json_bytes(data: dict[str, object]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True, init=False)
class PersistedContinuityPackageRecord:
    session_id: str
    continuity_state_digest: str
    source_graph_digest: str
    projection_policy_fingerprint: str
    package_digest: str
    continuity_state_payload_sha256: str
    package_record_digest: str
    schema_version: str

    def __init__(self, session_id: str, package: AssistantContinuityStatePackage) -> None:
        _require_non_empty_str("PersistedContinuityPackageRecord.session_id", session_id)
        if type(package) is not AssistantContinuityStatePackage:
            raise ValueError("PersistedContinuityPackageRecord requires exact AssistantContinuityStatePackage")
        _validate_package_current(package)
        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "continuity_state_digest", package.continuity_state_digest)
        object.__setattr__(self, "source_graph_digest", package.source_graph_digest)
        object.__setattr__(self, "projection_policy_fingerprint", package.projection_policy_fingerprint)
        object.__setattr__(self, "package_digest", package.package_digest)
        object.__setattr__(self, "continuity_state_payload_sha256", _digest_hex(package.continuity_state.semantic_canonical_bytes()))
        object.__setattr__(self, "schema_version", CANONICAL_VERSION)
        object.__setattr__(self, "package_record_digest", _digest_hex(self.semantic_canonical_bytes(include_digest=False)))

    def semantic_canonical_bytes(self, *, include_digest: bool = True) -> bytes:
        out = (
            _field("package_record.domain", PACKAGE_RECORD_DOMAIN_SEPARATOR)
            + _field("package_record.schema_version", self.schema_version)
            + _field("package_record.algorithm_revision", PACKAGE_RECORD_ALGORITHM_REVISION)
            + _field("package_record.session_id", self.session_id)
            + _field("package_record.state_digest", self.continuity_state_digest)
            + _field("package_record.source_graph_digest", self.source_graph_digest)
            + _field("package_record.policy_fingerprint", self.projection_policy_fingerprint)
            + _field("package_record.package_digest", self.package_digest)
            + _field("package_record.state_payload_sha256", self.continuity_state_payload_sha256)
        )
        if include_digest:
            out += _field("package_record.digest", self.package_record_digest)
        return out

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "continuity_state_digest": self.continuity_state_digest,
            "source_graph_digest": self.source_graph_digest,
            "projection_policy_fingerprint": self.projection_policy_fingerprint,
            "package_digest": self.package_digest,
            "continuity_state_payload_sha256": self.continuity_state_payload_sha256,
            "package_record_digest": self.package_record_digest,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "PersistedContinuityPackageRecord":
        obj = cls.__new__(cls)
        for key in (
            "session_id",
            "continuity_state_digest",
            "source_graph_digest",
            "projection_policy_fingerprint",
            "package_digest",
            "continuity_state_payload_sha256",
            "package_record_digest",
            "schema_version",
        ):
            value = data.get(key)
            if type(value) is not str:
                raise ValueError(f"package record {key} must be str")
            object.__setattr__(obj, key, value)
        _validate_package_record_integrity(obj)
        return obj


@dataclass(frozen=True, init=False)
class PersistedContinuityBindingRecord:
    storage_key: str
    serialized_session_id: str
    continuity_state_digest: str
    source_graph_digest: str
    projection_policy_fingerprint: str
    package_digest: str
    binding_digest: str
    binding_record_digest: str
    schema_version: str

    def __init__(self, storage_key: str, binding: AssistantContinuitySessionBinding) -> None:
        _require_non_empty_str("PersistedContinuityBindingRecord.storage_key", storage_key)
        _validate_binding_current(binding)
        if storage_key != binding.session_id:
            raise ValueError("storage key and binding session mismatch")
        object.__setattr__(self, "storage_key", storage_key)
        object.__setattr__(self, "serialized_session_id", binding.session_id)
        object.__setattr__(self, "continuity_state_digest", binding.continuity_state_digest)
        object.__setattr__(self, "source_graph_digest", binding.source_graph_digest)
        object.__setattr__(self, "projection_policy_fingerprint", binding.projection_policy_fingerprint)
        object.__setattr__(self, "package_digest", binding.package_digest)
        object.__setattr__(self, "binding_digest", binding.binding_digest)
        object.__setattr__(self, "schema_version", CANONICAL_VERSION)
        object.__setattr__(self, "binding_record_digest", _digest_hex(self.semantic_canonical_bytes(include_digest=False)))

    def semantic_canonical_bytes(self, *, include_digest: bool = True) -> bytes:
        out = (
            _field("binding_record.domain", BINDING_RECORD_DOMAIN_SEPARATOR)
            + _field("binding_record.schema_version", self.schema_version)
            + _field("binding_record.algorithm_revision", BINDING_RECORD_ALGORITHM_REVISION)
            + _field("binding_record.storage_key", self.storage_key)
            + _field("binding_record.serialized_session_id", self.serialized_session_id)
            + _field("binding_record.state_digest", self.continuity_state_digest)
            + _field("binding_record.source_graph_digest", self.source_graph_digest)
            + _field("binding_record.policy_fingerprint", self.projection_policy_fingerprint)
            + _field("binding_record.package_digest", self.package_digest)
            + _field("binding_record.binding_digest", self.binding_digest)
        )
        if include_digest:
            out += _field("binding_record.digest", self.binding_record_digest)
        return out

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "storage_key": self.storage_key,
            "serialized_session_id": self.serialized_session_id,
            "continuity_state_digest": self.continuity_state_digest,
            "source_graph_digest": self.source_graph_digest,
            "projection_policy_fingerprint": self.projection_policy_fingerprint,
            "package_digest": self.package_digest,
            "binding_digest": self.binding_digest,
            "binding_record_digest": self.binding_record_digest,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "PersistedContinuityBindingRecord":
        obj = cls.__new__(cls)
        for key in (
            "storage_key",
            "serialized_session_id",
            "continuity_state_digest",
            "source_graph_digest",
            "projection_policy_fingerprint",
            "package_digest",
            "binding_digest",
            "binding_record_digest",
            "schema_version",
        ):
            value = data.get(key)
            if type(value) is not str:
                raise ValueError(f"binding record {key} must be str")
            object.__setattr__(obj, key, value)
        _validate_binding_record_integrity(obj)
        return obj


@dataclass(frozen=True, init=False)
class ContinuityRuntimeSnapshot:
    storage_key: str
    package_record: PersistedContinuityPackageRecord
    binding_record: PersistedContinuityBindingRecord
    snapshot_digest: str
    schema_version: str

    def __init__(self, storage_key: str, package_record: PersistedContinuityPackageRecord, binding_record: PersistedContinuityBindingRecord) -> None:
        _require_non_empty_str("ContinuityRuntimeSnapshot.storage_key", storage_key)
        _validate_package_record_integrity(package_record)
        _validate_binding_record_integrity(binding_record)
        _assert_records_cross_bound(storage_key, package_record, binding_record)
        object.__setattr__(self, "storage_key", storage_key)
        object.__setattr__(self, "package_record", package_record)
        object.__setattr__(self, "binding_record", binding_record)
        object.__setattr__(self, "schema_version", CANONICAL_VERSION)
        object.__setattr__(self, "snapshot_digest", _digest_hex(self.semantic_canonical_bytes(include_digest=False)))

    def semantic_canonical_bytes(self, *, include_digest: bool = True) -> bytes:
        out = (
            _field("snapshot.domain", SNAPSHOT_DOMAIN_SEPARATOR)
            + _field("snapshot.schema_version", self.schema_version)
            + _field("snapshot.algorithm_revision", SNAPSHOT_ALGORITHM_REVISION)
            + _field("snapshot.storage_key", self.storage_key)
            + _field("snapshot.package_record", self.package_record.semantic_canonical_bytes().decode("utf-8"))
            + _field("snapshot.binding_record", self.binding_record.semantic_canonical_bytes().decode("utf-8"))
        )
        if include_digest:
            out += _field("snapshot.digest", self.snapshot_digest)
        return out

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "storage_key": self.storage_key,
            "package_record": self.package_record.to_dict(),
            "binding_record": self.binding_record.to_dict(),
            "snapshot_digest": self.snapshot_digest,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ContinuityRuntimeSnapshot":
        if data.get("schema_version") != CANONICAL_VERSION:
            raise ValueError("snapshot schema_version is frozen")
        storage_key = data.get("storage_key")
        if type(storage_key) is not str:
            raise ValueError("snapshot storage_key must be str")
        package_data = data.get("package_record")
        binding_data = data.get("binding_record")
        if type(package_data) is not dict or type(binding_data) is not dict:
            raise ValueError("snapshot records must be objects")
        package_record = PersistedContinuityPackageRecord.from_dict(package_data)
        binding_record = PersistedContinuityBindingRecord.from_dict(binding_data)
        obj = cls(storage_key, package_record, binding_record)
        stored_digest = data.get("snapshot_digest")
        if type(stored_digest) is not str:
            raise ValueError("snapshot_digest must be str")
        if obj.snapshot_digest != stored_digest:
            raise ValueError("snapshot digest mismatch")
        return obj


@dataclass(frozen=True)
class ContinuityPersistenceTransaction:
    transaction_id: str
    snapshot_digest: str
    status: str

    def __post_init__(self) -> None:
        _require_non_empty_str("ContinuityPersistenceTransaction.transaction_id", self.transaction_id)
        _require_sha256_hex("ContinuityPersistenceTransaction.snapshot_digest", self.snapshot_digest)
        if self.status not in ("prepared", "published", "validated"):
            raise ValueError("ContinuityPersistenceTransaction.status is not supported")

    def canonical_bytes(self) -> bytes:
        return (
            _field("transaction.domain", TRANSACTION_DOMAIN_SEPARATOR)
            + _field("transaction.id", self.transaction_id)
            + _field("transaction.snapshot_digest", self.snapshot_digest)
            + _field("transaction.status", self.status)
        )


@dataclass(frozen=True)
class ContinuityPersistenceAudit:
    session_id: str
    snapshot_digest: str
    diagnostics: tuple[str, ...]
    created_at: str

    def __post_init__(self) -> None:
        _require_non_empty_str("ContinuityPersistenceAudit.session_id", self.session_id)
        _require_sha256_hex("ContinuityPersistenceAudit.snapshot_digest", self.snapshot_digest)
        _require_tuple("ContinuityPersistenceAudit.diagnostics", self.diagnostics)
        if not all(type(item) is str for item in self.diagnostics):
            raise ValueError("ContinuityPersistenceAudit.diagnostics must contain str only")
        _require_non_empty_str("ContinuityPersistenceAudit.created_at", self.created_at)


class ContinuityPersistenceStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def storage_path(self, session_id: str) -> Path:
        _require_non_empty_str("ContinuityPersistenceStore.session_id", session_id)
        if "/" in session_id or "\\" in session_id or session_id in (".", ".."):
            raise ValueError("session_id is not a safe storage key")
        return self.root / f"{session_id}.snapshot.json"

    def write_snapshot(self, snapshot: ContinuityRuntimeSnapshot) -> ContinuityPersistenceTransaction:
        _validate_snapshot_integrity(snapshot)
        path = self.storage_path(snapshot.storage_key)
        existing = self._read_if_exists(path)
        if existing is not None:
            if existing.snapshot_digest == snapshot.snapshot_digest:
                return ContinuityPersistenceTransaction(f"tx-{snapshot.snapshot_digest}", snapshot.snapshot_digest, "validated")
            raise ValueError("same session cannot persist different continuity binding")
        payload = _json_bytes(snapshot.to_dict())
        with NamedTemporaryFile("wb", dir=self.root, prefix=f".{snapshot.storage_key}.", suffix=".tmp", delete=False) as tmp:
            tmp.write(payload)
            tmp_path = Path(tmp.name)
        tmp_snapshot = self._read_snapshot_path(tmp_path)
        if tmp_snapshot.snapshot_digest != snapshot.snapshot_digest:
            tmp_path.unlink(missing_ok=True)
            raise ValueError("prepared snapshot read-back mismatch")
        tmp_path.replace(path)
        read_back = self._read_snapshot_path(path)
        if read_back.snapshot_digest != snapshot.snapshot_digest:
            raise ValueError("published snapshot read-back mismatch")
        return ContinuityPersistenceTransaction(f"tx-{snapshot.snapshot_digest}", snapshot.snapshot_digest, "published")

    def read_snapshot(self, session_id: str) -> ContinuityRuntimeSnapshot:
        path = self.storage_path(session_id)
        if not path.exists():
            raise ValueError("no persisted continuity snapshot for session")
        snapshot = self._read_snapshot_path(path)
        if snapshot.storage_key != session_id:
            raise ValueError("snapshot storage key lookup mismatch")
        return snapshot

    def _read_if_exists(self, path: Path) -> ContinuityRuntimeSnapshot | None:
        if not path.exists():
            return None
        return self._read_snapshot_path(path)

    def _read_snapshot_path(self, path: Path) -> ContinuityRuntimeSnapshot:
        try:
            data = json.loads(path.read_bytes().decode("utf-8"))
        except Exception as e:
            raise ValueError("persisted snapshot bytes are invalid") from e
        if type(data) is not dict:
            raise ValueError("persisted snapshot root must be object")
        return ContinuityRuntimeSnapshot.from_dict(data)


class ContinuityRestartLoader:
    def __init__(self, store: ContinuityPersistenceStore) -> None:
        if type(store) is not ContinuityPersistenceStore:
            raise ValueError("ContinuityRestartLoader requires exact ContinuityPersistenceStore")
        self.store = store

    def load(self, session_id: str) -> ContinuityRuntimeSnapshot:
        return self.store.read_snapshot(session_id)


class ContinuityReplayGuard:
    def validate(self, snapshot: ContinuityRuntimeSnapshot, package: AssistantContinuityStatePackage, binding: AssistantContinuitySessionBinding) -> AssistantContinuitySessionBinding:
        _validate_snapshot_integrity(snapshot)
        _validate_package_current(package)
        _validate_binding_current(binding)
        _assert_snapshot_matches_runtime(snapshot, package, binding)
        runtime_store = ContinuityStateBindingStore()
        runtime_store.save(binding)
        return runtime_store.replay_validate(snapshot.storage_key, package)


class StrictContinuityPersistenceRuntime:
    def __init__(self, store: ContinuityPersistenceStore) -> None:
        if type(store) is not ContinuityPersistenceStore:
            raise ValueError("StrictContinuityPersistenceRuntime requires exact ContinuityPersistenceStore")
        self.store = store

    def persist(self, session_id: str, package: AssistantContinuityStatePackage, binding: AssistantContinuitySessionBinding) -> ContinuityPersistenceTransaction:
        _validate_package_current(package)
        _validate_binding_current(binding)
        if session_id != binding.session_id:
            raise ValueError("runtime session and binding session mismatch")
        StrictAssistantContinuityBinder().response_context(binding, package)
        package_record = PersistedContinuityPackageRecord(session_id, package)
        binding_record = PersistedContinuityBindingRecord(session_id, binding)
        snapshot = ContinuityRuntimeSnapshot(session_id, package_record, binding_record)
        return self.store.write_snapshot(snapshot)

    def restart(self, session_id: str) -> ContinuityRuntimeSnapshot:
        return ContinuityRestartLoader(self.store).load(session_id)


@runtime_checkable
class ContinuityPersistenceRuntime(Protocol):
    def persist(self, session_id: str, package: AssistantContinuityStatePackage, binding: AssistantContinuitySessionBinding) -> ContinuityPersistenceTransaction:
        ...

    def restart(self, session_id: str) -> ContinuityRuntimeSnapshot:
        ...


def _validate_package_current(package: AssistantContinuityStatePackage) -> None:
    if type(package) is not AssistantContinuityStatePackage:
        raise ValueError("expected exact AssistantContinuityStatePackage")
    if type(package.continuity_state) is not ContinuityState:
        raise ValueError("package continuity_state must be exact ContinuityState")
    if _digest_hex(package.continuity_state.semantic_canonical_bytes(include_digest=False)) != package.continuity_state_digest:
        raise ValueError("package continuity state digest mismatch")
    if package.continuity_state.continuity_state_digest != package.continuity_state_digest:
        raise ValueError("package stale continuity state digest")
    if package.source_graph_digest != package.continuity_state.source_graph_digest:
        raise ValueError("package source graph digest mismatch")
    if package.projection_policy_fingerprint != package.continuity_state.projection_policy_fingerprint:
        raise ValueError("package projection policy fingerprint mismatch")
    if package.active_claims != package.continuity_state.active_claims:
        raise ValueError("package active claims mismatch")
    if package.unresolved_conflicts != package.continuity_state.unresolved_conflicts:
        raise ValueError("package unresolved conflicts mismatch")
    if _digest_hex(package.semantic_canonical_bytes(include_digest=False)) != package.package_digest:
        raise ValueError("package digest mismatch")


def _validate_binding_current(binding: AssistantContinuitySessionBinding) -> None:
    if type(binding) is not AssistantContinuitySessionBinding:
        raise ValueError("expected exact AssistantContinuitySessionBinding")
    _require_non_empty_str("binding.session_id", binding.session_id)
    _require_sha256_hex("binding.continuity_state_digest", binding.continuity_state_digest)
    _require_sha256_hex("binding.source_graph_digest", binding.source_graph_digest)
    _require_sha256_hex("binding.projection_policy_fingerprint", binding.projection_policy_fingerprint)
    _require_sha256_hex("binding.package_digest", binding.package_digest)
    if _digest_hex(binding.semantic_canonical_bytes(include_digest=False)) != binding.binding_digest:
        raise ValueError("binding digest mismatch")


def _validate_package_record_integrity(record: PersistedContinuityPackageRecord) -> None:
    if type(record) is not PersistedContinuityPackageRecord:
        raise ValueError("expected exact PersistedContinuityPackageRecord")
    _require_non_empty_str("package_record.session_id", record.session_id)
    _require_sha256_hex("package_record.continuity_state_digest", record.continuity_state_digest)
    _require_sha256_hex("package_record.source_graph_digest", record.source_graph_digest)
    _require_sha256_hex("package_record.projection_policy_fingerprint", record.projection_policy_fingerprint)
    _require_sha256_hex("package_record.package_digest", record.package_digest)
    _require_sha256_hex("package_record.continuity_state_payload_sha256", record.continuity_state_payload_sha256)
    if record.schema_version != CANONICAL_VERSION:
        raise ValueError("package record schema_version is frozen")
    if _digest_hex(record.semantic_canonical_bytes(include_digest=False)) != record.package_record_digest:
        raise ValueError("package record digest mismatch")


def _validate_binding_record_integrity(record: PersistedContinuityBindingRecord) -> None:
    if type(record) is not PersistedContinuityBindingRecord:
        raise ValueError("expected exact PersistedContinuityBindingRecord")
    _require_non_empty_str("binding_record.storage_key", record.storage_key)
    _require_non_empty_str("binding_record.serialized_session_id", record.serialized_session_id)
    if record.storage_key != record.serialized_session_id:
        raise ValueError("storage key serialized session mismatch")
    _require_sha256_hex("binding_record.continuity_state_digest", record.continuity_state_digest)
    _require_sha256_hex("binding_record.source_graph_digest", record.source_graph_digest)
    _require_sha256_hex("binding_record.projection_policy_fingerprint", record.projection_policy_fingerprint)
    _require_sha256_hex("binding_record.package_digest", record.package_digest)
    _require_sha256_hex("binding_record.binding_digest", record.binding_digest)
    if record.schema_version != CANONICAL_VERSION:
        raise ValueError("binding record schema_version is frozen")
    if _digest_hex(record.semantic_canonical_bytes(include_digest=False)) != record.binding_record_digest:
        raise ValueError("binding record digest mismatch")


def _assert_records_cross_bound(storage_key: str, package_record: PersistedContinuityPackageRecord, binding_record: PersistedContinuityBindingRecord) -> None:
    if storage_key != package_record.session_id or storage_key != binding_record.storage_key or storage_key != binding_record.serialized_session_id:
        raise ValueError("snapshot storage/session identity mismatch")
    if package_record.continuity_state_digest != binding_record.continuity_state_digest:
        raise ValueError("snapshot state digest mismatch")
    if package_record.source_graph_digest != binding_record.source_graph_digest:
        raise ValueError("snapshot source graph digest mismatch")
    if package_record.projection_policy_fingerprint != binding_record.projection_policy_fingerprint:
        raise ValueError("snapshot policy fingerprint mismatch")
    if package_record.package_digest != binding_record.package_digest:
        raise ValueError("snapshot package digest mismatch")


def _validate_snapshot_integrity(snapshot: ContinuityRuntimeSnapshot) -> None:
    if type(snapshot) is not ContinuityRuntimeSnapshot:
        raise ValueError("expected exact ContinuityRuntimeSnapshot")
    _validate_package_record_integrity(snapshot.package_record)
    _validate_binding_record_integrity(snapshot.binding_record)
    _assert_records_cross_bound(snapshot.storage_key, snapshot.package_record, snapshot.binding_record)
    if snapshot.schema_version != CANONICAL_VERSION:
        raise ValueError("snapshot schema_version is frozen")
    if _digest_hex(snapshot.semantic_canonical_bytes(include_digest=False)) != snapshot.snapshot_digest:
        raise ValueError("snapshot digest mismatch")


def _assert_snapshot_matches_runtime(snapshot: ContinuityRuntimeSnapshot, package: AssistantContinuityStatePackage, binding: AssistantContinuitySessionBinding) -> None:
    if snapshot.storage_key != binding.session_id:
        raise ValueError("snapshot runtime session mismatch")
    if snapshot.package_record.continuity_state_digest != package.continuity_state_digest or snapshot.binding_record.continuity_state_digest != binding.continuity_state_digest:
        raise ValueError("snapshot runtime state digest mismatch")
    if snapshot.package_record.source_graph_digest != package.source_graph_digest or snapshot.binding_record.source_graph_digest != binding.source_graph_digest:
        raise ValueError("snapshot runtime source graph mismatch")
    if snapshot.package_record.projection_policy_fingerprint != package.projection_policy_fingerprint or snapshot.binding_record.projection_policy_fingerprint != binding.projection_policy_fingerprint:
        raise ValueError("snapshot runtime policy mismatch")
    if snapshot.package_record.package_digest != package.package_digest or snapshot.binding_record.package_digest != binding.package_digest:
        raise ValueError("snapshot runtime package mismatch")
    if snapshot.binding_record.binding_digest != binding.binding_digest:
        raise ValueError("snapshot runtime binding mismatch")
