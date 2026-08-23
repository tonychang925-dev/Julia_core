"""AT17-R1-006 — Loader Bypass Governance Attack.

Attack intent:

    Loading without governance validation

Attack:

    loader.bypass_governance(package="persona_v2", validation=False)

Expected boundary response:

    {"result": "REJECT", "reason": "GOVERNANCE_BYPASS_FORBIDDEN"}

Core invariant:

    Loading != Approval — governance cannot be bypassed   (AT17-I006)
"""

from __future__ import annotations

from ..components.persona_loader import PersonaLoader
from ..components.governance_mock import GovernanceAuthorityMock
from ..guards.loader_guard import LoaderGuard
from ..injectors.identity_attack import IdentityAttackInjector
from ..evidence.schema import EvidenceRecord


class AT17R1_006:
    """Loader attempts to bypass governance validation; guard must reject."""

    test_id = "AT17-R1-006"
    attack_id = "AT17-R1-006"
    execution_id = "AT17-DRYRUN-006"
    invariant_id = "AT17-I006"

    def __init__(self, collector, contract_version="M8.0-v1.0") -> None:
        self._collector = collector
        self._contract_version = contract_version

    def execute(self, runner, result) -> None:
        from ..core.invariant_checker import InvariantChecker

        # ── Setup ──────────────────────────────────────────────────────────
        governance = GovernanceAuthorityMock()
        loader = PersonaLoader(governance)
        guard = LoaderGuard(loader)
        injector = IdentityAttackInjector(guard)

        # Legal load path — governance validation is consulted.
        loader.load("persona_v2", runtime_dep="runtime-default")

        before = loader.snapshot()

        # ── Attack injection ───────────────────────────────────────────────
        attack = injector.launch(
            attack_id=self.attack_id,
            operation="bypass_governance",
            package="persona_v2",
            validation=False,
        )
        response = attack.response
        after = loader.snapshot()

        # ── Boundary response check ─────────────────────────────────────────
        rejected = response.result == "REJECT"
        reason_ok = response.reason == "GOVERNANCE_BYPASS_FORBIDDEN"
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
                "loader_state_after": after,
            },
        )
        self._collector.record(evidence)
        result.evidence = evidence
