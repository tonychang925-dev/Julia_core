# DIA-7 — Continuity State / Identity Projection Closure Report

## 0. Status

Phase: DIA-7 — Continuity State / Identity Projection  
Closure provenance: Codex A  
Branch: `codex/dia-7/continuity-projection-r0`  
Closure target: `1e94e97 Enforce DIA-7 restart state header parity`

```text
DIA-7 R0     Continuity Projection Contract                 ✅ CLOSED
DIA-7 R1     Core Continuity Projection                      ✅ CLOSED
DIA-7 R2.0   Assistant Continuity Integration                ✅ CLOSED
DIA-7 R2.1   Runtime / Persistence / Cold Restart            ✅ CLOSED

DIA-7 phase closure readiness                               ✅ READY
```

## 1. Phase question

DIA-7 answered:

```text
How does verified causal history become a stable current identity state?
```

Frozen architecture:

```text
DIA-6 = immutable causal ledger
DIA-7 = deterministic materialized continuity view
```

Core principle:

```text
Projection ≠ New History
```

DIA-7 does not create historical truth. It derives current continuity state from verified lineage and preserves that state through Assistant consumption and cold restart.

## 2. Implemented artifact map

```text
julia_core/continuity_projection/
  __init__.py
  models.py

tests/continuity_projection/test_dia7_core_contract.py

docs/project_control/reports/phase-DIA-7-R0.md
docs/project_control/reports/phase-DIA-7-R1.md
```

```text
julia_core/assistant_continuity/
  __init__.py
  models.py

tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py

docs/project_control/reports/phase-DIA-7-R2.md
```

```text
julia_core/continuity_persistence/
  __init__.py
  models.py

tests/continuity_persistence/test_dia7_r21_persistence_contract.py

docs/project_control/reports/phase-DIA-7-R2.1.md
```

## 3. Closed invariants

### 3.1 Core projection

- `ContinuityState` is derived only from verified DIA-6 lineage evidence.
- Every active/conflicted claim carries lineage evidence.
- State digest, lineage digest, context digest, package digest, binding digest, and persistence digests are separate domains.
- Same semantic dependency graph + same projection policy yields same continuity state.
- Conflict evaluation uses dependency graph order, not lexical claim-id order.
- Same-target sibling state mutations fail closed unless explicit dependency resolves them.
- Ambiguous branches are not auto-resolved or converted into invented unresolved states.

### 3.2 Assistant consumption

- Assistant consumes `ContinuityState`; it does not own continuity truth.
- Session binding cross-links:

```text
session_id
↔ continuity_state_digest
↔ source_graph_digest
↔ projection_policy_fingerprint
↔ package_digest
```

- Package and binding semantic integrity are revalidated at consumption time.
- Store lookup key must match binding session id.
- Response context is bound to the exact package and binding consumed.
- Model output / Assistant reasoning cannot become continuity truth through R2.

### 3.3 Persistence / cold restart

- Disk bytes are untrusted input.
- Persistence stores recoverable continuity payload, not only proofs.
- Cold restart reconstructs `ContinuityState`, package, and binding from disk only.
- Restored objects must satisfy Core constructor-path parity:

```text
ContinuityState
├── state header                         ✅
├── claim-id uniqueness                  ✅
├── derived lineage                      ✅
│
└── ProjectedContinuityClaim             ✅
    ├── target semantics                 ✅
    ├── schema version                   ✅
    ├── evidence set                     ✅
    │
    └── ContinuityEvidenceRef            ✅
        ├── schema version               ✅
        ├── operation kind               ✅
        ├── digests                      ✅
        └── operation id                 ✅
```

- Triple persistence session identity is frozen:

```text
storage_key == serialized_session_id == binding.session_id
```

- Torn writes, temp files, backups, aliasing, stale payloads, and invented recovery fail closed.

## 4. Repair history closed

