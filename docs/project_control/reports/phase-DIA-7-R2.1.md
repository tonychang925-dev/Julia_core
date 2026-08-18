# DIA-7 R2.1 — Runtime / Persistence Continuity Contract

## 0. Status

Phase: DIA-7 — Continuity State / Identity Projection  
Artifact: R2.1 Runtime / Persistence implementation  
Implementation provenance: Codex A  
Branch: `codex/dia-7/continuity-projection-r0`  
Base: DIA-7 R2.0.2 Assistant Continuity Integration `b8b2fe9`

DIA-7 R2.0.2 is treated as FINAL / CLOSED / FROZEN input.

R2.1 persists continuity trust artifacts. It does not create, repair, reinterpret, upgrade, or recover continuity truth.

## 1. Implemented module

```text
julia_core/continuity_persistence/
  __init__.py
  models.py

tests/continuity_persistence/test_dia7_r21_persistence_contract.py
```

Public runtime nouns:

- `PersistedContinuityBindingRecord`
- `PersistedContinuityPackageRecord`
- `ContinuityRuntimeSnapshot`
- `ContinuityPersistenceStore`
- `ContinuityPersistenceTransaction`
- `ContinuityRestartLoader`
- `ContinuityReplayGuard`
- `ContinuityPersistenceAudit`
- `StrictContinuityPersistenceRuntime`

## 2. Boundary

Valid path:

```text
Core ContinuityState
        ↓
R2.0 AssistantContinuityStatePackage / AssistantContinuitySessionBinding
        ↓
R2.1 persisted package/binding records
        ↓
ContinuityRuntimeSnapshot
        ↓
disk / restart / replay validation
```

Invalid path:

```text
persisted bytes
        ↓
trusted runtime state without reconstruction + digest validation + cross-binding
```

Disk bytes are untrusted input, including bytes written by this runtime earlier.

## 3. Triple session identity

R2.1 freezes:

```text
storage_key
== serialized_session_id
== binding.session_id
```

Any mismatch fails closed. No alias, fallback, recovery, or repair path exists in R2.1.

## 4. Persistence identity domains

R2.1 keeps separate identity domains:

```text
continuity_state_digest
package_digest
binding_digest
package_record_digest
binding_record_digest
snapshot_digest
```

Persistence record / snapshot digests exclude filesystem path, mtime, audit timestamp, runtime host, and process metadata.

## 5. Record validation

`PersistedContinuityPackageRecord` binds:

- session id
- continuity state digest
- source graph digest
- projection policy fingerprint
- package digest
- continuity state semantic payload SHA-256
- package record digest

`PersistedContinuityBindingRecord` binds:

- storage key
- serialized session id
- continuity state digest
- source graph digest
- projection policy fingerprint
- package digest
- binding digest
- binding record digest

Deserialization reconstructs record objects and recomputes record digests before acceptance.

## 6. Snapshot validation

`ContinuityRuntimeSnapshot` cross-binds package and binding records:

- storage/session identity equality
- state digest equality
- source graph digest equality
- projection policy fingerprint equality
- package digest equality
- snapshot digest recomputation

Package A + Binding B and old-package/new-binding torn snapshots fail closed.

## 7. Store semantics

`ContinuityPersistenceStore` writes complete snapshots only.

Write path:

```text
prepare complete snapshot
        ↓
validate snapshot
        ↓
write temp file
        ↓
read-back temp file and reconstruct snapshot
        ↓
atomic replace authoritative snapshot file
        ↓
read-back authoritative file and reconstruct snapshot
        ↓
return transaction
```

Restart path:

```text
read authoritative snapshot file
        ↓
deserialize bytes
        ↓
reconstruct records
        ↓
recompute record and snapshot digests
        ↓
key/session reconciliation
        ↓
return snapshot
```

Temporary files and backup files are not authoritative restart records.

## 8. Idempotency / replay

Duplicate semantics:

```text
same session + same snapshot digest
        → idempotent accept

same session + different snapshot digest
        → reject
```

R2.1 does not implement session evolution / rebinding.

`ContinuityReplayGuard` validates persisted snapshot against live R2.0 package and binding before replay acceptance.

## 9. Unsupported recovery semantics

R2.1 explicitly does not support:

- partial/torn write recovery
- stale backup fallback
- temp-file promotion on restart
- alias-based session recovery
- automatic repair of corrupted records
- automatic migration / upgrade of old records

Unsupported recovery cases fail closed.

## 10. Golden vectors

Fixed DIA-7 R2.1 fixture vectors:

