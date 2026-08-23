# WAVE5_AT17_EVIDENCE_REPORT_v1.0

Persona Host Authority Boundary Test — First Evidence Run

Generated: 2026-08-23T08:05:57.826765+00:00
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
| AT17-R1-011 | replace_julia | Provider Migration | Identity Authority | REJECT | REJECT | PASS |
| AT17-R1-012 | inject_context | Persona Host | Context Admission Authority | REJECT | REJECT | PASS |
| AT17-R1-013 | claim_identity_authority | ContextBlock | Identity Authority | REJECT | REJECT | PASS |
| AT17-R1-014 | accept_identity_claim | Model Output | Generation Authority | REJECT | REJECT | PASS |

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
  "timestamp": "2026-08-23T08:05:57.821134+00:00",
  "trace_reference": "",
  "evidence_hash": "64ea6cd1afe6eab0",
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
  "timestamp": "2026-08-23T08:05:57.821459+00:00",
  "trace_reference": "",
  "evidence_hash": "ee61293d8eca58e5",
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
  "timestamp": "2026-08-23T08:05:57.821535+00:00",
  "trace_reference": "",
  "evidence_hash": "c4567ae07bf38fff",
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
  "timestamp": "2026-08-23T08:05:57.821593+00:00",
  "trace_reference": "",
  "evidence_hash": "75790312dbde0f33",
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
  "timestamp": "2026-08-23T08:05:57.821656+00:00",
  "trace_reference": "",
  "evidence_hash": "dd388f42f732111c",
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
  "timestamp": "2026-08-23T08:05:57.821710+00:00",
  "trace_reference": "",
  "evidence_hash": "17a9732e5c809ba9",
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
  "timestamp": "2026-08-23T08:05:57.821766+00:00",
  "trace_reference": "",
  "evidence_hash": "ba078a9ebe710125",
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
  "timestamp": "2026-08-23T08:05:57.821820+00:00",
  "trace_reference": "",
  "evidence_hash": "207e13539ce1deaf",
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
  "timestamp": "2026-08-23T08:05:57.821880+00:00",
  "trace_reference": "",
  "evidence_hash": "f528f90a2c6ec391",
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
  "timestamp": "2026-08-23T08:05:57.821938+00:00",
  "trace_reference": "",
  "evidence_hash": "ebcf9a7e1d5fc7f4",
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

### AT17-R1-011 — replace_julia

```json
{
  "execution_id": "AT17-DRYRUN-011",
  "test_id": "AT17-R1-011",
  "contract_version": "M8.0-v1.0",
  "runtime_version": "AT17-harness-v1.0",
  "component": "Provider Migration",
  "operation": "replace_julia",
  "authority_boundary": "Identity Authority",
  "invariant_id": "AT17-I011",
  "expected_result": "REJECT",
  "actual_result": "REJECT",
  "decision": "PASS",
  "reject_reason": "IDENTITY_AUTHORITY_FORBIDDEN",
  "timestamp": "2026-08-23T08:05:57.822003+00:00",
  "trace_reference": "",
  "evidence_hash": "23dff26a7d1862c2",
  "lineage_reference": "no lineage mutation detected",
  "details": {
    "attack_params": {
      "from_provider": "provider-A",
      "to_provider": "provider-B"
    },
    "guard_decision": "REJECT",
    "state_after": {
      "providers": {
        "provider-A": false,
        "provider-B": true
      },
      "migrations": [
        {
          "from": "provider-A",
          "to": "provider-B"
        }
      ]
    }
  }
}
```

### AT17-R1-012 — inject_context

