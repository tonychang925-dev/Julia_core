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
