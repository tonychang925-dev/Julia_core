# WAVE5_AT17_EVIDENCE_REPORT_v0.1

Persona Host Authority Boundary Test — First Evidence Run

Generated: 2026-08-23T07:49:01.501753+00:00
Contract: M8.0 Persona Host Runtime Boundary Contract v1.0 (FINAL FREEZE ACCEPTED)

## 1. Test Environment

- Runtime: `at17_test_harness` v1.0 (TEST INFRASTRUCTURE ONLY)
- Repository: `julia_core` / branch `wave5/authority-consolidation`
- Attack model: Boundary Guard interception (check_request → reject → evidence)

## 2. Authority Model

```
Continuity Authority
    ↓
Julia Core Governance
    ↓
Validated Continuity Artifact
    ↓
Persona Host Runtime
    ↓
Product Runtime
```

Authority flows downward. Execution capability does not flow upward into semantic authority. Core invariant: Runtime Capability != Semantic Authority.

## 3. Attack Matrix Execution

| Test ID | Attack | Component | Boundary | Expected | Actual | Decision |
|---|---|---|---|---|---|---|
| AT17-R1-001 | create_identity | Registry | Identity Authority | REJECT | REJECT | PASS |
| AT17-R1-002 | set_latest_as_julia | Registry | Identity Authority | REJECT | REJECT | PASS |
| AT17-R1-003 | update_provenance | Resolver | Provenance Authority | REJECT | REJECT | PASS |

## 4. Reject Evidence

### AT17-R1-001 — create_identity

```json
{
  "execution_id": "AT17-DRYRUN-001",
  "test_id": "AT17-R1-001",
  "contract_version": "M8.0-v1.0",
  "runtime_version": "AT17-harness-v1.0",
  "component": "Registry",
  "operation": "create_identity",
  "authority_boundary": "Identity Authority",
  "invariant_id": "AT17-I001",
  "expected_result": "REJECT",
  "actual_result": "REJECT",
  "decision": "PASS",
  "reject_reason": "IDENTITY_AUTHORITY_FORBIDDEN",
  "timestamp": "2026-08-23T07:49:01.499695+00:00",
  "trace_reference": "",
  "evidence_hash": "69c243ad4846b691",
  "lineage_reference": "no lineage mutation detected",
  "details": {
    "attack_params": {
      "package": "persona_v2",
      "identity_name": "Julia"
    },
    "guard_decision": "REJECT",
    "registry_state_after": {
      "packages": {
        "persona_v2": {
          "versions": {
            "2.0.0": "ref://persona_v2/2.0.0"
          },
          "availability": {
            "2.0.0": "registered"
          }
        }
      },
      "lineage_log": [
        {
          "event": "register",
          "package": "persona_v2",
          "version": "2.0.0"
        }
      ]
    }
  }
}
```

### AT17-R1-002 — set_latest_as_julia

```json
{
  "execution_id": "AT17-DRYRUN-002",
  "test_id": "AT17-R1-002",
  "contract_version": "M8.0-v1.0",
  "runtime_version": "AT17-harness-v1.0",
  "component": "Registry",
  "operation": "set_latest_as_julia",
  "authority_boundary": "Identity Authority",
  "invariant_id": "AT17-I002",
  "expected_result": "REJECT",
  "actual_result": "REJECT",
  "decision": "PASS",
  "reject_reason": "IDENTITY_AUTHORITY_FORBIDDEN",
  "timestamp": "2026-08-23T07:49:01.500130+00:00",
  "trace_reference": "",
  "evidence_hash": "2f98a30c92412b82",
  "lineage_reference": "no lineage mutation detected",
  "details": {
    "attack_params": {
      "package": "persona_v2",
      "version": "2.0.0"
    },
    "guard_decision": "REJECT",
    "registry_state_after": {
      "packages": {
        "persona_v2": {
          "versions": {
            "2.0.0": "ref://persona_v2/2.0.0"
          },
          "availability": {
            "2.0.0": "registered"
          }
        }
      },
      "lineage_log": [
        {
          "event": "register",
          "package": "persona_v2",
          "version": "2.0.0"
        }
      ]
    }
  }
}
```

### AT17-R1-003 — update_provenance

```json
{
  "execution_id": "AT17-DRYRUN-003",
  "test_id": "AT17-R1-003",
  "contract_version": "M8.0-v1.0",
  "runtime_version": "AT17-harness-v1.0",
  "component": "Resolver",
  "operation": "update_provenance",
  "authority_boundary": "Provenance Authority",
  "invariant_id": "AT17-I003",
  "expected_result": "REJECT",
  "actual_result": "REJECT",
  "decision": "PASS",
  "reject_reason": "PROVENANCE_AUTHORITY_FORBIDDEN",
  "timestamp": "2026-08-23T07:49:01.500362+00:00",
  "trace_reference": "",
  "evidence_hash": "633836f7ed80e060",
  "lineage_reference": "no lineage mutation detected",
  "details": {
    "attack_params": {
      "ref": "ref://persona_v2/2.0.0",
      "provenance": {
        "source": "attacker-rewritten"
      }
    },
    "guard_decision": "REJECT",
    "resolver_state_after": {
      "artifacts": {
        "ref://persona_v2/2.0.0": {
          "schema_id": "persona-package-v1",
          "hash_value": "sha256:abcdef",
          "provenance": {
            "source": "governance-validated",
            "artifact": "persona_v2@2.0.0"
          }
        }
      }
    }
  }
}
```

## 5. Failed Attempts

None. All authority escalation attempts were rejected.

## 6. Boundary Integrity Assessment

- AT17-I001 (AT17-R1-001): no persona/artifact state and no lineage mutation under attack — confirmed via snapshot equality.
- AT17-I002 (AT17-R1-002): no persona/artifact state and no lineage mutation under attack — confirmed via snapshot equality.
- AT17-I003 (AT17-R1-003): no persona/artifact state and no lineage mutation under attack — confirmed via snapshot equality.

Constraint check:
- Harness is not an authority source: CONFIRMED
- Mock governance creates no identity transitions: CONFIRMED
- Every rejection produced auditable evidence: CONFIRMED

## 7. Final Decision

**PASS** — 3 attack(s) executed, 3 rejected as required.

Artifact Boundary closure status: AT17-R1-001 (Version Registry != Identity Registry), AT17-R1-002 (Artifact Version != Identity Authority), AT17-R1-003 (Artifact Provenance not rewritable by Resolver) all proven.
