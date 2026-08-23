"""AT17-R1-003 — Resolver Provenance Mutation Attack.

Attack intent:

    Resolver (artifact validator) → Provenance Authority

Attack:

    resolver.update_provenance(ref="ref://persona_v2/2.0.0", provenance=...)

Expected boundary response:

    {"result": "REJECT", "reason": "PROVENANCE_AUTHORITY_FORBIDDEN"}

Core invariant:

    Artifact Provenance cannot be rewritten by Resolver   (AT17-I003)
"""

from __future__ import annotations

from ..components.artifact_resolver import ArtifactResolver
from ..components.governance_mock import GovernanceAuthorityMock
from ..guards.resolver_guard import ResolverGuard
from ..injectors.identity_attack import IdentityAttackInjector
from ..evidence.schema import EvidenceRecord


class AT17R1_003:
    """Resolver attempts provenance mutation; guard must reject."""

    test_id = "AT17-R1-003"
    attack_id = "AT17-R1-003"
    execution_id = "AT17-DRYRUN-003"
    invariant_id = "AT17-I003"

    def __init__(self, collector, contract_version="M8.0-v1.0") -> None:
        self._collector = collector
        self._contract_version = contract_version

    def execute(self, runner, result) -> None:
        from ..core.invariant_checker import InvariantChecker

        # ── Setup ──────────────────────────────────────────────────────────
        governance = GovernanceAuthorityMock()
        resolver = ArtifactResolver()
        guard = ResolverGuard(resolver)
        injector = IdentityAttackInjector(guard)

        # Legal artifact registration with provenance — the resolver may hold
        # provenance references, but never mutate them.
        resolver.register_artifact(
            "ref://persona_v2/2.0.0",
            schema_id="persona-package-v1",
            hash_value="sha256:abcdef",
            provenance={"source": "governance-validated", "artifact": "persona_v2@2.0.0"},
        )

        before = resolver.snapshot()

        # ── Attack injection ───────────────────────────────────────────────
        attack = injector.launch(
            attack_id=self.attack_id,
            operation="update_provenance",
            ref="ref://persona_v2/2.0.0",
            provenance={"source": "attacker-rewritten"},
        )
        response = attack.response
        after = resolver.snapshot()

        # ── Boundary response check ─────────────────────────────────────────
        rejected = response.result == "REJECT"
        reason_ok = response.reason == "PROVENANCE_AUTHORITY_FORBIDDEN"
        boundary_ok = response.authority_boundary == "Provenance Authority"

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
                "resolver_state_after": after,
            },
        )
        self._collector.record(evidence)
        result.evidence = evidence
