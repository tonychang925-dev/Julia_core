# Wave5 AT-04-R1 Sabotage Evidence — Voice Reconnect UUID Identity

Status: R1 GREEN / IA HOLD / FREEZE NOT READY
Date: 2026-08-22
Scope: AT-04 voice reconnect canonical turn identity sabotage evidence
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Base remediation commit: `e966375`

## 1. Scope Lock

R1 validates attacks against the AT-04 identity boundary after minimal remediation.

Included:

```text
reused turn_id attack
unknown/stale conversation_id attack
transport/session identity spoof
fresh runtime recovery collision check
```

Excluded:

```text
AT-04 IA
AT-04 Freeze
AT-05 retry idempotency
voice architecture redesign
S2S/TTS/reconnect UX expansion
```

## 2. R1 Test Artifact

```text
tests/wave5/test_at04_voice_reconnect_uuid_identity.py
```

## 3. R1 Test Coverage

| TC | Validation target | Result |
|---|---|---:|
| TC-AT04-R1-001 | repeated reconnect simulation uses distinct canonical turn_id | PASS |
| TC-AT04-R1-002 | same turn_id + same content is idempotent retry / no duplicate | PASS |
| TC-AT04-R1-003 | same turn_id + different content conflicts on all backends | PASS |
| TC-AT04-R1-004 | stale reconnect conversation_id rejects / no ghost conversation | PASS |
| TC-AT04-R1-005 | transport/session ids cannot be canonical turn_id authority | PASS |
| TC-AT04-R1-006 | fresh runtime recovery preserves collision-free turn identity | PASS |

## 4. R1 Command

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at04_voice_reconnect_uuid_identity.py
```

Result:

```text
8 passed in 0.18s
```

## 5. Focused Regression Bundle

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at04_voice_reconnect_uuid_identity.py \
  tests/wave5/test_at04_turn_conflict_remediation.py \
  tests/wave5/test_at04_unknown_conversation_reject.py \
  tests/wave5/test_at03_text_voice_text.py \
  tests/wave5/test_at03_integration_acceptance.py \
  tests/test_voice_turn_reconciliation.py \
  tests/test_conversation_authority.py
```

Result:

```text
63 passed in 1.08s
```

## 6. R1 Gate Decision

```text
AT-04-R1 sabotage evidence: GREEN
AT-04 IA: HOLD
AT-04 Freeze: NOT READY
```

Next allowed step:

```text
AT-04 Integration Acceptance
```
