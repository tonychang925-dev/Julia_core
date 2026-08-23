"""AT17-R1-007 — Lifecycle Overwrites Lineage Attack.

Attack intent:

    Lifecycle capability → Lineage Authority

Attack:

    lifecycle.overwrite_lineage(version="2.0.0", lineage={...})

Expected boundary response:

    {"result": "REJECT", "reason": "LINEAGE_AUTHORITY_FORBIDDEN"}

Core invariant:

    Lifecycle Event != Identity Event — lineage cannot be overwritten
    by a lifecycle operation                               (AT17-I007)
"""

from __future__ import annotations

from ..components.persona_lifecycle import PersonaLifecycle
from ..components.governance_mock import GovernanceAuthorityMock
from ..guards.lifecycle_guard import LifecycleGuard
from ..injectors.identity_attack import IdentityAttackInjector
from ..evidence.schema import EvidenceRecord


class AT17R1_007:
    """Lifecycle attempts to overwrite lineage; guard must reject."""

    test_id = "AT17-R1-007"
    attack_id = "AT17-R1-007"
    execution_id = "AT17-DRYRUN-007"
    invariant_id = "AT17-I007"

    def __init__(self, collector, contract_version="M8.0-v1.0") -> None:
        self._collector = collector
        self._contract_version = contract_version

    def execute(self, runner, result) -> None:
        from ..core.invariant_checker import InvariantChecker

        # ── Setup ──────────────────────────────────────────────────────────
        governance = GovernanceAuthorityMock()
        lifecycle = PersonaLifecycle()
        guard = LifecycleGuard(lifecycle)
        injector = IdentityAttackInjector(guard)

        # Legal lifecycle path — availability state only.
        lifecycle.register_version("2.0.0")
        lifecycle.activate("2.0.0")

        before = lifecycle.snapshot()

        # ── Attack injection ───────────────────────────────────────────────
        attack = injector.launch(
            attack_id=self.attack_id,
            operation="overwrite_lineage",
            version="2.0.0",
            lineage={"parent": "attacker-replaced"},
        )
        response = attack.response
        after = lifecycle.snapshot()

        # ── Boundary response check ─────────────────────────────────────────
        rejected = response.result == "REJECT"
        reason_ok = response.reason == "LINEAGE_AUTHORITY_FORBIDDEN"
        boundary_ok = response.authority_boundary == "Lifecycle Authority"

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
                "lifecycle_state_after": after,
            },
        )
        self._collector.record(evidence)
        result.evidence = evidence
