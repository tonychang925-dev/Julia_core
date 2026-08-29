"""CapabilityDefinition registration for engineering.code_review.

Core owns the semantic CapabilityDefinition and its permission scope. The
concrete provider (EngineeringCodeReviewCapabilityProvider) is implemented in
Julia-AI-Assistant under the provider key ``external_review``; Core does not
import or host browser/DOM/ChatGPT transport.

Invocation is manual/explicit only (see invocation.py). No automatic cognitive
routing is registered here.
"""

from __future__ import annotations

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityStatus,
)
from julia_core.capability.policy import PermissionPolicy, PermissionRule
from julia_core.capability.registry import CapabilityRegistry

EXTERNAL_REVIEW_CAPABILITY = "engineering.code_review"
EXTERNAL_REVIEW_PROVIDER = "external_review"
EXTERNAL_REVIEW_SCOPE = "engineering.review.external"

INPUT_SCHEMA = {
    "review_id": "review identity (rvw_...)",
    "candidate_id": "candidate identity (cand_...)",
    "candidate_sha": "bound candidate git SHA",
    "bundle_digest": "digest of the exact ReviewBundle payload",
    "repository": "repository name",
    "objective": "review objective",
    "review_mode": "architecture_and_code",
    "questions": "explicit review questions",
}


def make_external_review_definition(*, status: CapabilityStatus = CapabilityStatus.REGISTERED) -> CapabilityDefinition:
    """Build the canonical engineering.code_review definition.

    status defaults to REGISTERED (defined but not validated). The provider
    side (Julia-AI-Assistant) may mark AVAILABLE after it binds the real
    external_review provider.
    """
    return CapabilityDefinition(
        name=EXTERNAL_REVIEW_CAPABILITY,
        description=(
            "Submit a governed engineering ReviewBundle to the currently bound "
            "external review session and capture the raw review response as "
            "typed execution truth. Manual/explicit invocation only."
        ),
        layer=CapabilityLayer.INTELLIGENCE,
        provider=EXTERNAL_REVIEW_PROVIDER,
        permission_scope=EXTERNAL_REVIEW_SCOPE,
        input_schema=dict(INPUT_SCHEMA),
        status=status,
        schema_version="1.0",
    )


def register_external_review_capability(
    registry: CapabilityRegistry,
    policy: PermissionPolicy | None = None,
    *,
    status: CapabilityStatus = CapabilityStatus.REGISTERED,
) -> CapabilityDefinition:
    """Register the engineering.code_review definition (and scope rule).

    Registration alone does NOT equal external-send authorization. The
    permission rule below grants ONLY the scope-level authorization owned by
    PermissionPolicy/CapabilityManager. Reaching the real provider additionally
    requires the guarded semantic ingress (a valid ReviewTransaction token from
    the Core ledger) — capability existence never implies send authority (B).

    No browser authority is registered.
    """
    definition = make_external_review_definition(status=status)
    registry.register_definition(definition)
    if policy is not None:
        policy.add_rule(PermissionRule(
            scope=EXTERNAL_REVIEW_SCOPE,
            allow=True,
            reason="Operator-triggered external code review submission (manual/explicit); "
                   "provider reach additionally requires governed review ingress token",
        ))
    return definition


__all__ = [
    "EXTERNAL_REVIEW_CAPABILITY",
    "EXTERNAL_REVIEW_PROVIDER",
    "EXTERNAL_REVIEW_SCOPE",
    "INPUT_SCHEMA",
    "make_external_review_definition",
    "register_external_review_capability",
]