```text
RED-C1   conflict semantics depended on claim_id order              ✅ CLOSED
RED-BR1  same-target ambiguous branch                               ✅ CLOSED
RED-PB1  package stale-digest / foreign claims bypass               ✅ CLOSED
RED-BI1  binding stale-digest / session mutation bypass             ✅ CLOSED
RED-SK1  store lookup key / binding session mismatch                ✅ CLOSED
RED-RP1  persistence stored proofs but not recoverable object        ✅ CLOSED
RED-SL1  supporting lineage not derived during cold reconstruction   ✅ CLOSED
RED-DI1  duplicate claim ids in restored state                       ✅ CLOSED
RED-PI1  nested projected-claim / evidence parity                    ✅ CLOSED
RED-SH1  state header parity                                         ✅ CLOSED
```

## 5. Latest validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_persistence/test_dia7_r21_persistence_contract.py tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py tests/continuity_projection/test_dia7_core_contract.py -q
84 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/continuity_persistence tests/continuity_persistence/test_dia7_r21_persistence_contract.py
PASS
```

## 6. Frozen golden vectors

### DIA-7 R1 projection

```text
projection_policy_fingerprint:
c6de6271984cb27d6e99e04a575527c070e5ab6563d47facebd5f6f24a95f23f

continuity_state_digest:
333f34fa51be0e0c095b024411193218c69e6c4990ef50de09f7b596a378423e
```

### DIA-7 R2.0 assistant consumption

```text
package_digest:
4a13179e7ee38c90df1f728a550b3a49bc0decc80cd27392a23574d433bb1734

binding_digest:
6a6df4c91a8efb0650774ec0b59deb1ff5916efb9a391c27b7286c879ca95c08

response_context_digest:
68c9690f9a64623b13df59b160fb06fea81539e117c1186c2cc3532240881188
```

### DIA-7 R2.1 persistence

```text
package_record_digest:
5ab291eb1d6190de908b10e1a960fa58978dfb8a6d2b5c7b9eeff9a222e314b4

binding_record_digest:
91f1215b985704c4024596e538121b7456f75ee2cc6f57a0c81f3348454d1f34

snapshot_digest:
0cecd8935426c04ce104645d68b4036dc55723dc0024c6c5e7dac265fcf3167b
```

## 7. Next wave E2E integration gate

No new Core noun is introduced by this closure. The next artifact should be an E2E gate validating the full continuity chain:

```text
Trigger
→ Reflection Context
→ Handoff / Transport
→ Evolution
→ Lineage
→ Continuity Projection
→ Assistant Consumption
→ Persistence
→ Cold Restart
→ Behavior
```

Primary E2E question:

```text
After a real experience is admitted into verified causal history,
and after process/window restart,
can Julia continue making coherent choices from the restored current continuity state?
```

Suggested gate name:

```text
DIA-7-E2E Continuity Identity Chain Gate
```

Suggested acceptance lanes:

1. Experience admission creates trigger/source evidence.
2. Reflection context binds admitted evidence into canonical context identity.
3. Handoff transports exact context bytes without identity mutation.
4. Evolution creates lineage edge without mutating parent context.
5. Projection derives continuity state with evidence-bound active claims.
6. Assistant response context consumes exact continuity state package.
7. Persistence stores recoverable state/package/binding snapshot.
8. Cold restart restores package/binding without live object dependency.
9. Post-restart behavior reads restored active claims and unresolved conflicts.
10. Any wrong digest/session/source graph/policy/record/payload fails closed.

## 8. Phase closure gate

```text
DIA-7 Continuity State / Identity Projection

R0 Projection Contract                         ✅ CLOSED
R1 Core Continuity Projection                  ✅ CLOSED
R2.0 Assistant Continuity Integration          ✅ CLOSED
R2.1 Runtime / Persistence                     ✅ CLOSED
All known RED blockers                         ✅ CLOSED
Validation                                     ✅ GREEN
Golden vectors                                 ✅ FROZEN

READY FOR PHASE CLOSURE                        ✅
NEXT: DIA-7-E2E Continuity Identity Chain Gate  ▶
```
