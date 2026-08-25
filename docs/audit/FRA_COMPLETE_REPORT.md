# FRA — FULL REALITY & ARCHITECTURE AUDIT
**Date: 2026-08-10 | Mode: READ ONLY | Changes: 0**

---

## FRA-A: VERSION AUTHORITY MATRIX

| Repo | Branch | Local HEAD | Remote HEAD | Ahead | Dirty | Untracked |
|------|--------|-----------|-------------|-------|-------|-----------|
| julia_core | main | 0d72b05 | b5d2c13 | +1 | 3 (test data,vision.py) | 2 (gap_analysis,vision_refs) |
| julia_ai_assistant | feature/voice-contract-v1 | 3674209 | 3674209 | 0 | 1 (diary) | 4 (test data,experiments) |
| julia_electron_v2 | codex/bugfix/electron-c10-c11-projection | 12fd0fb | 43aef03 | +3 | 1 (app.js +17 voiceSyncTimer) | 0 |
| Julia-Voice-S2S | feature/voice-c1b-workspace-reconcile | 49ef5ba | 49ef5ba | 0 | 0 | 0 |

### CRITICAL FINDINGS:
- **julia_electron_v2**: 3 local-only commits (12fd0fb, 9fcefc4, 1541f98) NOT on remote. Remote has different tip (43aef03).
- **julia_electron_v2**: +17 unauthorized unstaged lines (voiceSyncTimer) in app.js
- **julia_core**: 1 unauthorized untracked doc (CLIENT_CONVERGENCE_GAP_ANALYSIS.md)
- **Julia-Voice-S2S**: Clean, synced with remote

---

## FRA-B: DOCUMENT INVENTORY (KEY DOCS ONLY)

### NORMATIVE ARCHITECTURE
| Document | Declared Status | Assessment |
|----------|----------------|------------|
| JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0 | FROZEN — U0 amended | KEEP, REOPEN to v1.1 |
| ARCHITECTURE_INDEX.md | GOVERNED | STALE — all C-series show ⏳ but files say FROZEN |
| ARCHITECTURE_DOCUMENT_REGISTRY.md | GOVERNED | STALE — needs rebuild |

### C-SERIES CONTRACTS (all files claim FROZEN, INDEX claims ⏳)
| Contract | Status | Assessment |
|----------|--------|------------|
| C-00 Cognitive | FROZEN | 🟢 KEEP |
| C-01 Runtime | FROZEN | 🟠 REOPEN (cancellation vs CM-I05) |
| C-02 Conversation | FROZEN | 🔴 SUPERSEDE v2 (user lifecycle changed) |
| C-03 Context OS | FROZEN | 🟢 KEEP |
| C-04 Identity | FROZEN | 🟢 KEEP |
| C-05 Memory | FROZEN | 🟢 KEEP |
| C-06 Continuity | FROZEN | 🟢 KEEP |
| C-07 ModelProvider | FROZEN | 🟢 KEEP |
| C-08 Capability | FROZEN | 🟢 KEEP |
| C-09 Alignment | FROZEN | 🟢 KEEP |
| C-10 Gateway | FROZEN | 🟡 REVALIDATE implementation |
| C-11 Voice/Media | FROZEN | 🟡 REVALIDATE implementation |
| C-12 Evidence | FROZEN | 🟢 KEEP |

### CM PROGRAM
| Document | Declared Status | Assessment |
|----------|----------------|------------|
| CM-Core Contract v1.0 | FROZEN | 🟢 SEMANTICS KEEP, 🟠 CLEAN STATUS APPENDIX |
| CM-00 Reality Map | DRAFT IN PROGRESS | KEEP AS EVIDENCE |
| CM-00 Authority Graph | DRAFT IN PROGRESS | KEEP AS EVIDENCE |
| CM-00 Conflict Register | DRAFT IN PROGRESS | KEEP AS EVIDENCE |
| CM-SPIKE-01 | COMPLETE | KEEP AS EVIDENCE |
| CM-STORAGE-V2-DECISION | DECIDED | KEEP |
| CONVERSATION_V2_BASELINE | FROZEN BASELINE | 🔴 FALSE CLAIMS (Electron/Voice CLOSED) |
| EC00_ELECTRON_DELTA_AUDIT | COMPLETE | KEEP AS EVIDENCE |
| VC00_VOICE_DELTA_AUDIT | COMPLETE | KEEP AS EVIDENCE |
| VC02/04/05 Verification | VERIFIED | 🔴 FALSE — product doesn't work |

