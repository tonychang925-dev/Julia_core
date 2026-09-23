# RD1 P1-I5 — Structured Tool Invocation Real Rerun

- TASK_ID: `P1-I5-STRUCTURED-TOOL-INVOCATION-CONTRACT-CLOSURE-P0`
- Base: `cb507e6e96eeb2730b74e5587e5d638c450a6453`
- Query: `查一下 600519 今天的行情`

## Implementation

- The single structured invocation policy now defines the exact `request_envelope` and a stock-quote example.
- Context OS requires usable `name` and `arguments` envelope semantics before cognition.
- Decode-failure retries project `expected_invocation_protocol` from the validated parent policy.
- Retry continuations retain the original capability catalog and input schemas.
- The strict parser remains unchanged and performs no malformed-call repair or capability aliasing.

## Verification

```text
/opt/miniconda3/bin/python -m pytest \
  tests/runtime/test_structured_tool_invocation_contract.py \
  tests/runtime/test_r2_p3_context_os_typed_projection.py \
  tests/runtime/test_rd1_p2_i3b_production_iterative_reasoning_loop.py -q

55 passed in 0.32s
```

```text
git diff --check
PASS
```

## Real Product Rerun

- Conversation: `conv_p1_i5_structured_20260923`
- Turn: `turn_p1_i5_structured_20260923`
- Canonical current user `created_at`: `2026-09-23T17:40:22.195275+08:00`
- Model-visible temporal projection:
  - `current_turn_timestamp`: `2026-09-23T17:40:22.195275+08:00`
  - `current_date`: `2026-09-23`
  - `utc_offset`: `+08:00`
- Model-visible invocation contract included:
  - `request_envelope.name`: exact capability ID
  - `request_envelope.arguments`: capability-only argument object
  - `market.stock.quote.read`
  - `stock_id` and `trade_date` schemas

### Cognition Passes

| Pass | Mechanical result | Evidence |
|---|---|---|
| 1 | `TOOL_CALL_CONTROL_FAILURE / INVALID_CALL_SHAPE` | Valid JSON was embedded after prose; no execution |
| 2 | `TOOL_CALL_CONTROL_FAILURE / INVALID_CALL_SHAPE` | Tool call example inside prose; no execution |
| 3 | `TOOL_CALL_CONTROL_FAILURE / INVALID_CALL_SHAPE` | Placeholder `YYYY-MM-DD`; no execution |
| 4 | `EXACTLY_ONE_STRUCTURED_CALL` | `market.stock.quote.read`, `600519.SH`, `2026-09-23` |
| 5 | `FINAL_TEXT` | Fresh judgment from re-entered Market evidence |

Exact pass-4 request:

```json
{
  "name": "market.stock.quote.read",
  "arguments": {
    "stock_id": "600519.SH",
    "trade_date": "2026-09-23"
  }
}
```

### Market Result

- `operation_status`: `SUCCESS`
- `data_state`: `EMPTY`
- `payload`: `None`
- Failures: `0`
- No fallback date or substitute Market capability was used.

### Counters

- Core provider calls: `5`
- Cognition passes: `5`
- Tool-call control failures: `3`
- Structured tool calls: `1`
- Capability executions: `1`
- Stock quote calls: `1`
- Other Market calls: `0`
- Research calls: `0`
- ToolResult count: `1`
- Evidence count: `1`
- Evidence re-entry count: `1`

## Disposition

`P1_I5_REAL_PRODUCT_FLOW = PASS`

`BLOCKED_JULIA_STRUCTURED_TOOL_CONTRACT_MISUSE = RESOLVED`

No manual repair, synthetic Market response, fallback provider, cognition-policy change, Market semantic change, or merge was used.
