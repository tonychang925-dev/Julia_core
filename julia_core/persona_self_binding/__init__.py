"""Typed PersonaSelfBinding authority contracts.

This module is contract formation only.  It intentionally has no persistence,
runtime wiring, provider dispatch, or semantic fact authority.
"""

from julia_core.persona_self_binding.contracts import (
    AuthorityFamily,
    AuthorityReference,
    ExecutionSubstratePolicy,
    GovernanceEventType,
    GovernanceProvenanceEvent,
    IdentityAuthorityAssertion,
    IdentityAssertionDisposition,
    IntegrityContract,
    PersonaSelfBinding,
    PersonaSelfBindingContractError,
    PersonaSelfBindingErrorCode,
    PersonaSelfBindingLifecycle,
    RelationshipAuthority,
    RelationshipAuthorityState,
    SupersessionContract,
)
from julia_core.persona_self_binding.durable import (
    PersonaSelfBindingRecord,
    PersonaSelfBindingStore,
)
from julia_core.persona_self_binding.projection import (
    PersonaSelfBindingProjector,
    PersonaSelfBindingProjection,
)

__all__ = [
    "AuthorityFamily",
    "AuthorityReference",
    "ExecutionSubstratePolicy",
    "GovernanceEventType",
    "GovernanceProvenanceEvent",
    "IdentityAssertionDisposition",
    "IdentityAuthorityAssertion",
    "IntegrityContract",
    "PersonaSelfBinding",
    "PersonaSelfBindingContractError",
    "PersonaSelfBindingErrorCode",
    "PersonaSelfBindingLifecycle",
    "PersonaSelfBindingRecord",
    "PersonaSelfBindingStore",
    "PersonaSelfBindingProjector",
    "PersonaSelfBindingProjection",
    "RelationshipAuthority",
    "RelationshipAuthorityState",
    "SupersessionContract",
]
