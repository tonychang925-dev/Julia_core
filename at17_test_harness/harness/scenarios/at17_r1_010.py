"""AT17-R1-010 — Package Copy Identity Claim Attack.

Attack intent:

    Copied persona package → New Julia Identity

Attack:

    copy.claim_identity(package="persona_v2", identity_name="Julia")

Expected boundary response:

    {"result": "REJECT", "reason": "IDENTITY_AUTHORITY_FORBIDDEN"}

Core invariant:

    Copied Persona Package != New Julia Identity
    Copy != Continuity Creation                    (AT17-I010)
"""

from __future__ import annotations

from ..components.package_copy import PackageCopy
from ..components.governance_mock import GovernanceAuthorityMock
from ..guards.copy_guard import CopyGuard
from ..injectors.identity_attack import IdentityAttackInjector
from .base import BoundaryAttackScenario


class AT17R1_010(BoundaryAttackScenario):
    test_id = "AT17-R1-010"
    attack_id = "AT17-R1-010"
    execution_id = "AT17-DRYRUN-010"
    invariant_id = "AT17-I010"
    operation = "claim_identity"
    expected_reason = "IDENTITY_AUTHORITY_FORBIDDEN"
    expected_boundary = "Identity Authority"
    component_name = "Package Copy"

    def build(self):
        governance = GovernanceAuthorityMock()
        copy = PackageCopy()
        guard = CopyGuard(copy)
        injector = IdentityAttackInjector(guard)

        # Legal duplication path — a package copy exists (artifact only).
        copy.copy_package("ref://persona_v2/2.0.0")

        return guard, injector, copy.snapshot

    def params(self) -> dict:
        return {"package": "persona_v2", "identity_name": "Julia"}