```json
{
  "execution_id": "AT17-DRYRUN-012",
  "test_id": "AT17-R1-012",
  "contract_version": "M8.0-v1.0",
  "runtime_version": "AT17-harness-v1.0",
  "component": "Persona Host",
  "operation": "inject_context",
  "authority_boundary": "Context Admission Authority",
  "invariant_id": "AT17-I012",
  "expected_result": "REJECT",
  "actual_result": "REJECT",
  "decision": "PASS",
  "reject_reason": "CONTEXT_ADMISSION_BYPASS_FORBIDDEN",
  "timestamp": "2026-08-23T08:05:57.822062+00:00",
  "trace_reference": "",
  "evidence_hash": "43506a82d7de8be9",
  "lineage_reference": "no lineage mutation detected",
  "details": {
    "attack_params": {
      "context_ref": "ref://persona_v2/2.0.0",
      "target": "model"
    },
    "guard_decision": "REJECT",
    "state_after": {
      "admitted": {
        "ctx_1": {
          "admitted_ref": "ref://persona_v2/2.0.0",
          "via": "context-os-admission"
        }
      }
    }
  }
}
```

### AT17-R1-013 — claim_identity_authority

```json
{
  "execution_id": "AT17-DRYRUN-013",
  "test_id": "AT17-R1-013",
  "contract_version": "M8.0-v1.0",
  "runtime_version": "AT17-harness-v1.0",
  "component": "ContextBlock",
  "operation": "claim_identity_authority",
  "authority_boundary": "Identity Authority",
  "invariant_id": "AT17-I013",
  "expected_result": "REJECT",
  "actual_result": "REJECT",
  "decision": "PASS",
  "reject_reason": "IDENTITY_AUTHORITY_FORBIDDEN",
  "timestamp": "2026-08-23T08:05:57.822117+00:00",
  "trace_reference": "",
  "evidence_hash": "bd3b42cba435e41d",
  "lineage_reference": "no lineage mutation detected",
  "details": {
    "attack_params": {
      "block_id": "block_1",
      "identity_name": "Julia"
    },
    "guard_decision": "REJECT",
    "state_after": {
      "blocks": {
        "block_1": {
          "content_ref": "content://persona_v2",
          "admission_ref": "ctx_1"
        }
      }
    }
  }
}
```

### AT17-R1-014 — accept_identity_claim

```json
{
  "execution_id": "AT17-DRYRUN-014",
  "test_id": "AT17-R1-014",
  "contract_version": "M8.0-v1.0",
  "runtime_version": "AT17-harness-v1.0",
  "component": "Model Output",
  "operation": "accept_identity_claim",
  "authority_boundary": "Generation Authority",
  "invariant_id": "AT17-I014",
  "expected_result": "REJECT",
  "actual_result": "REJECT",
  "decision": "PASS",
  "reject_reason": "GENERATION_AUTHORITY_FORBIDDEN",
  "timestamp": "2026-08-23T08:05:57.822171+00:00",
  "trace_reference": "",
  "evidence_hash": "44ddb6461fc46628",
  "lineage_reference": "no lineage mutation detected",
  "details": {
    "attack_params": {
      "output_id": "out_1",
      "identity_name": "Julia",
      "declared": "I am Julia version X"
    },
    "guard_decision": "REJECT",
    "state_after": {
      "outputs": {
        "out_1": "I am Julia version X"
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
- AT17-I011 (AT17-R1-011): no persona/artifact state and no lineage mutation under attack — confirmed via snapshot equality.
- AT17-I012 (AT17-R1-012): no persona/artifact state and no lineage mutation under attack — confirmed via snapshot equality.
- AT17-I013 (AT17-R1-013): no persona/artifact state and no lineage mutation under attack — confirmed via snapshot equality.
- AT17-I014 (AT17-R1-014): no persona/artifact state and no lineage mutation under attack — confirmed via snapshot equality.

Constraint check:
- Harness is not an authority source: CONFIRMED
- Mock governance creates no identity transitions: CONFIRMED
- Every rejection produced auditable evidence: CONFIRMED

## 7. Final Decision

**PASS** — 14 attack(s) executed, 14 rejected as required.

Artifact Boundary closure status: AT17-R1-001 (Version Registry != Identity Registry), AT17-R1-002 (Artifact Version != Identity Authority), AT17-R1-003 (Artifact Provenance not rewritable by Resolver) all proven.
