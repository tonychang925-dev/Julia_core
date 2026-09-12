"""Backend-neutral durable authority persistence contracts."""

from .contracts import (
    AuthorityFamily,
    DurableAuthorityEnvelope,
    DurableAuthorityErrorCode,
    DurableAuthorityPersistenceError,
)
from .adapters import DurableAuthorityReader, DurableAuthorityWriter
from .reconstruction import (
    DurableAuthorityReconstructor,
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
    "restore_identity_repository",
    "restore_memory_experience_repository",
    "restore_runtime_binding_repository",
]
