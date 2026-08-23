"""AT17-R1-011 — Provider Migration Identity Replacement Attack.

Attack intent:

    Provider A → Provider B → replace_julia()

Expected boundary response:

    {"result": "REJECT", "reason": "IDENTITY_AUTHORITY_FORBIDDEN"}

Core invariant:

    Migration != Identity Replacement                (AT17-I011)
"""

from __future__ import annotations

from ..components.provider_migration import ProviderMigration
from ..components.governance_mock import GovernanceAuthorityMock
from ..guards.migration_guard import MigrationGuard
from ..injectors.identity_attack import IdentityAttackInjector
from .base import BoundaryAttackScenario


class AT17R1_011(BoundaryAttackScenario):
    test_id = "AT17-R1-011"
    attack_id = "AT17-R1-011"
    execution_id = "AT17-DRYRUN-011"
    invariant_id = "AT17-I011"
    operation = "replace_julia"
    expected_reason = "IDENTITY_AUTHORITY_FORBIDDEN"
    expected_boundary = "Identity Authority"
    component_name = "Provider Migration"

    def build(self):
        governance = GovernanceAuthorityMock()
        migration = ProviderMigration()
        guard = MigrationGuard(migration)
        injector = IdentityAttackInjector(guard)

        # Legal substrate migration — provider A → B (execution substrate only).
        migration.register_provider("provider-A")
        migration.register_provider("provider-B")
        migration.migrate_provider("provider-A", "provider-B")

        return guard, injector, migration.snapshot

    def params(self) -> dict:
        return {"from_provider": "provider-A", "to_provider": "provider-B"}
