"""AT17-R1-001 — Registry Identity Creation Attack.

Attack intent:

    Package Version → Identity Creation
    (Artifact → Identity Source)

Expected boundary response:

    {"result": "REJECT", "reason": "IDENTITY_AUTHORITY_FORBIDDEN"}

Core invariant:

    Version Registry != Identity Registry        (AT17-I001)
"""

from __future__ import annotations

from ..components.persona_registry import PersonaRegistry
from ..components.governance_mock import GovernanceAuthorityMock
from ..guards.registry_guard import RegistryGuard
from ..injectors.identity_attack import IdentityAttackInjector
from ..evidence.schema import EvidenceRecord


class AT17R1_001:
    """Registry attempts identity creation; boundary guard must reject it."""

    test_id = "AT17-R1-001"
    attack_id = "AT17-R1-001"
    execution_id = "AT17-DRYRUN-001"
    invariant_id = "AT17-I001"

    def __init__(self, collector, contract_version="M8.0-v1.0") -> None:
        self._collector = collector
        self._contract_version = contract_version

    def execute(self, runner, result) -> None:
        from ..core.invariant_checker import InvariantChecker

        # ── Setup ──────────────────────────────────────────────────────────
        governance = GovernanceAuthorityMock()
        registry = PersonaRegistry()
        guard = RegistryGuard(registry)
        injector = IdentityAttackInjector(guard)

        # Legal artifact-scope capability proves the registry works as a
        # version registry (and gives us state to snapshot).
        registry.register_package("persona_v2", "2.0.0", "ref://persona_v2/2.0.0")

        before = registry.snapshot()

        # ── Attack injection ───────────────────────────────────────────────
        attack = injector.launch(
            attack_id=self.attack_id,
            operation="create_identity",
            package="persona_v2",
            identity_name="Julia",
        )

        response = attack.response
        after = registry.snapshot()

        # ── Boundary response check ─────────────────────────────────────────
        rejected = response.result == "REJECT"
        reason_ok = response.reason == "IDENTITY_AUTHORITY_FORBIDDEN"
        boundary_ok = response.authority_boundary == "Identity Authority"

        # ── Invariant verification ──────────────────────────────────────────
        no_mutation = InvariantChecker().check_no_mutation(
            before, after, f"{self.invariant_id}-NO-MUTATION"
        )
        result.invariants.append(no_mutation)

        passed = rejected and reason_ok and boundary_ok and no_mutation.passed
        result.decision = "PASS" if passed else "FAIL"
        if not passed:
            result.errors.append(
                f"guard verdict unexpected: result={response.result} "
                f"reason={response.reason} boundary={response.authority_boundary} "
                f"no_mutation={no_mutation.passed}"
            )

        # ── Evidence record ─────────────────────────────────────────────────
        evidence = EvidenceRecord(
            execution_id=self.execution_id,
            test_id=self.test_id,
            contract_version=self._contract_version,
            runtime_version="AT17-harness-v1.0",
            component=response.component,
            operation=response.operation,
            authority_boundary=response.authority_boundary,
            invariant_id=self.invariant_id,
            expected_result="REJECT",
            actual_result=response.result,
            decision="PASS" if passed else "FAIL",
            reject_reason=response.reason or "NONE",
            lineage_reference="no lineage mutation detected",
            details={
                "attack_params": attack.request.params,
                "guard_decision": response.result,
                "registry_state_after": after,
            },
        )
        self._collector.record(evidence)
        result.evidence = evidence