### DOCUMENTS TO ARCHIVE/SUPERSEDE
| Document | Assessment |
|----------|------------|
| VOICE_C1B_L | Already SUPERSEDED ✅ |
| JULIA_CORE_PRINCIPLES | Already SUPERSEDED by Unified Architecture |
| ARCH-R0_AUTHORITY_MAP | Already SUPERSEDED |
| ARCHITECTURE_OVERVIEW | Already SUPERSEDED |
| CONTEXT_OS_DESIGN | Old design, superseded by C-03 |
| MEMORY_OS_DESIGN | Old design, superseded by C-05 |
| PERSONA_ENGINE_DESIGN | Old design, superseded by C-04 |
| CONTINUITY_OS_DESIGN | Old design, superseded by C-06 |
| ALIGNMENT_OS_DESIGN | Old design, superseded by C-09 |
| VOICE_OS_DESIGN | Old design, superseded by C-11 |
| M3.3.0_FINAL_FREEZE_REPORT | Unknown relevance |
| FINAL_ACCEPTANCE_EVIDENCE | FALSE — claims AT-01~AT-17 ALL PASS |
| CLIENT_CONVERGENCE_GAP_ANALYSIS | UNAUTHORIZED — DELETE-CANDIDATE |

---

## FRA-C: NORMATIVE CONFLICT REGISTER

### C-C001: C-02 vs CM-Core vs R1-B — User Message Lifecycle
```
C-02 v1 §6:   user: pending → completed | failed
CM-Core I05:  user durable before ACK, assistant failure ≠ user failure
R1-B code:    user: completed immediately, never failed on cognition exception
STATUS: CONFIRMED CONFLICT — C-02 v1 superseded by CM-Core
```

### C-C002: C-02 §10 vs VoiceWorkspace
```
C-02 §10 forbids: VoiceHistoryStore
Golden code: VoiceWorkspace stores completed user_content + assistant_content
STATUS: CODE VIOLATES CONTRACT — but contract itself may need v2
```

### C-C003: C-02 §11 vs flushVoiceWorkspace
```
C-02 §11 forbids: client sending local history as canonical truth
Golden code: flushVoiceWorkspace → commitExternalTurns → Core atomic append
STATUS: CODE VIOLATES CONTRACT — this is the Voice→Text bridge
```

### C-C004: ARCHITECTURE_INDEX vs C-*.md files
```
INDEX: all C-00~C-12 = ⏳ (not frozen)
FILES: all C-*.md = Status: FROZEN
STATUS: INDEX IS STALE — files claim FROZEN authority
```

### C-C005: CONVERSATION_V2_BASELINE vs Reality
```
BASELINE: Electron Convergence CLOSED, Voice Convergence CLOSED
REALITY: Voice→Text broken, Julia no session context
STATUS: BASELINE DOCUMENT IS FALSE
```

### C-C006: cancel_streaming_turn vs R1-B
```
conversation_runtime.py:326: user_msg status = "failed"
R1-B design: user unchanged on turn cancel
STATUS: INTERNAL CODE INCONSISTENCY
```

---

## FRA-D: CODE/CONTRACT COMPLIANCE

### ConversationRuntime (julia_core)
| Invariant | Location | Status | Evidence |
|-----------|----------|--------|----------|
| CM-I05 durable user | _accept_user_turn_locked | PASS | status=completed before return |
| CM-I05 durable user | begin_turn_streaming | PASS | status=completed, R1-B comment |
| CM-I05 durable user | cancel_streaming_turn:326 | FAIL | marks user=failed |
| CM-I12 full history | get_canonical_history | PASS | no fixed-N cap |
| CM-I19 idempotent | _accept_user_turn_locked | PASS | same turn_id+content → replay |
| CM-I19 conflict | _accept_user_turn_locked | PASS | different content → TurnConflictError |

### Brain (julia_ai_assistant)
| Requirement | Location | Status | Evidence |
|-------------|----------|--------|----------|
| Voice→native_stream | openai_compat.py:58 | PASS | conversation_id present → Core |
| external_history ignored | openai_compat.py | PASS | not passed to native_stream |
| User durable before cognition | begin_turn_streaming | PASS | R1-B code path |

