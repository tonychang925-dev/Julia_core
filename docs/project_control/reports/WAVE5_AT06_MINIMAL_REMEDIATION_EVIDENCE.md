# Wave5 AT-06 Minimal P0 Remediation Evidence — Cross-conversation Sabotage

Status: MINIMAL REMEDIATION GREEN / R1 HOLD
Date: 2026-08-22
Scope: AT-06 — Cross-conversation sabotage
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Base contract: `docs/authority/WAVE5_AT06_R0_CROSS_CONVERSATION_SABOTAGE_CONTRACT.md`
Audit: `docs/project_control/reports/WAVE5_AT06_CROSS_CONVERSATION_SABOTAGE_AUDIT.md`

## 1. Checkpoint

```text
AT-06 Audit: COMPLETE
AT-06 R0 Contract: READY FOR FREEZE
AT-06 Minimal P0 Remediation: GREEN
AT-06 R1: HOLD
AT-06 IA: HOLD
AT-06 Freeze: NOT READY
```

## 2. P0 Remediated

Audit P0:

```text
ContextExecutionRuntime.prepare(conversation_id="conv_B", history=[conv_A, conv_B])
  → ALPHA_PRIVATE_MARKER_001 from conv_A became provider-visible in conv_B
```

Remediated boundary:

```text
Context OS prepare for active conversation B
  + foreign/unscoped caller-supplied history
    → quarantined before ActiveTail/model-visible rendering
    → zero A marker in B provider-visible messages
```

## 3. Code Changes

Modified:

```text
julia_core/runtime/context_execution_runtime.py
julia_core/runtime/julia_session.py
tests/wave5/test_at06_context_boundary_remediation.py
```

### 3.1 Context OS scoped active tail

`ContextExecutionRuntime.prepare(...)` now filters supplied history before ActiveTail admission:

```text
active conversation_id present:
  keep only messages whose message.conversation_id == active conversation_id
  drop foreign conversation_id
  drop unscoped caller/cache history

active conversation_id empty:
  preserve legacy unscoped history for legacy chat compatibility
```

The admitted tail is stored in:

```text
CognitiveContextPackage.active_tail_messages
CognitiveContextPackage.active_tail_turn_ids
projection_metadata["conversation_history_scoped"] = True
```

### 3.2 Provider rendering cannot fallback to unsafe caller history

`CognitiveContextPackage.to_messages(...)` now renders the package's admitted `active_tail_messages` when the package has gone through scoped conversation-history preparation.

This prevents the subtle fallback bug where an empty admitted tail could otherwise fall back to the caller-supplied mixed/unscoped history.

### 3.3 JuliaSession uses admitted package tail

`JuliaSession._prepare_turn(...)` and tool-result continuation rendering now use:

```text
pkg.to_messages(pkg.active_tail_messages, text)
delta.to_messages(delta.active_tail_messages, "")
```

instead of recomputing/rendering directly from caller/runtime `ctx.history`.

## 4. Remediation Test Artifact

Added:

```text
tests/wave5/test_at06_context_boundary_remediation.py
```

Coverage:

| Test | Target | Status |
|---|---|---|
| `test_at06_rem_p0_context_os_drops_foreign_history_before_provider_visible` | conv_B prepare drops conv_A marker before provider-visible output | GREEN |
| `test_at06_rem_p0_boundary_provenance_records_dropped_foreign_history` | boundary provenance records dropped foreign history | GREEN |
| `test_at06_rem_p0_governed_scoped_history_still_passes` | correctly scoped conv_B history still visible | GREEN |
| `test_at06_rem_p0_active_conversation_drops_unscoped_cache_history` | active conversation drops unscoped client/cache history | GREEN |
| `test_at06_rem_p0_legacy_empty_conversation_preserves_unscoped_history` | legacy empty conversation mode remains compatible | GREEN |

## 5. Evidence Commands

### AT-06 remediation tests

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at06_context_boundary_remediation.py
```

Observed result:

```text
5 passed in 0.04s
```

### Wave5 AT-03/04/05 + AT-06 remediation + authority focused bundle

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
  tests/test_voice_turn_reconciliation.py \
  tests/test_conversation_authority.py
```

Observed result:

```text
80 passed in 1.49s
```

### Context runtime regression

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/test_a221_runtime_integration.py
```

Observed result:

```text
18 passed in 0.09s
```

### Storage/runtime isolation baseline

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/test_conversation_authority.py::TestInteractionIsolation::test_cross_conversation_isolation \
  tests/test_conversation_authority.py::TestConversationIsolation::test_history_isolation \
  tests/rt2_r3/test_core_acceptance.py::test_r3_at08_conversation_isolation \
  tests/rt2_r2/test_storage_v2_repository.py::test_b_at10_cross_conversation_isolation \
  tests/spikes/test_cm_spike_01_durable_acceptance.py::test_sp07_cross_conversation_isolation
```

Observed result:

```text
5 passed in 0.18s
```

### Compile check

```bash
/opt/miniconda3/bin/python -m compileall -q \
  julia_core \
  tests/wave5/test_at06_context_boundary_remediation.py
```

Observed result:

```text
compileall_exit=0
```

## 6. Non-Evidence Note

A broader HTTP E2E test file was attempted during local regression, but `tests/e2e/test_e2e_full.py::test_e2e04` requires access to `127.0.0.1:18089` and failed under the current sandbox with:

```text
PermissionError: [Errno 1] Operation not permitted
```

That sandbox-local HTTP failure is not used as AT-06 remediation evidence. The AT-06 remediation evidence above is based on local in-process Core/Context OS tests.

## 7. Scope Control

This remediation did not change:

```text
search architecture
Electron architecture
authorization / multi-user tenancy
encryption
segment rotation
pagination
retry / reconnect semantics
provider behavior policy
```

The change is limited to:

```text
Context OS conversation-history admission boundary
JuliaSession rendering from admitted package tail
```

## 8. Gate Decision

```text
AT-06 Minimal P0 Remediation: GREEN
AT-06 R1 Permanent Acceptance: NEXT
AT-06 IA: HOLD
AT-06 Freeze: NOT READY
```
