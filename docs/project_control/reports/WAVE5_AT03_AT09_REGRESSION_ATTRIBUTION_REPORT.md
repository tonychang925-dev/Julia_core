# WAVE5_AT03_AT09_REGRESSION_ATTRIBUTION_REPORT

Status: ATTRIBUTION COMPLETE (patch pending approval)
Date: 2026-08-23
Repository: `/Users/admin/julia_core` / branch `wave5/authority-consolidation`
Suite: `tests/wave5/` — 100 passed / **14 failed**

---

## Summary

All 14 failures classified as **Category B — Real Regression**.
No Category A (expected boundary evolution), no Category C (test infrastructure drift).

Failures converge to **two root-cause clusters**:

```text
Cluster R1 (3 failures): conversation_id allocation collision   → authority impact HIGH
Cluster R2 (11 failures): canonical history projection drops    → authority impact MED
                              authority-defining fields
```

| Cluster | Failures | Classification | Authority impact |
|---|---|---|---|
| R1 | 3 | B | HIGH (identity allocator uniqueness lost) |
| R2 | 11 | B | MED (read projection degraded; persistence intact) |

---

# Regression Attribution Record — Cluster R1

## Conversation_id allocation collision

Test (3):
- `test_at05_retry_idempotency.py::test_tc_at05_r1_007_same_turn_id_in_different_conversations_is_isolated`
- `test_at06_cross_conversation_sabotage.py::test_tc_at06_r1_006_storage_marker_isolation_through_reads_and_recovery`
- `test_at06_cross_conversation_sabotage.py::test_tc_at06_r1_008_runtime_interaction_cache_is_conversation_scoped`

Failure:
- R1-007: `TurnConflictError: Turn shared-turn-string: content differs from persisted`
- R1-006: `BETA_PRIVATE_MARKER_002` leaked into conversation A text
- R1-008: `state_b.identity_checks == 1` (expected 0)

Observed:
- `conversation_runtime.py:395` allocates `f"conv_{time}_{id(self)}"`.
  Two `create_conversation()` calls on the same runtime within the same second
  return the SAME conversation_id (verified empirically).

Expected:
- Each create produces a distinct canonical conversation_id (conversation
  isolation invariant, AT-05/AT-06 frozen).

Classification: **B**

Boundary: Conversation Identity Authority — the Core identity allocator.

Authority impact:
- HIGH. The identity allocator loses uniqueness → different logical
  conversations collapse into one canonical conversation → storage / cache /
  idempotency / search all see merged state. Silent cross-conversation
  leakage within the same second.

Lineage impact: HIGH (turn identity collides across conversations).

Decision: **Code fix required** — restore unique allocation.

Evidence:
- `conversation_runtime.py:395` (collision), at04 `conversation_runtime.py:592`
  uses `f"conv_{uuid.uuid4().hex}"` (unique).

Action (pending approval): adopt `allocate_conversation_id()` → `uuid.uuid4().hex`.

---

# Regression Attribution Record — Cluster R2

## Canonical history projection drops authority-defining fields

Test (11):
- `test_at03_text_voice_text.py::test_tc_at03_r1_001` / `_004` / `_005`
- `test_at04_unknown_conversation_reject.py::test_tc_at04_rem_p0g2_003`
- `test_at04_voice_reconnect_uuid_identity.py::test_tc_at04_r1_001` / `_005` / `_006`
- `test_at05_integration_acceptance.py::test_tc_at05_ia_005`
- `test_at05_retry_idempotency.py::test_tc_at05_r1_008`
- `test_at07_integration_acceptance.py::test_tc_at07_ia_004`
- `test_at07_segment_boundary.py::test_tc_at07_r1_004`

Failure:
- `KeyError: 'turn_id'` / `KeyError: 'modality'` (cluster 1)
- `active_tail_turn_ids == []` / `context_000 not in visible` (cluster 4)

Observed:
- `conversation_runtime.py:201-205` `get_canonical_history` returns only
  `{"role": m.role, "content": m.content}`, dropping
  turn_id / modality / status / conversation_id.
- Downstream `_scope_history_to_conversation` (context_execution_runtime.py:383)
  then discards ALL messages as unscoped → active tail empty.

Expected:
- Canonical history carries full message fidelity (turn_id, modality,
  status, conversation_id) — the AT-03/04/07 frozen invariants read these
  authority-defining fields.

Classification: **B**

Boundary: Canonical read model / Conversation identity projection.

Authority impact:
- MED. Persistence is intact; the read projection degrades. turn_id / modality
  are AT-03-frozen authority invariants — their absence breaks canonical-order
  verification and disables Context OS conversation scoping (active tail empty).

Lineage impact: MED (turn identity invisible in history projection).

Decision: **Code fix required** — restore full-fidelity projection.

Evidence:
- `conversation_runtime.py:201-205` (drops fields, despite docstring claiming
  "FULL completed canonical history"), at04 branch contains the full-fidelity
  repair (`fe8ba2c` W4-BASE-R2) not merged into cm-r0-fix.

Action (pending approval): return `m.to_dict()` (full fidelity) from
`get_canonical_history`.

---

## Fix Priority

```text
1. Cluster R1 (conversation_id uniqueness)     — HIGH authority impact, silent
2. Cluster R2 (full-fidelity history)          — restores 11 failures
```

Both fixes are minimal, restore frozen behavior, and do NOT change the
authority model. Tests and harness need no modification.

## Acceptance of this report

```text
[ ] Attribution complete (14/14 → R1×3 + R2×11)
[ ] Classification: B (real regression), no A/C
[ ] Root causes code-verified
[ ] Fix plan minimal, authority-neutral
```

Patch code ONLY after this report is accepted.