```text
package_record_digest:
809ba8fa5a18ed8fae9713f2901157d1158cc0188df32946e963878b7eb808d0

binding_record_digest:
91f1215b985704c4024596e538121b7456f75ee2cc6f57a0c81f3348454d1f34

snapshot_digest:
35bcc4a6bc689901084c9943d8f99b6e2a9c205ba6899a17cc841c176faec71f
```

## 11. Acceptance matrix

| Acceptance target | Status |
| --- | --- |
| storage key / serialized session / binding session triple identity | ✅ |
| persisted record digest recomputed on deserialize | ✅ |
| package A + binding B rejected | ✅ |
| old package + new binding torn snapshot rejected | ✅ |
| corrupted / truncated persisted bytes fail restart | ✅ |
| exact duplicate write idempotent | ✅ |
| same session different binding rejected | ✅ |
| temp file not authoritative | ✅ |
| corrupt primary does not fallback to stale backup | ✅ |
| replay guard validates snapshot/package/binding chain | ✅ |
| audit metadata does not affect snapshot identity | ✅ |
| golden vectors frozen | ✅ |

## 12. Owner validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_persistence/test_dia7_r21_persistence_contract.py -q
11 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_persistence/test_dia7_r21_persistence_contract.py tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py tests/continuity_projection/test_dia7_core_contract.py -q
59 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/continuity_persistence tests/continuity_persistence/test_dia7_r21_persistence_contract.py
PASS
```

## 13. R2.1 Gate summary

```text
DIA-7 R2.1 Runtime / Persistence Continuity Contract

Codex A implementation                    ✅ COMPLETE
DIA-7 R2.1 focused tests                   ✅ 11 passed
DIA-7 R2/R1 regression                     ✅ included in 59 passed
DIA-6/DIA-5/DIA-4/DIA-3 regression         ✅ 97 passed
compileall                                 ✅ PASS

Ready for Mira review                      ▶
Codex B sabotage                           ⏸ HOLD
Final freeze                               ⏸
```

---

# DIA-7 R2.1.1 — RED-RP1 Recoverable Payload Repair

## 14. Repair status

Previous target: `7a596af214f648de5de791deb7f8d362ab5bada7`  
Mira review: RED-RP1 accepted  
Repair provenance: Codex A

Blocked finding:

```text
Persistence persisted proofs, not the persisted object.
```

The previous snapshot stored package/binding metadata and digests, but did not persist enough semantic payload to rebuild `ContinuityState`, `AssistantContinuityStatePackage`, and `AssistantContinuitySessionBinding` after process death.

## 15. Repair scope

R2.1 package record now includes recoverable `continuity_state_payload` plus payload SHA. Restart now returns a restored runtime artifact instead of only a proof snapshot.

Changed:

- `julia_core/continuity_persistence/models.py`
- `julia_core/continuity_persistence/__init__.py`
- `tests/continuity_persistence/test_dia7_r21_persistence_contract.py`
- `docs/project_control/reports/phase-DIA-7-R2.1.md`

## 16. Restored runtime path

Cold restart now performs:

```text
authoritative snapshot file
    ↓
deserialize snapshot
    ↓
validate snapshot/record digests
    ↓
extract persisted ContinuityState payload
    ↓
reconstruct exact ContinuityState semantic object
    ↓
recompute continuity_state_digest
    ↓
construct AssistantContinuityStatePackage through R2.0 constructor
    ↓
construct AssistantContinuitySessionBinding(session_id, package)
    ↓
compare reconstructed package/binding identities against persisted records
    ↓
return RestoredContinuityRuntime(snapshot, state, package, binding)
```

Binding is not trusted by raw JSON field assignment. It is reconstructed through the R2.0 constructor, then compared against persisted binding record identity.

## 17. New noun

Added:

- `RestoredContinuityRuntime`

Fields:

- `snapshot`
- `continuity_state`
- `package`
- `binding`

## 18. RED-RP1 acceptance matrix

| RED-RP1 repair target | Status |
| --- | --- |
| True cold restart restores package + binding using disk only | ✅ |
| Restart API requires no external live Package/Binding | ✅ |
| Persisted state payload tamper with old SHA/digests rejects | ✅ |
| Attacker recomputes payload SHA only -> record/snapshot identity rejects | ✅ |
| Package-record metadata A + foreign semantic payload B rejects | ✅ |
| Cold-restored package/binding can create R2.0 response context | ✅ |
| Existing record / snapshot / triple-session / torn-write tests remain green | ✅ |

## 19. Updated golden vectors

Package record and snapshot identities changed because recoverable payload is now included in package record semantic identity.

```text
package_record_digest:
5ab291eb1d6190de908b10e1a960fa58978dfb8a6d2b5c7b9eeff9a222e314b4

