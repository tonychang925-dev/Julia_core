"""Exact local-filesystem durable authority adapter.

The filesystem is a non-authoritative physical adapter, not the selected
production storage architecture. All governed-object semantics remain owned by
the accepted durable-authority contract.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
from pathlib import Path

from .contracts import (
    AuthorityFamily,
    DurableAuthorityEnvelope,
    DurableAuthorityErrorCode,
    DurableAuthorityPersistenceError,
    canonical_json,
)
from .serialization import envelope_from_dict, validate_envelope_semantics


_ENVELOPE_SUFFIX = ".envelope.json"
_FAMILIES = tuple(member.value for member in AuthorityFamily)
_READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW
_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


class ExactLocalFilesystemDurableAuthorityAdapter:
    """Immutable exact-ref envelope store for one explicitly supplied root."""

    __slots__ = ("_family_paths", "_root")

    def __init__(self, root: str | Path) -> None:
        if not isinstance(root, (str, Path)) or not str(root):
            raise _storage_failure("durable authority root must be explicitly supplied")
        supplied_root = Path(root)
        if not supplied_root.is_absolute():
            raise _storage_failure("durable authority root must be absolute")
        root_path = supplied_root
        _require_directory(root_path, "durable authority root")
        family_paths = {}
        for family_name in _FAMILIES:
            family_path = root_path / family_name
            _require_directory(family_path, f"durable authority family {family_name}")
            family_paths[family_name] = family_path
        object.__setattr__(self, "_root", root_path)
        object.__setattr__(self, "_family_paths", family_paths)

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("durable filesystem adapter bindings are immutable")

    def __delattr__(self, name: str) -> None:
        raise TypeError("durable filesystem adapter bindings are immutable")

    def read_exact(
        self,
        authority_family: AuthorityFamily,
        ref: object,
    ) -> DurableAuthorityEnvelope:
        family = _require_family(authority_family)
        ref_uri = _require_ref_uri(ref)
        expected_digest = _ref_digest(ref_uri)
        path = self._family_paths[family.value] / _object_name(expected_digest)
        envelope = _read_validated(path, family, expected_digest)
        if envelope.authority_object_ref != ref_uri:
            raise _storage_failure(
                "durable authority path belongs to another exact ref"
            )
        return envelope

    def list_exact_refs(self, authority_family: AuthorityFamily) -> tuple[str, ...]:
        family = _require_family(authority_family)
        directory = self._family_paths[family.value]
        refs = []
        try:
            entries = list(os.scandir(directory))
        except OSError as error:
            raise _storage_failure(
                "durable authority family cannot be enumerated"
            ) from error
        for entry in entries:
            expected_digest = _filename_digest(entry.name)
            if expected_digest is None:
                raise _storage_failure(
                    "durable authority family contains an unexpected entry"
                )
            envelope = _read_validated(directory / entry.name, family, expected_digest)
            refs.append(envelope.authority_object_ref)
        return tuple(sorted(refs))

    def write_exact(self, envelope: DurableAuthorityEnvelope) -> None:
        if type(envelope) is not DurableAuthorityEnvelope:
            raise _storage_failure("durable write requires an exact envelope object")
        validate_envelope_semantics(envelope)
        family = envelope.authority_family
        directory = self._family_paths[family.value]
        final_path = directory / _object_name(
            _ref_digest(envelope.authority_object_ref)
        )
        requested_bytes = _physical_bytes(envelope)

        if _path_exists(final_path):
            existing_bytes = _read_raw_bytes(final_path)
            _require_exact_bytes(existing_bytes, requested_bytes)
            _read_validated(
                final_path, family, _ref_digest(envelope.authority_object_ref)
            )
            return

        temporary_path = directory / (
            f".{os.getpid()}.{secrets.token_hex(16)}{_ENVELOPE_SUFFIX}"
        )
        descriptor = _create_exclusive_file(temporary_path)
        try:
            try:
                _write_all(descriptor, requested_bytes)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except BaseException as error:
            try:
                os.unlink(temporary_path)
                _fsync_directory(directory)
            except OSError:
                raise error from None
            raise

        try:
            try:
                os.link(temporary_path, final_path, follow_symlinks=False)
                _fsync_directory(directory)
            except FileExistsError:
                existing_bytes = _read_raw_bytes(final_path)
                _require_exact_bytes(existing_bytes, requested_bytes)
                _read_validated(
                    final_path, family, _ref_digest(envelope.authority_object_ref)
                )
            finally:
                try:
                    os.unlink(temporary_path)
                    _fsync_directory(directory)
                except OSError as cleanup_error:
                    raise _storage_failure(
                        "durable authority temporary object cleanup failed"
                    ) from cleanup_error
        except OSError as error:
            raise _storage_failure("durable authority write failed") from error


def _physical_bytes(envelope: DurableAuthorityEnvelope) -> bytes:
    return (canonical_json(envelope.to_dict()) + "\n").encode("utf-8")


def _object_name(ref_digest: str) -> str:
    return f"{ref_digest}{_ENVELOPE_SUFFIX}"


def _ref_digest(ref_uri: str) -> str:
    return hashlib.sha256(ref_uri.encode("utf-8")).hexdigest()


def _filename_digest(name: str) -> str | None:
    if not name.endswith(_ENVELOPE_SUFFIX) or name.startswith("."):
        return None
    digest = name[: -len(_ENVELOPE_SUFFIX)]
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        return None
    return digest


def _read_validated(
    path: Path, family: AuthorityFamily, expected_path_digest: str
) -> DurableAuthorityEnvelope:
    raw = _read_raw_bytes(path)
    if (
        len(raw) < 2
        or not raw.endswith(b"\n")
        or raw.endswith(b"\n\n")
        or raw[:-1].endswith(b"\n")
    ):
        raise _storage_failure("durable authority physical encoding is malformed")
    try:
        text = raw[:-1].decode("utf-8")
        decoded = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_names,
            parse_constant=_reject_non_standard_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise _storage_failure("durable authority bytes are not strict JSON") from error
    try:
        envelope = envelope_from_dict(decoded)
        validate_envelope_semantics(envelope)
    except DurableAuthorityPersistenceError:
        raise
    except (TypeError, ValueError) as error:
        raise _storage_failure("durable authority envelope is malformed") from error
    if (
        envelope.authority_family is not family
        or _ref_digest(envelope.authority_object_ref) != expected_path_digest
        or _physical_bytes(envelope) != raw
    ):
        raise _storage_failure("durable authority object address is inconsistent")
    return envelope


def _read_raw_bytes(path: Path) -> bytes:
    try:
        descriptor = os.open(path, _READ_FLAGS)
    except OSError as error:
        raise _storage_failure("durable authority object is unavailable") from error
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise _storage_failure("durable authority object is not a regular file")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
    except OSError as error:
        raise _storage_failure("durable authority object cannot be read") from error
    finally:
        os.close(descriptor)
    return b"".join(chunks)


def _write_all(descriptor: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise _storage_failure("durable authority physical write was incomplete")
        view = view[written:]


def _create_exclusive_file(path: Path) -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        return os.open(path, flags, 0o600)
    except OSError as error:
        raise _storage_failure(
            "durable authority temporary object cannot be created"
        ) from error


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, _DIRECTORY_FLAGS)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _require_directory(path: Path, label: str) -> None:
    try:
        descriptor = os.open(path, _DIRECTORY_FLAGS)
    except OSError as error:
        raise _storage_failure(f"{label} is unavailable") from error
    try:
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise _storage_failure(f"{label} is not a directory")
    finally:
        os.close(descriptor)


def _require_family(family: object) -> AuthorityFamily:
    if type(family) is not AuthorityFamily:
        raise _storage_failure("durable authority family must be exact")
    return family


def _require_ref_uri(ref: object) -> str:
    ref_uri = getattr(ref, "uri", None)
    if type(ref_uri) is not str or not ref_uri:
        raise _storage_failure("durable authority lookup requires an exact typed ref")
    return ref_uri


def _path_exists(path: Path) -> bool:
    return os.path.lexists(path)


def _require_exact_bytes(existing: bytes, requested: bytes) -> None:
    if existing != requested:
        raise DurableAuthorityPersistenceError(
            DurableAuthorityErrorCode.DUPLICATE_CONFLICT,
            "conflicting durable authority duplicate",
        )


def _object_without_duplicate_names(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("durable JSON object contains a duplicate field")
        result[key] = value
    return result


def _reject_non_standard_constant(value: str):
    raise ValueError(f"non-standard JSON constant is forbidden: {value}")


def _storage_failure(message: str) -> DurableAuthorityPersistenceError:
    return DurableAuthorityPersistenceError(
        DurableAuthorityErrorCode.MALFORMED_ENVELOPE,
        message,
    )


__all__ = ["ExactLocalFilesystemDurableAuthorityAdapter"]
