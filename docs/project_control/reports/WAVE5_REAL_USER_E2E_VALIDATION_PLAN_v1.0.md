# WAVE5_REAL_USER_E2E_VALIDATION_PLAN_v1.0

Status: VALIDATION PLAN (execution pending)
Date: 2026-08-24
Prerequisite: AT-01~20 PASS (engineering acceptance)
Gate: Final Freeze is WAITING for Real User E2E — pytest PASS does not equal user-perceived continuity.

---

## 0. Why This Layer Exists

AT-01~20 prove the system does not LOSE continuity at the design/boundary
level (component & boundary verification).

Real User E2E proves a real user, using the real entry points and the real
service chain, does not EXPERIENCE continuity breakage.

```text
AT = component/boundary verification (necessary)
Real User E2E = user-perceived continuity (sufficient for freeze)
Both required before Wave5 Final Freeze.
```

## 1. Objective

A real user goes through a complete session lifecycle from the real entry
point; after real lifecycle events (client close / Brain restart / S2S
disconnect), the recovered continuity matches the user's perception.

## 2. Real User E2E Scenarios

### E2E-01 — Create a real user session

Entry: Electron Client → Brain :18089 (text) / S2S :8765 (voice).

User actions:

```text
Text message
Voice message
Multiple turns
```

Produced:

```text
Conversation
+ Turns
+ Metadata
```

### E2E-02 — Real lifecycle events (no mocks)

```text
Client:   close Electron
Backend:  restart Brain :18089
Voice:    disconnect S2S :8765
```

Real components, real processes — not test mocks.

### E2E-03 — User returns

Restart:

```text
Electron
Brain
S2S
```

User provides only:

```text
conversation_id (or normal login context)
```

### E2E-04 — User verifies continuity

From the USER'S VIEW (not just DB):

```text
history still present
order correct
voice/text mixed timeline normal
diary not lost
no duplicate messages
no "start over" feeling
```

## 3. Evidence Requirements

Not just `pytest passed`. Required:

### Before Snapshot

```json
{
  "conversation_id": "",
  "turn_count": 0,
  "last_turn": "",
  "diary_refs": []
}
```

### Lifecycle Event Log

```text
Electron shutdown   <timestamp>
Brain restart       <timestamp>
S2S reconnect       <timestamp>
```

### After Snapshot (compare before == after)

```text
conversation lineage
turn ordering
diary provenance
references
```

## 4. Execution Environment (real service chain)

```text
[Mac]    Electron v2  → Brain :18089 → ConversationRuntime
                            ↑
         tunnel -R 8089:18089 (AutoDL bridge)
[AutoDL] Frontend :7860 ← S2S :8765 → 8089 tunnel → Mac Brain
```

- Brain: launchd `com.julia.brain.18089` (approved SHA)
- S2S/Frontend: AutoDL release `98071f3` (SOP v1.1)
- Voice tunnel: Mac 7860/8765 → AutoDL

## 5. Pass Criteria

```text
[ ] E2E-01 session created with text + voice turns (real entry points)
[ ] E2E-02 lifecycle events executed on real components
[ ] E2E-03 recovery with only conversation_id
[ ] E2E-04 user-visible continuity: before == after snapshots
    (lineage / order / modality / diary / no duplicates)
[ ] Evidence bundle produced (before/after + event log)
```

## 6. Gate

```text
AT-01~20:            PASS ✅
Engineering Acceptance: PASS ✅
Real User E2E:       PENDING ⏳  ← THIS PLAN
Final Freeze:        WAITING FOR E2E
```

## 7. Note

No Freeze Record will be generated until Real User E2E passes.
