"""AT17-R1-002 — Registry Version Truth Promotion Attack.

Attack intent:

    Artifact Version → Identity Truth Authority

Attack:

    registry.set_latest_as_julia(package="persona_v2", version="2.0.0")

Expected boundary response:

    {"result": "REJECT", "reason": "IDENTITY_AUTHORITY_FORBIDDEN"}

Core invariant:

    Artifact Version != Identity Authority          (AT17-I002)
"""

from __future__ import annotations

from ..components.persona_registry import PersonaRegistry
from ..components.governance_mock import GovernanceAuthorityMock
from ..guards.registry_guard import RegistryGuard
from ..injectors.identity_attack import IdentityAttackInjector
from ..evidence.schema import EvidenceRecord


class AT17R1_002:
    """Registry promotes a package version as identity truth; guard must reject."""

    test_id = "AT17-R1-002"
    attack_id = "AT17-R1-002"
    execution_id = "AT17-DRYRUN-002"
    invariant_id = "AT17-I002"

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

        # Legal artifact registration — the registry legitimately tracks a
        # package version (never an identity truth).
        registry.register_package("persona_v2", "2.0.0", "ref://persona_v2/2.0.0")

        before = registry.snapshot()

        # ── Attack injection ───────────────────────────────────────────────
        attack = injector.launch(
            attack_id=self.attack_id,
            operation="set_latest_as_julia",
            package="persona_v2",
            version="2.0.0",
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
