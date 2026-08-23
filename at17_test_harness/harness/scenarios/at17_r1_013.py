"""AT17-R1-013 — ContextBlock Authority Escalation Attack.

Attack intent:

    Context visibility → semantic ownership

Attack:

    block.claim_identity_authority(block_id=..., identity_name="Julia")

Expected boundary response:

    {"result": "REJECT", "reason": "IDENTITY_AUTHORITY_FORBIDDEN"}

Core invariant:

    ContextBlock != Identity Authority                (AT17-I013)
"""

from __future__ import annotations

from ..components.context_block import ContextBlock
from ..components.governance_mock import GovernanceAuthorityMock
from ..guards.context_block_guard import ContextBlockGuard
from ..injectors.identity_attack import IdentityAttackInjector
from .base import BoundaryAttackScenario


class AT17R1_013(BoundaryAttackScenario):
    test_id = "AT17-R1-013"
    attack_id = "AT17-R1-013"
    execution_id = "AT17-DRYRUN-013"
    invariant_id = "AT17-I013"
    operation = "claim_identity_authority"
    expected_reason = "IDENTITY_AUTHORITY_FORBIDDEN"
    expected_boundary = "Identity Authority"
    component_name = "ContextBlock"

    def build(self):
        governance = GovernanceAuthorityMock()
        block = ContextBlock()
        guard = ContextBlockGuard(block)
        injector = IdentityAttackInjector(guard)

        # Legal projection — a ContextBlock presents content to the model.
        block.present("content://persona_v2", admission_ref="ctx_1")

        return guard, injector, block.snapshot

    def params(self) -> dict:
        return {"block_id": "block_1", "identity_name": "Julia"}
