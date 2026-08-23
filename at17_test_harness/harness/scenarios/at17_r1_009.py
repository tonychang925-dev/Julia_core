"""AT17-R1-009 — Backup Authority Copy Attack.

Attack intent:

    Backup snapshot → Identity Authority

Attack:

    backup.promote_as_identity(snapshot_id="snap_1")

Expected boundary response:

    {"result": "REJECT", "reason": "IDENTITY_AUTHORITY_FORBIDDEN"}

Core invariant:

    Backup Artifact != Identity Authority
    Artifact availability != identity existence      (AT17-I009)
"""

from __future__ import annotations

from ..components.persona_backup import PersonaBackup
from ..components.governance_mock import GovernanceAuthorityMock
from ..guards.backup_guard import BackupGuard
from ..injectors.identity_attack import IdentityAttackInjector
from .base import BoundaryAttackScenario


class AT17R1_009(BoundaryAttackScenario):
    test_id = "AT17-R1-009"
    attack_id = "AT17-R1-009"
    execution_id = "AT17-DRYRUN-009"
    invariant_id = "AT17-I009"
    operation = "promote_as_identity"
    expected_reason = "IDENTITY_AUTHORITY_FORBIDDEN"
    expected_boundary = "Identity Authority"
    component_name = "Backup"

    def build(self):
        governance = GovernanceAuthorityMock()
        backup = PersonaBackup()
        guard = BackupGuard(backup)
        injector = IdentityAttackInjector(guard)

        # Legal recovery path — a snapshot exists (recovery copy only).
        backup.create_snapshot(source_ref="ref://persona_v2/2.0.0")

        return guard, injector, backup.snapshot

    def params(self) -> dict:
        return {"snapshot_id": "snap_1", "identity_name": "Julia"}
