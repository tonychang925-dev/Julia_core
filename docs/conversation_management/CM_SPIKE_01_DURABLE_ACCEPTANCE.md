# CM-SPIKE-01 — Durable User Acceptance Feasibility Report

**Date:** 2026-08-10  
**Status:** COMPLETE  
**Question:** Can accept_user_turn() durably write a user message before returning ACK, such that kill-9 recovery works?

---

## 1. Experimental Setup

```
Test module:   tests/spikes/test_cm_spike_01_durable_acceptance.py
Primitive:     accept_user_turn(repo, conversation_id, turn_id, modality, content)
Dependency:    SessionRepository (existing production code, no modifications)
Store:         Temp copies of conversations.json (NOT production data)
Production mutation: 0
```

### accept_user_turn semantics

1. Validate conversation exists
2. Idempotency check (same turn_id + same content → ACK, no duplicate)
3. Conflict check (same turn_id + different content → TurnConflictError)
4. `repo.add_message(status="accepted")` → calls `_save()` → fsync + os.replace
5. Return ACK with `durable=true`

Key: step 4 completes (fsync confirmed) BEFORE step 5 returns ACK.

---

## 2. Results

### SP-01 Normal Durable Append — PASS
```
accept T17 → ACK {accepted:true, durable:true}
restart → T17 content="hello spike", status="accepted"
```

### SP-02 Idempotent Retry — PASS
```
accept(T17, "hello") → ACK, idempotent=false
accept(T17, "hello") → ACK, idempotent=true
restart → exactly 1 message for T17
```

### SP-03 ID/Content Conflict — PASS
```
accept(T17, "original") → ACK
accept(T17, "different") → TurnConflictError
restart → T17 content = "original" (not overwritten)
```

### SP-04 Crash-After-ACK Recovery — PASS
```
Subprocess: accept → write ACK witness → exit (simulated kill-9)
Reload store → T17 "crash-after-ack-test" present with status="accepted"
```

### SP-05 Cognition Independence — PASS
```
accept T17 → simulated cognition failure
T17 still present after reload, status="accepted"
```

### SP-06 Same-Conversation Concurrency — PASS
```
10 threads, 10 distinct turn_ids → 10 successes
Reload → exactly 10 user turns, no corruption
Reload again → consistent
```

### SP-07 Cross-Conversation Isolation — PASS
```
4 threads: A1, B1, A2, B2 (interleaved)
Reload: A={A1, A2}, B={B1, B2}
Zero cross-contamination
```

### SP-08 Existing-Store Compatibility — PASS
```
Load existing-format JSON → append new turn → reload
Existing message preserved, new message present
```

### SP-09 Sequential Latency Benchmark
```
N = 500 sequential writes, 0 errors

p50:    3.93ms
p95:    7.73ms
p99:    9.96ms
max:   11.63ms

All measurements below 50ms engineering SLO.
Note: whole-file JSON rewrite; latency grows with file size.
```

### SP-10 FS-Level Durability — PASS
```
SessionRepository._save() confirmed:
  ✅ os.fsync (durability boundary)
  ✅ os.replace (atomic rename)
  ✅ temp-file pattern (write to .tmp, rename to .json)
```

---

## 3. Contract Implication

### Verdict: FEASIBLE_WITH_STORAGE_CHANGE ⬡

The CM-I05 invariant (durable user acceptance before ACK) is **semantically validated** by the existing `SessionRepository` atomic write pattern. All 8 sabotage tests pass.

However, the current single-JSON-file storage has a known scalability limitation:

```
Latency grows linearly with total store size.
p50=3.9ms at ~500 messages.
Estimated p50 at 10,000 messages: proportionally higher.
```

This does **not** challenge CM-I05. It means:
- CM-I05 is architecturally valid ✅
- Current persistence primitive is functionally correct ✅
- Storage implementation may need evolution for scale ⬡
- Contract freezing is NOT blocked by storage concerns ⬡

### What this spike does NOT change

```
CM-I05 semantics:            UNCHANGED
CM-Core invariants:          UNCHANGED
Production code:             0 modifications
Production conversations.json:  untouched
```

---

## 4. CM-SPIKE-01 Exit Gate

```
SP-01 Normal durable append            ✅ PASS
SP-02 Idempotent retry                 ✅ PASS
SP-03 ID/content conflict              ✅ PASS
SP-04 Crash-after-ACK recovery         ✅ PASS
SP-05 User survives cognition failure  ✅ PASS
SP-06 Same-conversation safety         ✅ PASS
SP-07 Cross-conversation isolation     ✅ PASS
SP-08 Existing-store compatibility     ✅ PASS
SP-09 Latency benchmark                ✅ p50=3.9ms
SP-10 fsync confirmed                   ✅ PASS

Production mutation                    0

Durability semantics                   ✅ PASS
Feasibility                            B (FEASIBLE_WITH_STORAGE_CHANGE)

CM-Core Final Freeze                   🟢 NOT BLOCKED
→ CM-Core v1.0 🔒 FROZEN
→ ConversationRuntime v2 GO
```

---

*End CM-SPIKE-01*
