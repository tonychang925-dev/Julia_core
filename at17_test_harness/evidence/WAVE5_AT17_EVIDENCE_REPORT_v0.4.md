# WAVE5_AT17_EVIDENCE_REPORT_v0.4

Persona Host Authority Boundary Test — First Evidence Run

Generated: 2026-08-23T08:00:55.785633+00:00
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
| AT17-R1-004 | change_lineage | Resolver | Provenance Authority | REJECT | REJECT | PASS |
| AT17-R1-005 | create_identity | Loader | Identity Authority | REJECT | REJECT | PASS |
| AT17-R1-006 | bypass_governance | Loader | Identity Authority | REJECT | REJECT | PASS |
| AT17-R1-007 | overwrite_lineage | Lifecycle | Lifecycle Authority | REJECT | REJECT | PASS |
| AT17-R1-008 | rewrite_history | Lifecycle | Lifecycle Authority | REJECT | REJECT | PASS |
| AT17-R1-009 | promote_as_identity | Backup | Identity Authority | REJECT | REJECT | PASS |
| AT17-R1-010 | claim_identity | Package Copy | Identity Authority | REJECT | REJECT | PASS |

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
  "timestamp": "2026-08-23T08:00:55.779898+00:00",
  "trace_reference": "",
  "evidence_hash": "990c4951ce4fe45a",
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
  "timestamp": "2026-08-23T08:00:55.780309+00:00",
  "trace_reference": "",
  "evidence_hash": "903c7bd0b12aad8c",
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
  "timestamp": "2026-08-23T08:00:55.780383+00:00",
  "trace_reference": "",
  "evidence_hash": "f16c8c1ba1d81e5d",
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

### AT17-R1-004 — change_lineage