binding_record_digest:
91f1215b985704c4024596e538121b7456f75ee2cc6f57a0c81f3348454d1f34

snapshot_digest:
0cecd8935426c04ce104645d68b4036dc55723dc0024c6c5e7dac265fcf3167b
```

## 20. Repair validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_persistence/test_dia7_r21_persistence_contract.py -q
16 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_persistence/test_dia7_r21_persistence_contract.py tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py tests/continuity_projection/test_dia7_core_contract.py -q
64 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/continuity_persistence tests/continuity_persistence/test_dia7_r21_persistence_contract.py
PASS
```

## 21. Repair gate summary

```text
DIA-7 R2.1.1 Runtime / Persistence Continuity Contract

RED-RP1 recoverable cold restart payload       ✅ CLOSED
DIA-7 R2.1 focused tests                       ✅ 16 passed
DIA-7 R2/R1 regression                         ✅ included in 64 passed
DIA-6/DIA-5/DIA-4/DIA-3 regression             ✅ 97 passed
compileall                                      ✅ PASS

Ready for Mira re-review                       ▶
Codex B sabotage                               ⏸ HOLD
Final freeze                                   ⏸
```

---

# DIA-7 R2.1.2 — RED-SL1 Derived Lineage Invariant Repair

## 22. Repair status

Previous target: `b3dbbf7`  
Review: RED-SL1 accepted  
Repair provenance: Codex A

Blocked finding:

```text
supporting_lineage_digests could be trusted from persisted payload
instead of being re-derived from claim evidence during cold restart.
```

This allowed a reconstructed `ContinuityState` payload to carry a self-consistent digest over an invalid lineage summary if payload fields were treated as authoritative.

## 23. Closed invariant

R2.1.2 freezes:

```text
ContinuityState.supporting_lineage_digests
must equal the sorted unique union of every lineage_digest
in active_claims + unresolved_conflicts supporting_evidence_refs.
```

During cold restart reconstruction:

```text
persisted state payload
    ↓
reconstruct projected claims and evidence refs
    ↓
derive lineage digest union from evidence
    ↓
compare against payload.supporting_lineage_digests
    ↓
only then accept state digest validation
```

The persisted `supporting_lineage_digests` field is no longer trusted as an independent truth source.

## 24. RED-SL1 acceptance matrix

| RED-SL1 repair target | Status |
| --- | --- |
| Missing supporting lineage digest rejects on restart | ✅ |
| Extra underived supporting lineage digest rejects on restart | ✅ |
| Claim evidence changed without matching derived lineage set rejects | ✅ |
| Existing cold restart / payload recovery remains green | ✅ |

## 25. Repair validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_persistence/test_dia7_r21_persistence_contract.py -q
19 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_persistence/test_dia7_r21_persistence_contract.py tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py tests/continuity_projection/test_dia7_core_contract.py -q
67 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/continuity_persistence tests/continuity_persistence/test_dia7_r21_persistence_contract.py
PASS
```

## 26. Repair gate summary

```text
DIA-7 R2.1.2 Runtime / Persistence Continuity Contract

RED-RP1 recoverable cold restart payload       ✅ CLOSED
RED-SL1 derived lineage invariant              ✅ CLOSED
DIA-7 R2.1 focused tests                       ✅ 19 passed
DIA-7 R2/R1 regression                         ✅ included in 67 passed
DIA-6/DIA-5/DIA-4/DIA-3 regression             ✅ 97 passed
compileall                                      ✅ PASS

Ready for Mira re-review                       ▶
Codex B re-sabotage                            ⏸ HOLD
Final freeze                                   ⏸
```

---

# DIA-7 R2.1.3 — RED-DI1 Constructor Invariant Parity Repair

## 27. Repair status

Previous target: `1394b28`  
Review: RED-DI1 accepted  
Repair provenance: Codex A

Blocked finding:

```text
cold reconstruction used ContinuityState.__new__ and could miss Core constructor invariants.
```

Specific blocker:

```text
claim_id must be unique across active_claims + unresolved_conflicts.
```

## 28. Constructor parity invariant

R2.1.3 freezes:

```text
Cold reconstruction must re-enforce every ContinuityState constructor invariant
before digest acceptance.
```

Reconstruction validation order:

```text
reconstruct active / conflicted projected claims
    ↓
sort canonical claim collections
    ↓
validate projected-claim shape parity
    ↓
validate duplicate claim ids across active + unresolved
    ↓
derive supporting lineage from evidence
    ↓
compare derived lineage with payload lineage field
    ↓
