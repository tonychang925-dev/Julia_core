# Wave5 AT-06-R1 Sabotage Evidence — Cross-conversation Isolation

Status: R1 GREEN
Date: 2026-08-22
Scope: AT-06 — Cross-conversation sabotage
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Base contract: `docs/authority/WAVE5_AT06_R0_CROSS_CONVERSATION_SABOTAGE_CONTRACT.md`
Remediation: `docs/project_control/reports/WAVE5_AT06_MINIMAL_REMEDIATION_EVIDENCE.md`

## 1. Checkpoint

```text
AT-06 Audit: COMPLETE
AT-06 R0 Contract: READY FOR FREEZE
AT-06 Minimal P0 Remediation: GREEN
AT-06 R1 Permanent Sabotage Evidence: GREEN
AT-06 IA: HOLD
AT-06 Freeze: NOT READY
```

## 2. R1 Purpose

AT-06-R1 proves that attacks against canonical conversation isolation cannot make foreign conversation content provider-visible after the minimal Context OS remediation.

Frozen rule:

```text
Conversation boundary is a canonical isolation boundary.
```

Model-visible rule:

```text
foreign conversation history / search candidate / cache item
  ≠
current conversation context authority
```

## 3. Permanent Test Artifact

Added:

```text
tests/wave5/test_at06_cross_conversation_sabotage.py
```

## 4. Test Case Coverage

| Test Case | Target | Status |
|---|---|---|
| TC-AT06-R1-001 | foreign history injection cannot become provider-visible | GREEN |
| TC-AT06-R1-002 | foreign retrieval/search candidate cannot be used as current transcript | GREEN |
| TC-AT06-R1-003 | unscoped history/cache item cannot default to active conversation | GREEN |
| TC-AT06-R1-004 | client/session cache contamination cannot enter active context | GREEN |
| TC-AT06-R1-005 | empty ActiveTail does not fallback to unsafe caller history | GREEN |
| TC-AT06-R1-006 | storage A/B marker isolation through canonical reads and recovery | GREEN |
| TC-AT06-R1-007 | search marker-specific query returns only matching conversation handle | GREEN |
| TC-AT06-R1-008 | runtime interaction cache remains conversation scoped | GREEN |

## 5. Evidence Commands

### AT-06 R1 permanent sabotage tests

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at06_cross_conversation_sabotage.py
```

Observed result:

```text
8 passed in 0.19s
```

### AT-06 remediation + R1 bundle

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at06_context_boundary_remediation.py \
  tests/wave5/test_at06_cross_conversation_sabotage.py
```

Observed result:

```text
13 passed in 0.16s
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
  tests/test_voice_turn_reconciliation.py \
  tests/test_conversation_authority.py
```

Observed result:

```text
88 passed in 1.66s
```

## 6. R0 Invariant Mapping

| R0 Invariant | R1 Evidence |
|---|---|
| AT06-I01 conversation boundary is canonical isolation boundary | TC-AT06-R1-001, 006, 008 |
| AT06-I02 storage read/recovery scoped by conversation_id | TC-AT06-R1-006 |
| AT06-I03 search results are derived candidates, not current-conversation authority | TC-AT06-R1-002, 007 |
| AT06-I04 context preparation scoped by canonical conversation identity | TC-AT06-R1-001, 003, 005 |
| AT06-I05 caller-supplied history is not authority | TC-AT06-R1-001, 003, 004, 005 |
| AT06-I06 Context OS preserves boundary after retrieval/candidate mistakes | TC-AT06-R1-002 |
| AT06-I07 Electron/client/session cache is not canonical history or Context OS input authority | TC-AT06-R1-004 |
| AT06-I08 runtime/interaction caches scoped by conversation_id | TC-AT06-R1-008 |
| AT06-I09 provider-visible context contains no foreign marker | TC-AT06-R1-001, 002, 003, 004, 005 |
| AT06-I10 fresh runtime/repository recovery preserves A/B isolation | TC-AT06-R1-006, 008 |

## 7. Key Findings Proven by R1

### 7.1 Foreign history injection fails closed

Conversation B preparation with mixed A+B history admits only B messages. A marker is absent from provider-visible output, and boundary provenance records the drop.

### 7.2 Search/retrieval candidates cannot become current transcript authority

A derived search candidate carrying `conversation_id=A` cannot seed conversation B's provider-visible history. The rendered messages contain only the system situation frame and the current B user prompt.

### 7.3 Missing conversation scope is not implicit permission

Unscoped caller-supplied history is not treated as belonging to the active conversation. Active conversation preparation drops unscoped history rather than defaulting it to B.

### 7.4 Client/session cache contamination is blocked

A simulated Electron/session cache containing A+B items cannot leak A marker into B. B-scoped cache item remains eligible; A-scoped cache item is dropped.

### 7.5 Empty ActiveTail has no unsafe fallback

If all supplied history is foreign or unscoped, admitted ActiveTail is empty and provider-visible output does not fall back to unsafe caller history.

### 7.6 Storage and recovery remain isolated

After fresh repository/runtime recovery, conversation A reads A marker only and conversation B reads B marker only.

### 7.7 Search marker-specific behavior is preserved

Marker-specific search returns only the matching conversation handle. Broad search may return both handles, but it remains a derived result list, not current-conversation context authority.

### 7.8 Runtime interaction cache remains conversation-scoped

Interaction state for A does not seed B, including after fresh runtime rebuild from canonical repository.

## 8. Non-Goals Preserved

R1 did not enter:

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

## 9. Gate Decision

```text
AT-06 R1 Permanent Sabotage Evidence: GREEN
AT-06 Integration Acceptance: NEXT
AT-06 Freeze: NOT READY
```
