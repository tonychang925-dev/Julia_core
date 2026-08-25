# Julia Phase 5 — Authority Reconciliation Register v1.0

**Status:** GOVERNANCE EVIDENCE / G-AR PASS  
**Date:** 2026-08-11  
**Purpose:** prevent historical Git/doc/test claims from being mistaken for current deployed production authority.

## Evidence classes

```text
REMOTE_GIT_EVIDENCE
LOCAL_GIT_EVIDENCE
LOCAL_WORKTREE_EVIDENCE
DEPLOYED_ARTIFACT_EVIDENCE
LIVE_RUNTIME_EVIDENCE
HUMAN_BEHAVIOR_EVIDENCE
CONVERSATION/LIBRARY_HISTORICAL_EVIDENCE
```

No class substitutes for another without explicit equivalence proof.

## Reconciled records

| ID | Prior claim/artifact | New status | Current authority statement |
|---|---|---|---|
| AR-001 | `b2c7567` Voice Golden baseline | HISTORICAL/RECOVERY GOLDEN | Attested recovery baseline; not current live frontend |
| AR-002 | current deployed path under `/golden/` | DEPLOYED ARTIFACT | Current live frontend is C1B-R/49ef5ba-generation transitional artifact |
| AR-003 | old C2-04 Voice barge-in → CRT cancel | SUPERSEDED | Current pre-RMD-3 live route does not yet prove CRT cancellation |
| AR-004 | old C2-05 Golden user-loss attribution | SUPERSEDED AS GOLDEN ATTRIBUTION | Historical native CRT cancel defect confirmed and fixed by RMD-1 |
| AR-005 | `bc05c332` Voice Convergence CLOSED | HISTORICAL ACCEPTANCE | Does not establish current Voice→CRT production convergence |
| AR-006 | `ee37a283` Conversation V2 baseline CLOSED | HISTORICAL ACCEPTANCE | Core authority work is evidence; Voice convergence claims superseded by later forensics |
| AR-007 | `b5d2c137` E2E 27/27 PASS | HISTORICAL ACCEPTANCE | Test success under prior path assumptions; not current production authority |
| AR-008 | `speech-to-speech==0.2.12` live handler | DEPLOYED ARTIFACT EVIDENCE | PID 2118 / Python 3.10 / handler hash attested by WB-JA-08 |
| AR-009 | S2S session metadata propagation | LIVE RUNTIME EVIDENCE | session accepts conversation_id metadata, but handler currently omits it from Brain request |
| AR-010 | S2S cancel behavior | DEPLOYED SOURCE EVIDENCE | MARKS_STALE_ONLY; explicit active HTTP cancellation not proven until RMD-3G |

## Binding rule

Terms such as `Golden`, `current`, `HEAD`, `main`, `production`, `PASS`, and `CLOSED` are invalid in Phase 5 evidence unless accompanied by the relevant Version Authority Envelope or evidence-class qualifier.

## Gate verdict

```text
G-AR: PASS

Reason:
- known conflicting acceptance records are reclassified;
- live/deployed/source evidence is separated;
- WB-JA-08 closes the remaining S2S deployed-source identity ambiguity.
```