validate continuity_state_digest
```

Additional parity checks now enforced:

- active collection contains only `ProjectedContinuityClaim` with `ACTIVE` status
- unresolved collection contains only `ProjectedContinuityClaim` with `CONFLICTED` status
- claim ids unique across active + unresolved
- claim ids / payload / projection rule id non-empty
- evidence refs are non-empty per claim
- evidence refs are duplicate-free per claim
- evidence lineage / parent / child digests are SHA-256
- evidence operation id non-empty

## 29. RED-DI1 acceptance matrix

| RED-DI1 repair target | Status |
| --- | --- |
| duplicate within active_claims -> reject | ✅ |
| duplicate within unresolved_conflicts -> reject | ✅ |
| same claim_id across active + unresolved -> reject | ✅ |
| distinct IDs with identical payloads -> valid shape | ✅ |
| valid cold restart remains green | ✅ |
| golden vectors unchanged | ✅ |

## 30. Repair validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_persistence/test_dia7_r21_persistence_contract.py -q
23 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_persistence/test_dia7_r21_persistence_contract.py tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py tests/continuity_projection/test_dia7_core_contract.py -q
71 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/continuity_persistence tests/continuity_persistence/test_dia7_r21_persistence_contract.py
PASS
```

Golden vectors remain stable from R2.1.1 / R2.1.2:

```text
package_record_digest:
5ab291eb1d6190de908b10e1a960fa58978dfb8a6d2b5c7b9eeff9a222e314b4

binding_record_digest:
91f1215b985704c4024596e538121b7456f75ee2cc6f57a0c81f3348454d1f34

snapshot_digest:
0cecd8935426c04ce104645d68b4036dc55723dc0024c6c5e7dac265fcf3167b
```

## 31. Repair gate summary

```text
DIA-7 R2.1.3 Runtime / Persistence Continuity Contract

RED-RP1 recoverable cold restart payload       ✅ CLOSED
RED-SL1 derived lineage invariant              ✅ CLOSED
RED-DI1 duplicate claim ids / constructor parity ✅ CLOSED
DIA-7 R2.1 focused tests                       ✅ 23 passed
DIA-7 R2/R1 regression                         ✅ included in 71 passed
DIA-6/DIA-5/DIA-4/DIA-3 regression             ✅ 97 passed
compileall                                      ✅ PASS

Ready for Mira re-review                       ▶
Codex B re-sabotage                            ⏸ HOLD
Final freeze                                   ⏸
```

---

# DIA-7 R2.1.4 — RED-PI1 Nested Constructor Parity Repair

## 32. Repair status

Previous target: `e2e7308`  
Review: RED-PI1 accepted  
Repair provenance: Codex A

Blocked finding:

```text
cold reconstruction enforced ContinuityState shape,
but nested ProjectedContinuityClaim / ContinuityEvidenceRef constructor parity
could still be bypassed by __new__ reconstruction.
```

## 33. Nested constructor parity invariant

R2.1.4 freezes:

```text
Every reconstructed Core object must satisfy the invariants of the Core
constructor path that could legally have produced it.
```

Nested projected-claim parity now enforces:

- `target_claim_id` non-empty
- projected claim schema version equals frozen DIA-7 Continuity Projection version
- `APPEND` requires `target_claim_id == "none"`
- non-`APPEND` rules require `target_claim_id != "none"`

Nested evidence-ref parity now enforces:

- evidence ref schema version equals frozen DIA-7 Continuity Projection version
- `operation_kind` is exact DIA-6 `ContextEvolutionKind`
- lineage / parent / child digests are SHA-256
- operation id non-empty

## 34. RED-PI1 acceptance matrix

| RED-PI1 repair target | Status |
| --- | --- |
| APPEND + target != none -> reject | ✅ |
| non-APPEND + target == none -> reject | ✅ |
| empty target_claim_id -> reject | ✅ |
| foreign projected claim schema_version -> reject | ✅ |
| foreign evidence schema_version -> reject | ✅ |
| valid CORRECT / SUPERSEDE / DEPRECATE / UNRESOLVED target shapes -> green | ✅ |
| valid APPEND + none -> green | ✅ |
| golden vectors unchanged | ✅ |

## 35. Repair validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_persistence/test_dia7_r21_persistence_contract.py -q
30 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_persistence/test_dia7_r21_persistence_contract.py tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py tests/continuity_projection/test_dia7_core_contract.py -q
78 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/continuity_persistence tests/continuity_persistence/test_dia7_r21_persistence_contract.py
PASS
```

Golden vectors remain stable:

```text
package_record_digest:
5ab291eb1d6190de908b10e1a960fa58978dfb8a6d2b5c7b9eeff9a222e314b4

