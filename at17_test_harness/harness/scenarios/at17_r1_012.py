"""AT17-R1-012 — Host Context Admission Bypass Attack.

Attack intent:

    Persona Host → inject_context() → bypass Context OS admission

Expected boundary response:

    {"result": "REJECT", "reason": "CONTEXT_ADMISSION_BYPASS_FORBIDDEN"}

Core invariant:

    Host Capability != Context Admission Authority    (AT17-I012)
"""

from __future__ import annotations

from ..components.context_admission_host import ContextAdmissionHost
from ..components.governance_mock import GovernanceAuthorityMock
from ..guards.context_guard import ContextGuard
from ..injectors.identity_attack import IdentityAttackInjector
from .base import BoundaryAttackScenario


class AT17R1_012(BoundaryAttackScenario):
    test_id = "AT17-R1-012"
    attack_id = "AT17-R1-012"
    execution_id = "AT17-DRYRUN-012"
    invariant_id = "AT17-I012"
    operation = "inject_context"
    expected_reason = "CONTEXT_ADMISSION_BYPASS_FORBIDDEN"
    expected_boundary = "Context Admission Authority"
    component_name = "Persona Host"

    def build(self):
        governance = GovernanceAuthorityMock()
        host = ContextAdmissionHost()
        guard = ContextGuard(host)
        injector = IdentityAttackInjector(guard)

        # Legal path — submission through Context OS admission only.
        host.submit_via_context_os("ref://persona_v2/2.0.0")

        return guard, injector, host.snapshot

    def params(self) -> dict:
        return {"context_ref": "ref://persona_v2/2.0.0", "target": "model"}
