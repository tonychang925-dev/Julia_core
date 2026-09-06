# RD1-L1-R10-F1 Market Read → Research Context Projection Closure

## Authorization

`EXPLICIT_TONY_GO_R10_F1_MARKET_READ_TO_RESEARCH_CONTEXT_PROJECTION_CONTRACT_CLOSURE`

## Identity and Scope

- Core base SHA: `6c2975da1a476c04e896fe868b3df4d50f146f45`
- Core source-closure SHA: `b9d1e396a71c3d270371c232be0868b76e6e5824`
- Final head SHA: the exact SHA of this report-only commit, returned as `CORE_HEAD_SHA`; a commit cannot embed its own final hash without changing that hash.
- Production files changed: 1
  - `julia_core/runtime/research_continuation.py`
- Test files changed: 1
  - `tests/runtime/test_r10_f1_market_context_projection.py`
- Market production files changed: 0
- D1, Assistant, Client, and Voice files changed: 0
- New capabilities, result families, evidence families, and workflow runtimes: 0

## Contract Shapes

The frozen Market read payload contains:

```text
event
theme_relations
missing_fields
```

The projection accepts only that payload envelope. `missing_fields` is validated
as a bounded array of strings, deliberately excluded from the frozen research
context, and never used to fabricate event data.

The exact event whitelist is:

```text
event_id
event_type
summary
direction
confidence
occurred_at
title
source_category
source_name
source_url
source_trace_id
news_id
```

The exact relation whitelist is:

```text
subject_key
subject_name
relation_type
confidence
match_reason
evidence
source
source_trace_id
updated_at
```

## Projection Rule

`SameTurnResearchContinuation` now calls the narrow
`_project_market_read_payload()` helper after a successful Market read and
before `MarketEventResearchAdapter.validate_context()`.

The helper:

- requires the selected resolver event ID and payload event ID to match exactly;
- copies only frozen event and relation fields;
- explicitly removes the known Market relation transport extras `created_at`
  and `run_id`;
- converts bounded numeric-string confidence values to numeric values at the
  projection boundary without synthesizing or defaulting any value;
- preserves nullable event values and an empty relation list;
- retains `source_trace_id`, `source_name`, `source_url`, and `news_id`;
- rejects missing required fields, event-ID drift, malformed `missing_fields`,
  and every unapproved semantic field;
- returns only the strict `{event, theme_relations}` Core context.

`MarketEventResearchAdapter._parse_event()` and `_parse_relation()` remain
unchanged and continue to reject unknown fields and invalid required values.
Projection compatibility does not weaken adapter validation.

## Verification

Focused R10-F1 fixture coverage proves:

- realistic Market read envelope → projection → adapter validation →
  `research.event.enrich` request construction;
- event ID and provenance ID `215257`;
- relation extras `created_at` and `run_id` are excluded;
- `missing_fields` is excluded from the frozen context;
- empty relations remain valid;
- an unapproved semantic field fails closed;
- event-ID mismatch fails closed;
- missing required event and relation fields fail closed;
- direct adapter unknown-field rejection remains strict.

Required regression command:

```text
/opt/miniconda3/bin/pytest -q \
  tests/runtime/test_i4_same_turn_research_orchestration.py \
  tests/runtime/test_i1_streaming_capability_continuation.py \
  tests/research/test_c1_research_event_enrichment.py \
  tests/research/test_c2_preliminary_research_judgment.py \
  tests/runtime/test_l1_f2_deterministic_research_desk_ingress.py \
  tests/runtime/test_r10_f1_market_context_projection.py
``+

Result: `104 passed`.

Static checks:

```text
python -m compileall -q \
  julia_core/runtime/research_continuation.py \
  tests/runtime/test_r10_f1_market_context_projection.py
git diff --check
```

Both passed before the source-closure commit.

## Execution Counters

```text
USER_TURNS = 0
REAL_RESOLVER_EXECUTIONS = 0
MARKET_EVENT_READ_EXECUTIONS = 0
REAL_DB_QUERIES = 0
DB_WRITES = 0
D1_EXECUTIONS = 0
C1_EXECUTIONS = 0
C2_EXECUTIONS = 0
RETRY = 0
FALLBACK = 0
```

Only deterministic in-process fixtures were executed.

## Verdict

```text
R10_F1_READY_TO_CLOSE = YES
R10_REPROBE_READY = YES
R10_REPROBE_AUTHORIZED = NO
VERDICT = PASS
```
