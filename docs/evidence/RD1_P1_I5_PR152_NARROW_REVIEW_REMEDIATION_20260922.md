# RD1-V1 P1-I5 — PR152 Narrow Review Remediation

## Candidate

- TASK_ID: `P1-I5-PR152-NARROW-REVIEW-REMEDIATION-P0`
- PR: `#152`
- Reviewed base head: `357fcd6b621b943a6cd8dd9c5ae2af2ccbf49b1e`

## Corrections

- Review `4069761519`: ingress-focused tests now explicitly stub the Core cold-start seam and run with `DEEPSEEK_API_KEY` unset. Production initialization still checks the real credential and fails closed.
- Review `4069761525`: production initialization is serialized with an `RLock`. The sticky attempted state is assigned only after a terminal failure, while successful construction and registration remain under the lock. Concurrent callers receive the same provider binding.
- Review `4069761537`: DeepSeek content must be a non-whitespace string. Empty, space, newline, and tab outputs all fail closed.
- Review `4069761544`: no code change or scope expansion. The provider remains transitional Core Context OS message ingress; ProviderExecutionEnvelopeV2 runtime cutover is not claimed or implemented by PR152 and requires owner disposition.

## Verification

Credential-unset focused suite:

```text
env -u DEEPSEEK_API_KEY /opt/miniconda3/bin/python -m pytest \
  tests/providers/test_deepseek_cognition_provider.py \
  tests/public/test_rd1_core_public_conversation_ingress_p0.py \
  tests/public/test_rd1_market_public_composition_binding.py -q

27 passed in 0.50s
```

Concurrency regression:

- `test_concurrent_initialization_has_one_terminal_provider_result`
- Eight concurrent callers blocked while one provider constructor was in flight.
- Result: no errors, one construction, one production binding, eight identical provider references.

Whitespace regression:

- Inputs `""`, `" "`, `"\n"`, and `"\t"` all raise `DeepSeekCognitionProviderError`.
- No fallback or completed Assistant response is produced.

NCF:

```text
NCF_GATE = PASS
P0_NEW = 0
P1_NEW = 0
P2_NEW = 0
BASELINE_EXPANDED = NO
```

## Real Smoke

- Canonical Assistant path: `/private/tmp/rd1_i5_market_only_e2e_20260921_0925/assistant/voice_api`
- Query: `查一下 600519 今天的行情`
- Conversation create: HTTP `200`
- Turn: HTTP `200`, status `completed`
- Real DeepSeek request count: `1`
- Provider response SHA-256: `3cddadd0a3ff93058b24050e2ff06afec12eebcffb07a02fb083d938b5d42ff1`
- Assistant direct LLM call: `NO`
- Final response nonempty: `YES`
- Pass-1 `FINAL_TEXT`: observed and recorded; no cognition-policy correction attempted.
- Raw sanitized summary: `/private/tmp/pr152_real_deepseek_smoke.json`
