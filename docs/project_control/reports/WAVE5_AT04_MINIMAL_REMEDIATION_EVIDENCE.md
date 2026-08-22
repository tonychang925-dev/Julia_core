# Wave5 AT-04 Minimal Remediation Evidence

Status: MINIMAL REMEDIATION GREEN / R1 GREEN / IA GREEN / FROZEN
Date: 2026-08-22
Scope: AT-04 P0-GAP-1 and P0-GAP-2 only
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Base checkpoint: `a59d625`

## 1. Scope Lock

This remediation fixes only:

```text
P0-GAP-1 turn_id conflict fail closed
P0-GAP-2 unknown/stale conversation_id reject
```

Explicitly not included:

```text
AT-04 R1 sabotage evidence
AT-04 IA
AT-04 freeze
AT-05
voice architecture redesign
S2S/TTS/reconnect UX expansion
```

## 2. Root Cause

### P0-GAP-1

`StorageV2ConversationRepository.append_external_turns_atomic()` treated any existing `turn_id` as idempotent skip without comparing incoming content/modality/assistant status against canonical messages.

### P0-GAP-2

`ConversationRuntime._accept_user_turn_locked()` auto-created a conversation when `conversation_id` was unknown. Because `process_turn()` delegates user acceptance to this method, reconnect/turn ingestion could manufacture ghost canonical truth.

## 3. Minimal Fix Applied

### Code changes

```text
julia_core/conversation_state/storage_v2_repository.py
```

- Added existing-turn comparison before idempotent skip.
- Same turn + identical content/modality/status remains idempotent.
- Same turn + different content/status raises `TurnConflictError`.

```text
julia_core/runtime/conversation_runtime.py
```

- Unknown `conversation_id` in user turn ingestion now raises `ConversationNotFoundError`.
- Removed implicit create from turn ingestion path.
- Explicit `create_conversation()` remains the governed creation path.

### Test changes

```text
tests/wave5/test_at04_turn_conflict_remediation.py
tests/wave5/test_at04_unknown_conversation_reject.py
tests/test_conversation_authority.py
```

- Added remediation tests for P0-GAP-1/P0-GAP-2.
- Updated legacy authority fixture to explicitly create known conversations instead of relying on `process_turn()` auto-create side effects.

## 4. Pre-Fix Evidence

Initial remediation tests before implementation:

```text
4 failed, 3 passed
```

Failures mapped to:

- StorageV2 did not raise conflict on same `turn_id` + different content.
- StorageV2 did not raise conflict on same user + changed assistant content.
- `process_turn()` did not reject unknown `conversation_id`.
- `accept_user_turn()` did not reject unknown `conversation_id`.

## 5. Verification Evidence

### Remediation tests

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at04_turn_conflict_remediation.py \
  tests/wave5/test_at04_unknown_conversation_reject.py
```

Result:

```text
7 passed in 0.13s
```

### AT-03 wave5 regression

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at03_text_voice_text.py \
  tests/wave5/test_at03_integration_acceptance.py
```

Result:

```text
9 passed in 0.16s
```

### Voice reconciliation regression

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q tests/test_voice_turn_reconciliation.py
```

Result:

```text
15 passed in 0.08s
```

### Legacy authority regression after explicit-create fixture update

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q tests/test_conversation_authority.py
```

Result:

```text
24 passed in 0.64s
```

### Focused Wave5/authority bundle

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at04_turn_conflict_remediation.py \
  tests/wave5/test_at04_unknown_conversation_reject.py \
  tests/wave5/test_at03_text_voice_text.py \
  tests/wave5/test_at03_integration_acceptance.py \
  tests/test_voice_turn_reconciliation.py \
  tests/test_conversation_authority.py
```

Result:

```text
55 passed in 0.82s
```

### StorageV2 / cutover / management regression

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/rt2_r2/test_storage_v2_repository.py \
  tests/rt2_r2/test_cutover.py \
  tests/test_conversation_management_service.py
```

Result:

```text
42 passed in 0.72s
```

### Compile check

```bash
/opt/miniconda3/bin/python -m compileall -q julia_core tests
```

Result:

```text
compileall_exit=0
```

## 6. Gate Position After Remediation

```text
AT-04 Minimal Remediation: GREEN
AT-04 R1: GREEN
AT-04 IA: GREEN
AT-04 Freeze: FROZEN
```

Next allowed step:

```text
AT-04-R1 sabotage evidence
```

Only after this remediation commit is reviewed/accepted.