```json
{
  "execution_id": "AT17-DRYRUN-004",
  "test_id": "AT17-R1-004",
  "contract_version": "M8.0-v1.0",
  "runtime_version": "AT17-harness-v1.0",
  "component": "Resolver",
  "operation": "change_lineage",
  "authority_boundary": "Provenance Authority",
  "invariant_id": "AT17-I004",
  "expected_result": "REJECT",
  "actual_result": "REJECT",
  "decision": "PASS",
  "reject_reason": "LINEAGE_AUTHORITY_FORBIDDEN",
  "timestamp": "2026-08-23T08:00:55.780442+00:00",
  "trace_reference": "",
  "evidence_hash": "ef3844e9f5200c43",
  "lineage_reference": "no lineage mutation detected",
  "details": {
    "attack_params": {
      "ref": "ref://persona_v2/2.0.0",
      "lineage": {
        "parent": "attacker-replaced"
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

### AT17-R1-005 — create_identity

```json
{
  "execution_id": "AT17-DRYRUN-005",
  "test_id": "AT17-R1-005",
  "contract_version": "M8.0-v1.0",
  "runtime_version": "AT17-harness-v1.0",
  "component": "Loader",
  "operation": "create_identity",
  "authority_boundary": "Identity Authority",
  "invariant_id": "AT17-I005",
  "expected_result": "REJECT",
  "actual_result": "REJECT",
  "decision": "PASS",
  "reject_reason": "IDENTITY_AUTHORITY_FORBIDDEN",
  "timestamp": "2026-08-23T08:00:55.780504+00:00",
  "trace_reference": "",
  "evidence_hash": "01dc9074ee7dc4ae",
  "lineage_reference": "no lineage mutation detected",
  "details": {
    "attack_params": {
      "package": "persona_v2",
      "identity_name": "Julia"
    },
    "guard_decision": "REJECT",
    "loader_state_after": {
      "carriers": {
        "persona_v2": {
          "package_ref": "persona_v2",
          "carrier_ref": "carrier://persona_v2",
          "runtime_dep": "runtime-default"
        }
      }
    }
  }
}
```

### AT17-R1-006 — bypass_governance

```json
{
  "execution_id": "AT17-DRYRUN-006",
  "test_id": "AT17-R1-006",
  "contract_version": "M8.0-v1.0",
  "runtime_version": "AT17-harness-v1.0",
  "component": "Loader",
  "operation": "bypass_governance",
  "authority_boundary": "Identity Authority",
  "invariant_id": "AT17-I006",
  "expected_result": "REJECT",
  "actual_result": "REJECT",
  "decision": "PASS",
  "reject_reason": "GOVERNANCE_BYPASS_FORBIDDEN",
  "timestamp": "2026-08-23T08:00:55.780558+00:00",
  "trace_reference": "",
  "evidence_hash": "c69ab607eab4773f",
  "lineage_reference": "no lineage mutation detected",
  "details": {
    "attack_params": {
      "package": "persona_v2",
      "validation": false
    },
    "guard_decision": "REJECT",
    "loader_state_after": {
      "carriers": {
        "persona_v2": {
          "package_ref": "persona_v2",
          "carrier_ref": "carrier://persona_v2",
          "runtime_dep": "runtime-default"
        }
      }
    }
  }
}
```

### AT17-R1-007 — overwrite_lineage

```json
{
  "execution_id": "AT17-DRYRUN-007",
  "test_id": "AT17-R1-007",
  "contract_version": "M8.0-v1.0",
  "runtime_version": "AT17-harness-v1.0",
  "component": "Lifecycle",
  "operation": "overwrite_lineage",
  "authority_boundary": "Lifecycle Authority",
  "invariant_id": "AT17-I007",
  "expected_result": "REJECT",
  "actual_result": "REJECT",
  "decision": "PASS",
  "reject_reason": "LINEAGE_AUTHORITY_FORBIDDEN",
  "timestamp": "2026-08-23T08:00:55.780613+00:00",
  "trace_reference": "",
  "evidence_hash": "de4fa66addd4f188",
  "lineage_reference": "no lineage mutation detected",
  "details": {
    "attack_params": {
      "version": "2.0.0",
      "lineage": {
        "parent": "attacker-replaced"
      }
    },
    "guard_decision": "REJECT",
    "lifecycle_state_after": {
      "versions": {
        "2.0.0": "active"
      },
      "history_log": [
        {
          "event": "register",
          "version": "2.0.0"
        },
        {
          "event": "activate",
          "version": "2.0.0"
        }
      ]
    }
  }
}
```

### AT17-R1-008 — rewrite_history

```json
{
  "execution_id": "AT17-DRYRUN-008",
  "test_id": "AT17-R1-008",
  "contract_version": "M8.0-v1.0",
  "runtime_version": "AT17-harness-v1.0",
  "component": "Lifecycle",
  "operation": "rewrite_history",
  "authority_boundary": "Lifecycle Authority",
  "invariant_id": "AT17-I008",
  "expected_result": "REJECT",
  "actual_result": "REJECT",
  "decision": "PASS",
  "reject_reason": "HISTORY_AUTHORITY_FORBIDDEN",
  "timestamp": "2026-08-23T08:00:55.780668+00:00",
  "trace_reference": "",
  "evidence_hash": "ce9b9ae16bf7ef80",
  "lineage_reference": "no lineage mutation detected",
  "details": {
    "attack_params": {
      "version": "2.0.0",
      "history": {
        "causal": "attacker-replaced"
      }
    },
    "guard_decision": "REJECT",
    "lifecycle_state_after": {
      "versions": {
        "2.0.0": "registered"
      },
      "history_log": [
        {
          "event": "register",
          "version": "2.0.0"
        },
        {
          "event": "activate",
          "version": "2.0.0"
        },
        {
          "event": "rollback",
          "version": "2.0.0"
        }
      ]
    }
  }
}
```

### AT17-R1-009 — promote_as_identity

```json
{
  "execution_id": "AT17-DRYRUN-009",
  "test_id": "AT17-R1-009",
  "contract_version": "M8.0-v1.0",
  "runtime_version": "AT17-harness-v1.0",
  "component": "Backup",
  "operation": "promote_as_identity",
  "authority_boundary": "Identity Authority",
  "invariant_id": "AT17-I009",
  "expected_result": "REJECT",
  "actual_result": "REJECT",
  "decision": "PASS",
  "reject_reason": "IDENTITY_AUTHORITY_FORBIDDEN",
  "timestamp": "2026-08-23T08:00:55.780734+00:00",
  "trace_reference": "",
  "evidence_hash": "a3525634f82ceb91",
  "lineage_reference": "no lineage mutation detected",
  "details": {
    "attack_params": {
      "snapshot_id": "snap_1",
      "identity_name": "Julia"
    },
    "guard_decision": "REJECT",
    "state_after": {
      "snapshots": {
        "snap_1": {
          "source_ref": "ref://persona_v2/2.0.0",
          "created_from": "validated continuity material"
        }
      }
    }
  }
}
```

### AT17-R1-010 — claim_identity

```json
{
  "execution_id": "AT17-DRYRUN-010",
  "test_id": "AT17-R1-010",
  "contract_version": "M8.0-v1.0",
  "runtime_version": "AT17-harness-v1.0",
  "component": "Package Copy",
  "operation": "claim_identity",
  "authority_boundary": "Identity Authority",
  "invariant_id": "AT17-I010",
  "expected_result": "REJECT",
  "actual_result": "REJECT",
  "decision": "PASS",
  "reject_reason": "IDENTITY_AUTHORITY_FORBIDDEN",
  "timestamp": "2026-08-23T08:00:55.780790+00:00",
  "trace_reference": "",
  "evidence_hash": "b5ae97edf2d2fadb",
  "lineage_reference": "no lineage mutation detected",
  "details": {
    "attack_params": {
      "package": "persona_v2",
      "identity_name": "Julia"
    },
    "guard_decision": "REJECT",
    "state_after": {
      "copies": {
        "copy_1": {
          "package_ref": "ref://persona_v2/2.0.0",
          "copy_ref": "copy://ref://persona_v2/2.0.0"
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
- AT17-I004 (AT17-R1-004): no persona/artifact state and no lineage mutation under attack — confirmed via snapshot equality.
- AT17-I005 (AT17-R1-005): no persona/artifact state and no lineage mutation under attack — confirmed via snapshot equality.
- AT17-I006 (AT17-R1-006): no persona/artifact state and no lineage mutation under attack — confirmed via snapshot equality.
- AT17-I007 (AT17-R1-007): no persona/artifact state and no lineage mutation under attack — confirmed via snapshot equality.
- AT17-I008 (AT17-R1-008): no persona/artifact state and no lineage mutation under attack — confirmed via snapshot equality.
- AT17-I009 (AT17-R1-009): no persona/artifact state and no lineage mutation under attack — confirmed via snapshot equality.
- AT17-I010 (AT17-R1-010): no persona/artifact state and no lineage mutation under attack — confirmed via snapshot equality.

Constraint check:
- Harness is not an authority source: CONFIRMED
- Mock governance creates no identity transitions: CONFIRMED
- Every rejection produced auditable evidence: CONFIRMED

## 7. Final Decision

**PASS** — 10 attack(s) executed, 10 rejected as required.

Artifact Boundary closure status: AT17-R1-001 (Version Registry != Identity Registry), AT17-R1-002 (Artifact Version != Identity Authority), AT17-R1-003 (Artifact Provenance not rewritable by Resolver) all proven.
