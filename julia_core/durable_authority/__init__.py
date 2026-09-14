"""Backend-neutral durable authority persistence contracts."""

from .contracts import (
    AuthorityFamily,
    DurableAuthorityEnvelope,
    DurableAuthorityErrorCode,
    DurableAuthorityPersistenceError,
)
from .adapters import DurableAuthorityReader, DurableAuthorityWriter
from .filesystem_adapter import FilesystemDurableAuthorityReader
from .reconstruction import (
    DurableAuthorityReconstructor,
    reconstruct_from_durable_authority,
    restore_identity_repository,
    restore_memory_experience_repository,
    restore_runtime_binding_repository,
)
from .serialization import (
    build_identity_envelope,
    build_memory_experience_envelope,
    build_runtime_binding_envelope,
    envelope_from_dict,
)

__all__ = [
    "AuthorityFamily",
    "DurableAuthorityEnvelope",
    "DurableAuthorityErrorCode",
    "DurableAuthorityPersistenceError",
    "DurableAuthorityReader",
    "DurableAuthorityReconstructor",
    "DurableAuthorityWriter",
    "build_identity_envelope",
    "build_memory_experience_envelope",
    "build_runtime_binding_envelope",
    "envelope_from_dict",
    "FilesystemDurableAuthorityReader",
    "reconstruct_from_durable_authority",
    "restore_identity_repository",
    "restore_memory_experience_repository",
    "restore_runtime_binding_repository",
]
