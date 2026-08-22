# Wave5 AT-04 IA / Final Freeze Evidence Bundle

Status: FROZEN
Date: 2026-08-22
Scope: AT-04 — Voice reconnect UUID identity
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Base lineage: `a59d625` R0 → `e966375` remediation → `30eb91e` R1

## 1. Checkpoint

```text
Wave5 Authority Boundary Set        FROZEN
AT-01 Conversation Create Durability FROZEN
AT-02 Accepted User Crash            FROZEN
AT-03 Text → Voice → Text            FROZEN
AT-04 Audit                          COMPLETE
AT-04 R0 Contract                    FROZEN
AT-04 Minimal Remediation            GREEN
AT-04 R1 Sabotage Evidence           GREEN
AT-04 Integration Acceptance          GREEN
```

## 2. Artifacts

```text
docs/project_control/reports/WAVE5_AT04_VOICE_RECONNECT_UUID_IDENTITY_AUDIT.md
docs/authority/WAVE5_AT04_R0_VOICE_RECONNECT_UUID_IDENTITY_CONTRACT.md
docs/project_control/reports/WAVE5_AT04_MINIMAL_REMEDIATION_EVIDENCE.md
docs/project_control/reports/WAVE5_AT04_R1_SABOTAGE_EVIDENCE.md
tests/wave5/test_at04_turn_conflict_remediation.py
tests/wave5/test_at04_unknown_conversation_reject.py
tests/wave5/test_at04_voice_reconnect_uuid_identity.py
tests/wave5/test_at04_integration_acceptance.py
```

## 3. IA Test Coverage

| TC | Validation target | Result |
|---|---|---:|
| TC-AT04-IA-001 | real management/runtime path creates distinct turn IDs after reconnect | PASS |
| TC-AT04-IA-002 | real retry path is idempotent and does not duplicate | PASS |
| TC-AT04-IA-003 | real conflict path rejects and preserves canonical transcript | PASS |
| TC-AT04-IA-004 | stale reconnect conversation_id is rejected via governed surface | PASS |
| TC-AT04-IA-005 | fresh recovery preserves collision-free canonical turn identity | PASS |

## 4. IA Command

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at04_integration_acceptance.py
```

Result:

```text
5 passed in 0.16s
```

## 5. Final AT-04 Focused Evidence Bundle

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at04_integration_acceptance.py \
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
68 passed in 1.06s
```

## 6. Storage / Management Regression

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/rt2_r2/test_storage_v2_repository.py \
  tests/rt2_r2/test_cutover.py \
  tests/test_conversation_management_service.py
```

Result:

```text
42 passed in 0.74s
```

## 7. Compile Check

```bash
/opt/miniconda3/bin/python -m compileall -q julia_core tests
```

Result:

```text
compileall_exit=0
```

## 8. Final Evidence Conclusion

AT-04 proves:

```text
voice reconnect / transport retry
  ↓
never obtains canonical turn identity authority
```

Confirmed boundaries:

- distinct voice utterances after reconnect use distinct canonical `turn_id` values;
- same `turn_id` + same content remains idempotent retry;
- same `turn_id` + different content fails closed;
- stale/unknown reconnect `conversation_id` cannot create ghost canonical truth;
- transport/session metadata is not canonical `turn_id` authority;
- fresh recovery preserves collision-free canonical turn identity.

## 9. Gate Decision

```text
AT-04 Integration Acceptance: GREEN
AT-04 Final Freeze Evidence: FROZEN
```

Next allowed step:

```text
AT-04 final freeze record / review acceptance
```