binding_record_digest:
91f1215b985704c4024596e538121b7456f75ee2cc6f57a0c81f3348454d1f34

snapshot_digest:
0cecd8935426c04ce104645d68b4036dc55723dc0024c6c5e7dac265fcf3167b
```

## 36. Repair gate summary

```text
DIA-7 R2.1.4 Runtime / Persistence Continuity Contract

RED-RP1 recoverable cold restart payload       ✅ CLOSED
RED-SL1 derived lineage invariant              ✅ CLOSED
RED-DI1 duplicate claim ids / constructor parity ✅ CLOSED
RED-PI1 nested projected-claim/evidence parity ✅ CLOSED
DIA-7 R2.1 focused tests                       ✅ 30 passed
DIA-7 R2/R1 regression                         ✅ included in 78 passed
DIA-6/DIA-5/DIA-4/DIA-3 regression             ✅ 97 passed
compileall                                      ✅ PASS

Ready for Mira re-review                       ▶
Codex B re-sabotage                            ⏸ HOLD
Final freeze                                   ⏸
```

---

# DIA-7 R2.1.5 — RED-SH1 State Header Parity Repair

## 37. Repair status

Previous target: `ad920c0`  
Review: RED-SH1 accepted  
Repair provenance: Codex A

Blocked finding:

```text
cold reconstruction enforced state shape and nested claim/evidence parity,
but state-level header fields could still be restored as arbitrary payload fields.
```

## 38. Header constructor parity invariant

R2.1.5 freezes:

```text
Restored ContinuityState header fields must satisfy the Core constructor path
shape before claim reconstruction and before digest acceptance.
```

Header parity now enforces:

- `state_schema_version == dia7-continuity-projection-v1`
- `projection_policy_revision` non-empty
- `projection_policy_fingerprint` is SHA-256
- `source_graph_revision` non-empty
- `source_graph_digest` is SHA-256
- `continuity_state_digest` is SHA-256

This does not attempt to prove the current policy object still exists. It only proves the restored state header has a shape Core could have produced.

## 39. Full cold reconstruction parity tree

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

## 40. RED-SH1 acceptance matrix

| RED-SH1 repair target | Status |
| --- | --- |
| foreign state_schema_version with recomputed payload digest -> reject | ✅ |
| empty projection_policy_revision -> reject | ✅ |
| malformed projection_policy_fingerprint -> reject | ✅ |
| empty source_graph_revision -> reject | ✅ |
| malformed source_graph_digest -> reject | ✅ |
| valid original state header -> green | ✅ |
| golden vectors unchanged | ✅ |

## 41. Repair validation evidence

Executed by Codex A:

```text
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_persistence/test_dia7_r21_persistence_contract.py -q
36 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/continuity_persistence/test_dia7_r21_persistence_contract.py tests/assistant_continuity/test_dia7_r2_assistant_continuity_contract.py tests/continuity_projection/test_dia7_core_contract.py -q
84 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest tests/context_evolution/test_dia6_core_contract.py tests/reflection_handoff/test_dia5_core_contract.py tests/reflection_context/test_dia4_core_contract.py tests/reflection_trigger/test_dia3_core_contract.py -q
97 passed

/opt/miniconda3/envs/theme_matcher_env/bin/python -m compileall -q julia_core/continuity_persistence tests/continuity_persistence/test_dia7_r21_persistence_contract.py
PASS
```

Golden vectors remain stable:

```text
package_record_digest:
5ab291eb1d6190de908b10e1a960fa58978dfb8a6d2b5c7b9eeff9a222e314b4

binding_record_digest:
91f1215b985704c4024596e538121b7456f75ee2cc6f57a0c81f3348454d1f34

snapshot_digest:
0cecd8935426c04ce104645d68b4036dc55723dc0024c6c5e7dac265fcf3167b
```

## 42. Repair gate summary

```text
DIA-7 R2.1.5 Runtime / Persistence Continuity Contract

RED-RP1 recoverable cold restart payload          ✅ CLOSED
RED-SL1 derived lineage invariant                 ✅ CLOSED
RED-DI1 state shape parity                        ✅ CLOSED
RED-PI1 nested projected-claim/evidence parity    ✅ CLOSED
RED-SH1 state header parity                       ✅ CLOSED
DIA-7 R2.1 focused tests                          ✅ 36 passed
DIA-7 R2/R1 regression                            ✅ included in 84 passed
DIA-6/DIA-5/DIA-4/DIA-3 regression                ✅ 97 passed
compileall                                         ✅ PASS

Ready for Mira re-review                          ▶
Codex B re-sabotage                               ⏸ HOLD
Final freeze                                      ⏸
```