### Electron (julia_electron_v2)
| Requirement | Location | Status | Evidence |
|-------------|----------|--------|----------|
| Core-first create | main.js IPC handler | PASS | createConversationViaCore |
| conversation_id transport | bootstrapVoiceWorkspace | PASS | sends conversationId to Voice |
| Voice→Text projection | app.js:194-200 | READY | listens julia.voice.transcript |
| Voice→Text projection | VOICE FRONTEND | FAIL | sends julia.voice.live-message (different type!) |

### Voice Frontend (AutoDL deployed)
| Requirement | Location | Status | Evidence |
|-------------|----------|--------|----------|
| ASR final → Core | S2S→Brain path | PASS | begin_turn_streaming |
| VoiceWorkspace history | voice-workspace.js | FAIL | stores completed turns |
| flush→Core | flushVoiceWorkspace | FAIL | C-02 §11 violation |

---

## FRA-E: RUNTIME PROVENANCE

| Layer | PID | Code Source | Status |
|-------|-----|-------------|--------|
| Brain :18089 | 36870 | julia_ai_assistant + julia_core PYTHONPATH | RUNNING |
| Electron | 67826 | julia_electron_v2 (cwd verified) | RUNNING |
| S2S :8765 | AutoDL | speech-to-speech 0.2.12 (PyPI) | RUNNING |
| Frontend :7860 | AutoDL | GOLDEN frontend files (main.js 22033fd3) | UNKNOWN — AutoDL unreachable |

---

## FRA-F: UNKNOWN / QUESTION REGISTER

Q-001: Why does julia_electron_v2 have 3 local-only commits not on remote?
Q-002: What code does Frontend :7860 actually run? (AutoDL disconnected during audit)
Q-003: Does Brain import julia_core from /Users/admin/julia_core or from a frozen copy?
Q-004: Is cancel_streaming_turn:326 actually called in Voice path?
Q-005: Does the 1008 "All slots in use" error come from S2S session leak?
Q-006: Which contract takes precedence: C-02 v1 or CM-Core?
Q-007: Does ARCHITECTURE_INDEX reflect actual freeze state or aspirational state?
Q-008: Is CONVERSATION_V2_BASELINE.md intentionally false or stale?

---

## FRA-G: PRELIMINARY DISPOSITION

### KEEP (Architecture Correct)
- Unified Architecture v1.0 (reopen to v1.1 for turn lifecycle update)
- C-00, C-03, C-04, C-05, C-06, C-07, C-08, C-09, C-12
- CM-Core Invariants (I01-I20)
- Voice Supervisor
- Operations Runbooks

### REOPEN (Needs Amendment)
- C-01 (cancellation vs CM-I05)
- C-10 (implementation never verified)
- C-11 (implementation never verified)
- Unified Architecture (turn lifecycle stale)

### SUPERSEDE (Replace with v2)
- C-02 → generate C-02 v2 from CM-Core

### REVOKE (False Claims)
- CONVERSATION_V2_BASELINE: "Electron CLOSED" → FALSE
- CONVERSATION_V2_BASELINE: "Voice CLOSED" → FALSE
- VC02/04/05 "VERIFIED" → FALSE
- E2E "27/27 PASS" → RECLASSIFY as integration tests

### DELETE-CANDIDATE
- CLIENT_CONVERGENCE_GAP_ANALYSIS.md (unauthorized)
- FINAL_ACCEPTANCE_EVIDENCE.md (false claims)

### HISTORICAL/ARCHIVE
- Old subsystem designs (CONTEXT_OS_DESIGN, MEMORY_OS_DESIGN, etc.)
- VOICE_C1B-R, VOICE_C1B-L (already marked SUPERSEDED)
- Old API contracts (LEGACY-CONTRACT, revalidation required)

---

## FRA-H: DECISIONS REQUIRED FROM TONY

1. Is C-02 v1 officially superseded by CM-Core?
2. Should ARCHITECTURE_INDEX be rebuilt immediately?
3. Should unauthorized app.js +17 lines be reverted?
4. Should CONVERSATION_V2_BASELINE be revoked?
5. Should unauthorized CLIENT_CONVERGENCE_GAP_ANALYSIS.md be deleted?
6. Should the 3 local-only Electron commits be pushed or discarded?
7. Which contract takes precedence for Voice turn lifecycle?
8. Confirm: ARCHITECTURE_INDEX or C-*.md files — which reflects true freeze state?

