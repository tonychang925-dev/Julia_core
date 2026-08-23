"""Shared boundary-attack scenario base.

A scenario sets up a guarded component, injects one unauthorized operation,
verifies the guard verdict + zero mutation, and records auditable evidence.

Subclasses define:

    test_id / attack_id / execution_id / invariant_id
    operation / expected_reason / expected_boundary
    component_name
    build()   → (guard, injector, snapshot_fn)
    params()  → dict of attack kwargs
"""

from __future__ import annotations

from typing import Callable

from ..evidence.schema import EvidenceRecord


class BoundaryAttackScenario:
    test_id = ""
    attack_id = ""
    execution_id = ""
    invariant_id = ""
    operation = ""
    expected_reason = ""
    expected_boundary = ""
    component_name = ""

    def __init__(self, collector, contract_version="M8.0-v1.0") -> None:
        self._collector = collector
        self._contract_version = contract_version

    # ── subclass hooks ────────────────────────────────────────────────────
    def build(self):
        """Return (guard, injector, snapshot_fn) with the component set up."""
        raise NotImplementedError

    def params(self) -> dict:
        """Attack kwargs."""
        raise NotImplementedError

    # ── execution ─────────────────────────────────────────────────────────
    def execute(self, runner, result) -> None:
        from ..core.invariant_checker import InvariantChecker
        from ..injectors.identity_attack import IdentityAttackInjector

        guard, injector, snapshot_fn = self.build()
        before = snapshot_fn()

        attack = injector.launch(
            attack_id=self.attack_id,
            operation=self.operation,
            **self.params(),
        )
        response = attack.response
        after = snapshot_fn()

        # Boundary response check.
        rejected = response.result == "REJECT"
        reason_ok = response.reason == self.expected_reason
        boundary_ok = response.authority_boundary == self.expected_boundary

        # Invariant verification: zero semantic mutation under attack.
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

        # Evidence record.
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
                "state_after": after,
            },
        )
        self._collector.record(evidence)
        result.evidence = evidence
