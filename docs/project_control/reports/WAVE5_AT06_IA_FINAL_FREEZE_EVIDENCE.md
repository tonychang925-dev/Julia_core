# Wave5 AT-06 Integration Acceptance / Final Freeze Evidence — Cross-conversation Sabotage

Status: IA GREEN / FINAL FREEZE EVIDENCE READY
Date: 2026-08-22
Scope: AT-06 — Cross-conversation sabotage
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Base contract: `docs/authority/WAVE5_AT06_R0_CROSS_CONVERSATION_SABOTAGE_CONTRACT.md`
R1 evidence: `docs/project_control/reports/WAVE5_AT06_R1_SABOTAGE_EVIDENCE.md`
Remediation: `docs/project_control/reports/WAVE5_AT06_MINIMAL_REMEDIATION_EVIDENCE.md`

## 1. Checkpoint

```text
Wave5 Authority Boundary Set         FROZEN
AT-01 Conversation Create Durability  FROZEN
AT-02 Accepted User Crash             FROZEN READY
AT-03 Text → Voice → Text             FROZEN READY / evidence committed
AT-04 Voice reconnect UUID identity   FROZEN
AT-05 Retry Idempotency               FROZEN
AT-06 Cross-conversation sabotage     IA GREEN / FROZEN READY
```

## 2. IA Purpose

AT-06 IA verifies the integrated path, not only isolated sabotage helpers:

```text
ConversationManagementService create/read/search
  ↓
ConversationRuntime governed turn path
  ↓
StorageV2 canonical repository scoped by conversation_id
  ↓
retrieval / supplied context / cache simulation
  ↓
Context OS conversation-boundary admission
  ↓
provider-visible message handoff
  ↓
zero foreign conversation marker
```

IA keeps scope narrow. It does not test AT-07 segment rotation, search optimization, authorization redesign, encryption, or Electron architecture redesign.

## 3. Integration Test Artifact

Added:

```text
tests/wave5/test_at06_integration_acceptance.py
```

## 4. IA Test Case Coverage

| Test Case | Target | Status |
|---|---|---|
| TC-AT06-IA-001 | real B request with injected A history has zero A provider-visible marker | GREEN |
| TC-AT06-IA-002 | real search candidate from A cannot become B visible context | GREEN |
| TC-AT06-IA-003 | real fresh runtime/repository recovery preserves A/B isolation | GREEN |
| TC-AT06-IA-004 | real client/session cache simulation cannot become Context OS authority | GREEN |
| TC-AT06-IA-005 | real provider handoff sees only current conversation authority | GREEN |

## 5. Evidence Commands

### AT-06 IA

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at06_integration_acceptance.py
```

Observed result:

```text
5 passed in 0.22s
```

### AT-06 full evidence bundle

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at06_context_boundary_remediation.py \
  tests/wave5/test_at06_cross_conversation_sabotage.py \
  tests/wave5/test_at06_integration_acceptance.py
```

Observed result:

```text
18 passed in 0.29s
```

### Wave5 AT-03/04/05/06 + authority focused bundle

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at03_text_voice_text.py \
  tests/wave5/test_at03_integration_acceptance.py \
  tests/wave5/test_at04_voice_reconnect_uuid_identity.py \
  tests/wave5/test_at04_integration_acceptance.py \
  tests/wave5/test_at05_retry_idempotency.py \
  tests/wave5/test_at05_integration_acceptance.py \
  tests/wave5/test_at06_context_boundary_remediation.py \
  tests/wave5/test_at06_cross_conversation_sabotage.py \
  tests/wave5/test_at06_integration_acceptance.py \
  tests/test_voice_turn_reconciliation.py \
  tests/test_conversation_authority.py
```

Observed result:

```text
93 passed in 1.73s
```

### Compile check

```bash
/opt/miniconda3/bin/python -m compileall -q \
  julia_core \
  tests/wave5/test_at06_integration_acceptance.py
```

Observed result:

```text
compileall_exit=0
```

## 6. IA Findings

### 6.1 Real B request with injected A history is boundary-gated

IA creates A and B through `ConversationManagementService`, writes markers through `ConversationRuntime`, reads canonical messages through the management surface, then injects A+B history into B Context OS preparation.

Observed:

```text
BETA marker visible in B
ALPHA marker absent from B provider-visible messages
conversation_boundary provenance present
```

### 6.2 Search candidates remain non-authoritative

IA verifies `search(ALPHA)` returns A, then simulates a search/retrieval layer incorrectly passing A canonical messages to B context preparation.

Observed:

```text
A candidate exists
A marker not provider-visible in B
B marker not fabricated if B history was not supplied
no unsafe fallback
```

This proves search relevance is not current-conversation context authority.

### 6.3 Fresh runtime/repository recovery preserves A/B isolation

IA closes the first StorageV2 runtime, opens a fresh runtime/service over the same repository, and verifies:

```text
A read → ALPHA only
B read → BETA only
Context OS for B over B messages → BETA only, zero ALPHA
```

### 6.4 Client/session cache simulation is non-authoritative

IA simulates a contaminated client/session cache containing:

```text
A canonical messages
unscoped client cache secret
B canonical messages
```

When active conversation is B, observed provider-visible output contains B marker only. A marker and unscoped cache secret are absent.

### 6.5 Provider handoff receives only current-conversation authority

IA renders Context OS output and hands it to a capturing provider stub.

Observed final provider messages:

```text
ALPHA absent
BETA present
final user prompt present
all prior conversation messages scoped to B
```

This confirms the actual model-consumption surface is protected, not only internal package state.

## 7. Boundary Confirmed

AT-06 final evidence now proves:

```text
Conversation boundary is a canonical isolation boundary.
```

Expanded:

```text
storage A/B isolation
  +
search candidate non-authority
  +
Context OS admission boundary
  +
client/session cache non-authority
  +
provider-visible handoff gate
  →
zero cross-conversation marker leakage
```

## 8. Non-Goals Preserved

IA did not enter:

- AT-07 segment rotation
- AT-08 pagination
- search optimization
- vector index architecture
- multi-user authorization
- encryption
- distributed tenancy
- Electron architecture redesign
- voice architecture redesign
- provider response quality
- retry/reconnect semantics

## 9. Gate Decision

```text
AT-06 Audit: COMPLETE
AT-06 R0 Contract: READY FOR FREEZE
AT-06 Minimal P0 Remediation: GREEN
AT-06 R1 Permanent Sabotage Evidence: GREEN
AT-06 Integration Acceptance: GREEN
AT-06 Final Freeze Evidence: FROZEN READY
```

Next:

```text
AT-06 Final Freeze Record
```
